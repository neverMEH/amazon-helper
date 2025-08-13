# AMC Query Execution 0 Rows Fix

## Problem Identified
AMC query executions were returning 0 rows even though the same queries work on other platforms. The root cause was that date parameters from the frontend were not being properly passed to the AMC API.

## Issues Fixed

### 1. **Hardcoded Time Window (CRITICAL)**
**Before:** The AMC API client was ignoring execution parameters and always using today's date:
```python
"timeWindowStart": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%S'),
"timeWindowEnd": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
```

**After:** Now properly extracts and uses date parameters from execution:
```python
# Extract date parameters from parameter_values
for start_key in ['startDate', 'start_date', 'timeWindowStart', 'beginDate']:
    if start_key in parameter_values:
        time_window_start = parameter_values[start_key]
        break

# Format dates properly for AMC API (no timezone suffix)
if 'T' in str(time_window_start):
    time_window_start = str(time_window_start).replace('Z', '').split('+')[0].split('.')[0]
else:
    time_window_start = f"{time_window_start}T00:00:00"
```

### 2. **Enhanced Logging**
Added comprehensive logging to help diagnose issues:
- Log execution parameters received
- Log date parameter extraction and formatting
- Log CSV preview to see if data is being returned
- Log specific warnings when results are empty with common causes

### 3. **Date Format Handling**
The fix now handles multiple date formats:
- ISO format with timezone: `2024-01-01T00:00:00Z`
- ISO format without timezone: `2024-01-01T00:00:00`
- Date only format: `2024-01-01`
- Both camelCase (`startDate`) and snake_case (`start_date`) parameter names

## Files Modified
1. `/root/amazon-helper/amc_manager/services/amc_api_client.py`
   - Fixed `create_workflow_execution` method to use date parameters
   - Enhanced logging in `get_execution_results` and `download_and_parse_csv`

2. `/root/amazon-helper/amc_manager/services/amc_execution_service.py`
   - Added logging for execution parameters and prepared SQL

## How to Verify the Fix

### 1. Check Logs
When executing a workflow, look for these log entries:
```
INFO: Execution parameters received: {'startDate': '2024-01-01', 'endDate': '2024-01-07', ...}
INFO: Found start date parameter 'startDate': 2024-01-01
INFO: Found end date parameter 'endDate': 2024-01-07
INFO: Formatted start date for AMC: 2024-01-01T00:00:00
INFO: Formatted end date for AMC: 2024-01-07T23:59:59
```

### 2. Monitor Network Traffic
In browser DevTools, check the `/execute` request payload:
```json
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-07",
  "other_params": "..."
}
```

### 3. Check AMC API Request
The logs should show the correct time window in the AMC API request:
```json
{
  "workflowId": "wf_example",
  "timeWindowType": "EXPLICIT",
  "timeWindowStart": "2024-01-01T00:00:00",
  "timeWindowEnd": "2024-01-07T23:59:59",
  "timeWindowTimeZone": "America/New_York"
}
```

## Common Issues That May Still Cause 0 Rows

### 1. **AMC Data Lag**
AMC typically has a 24-48 hour data lag. Recent data may not be available yet.
**Solution:** Use dates from 3-7 days ago for testing.

### 2. **Timezone Mismatch**
AMC uses `America/New_York` timezone by default. Your data might be in a different timezone.
**Solution:** Adjust date ranges to account for timezone differences.

### 3. **Query Filters Too Restrictive**
The SQL query WHERE clauses might be filtering out all data.
**Solution:** Start with a simple query like `SELECT COUNT(*) FROM dsp_impressions` to verify data exists.

### 4. **Parameter Substitution Issues**
Parameters in the SQL query might not be getting replaced correctly.
**Solution:** Check logs for "Prepared SQL query" to see the final query being executed.

### 5. **No Data for Date Range**
The account might genuinely have no data for the selected date range.
**Solution:** Verify data availability in the AMC console directly.

## Testing Script
Use the provided test script to verify date parameter handling:
```bash
python scripts/test_execution_dates.py
```

This will test various date formats and show how they're being processed.

## Next Steps if Still Getting 0 Rows

1. **Enable Debug Logging**
   Set logging level to DEBUG to see full API requests/responses

2. **Test in AMC Console**
   Run the same query with the same date range directly in AMC console

3. **Check S3 CSV Content**
   The logs now show CSV preview - check if headers are present but no data rows

4. **Verify Account Permissions**
   Ensure the account has access to the data being queried

5. **Check for AMC API Errors**
   Look for validation errors or warnings in the execution status response