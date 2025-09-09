# AMC Mock Mode Execution Issues

## Problem Summary
When `AMC_USE_REAL_API=false` (mock mode), the system generates fake execution IDs that don't exist in the actual AMC system. This causes status checks to fail with "Workflow execution with ID ... does not exist" errors.

## Root Cause
1. **Mock Mode Enabled**: The `.env` file has `AMC_USE_REAL_API=false`
2. **Fake Execution IDs**: Mock mode generates UUIDs that aren't real AMC executions
3. **Status Check Failures**: When polling for status, AMC API returns 400 errors because these executions don't exist

## Error Pattern
```
Failed to get execution status: Status 400, Response: {'code': '400', 'details': 'Workflow execution with ID xxx does not exist.'}
```

## Solution

### Option 1: Enable Real AMC API (Recommended for Production)
```bash
# In .env file, change:
AMC_USE_REAL_API=true
```

### Option 2: Fix Mock Mode Behavior
The mock mode should be fixed to properly simulate the entire execution lifecycle:
1. Store mock execution IDs in memory/database
2. Return appropriate status when polled
3. Simulate execution completion after a delay

## Current Behavior in Mock Mode
- Creates fake execution with random UUID
- Returns pending status immediately
- Fails when trying to check status later

## Files Affected
- `amc_manager/services/amc_execution_service.py` - Handles execution creation and polling
- `amc_manager/services/execution_status_poller.py` - Background service that polls for updates
- `.env` - Configuration file with `AMC_USE_REAL_API` setting

## Workaround
To prevent errors in mock mode, the status poller could skip AMC API calls when in mock mode:
```python
if not settings.amc_use_real_api:
    # Skip real API calls in mock mode
    return {"status": "completed", "progress": 100}
```

## Testing Requirements
1. Test with `AMC_USE_REAL_API=true` for real executions
2. Test with `AMC_USE_REAL_API=false` to ensure mock mode works correctly
3. Verify execution tracking in `report_data_weeks` table works in both modes