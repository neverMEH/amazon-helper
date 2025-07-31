# How to Update for Real AMC Execution

## Current Problem
The `amc_execution_service.py` uses `_simulate_amc_execution()` which returns mock data instead of executing real queries.

## Solution

### 1. Replace the simulation call in `execute_workflow()`:

```python
# Current (line 78-82):
execution_result = self._simulate_amc_execution(
    instance_id=instance['instance_id'],
    sql_query=sql_query,
    execution_id=execution['execution_id']
)

# Replace with:
execution_result = self._execute_real_amc_query(
    instance_id=instance['instance_id'],
    sql_query=sql_query,
    execution_id=execution['execution_id'],
    user_id=user_id
)
```

### 2. Add the new method `_execute_real_amc_query()`:

```python
def _execute_real_amc_query(
    self,
    instance_id: str,
    sql_query: str,
    execution_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Execute real AMC query using Amazon API"""
    
    # Get user's Amazon OAuth token
    # This needs to be implemented - currently we only have local auth
    amazon_token = self._get_user_amazon_token(user_id)
    if not amazon_token:
        return {
            "status": "failed",
            "error": "No valid Amazon OAuth token found"
        }
    
    # Get entity ID for the instance
    entity_id = self._get_entity_id_for_instance(instance_id)
    
    # Create AMC execution
    from .amc_api_client import amc_api_client
    
    result = amc_api_client.create_workflow_execution(
        instance_id=instance_id,
        sql_query=sql_query,
        access_token=amazon_token,
        entity_id=entity_id
    )
    
    if not result.get('success'):
        return {
            "status": "failed",
            "error": result.get('error', 'Failed to create execution')
        }
    
    amc_execution_id = result['executionId']
    
    # Poll for completion
    max_attempts = 60  # 5 minutes max
    for attempt in range(max_attempts):
        status = amc_api_client.get_execution_status(
            execution_id=amc_execution_id,
            access_token=amazon_token,
            entity_id=entity_id
        )
        
        if status.get('status') == 'completed':
            # Get results
            results = amc_api_client.get_execution_results(
                execution_id=amc_execution_id,
                access_token=amazon_token,
                entity_id=entity_id
            )
            
            # Parse and store results
            # This would need to download from S3 and parse CSV/JSON
            
            return {
                "status": "completed",
                "amc_execution_id": amc_execution_id,
                "row_count": results.get('metadata', {}).get('rowCount', 0),
                "results_url": results.get('resultUrl')
            }
        
        elif status.get('status') == 'failed':
            return {
                "status": "failed",
                "error": status.get('error', 'Query execution failed')
            }
        
        # Update progress
        self._update_execution_progress(
            execution_id, 'running', status.get('progress', 50)
        )
        
        time.sleep(5)  # Wait 5 seconds before next check
    
    return {
        "status": "failed",
        "error": "Execution timed out after 5 minutes"
    }
```

## Required Prerequisites

### 1. Amazon OAuth Token Storage
Currently, the system only stores local JWT tokens. You need:
- Store Amazon OAuth access tokens when users log in
- Implement token refresh mechanism
- Associate tokens with users

### 2. Entity ID Mapping
Need to know which entity ID to use for each AMC instance:
- Could be stored in the `amc_instances` table
- Or retrieved from the AMC accounts

### 3. S3 Configuration
AMC requires an S3 bucket for output:
- Configure S3 bucket in settings
- Implement S3 download functionality
- Parse CSV/JSON results

### 4. Error Handling
Real API calls will have more failure modes:
- Invalid SQL syntax
- Permission denied
- Rate limiting
- Network timeouts

## Alternative: Use AMC SDK

If available, use the official AMC SDK instead of raw API calls:

```python
from amc_sdk import AMCClient

client = AMCClient(
    access_token=token,
    client_id=settings.AMAZON_CLIENT_ID
)

execution = client.create_execution(
    instance_id=instance_id,
    sql_query=sql_query
)

# Wait for completion
execution.wait_until_complete()

# Get results
results = execution.get_results()
```

## Testing Real Execution

1. First, verify AMC API access:
```python
# Test script to verify AMC API works
result = amc_api_client.create_workflow_execution(
    instance_id="amchnfozgta",  # Sandbox instance
    sql_query="SELECT COUNT(*) FROM dataset",
    access_token=valid_token,
    entity_id="ENTITYEJZCBSCBH4HZ"
)
print(result)
```

2. Start with simple queries on sandbox instances
3. Handle all error cases before production use

## Important Notes

- **Without real Amazon OAuth tokens**, the system cannot execute real queries
- **Without AMC API documentation**, the exact API format may differ
- **S3 access** is required to retrieve results
- Consider keeping simulation mode as a fallback for development/testing