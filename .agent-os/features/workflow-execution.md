# Workflow Execution System

## Overview

The workflow execution system is the core feature of RecomAMP that enables users to run AMC SQL queries against Amazon Marketing Cloud instances. It handles query execution, result processing, and status monitoring with comprehensive error handling and retry logic.

## Key Components

### Backend Services
- `amc_manager/services/workflow_service.py` - Main workflow management
- `amc_manager/services/amc_api_client_with_retry.py` - AMC API communication with retry logic
- `amc_manager/services/execution_poller.py` - Background status polling service
- `amc_manager/api/supabase/workflows.py` - API endpoints

### Frontend Components
- `frontend/src/pages/WorkflowDetail.tsx` - Workflow detail view with execution
- `frontend/src/components/ExecutionResults.tsx` - Results display
- `frontend/src/components/SQLEditor.tsx` - Monaco-based SQL editor

### Database Tables
- `workflows` - Workflow definitions and SQL queries
- `workflow_executions` - Execution history and results
- `amc_instances` - AMC instance configurations
- `amc_accounts` - Account details with entity_id

## Recent Changes (2025-09-11)

### Critical Workflow ID Handling Fix
- **Issue**: Workflows with string IDs (prefixed with 'wf_') were causing PostgreSQL UUID parsing errors (error code 22P02)
- **Root Cause**: System has dual ID system with both UUID 'id' field and string 'workflow_id' field
- **Solution**: Enhanced `db_service.get_workflow_by_id_sync()` to intelligently handle both ID types

### Changes Made
1. **Enhanced ID Detection Logic**: Added UUID format validation to determine query strategy
2. **Smart Query Routing**: Queries UUID 'id' field for valid UUIDs, 'workflow_id' field for string IDs
3. **Service Consistency**: Updated `amc_execution_service` and `batch_execution_service` to use centralized db_service method

### Technical Implementation
```python
# New dual ID handling pattern in db_service.py
def get_workflow_by_id_sync(self, workflow_id: str):
    # Check if workflow_id looks like a UUID
    is_uuid = False
    if workflow_id and not workflow_id.startswith('wf_'):
        try:
            import uuid as uuid_lib
            uuid_lib.UUID(workflow_id)
            is_uuid = True
        except (ValueError, AttributeError):
            is_uuid = False
    
    if is_uuid:
        # Query by UUID 'id' field
        response = self.client.table('workflows')\
            .eq('id', workflow_id).execute()
    else:
        # Query by string 'workflow_id' field
        response = self.client.table('workflows')\
            .eq('workflow_id', workflow_id).execute()
```

## Technical Implementation

### Execution Flow
1. **Query Validation** - Parameter substitution and SQL validation
2. **AMC API Call** - Create execution via AMC API
3. **Status Polling** - Background service monitors execution status
4. **Result Processing** - Download and store results when complete
5. **Notification** - Update UI with completion status

### Parameter System
```python
# Parameter substitution in WorkflowService
def substitute_parameters(self, sql_query: str, parameters: Dict[str, Any]) -> str:
    # Handle campaign_ids, asin_list, date ranges
    # Replace {{parameter_name}} with actual values
    return substituted_sql
```

### AMC API Integration
```python
# Critical: Use instance_id (string) not internal UUID
result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,  # AMC instance ID (e.g., "amcibersblt")
    user_id=user_id,
    entity_id=entity_id,     # From amc_accounts.account_id
)
```

### Status Polling
The execution poller runs every 15 seconds:
```python
# execution_poller.py
async def poll_executions(self):
    pending_executions = self.get_pending_executions()
    for execution in pending_executions:
        status = await self.check_execution_status(execution)
        if status in ['SUCCESS', 'FAILED']:
            await self.finalize_execution(execution, status)
```

## Data Flow

1. **User Initiates**: Click "Execute" in WorkflowDetail
2. **Parameter Processing**: Replace query parameters with actual values
3. **AMC Submission**: Submit to Amazon Marketing Cloud
4. **Background Monitoring**: Poller checks status every 15 seconds
5. **Result Retrieval**: Download results when execution completes
6. **UI Update**: Real-time status updates via polling

## Interconnections

### With Scheduling System
- Scheduled workflows use same execution path
- Schedule executor calls workflow execution service

### With Data Collections
- Collections create multiple workflow executions
- Use same result processing pipeline

### With Instance Management
- Requires valid AMC instance configuration
- Uses instance_id and entity_id for API calls

## Error Handling

### Retry Logic
```python
# Automatic retries with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(AMCAPIException)
)
async def create_workflow_execution(self, ...):
```

### Common Error Patterns
- **403 Forbidden**: Wrong instance_id or missing entity_id
- **Token Expired**: Triggers automatic token refresh
- **Query Timeout**: AMC queries have 10-minute timeout
- **Data Not Available**: 14-day data lag handling
- **PostgreSQL UUID Error (22P02)**: "invalid input syntax for type uuid" - Fixed by dual ID handling in db_service

## Testing Considerations

### Unit Tests
```python
# tests/test_workflow_service.py
def test_parameter_substitution():
    # Test campaign_ids, asin_list, date substitution

def test_execution_creation():
    # Mock AMC API responses
```

### Integration Tests
```python
# tests/amc/test_workflow_execution.py
async def test_full_execution_flow():
    # End-to-end execution test with mock AMC
```

## Performance Optimization

### Result Caching
- Execution results cached in database
- Avoid re-running identical queries
- Cache invalidation on parameter changes

### Concurrent Execution
- Multiple workflows can run simultaneously
- Instance-level throttling to respect AMC limits
- Queue management for high-volume executions

## Monitoring and Debugging

### Execution Tracking
```sql
-- Monitor active executions
SELECT * FROM workflow_executions 
WHERE status IN ('PENDING', 'RUNNING')
ORDER BY created_at DESC;
```

### Debug Information
- Full query logging with parameters
- AMC API request/response logging
- Execution timing and performance metrics