# Plan: Implementing Real AMC Query Execution

## Current State
- The system uses `_simulate_amc_execution()` which returns mock data
- We have working AMC API authentication (as shown in `amc_instances_working.py`)
- We need to replace the simulation with actual AMC API calls

## Required AMC API Endpoints

### 1. Create Workflow Execution
```
POST https://advertising-api.amazon.com/amc/workflowExecutions
Headers:
  - Amazon-Advertising-API-ClientId: {client_id}
  - Authorization: Bearer {access_token}
  - Amazon-Advertising-API-MarketplaceId: {marketplace_id}
  - Amazon-Advertising-API-AdvertiserId: {entity_id}
  - Content-Type: application/json

Body:
{
  "workflowId": "{workflow_id}",
  "instanceId": "{amc_instance_id}",
  "sqlQuery": "{sql_query}",
  "outputLocation": "s3://bucket/path",
  "dataFormat": "CSV"
}
```

### 2. Get Execution Status
```
GET https://advertising-api.amazon.com/amc/workflowExecutions/{executionId}
Headers: (same as above)
```

### 3. Get Execution Results
```
GET https://advertising-api.amazon.com/amc/workflowExecutions/{executionId}/results
Headers: (same as above)
```

## Implementation Steps

1. **Add AMC API client methods**:
   - `create_workflow_execution()`
   - `get_execution_status()`
   - `get_execution_results()`

2. **Update `_simulate_amc_execution()` to `_execute_amc_query()`**:
   - Make real API call to create execution
   - Poll for status updates
   - Retrieve results when complete

3. **Handle authentication**:
   - Get user's Amazon OAuth token
   - Refresh token if expired
   - Pass correct headers with entity ID

4. **Error handling**:
   - API rate limits
   - Invalid queries
   - Permission errors
   - Timeout handling

## Challenges

1. **Authentication**: Need real Amazon OAuth tokens (not just local auth)
2. **S3 Output**: AMC requires an S3 bucket for output
3. **Permissions**: User must have access to the AMC instance
4. **API Documentation**: Amazon's AMC API docs are not public

## Alternative Approach

If we can't get the exact API format, we could:
1. Use the AMC console API (reverse engineer from browser)
2. Use AWS SDK with proper credentials
3. Implement a proxy service that handles AMC execution

## Next Steps

To implement real execution, we need:
1. Valid Amazon OAuth access token
2. AMC API documentation or working examples
3. S3 bucket configuration for results
4. Update the execution service to use real API calls