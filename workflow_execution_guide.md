# Workflow Execution Guide

This guide shows how to execute workflows and handle results or errors.

## 1. Executing a Workflow

### From the UI:
1. Navigate to a workflow detail page
2. Click the "Execute" button
3. Configure parameters if needed (default values are provided)
4. Click "Execute Workflow"

### Via API:
```python
import requests

# Login first
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'your-email@example.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute workflow
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 30}  # Optional parameters

resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)
execution = resp.json()
execution_id = execution['execution_id']
```

## 2. Monitoring Execution Status

The execution modal automatically polls for status every 2 seconds and shows:
- Progress bar (0-100%)
- Current status (pending, running, completed, failed)
- Execution metadata (ID, start time, duration)
- Error messages if the execution fails

### Via API:
```python
# Get execution status
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/status', 
                    headers=headers)
status = resp.json()

# Check status
if status['status'] == 'completed':
    print(f"Success! Rows: {status.get('row_count', 0)}")
elif status['status'] == 'failed':
    print(f"Failed: {status.get('error_message', 'Unknown error')}")
```

## 3. Handling Failed Executions

When an execution fails, the UI shows:
- A red error box with the error message
- The exact error from AMC or the backend
- You can close the modal and adjust your SQL query or parameters

Common failure reasons:
- Invalid SQL syntax
- Missing required parameters
- AMC instance not accessible
- Query timeout

To iterate on failures:
1. Note the error message
2. Close the execution modal
3. Edit the workflow SQL query or parameters
4. Try executing again

## 4. Downloading Results

### From the UI:
Once execution completes successfully:
1. Click "View Results" to see the data table
2. Click "Download CSV" to download all results
3. The CSV includes all rows and columns from the query

### Via API:
```python
# Get results after completion
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                    headers=headers)
results = resp.json()

# results contains:
# - columns: Array of column definitions [{name, type}]
# - rows: Array of row data
# - total_rows: Total number of rows
# - execution_details: Runtime metrics
```

## 5. Result Visualization

The UI provides two views:
1. **Table View**: Shows raw data in a grid format
2. **Insights View**: Shows key statistics and visualizations (when applicable)

Toggle between views using the "Show Insights" / "Show Table" button.

## 6. Execution History

To view past executions:
1. Go to the workflow detail page
2. Click on the "Executions" tab
3. See all past executions with their status, duration, and row counts
4. Click on any execution to view its details

## Current Limitations

Since we're using simulated AMC execution:
- Results are mock data based on query type
- Execution completes in ~3 seconds
- Real AMC integration would provide actual query results

## Example: Complete Workflow

1. Create a workflow with SQL:
```sql
SELECT 
  journey_type,
  COUNT(DISTINCT user_id) as user_count,
  AVG(touchpoints) as avg_touchpoints
FROM conversions
WHERE event_date >= '{{start_date}}'
  AND event_date <= '{{end_date}}'
GROUP BY journey_type
```

2. Execute with parameters:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

3. Monitor progress (0% → 10% → 50% → 90% → 100%)

4. View results table or download CSV

5. If it fails, check error message and adjust SQL/parameters accordingly