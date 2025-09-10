# AMC API Integration

## Overview
The AMC API integration is the core external dependency that enables RecomAMP to execute SQL queries against Amazon Marketing Cloud instances. This document details how we authenticate, execute queries, and handle results.

## Key Components

### Service Files
- `amc_manager/services/amc_api_client.py` - Base API client
- `amc_manager/services/amc_api_client_with_retry.py` - Retry wrapper with token refresh
- `amc_manager/api/supabase/amc_executions.py` - Execution endpoints

### Database Tables
- `amc_instances` - Stores instance configurations
- `amc_accounts` - Contains entity_id needed for API calls
- `workflow_executions` - Tracks execution status and results

## API Authentication Flow

```python
# Step 1: Get user's OAuth token from database
user = db.table('users').select('*').eq('id', user_id).execute()
encrypted_token = user.data[0]['encrypted_access_token']

# Step 2: Decrypt token
access_token = token_service.decrypt_token(encrypted_token)

# Step 3: Prepare headers for AMC API
headers = {
    "Amazon-Advertising-API-ClientId": settings.AMAZON_CLIENT_ID,
    "Amazon-Advertising-API-AdvertiserId": entity_id,  # From amc_accounts
    "Authorization": f"Bearer {access_token}"
}
```

## Critical ID Resolution

### The Instance ID Problem
```python
# ❌ WRONG - Using internal UUID causes 403 errors
instance_uuid = "550e8400-e29b-41d4-a716-446655440000"
url = f"/amc/instances/{instance_uuid}/workflows"  # FAILS

# ✅ CORRECT - Using AMC instance ID
instance_id = "amcibersblt"  # The actual AMC instance identifier
url = f"/amc/instances/{instance_id}/workflows"  # SUCCESS
```

### Entity ID Resolution
```python
# Every instance needs its associated entity_id for API calls
instance_data = db.table('amc_instances')\
    .select('*, amc_accounts(*)')\  # JOIN to get entity_id
    .eq('instance_id', instance_id)\
    .execute()

entity_id = instance_data['amc_accounts']['account_id']  # Required for headers
```

## Workflow Execution Lifecycle

### 1. Create Workflow
```python
async def create_workflow(instance_id: str, sql_query: str, parameters: dict):
    # Validate SQL against AMC rules
    validated_query = validate_amc_sql(sql_query)
    
    # Substitute parameters
    final_query = substitute_parameters(validated_query, parameters)
    
    # Create workflow via API
    response = await http_client.post(
        f"{AMC_BASE_URL}/amc/instances/{instance_id}/workflows",
        json={
            "workflowDefinition": {
                "sql": final_query,
                "outputS3URI": f"s3://bucket/{instance_id}/outputs/"
            }
        },
        headers=headers
    )
    
    return response.json()["workflowId"]
```

### 2. Create Execution
```python
async def create_execution(workflow_id: str, time_window: dict):
    response = await http_client.post(
        f"{AMC_BASE_URL}/amc/instances/{instance_id}/executions",
        json={
            "workflowId": workflow_id,
            "parameterValues": {
                "startDate": time_window["start"],  # Format: "2025-07-01T00:00:00"
                "endDate": time_window["end"]       # No 'Z' suffix!
            }
        },
        headers=headers
    )
    
    execution_id = response.json()["executionId"]
    
    # Store in database for tracking
    db.table('workflow_executions').insert({
        'workflow_id': workflow_id,
        'amc_execution_id': execution_id,
        'status': 'PENDING',
        'instance_id': instance_id
    }).execute()
    
    return execution_id
```

### 3. Poll Execution Status
```python
# Handled by execution_status_poller.py service
async def poll_status(execution_id: str):
    while True:
        response = await http_client.get(
            f"{AMC_BASE_URL}/amc/instances/{instance_id}/executions/{execution_id}",
            headers=headers
        )
        
        status = response.json()["status"]
        
        # Update database
        db.table('workflow_executions').update({
            'status': status,
            'updated_at': datetime.now()
        }).eq('amc_execution_id', execution_id).execute()
        
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
            
        await asyncio.sleep(15)  # Poll every 15 seconds
```

### 4. Download Results
```python
async def download_results(execution_id: str):
    if status == 'SUCCEEDED':
        # Get result location
        response = await http_client.get(
            f"{AMC_BASE_URL}/amc/instances/{instance_id}/executions/{execution_id}/results",
            headers=headers
        )
        
        result_url = response.json()["resultS3URI"]
        
        # Download and parse results
        results = await download_from_s3(result_url)
        
        # Store in database
        db.table('workflow_executions').update({
            'results': results,
            'row_count': len(results),
            'completed_at': datetime.now()
        }).eq('amc_execution_id', execution_id).execute()
```

## Rate Limiting & Retry Strategy

### Rate Limits
- **10 requests/second** per instance
- **100 concurrent executions** per instance
- **429 responses** include Retry-After header

### Retry Implementation
```python
# From amc_api_client_with_retry.py
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((HTTPStatusError, RequestError))
)
async def api_call_with_retry(method, url, **kwargs):
    # Automatically refresh token if 401
    if response.status_code == 401:
        new_token = await token_service.refresh_access_token(user_id)
        kwargs['headers']['Authorization'] = f"Bearer {new_token}"
        return await method(url, **kwargs)
    
    # Handle rate limiting
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        await asyncio.sleep(retry_after)
        return await method(url, **kwargs)
```

## Parameter Handling

### Large Parameter Lists
```python
# Problem: AMC has character limits for parameters
# Solution: Inject parameters directly into SQL

def handle_large_parameters(sql_query: str, campaigns: list):
    if len(campaigns) > 100:
        # Use VALUES clause injection
        values_clause = "VALUES " + ", ".join([f"('{c}')" for c in campaigns])
        
        modified_query = f"""
        WITH campaign_list AS ({values_clause})
        {sql_query.replace('@campaigns', '(SELECT * FROM campaign_list)')}
        """
        
        return modified_query
    else:
        # Standard parameter substitution
        return sql_query.replace('@campaigns', str(campaigns))
```

## Error Handling

### Common Errors and Solutions
```python
ERROR_HANDLERS = {
    "VALIDATION_ERROR": lambda e: validate_and_fix_sql(e.query),
    "THRESHOLD_NOT_MET": lambda e: suggest_broader_scope(e),
    "QUOTA_EXCEEDED": lambda e: queue_for_later_execution(e),
    "PERMISSION_DENIED": lambda e: verify_instance_access(e),
    "INVALID_DATE_FORMAT": lambda e: fix_date_format(e.dates)
}

async def handle_amc_error(error_response):
    error_type = error_response.get('errorType')
    handler = ERROR_HANDLERS.get(error_type, log_unknown_error)
    return await handler(error_response)
```

## Interconnections

### Connected Systems
1. **Authentication System** - Provides OAuth tokens
2. **Instance Management** - Supplies instance_id and entity_id
3. **Workflow Execution** - Consumes API for query execution
4. **Execution Monitoring** - Polls API for status updates
5. **Data Collections** - Uses API for batch executions
6. **Token Refresh Service** - Maintains valid tokens

### Data Flow
```
User Request → Workflow Service → AMC API Client → AMC API
                      ↓                 ↓
                Database ← Execution Monitor ← Status Updates
```

## Testing Considerations

### Mock Mode
```python
# Environment variable controls real vs mock API
AMC_USE_REAL_API = os.getenv('AMC_USE_REAL_API', 'false') == 'true'

if not AMC_USE_REAL_API:
    # Return mock responses for development
    return mock_successful_execution()
```

### Integration Tests
```python
async def test_full_execution_flow():
    # 1. Create workflow
    workflow_id = await create_workflow(test_instance, test_query)
    assert workflow_id is not None
    
    # 2. Execute workflow
    execution_id = await create_execution(workflow_id, test_params)
    assert execution_id is not None
    
    # 3. Poll until complete
    status = await poll_until_complete(execution_id, timeout=300)
    assert status in ['SUCCEEDED', 'FAILED']
    
    # 4. Verify results stored
    results = await get_execution_results(execution_id)
    assert results is not None
```

## Performance Optimizations

### Caching Strategy
```python
# Cache instance configurations
@lru_cache(maxsize=100)
def get_instance_config(instance_id: str):
    return db.table('amc_instances').select('*').eq('instance_id', instance_id).execute()

# Cache entity_id mappings
@lru_cache(maxsize=100)
def get_entity_id(account_id: str):
    return db.table('amc_accounts').select('account_id').eq('id', account_id).execute()
```

### Batch Processing
```python
# Process multiple executions efficiently
async def batch_create_executions(workflows: list):
    tasks = []
    for workflow in workflows:
        task = create_execution(workflow['id'], workflow['params'])
        tasks.append(task)
    
    # Execute concurrently with limit
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
    async with semaphore:
        results = await asyncio.gather(*tasks)
    
    return results
```

## Security Considerations

1. **Token Encryption** - All tokens stored encrypted with Fernet
2. **API Key Protection** - Client ID/Secret in environment variables
3. **Instance Access Control** - User permissions checked before API calls
4. **Audit Logging** - All API calls logged with user context
5. **Rate Limit Protection** - Prevents API abuse and quota exhaustion