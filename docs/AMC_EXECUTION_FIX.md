# AMC Execution Fixes - 2025-08-13

## Problem 1: Queries Returning 0 Rows
AMC query executions were returning 0 rows even though the same queries return data when run on other platforms.

### Root Cause
The AMC API client was **completely ignoring date parameters** passed from the frontend and always using today's date range. Since AMC has a 14-day data lag, queries for today's data always return 0 rows.

### Solution Implemented

#### 1. Date Parameter Extraction (amc_api_client.py)
Modified to properly extract date parameters:
- Looks for `startDate`, `start_date`, `endDate`, `end_date` in execution parameters
- Handles multiple date formats (ISO with/without timezone, date-only)
- Uses actual dates from frontend instead of hardcoded `datetime.utcnow()`

#### 2. AMC Data Lag Handling
- Default date range changed from "today" to "14-21 days ago"
- This accounts for AMC's 14-day data processing lag
- Ensures queries have data available to return

#### 3. Date Format Compliance
- Removes timezone suffixes ('Z') from dates - AMC doesn't accept them
- Formats dates as `YYYY-MM-DDTHH:MM:SS` without timezone
- Adds proper time components (00:00:00 for start, 23:59:59 for end)

## Problem 2: All Executions Stuck in "Pending" Status
Executions remained in "pending" status indefinitely, never updating to running/completed/failed.

### Root Cause
No background process was polling AMC API for execution status updates. The system created executions but never checked their progress.

### Solution Implemented

#### 1. Automatic Status Polling Service
Created `ExecutionStatusPoller` service that:
- Runs every 15 seconds automatically
- Polls all pending/running executions from the last 2 hours
- Updates status from AMC API responses
- Stops polling completed/failed executions

#### 2. Manual Refresh Endpoint
Added endpoint for immediate status updates:
```
POST /api/executions/refresh-status/{execution_id}
```

#### 3. Integration with Application Lifecycle
- Poller starts automatically when backend starts
- Stops gracefully on shutdown
- Integrated into `main_supabase.py` lifespan events

## Testing & Verification

### Test Date Handling
```bash
python scripts/test_execution_dates.py
```

### Verify in Logs
When executing a workflow, check for:
```
Found start date parameter 'startDate': 2025-07-25
Formatted start date for AMC: 2025-07-25T00:00:00
Using default date range (accounting for AMC data lag): 2025-07-23T00:00:00 to 2025-07-30T23:59:59
```

When polling runs, check for:
```
Started execution status poller (interval: 15s)
Found X executions to poll
Polling status for execution exec_XXX (AMC: XXX)
Execution exec_XXX: status=running, progress=50%
```

## Best Practices

### Date Selection
- Always use dates at least 14 days old
- For testing, use dates 15-30 days ago
- AMC uses America/New_York timezone

### Query Testing
Simple test query to verify data exists:
```sql
SELECT COUNT(*) as record_count
FROM dsp_impressions
WHERE dt >= '2025-07-15' AND dt <= '2025-07-29'
```

### Status Monitoring
- Executions auto-update every 15 seconds
- Use refresh button in UI for immediate update
- Check "All Executions" view to see status progression

## Files Modified
- `/amc_manager/services/amc_api_client.py` - Date parameter extraction
- `/amc_manager/services/execution_status_poller.py` - New polling service
- `/amc_manager/api/supabase/amc_executions.py` - Manual refresh endpoint
- `/main_supabase.py` - Integration of polling service
- `/frontend/src/components/executions/AMCExecutionDetail.tsx` - Added instance/query names

## Common Issues & Solutions

### Still Getting 0 Rows?
1. Check date range is old enough (14+ days)
2. Verify instance has access to data sources (DSP, SP, etc.)
3. Check query syntax - no SELECT * allowed in AMC
4. Verify entity ID matches your advertiser access

### Status Not Updating?
1. Check backend logs for polling errors
2. Verify AMC execution ID is being saved
3. Use manual refresh endpoint to force update
4. Check that execution is less than 2 hours old

### Date Format Errors?
1. Frontend should send dates as ISO strings
2. Backend removes timezone suffixes automatically
3. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format

## Code Examples

### Correct Date Handling
```python
# In amc_api_client.py
if not time_window_start or not time_window_end:
    # Account for AMC's 14-day data lag
    end_date = datetime.utcnow() - timedelta(days=14)  # 14 days ago
    start_date = end_date - timedelta(days=7)  # 21 days ago
    time_window_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')  # No 'Z'!
    time_window_end = end_date.strftime('%Y-%m-%dT%H:%M:%S')
```

### Polling Service Integration
```python
# In main_supabase.py
from amc_manager.services.execution_status_poller import execution_status_poller

async def lifespan(app: FastAPI):
    # Startup
    await execution_status_poller.start()
    logger.info("✓ Execution status poller started")
    
    yield
    
    # Shutdown
    await execution_status_poller.stop()
```

## Impact
These fixes resolve two critical issues that were preventing AMC queries from returning data and showing execution progress. The system now:
1. Properly uses date parameters from the frontend
2. Accounts for AMC's data lag
3. Automatically updates execution statuses
4. Provides visibility into query execution progress