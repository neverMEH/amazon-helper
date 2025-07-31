# Quick Guide: Workflow Execution Results & Error Handling

## Current Status

The workflow execution system is working but results are stored with empty values. Here's how to use it:

## 1. Executing Workflows

### Via UI:
- Go to any workflow detail page
- Click "Execute" button
- Adjust parameters if needed
- Click "Execute Workflow"

### Via API:
```bash
# Get token
TOKEN=$(curl -X POST 'http://localhost:8001/api/auth/login?email=nick@nevermeh.com&password=' 2>/dev/null | jq -r .access_token)

# Execute workflow
EXEC_ID=$(curl -X POST "http://localhost:8001/api/workflows/wf_path_to_conversion_7cd2651c/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 30}' \
  2>/dev/null | jq -r .execution_id)

echo "Execution ID: $EXEC_ID"
```

## 2. Monitoring Execution

The UI automatically polls every 2 seconds and shows:
- Progress bar (0-100%)
- Status: pending → running → completed/failed
- Error messages if failed

### Check status via API:
```bash
curl -X GET "http://localhost:8001/api/workflows/executions/$EXEC_ID/status" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 3. Handling Errors

When execution fails:
- **In UI**: A red error box shows the exact error message
- **Via API**: Check the `error_message` field in status response

Common errors and fixes:
- "Missing required parameters" → Add the parameter to your execution request
- "Invalid SQL syntax" → Edit the workflow SQL query
- "Access denied" → Check AMC instance permissions

## 4. Downloading Results

**Current Issue**: Results are stored but with empty values. The execution completes successfully but result_columns and result_rows are null.

To fix this in the future:
1. The `_update_execution_completed` method needs to properly store the results
2. The simulated results are generated but not being saved correctly

### What works now:
- Execution starts and completes
- Status tracking works
- Error handling works
- The UI shows execution status correctly

### What needs fixing:
- Result data storage (columns, rows)
- CSV download will work once results are stored

## 5. Example Error Scenario

To see error handling:
1. Create a workflow with invalid SQL like:
   ```sql
   SELECT * FROM non_existent_table
   ```
2. Execute it
3. The error message will show in the UI
4. Fix the SQL and re-execute

## Summary

The execution system is functional for:
- Starting executions ✓
- Monitoring progress ✓
- Showing errors ✓
- Tracking completion ✓

Still needs:
- Result data to be properly stored in the database
- CSV download will then work automatically

The UI components for viewing and downloading results are already implemented and will work once the backend stores the data correctly.