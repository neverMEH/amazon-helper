# Workflow ID Truncation Fix Summary

## Issue Identified
The workflow execution was failing with error: "Workflow wf_e27c2385_b1ed_4bcf_a not found"

### Root Cause
In `/root/amazon-helper/amc_manager/services/amc_execution_service.py` line 104, the code was truncating the workflow UUID to 20 characters when generating an AMC workflow ID:
```python
# OLD CODE (BUGGY)
amc_workflow_id = f"wf_{re.sub(r'[^a-zA-Z0-9]', '_', workflow_id[:20])}"
```

The problem was that `workflow_id` parameter was receiving a UUID (36 characters), and truncating it to 20 characters created an invalid identifier.

## Solution Implemented

### Key Changes Made
1. **File Modified**: `/root/amazon-helper/amc_manager/services/amc_execution_service.py`

2. **Fix Applied** (lines 103-114):
   - Now properly uses the `workflow_id` field from the database (format: `wf_XXXXXXXX`)
   - Falls back to generating from workflow name if `workflow_id` field is missing
   - Added logging for better debugging

```python
# NEW CODE (FIXED)
# Use the workflow's workflow_id field if available, otherwise generate one
if workflow.get('workflow_id'):
    # Use existing workflow_id from database (already in AMC-compliant format)
    amc_workflow_id = workflow['workflow_id']
    logger.info(f"Using existing workflow_id from database: {amc_workflow_id}")
else:
    # Generate AMC-compliant workflow ID from workflow name or UUID
    workflow_name = workflow.get('name', workflow_id)
    # Ensure AMC-compliant format: alphanumeric and underscores only
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', workflow_name[:30])
    amc_workflow_id = f"wf_{clean_name}"
    logger.info(f"Generated new AMC workflow ID: {amc_workflow_id} from name: {workflow_name}")
```

3. **Enhanced Error Detection** (lines 58-62):
   - Added detection for truncated IDs to help diagnose similar issues

## Data Flow Clarification

1. **Database Schema**:
   - `workflows.id` - UUID (internal database ID)
   - `workflows.workflow_id` - TEXT (AMC-compliant ID like `wf_XXXXXXXX`)

2. **API Flow**:
   - Frontend sends UUID to API endpoint
   - API retrieves workflow by UUID
   - API passes UUID to execution service
   - Execution service fetches workflow details
   - Execution service uses `workflow_id` field for AMC operations

## Testing Results

Created test script `/root/amazon-helper/scripts/test_workflow_execution_fix.py` that confirms:
- ✅ Workflows are retrieved correctly using UUID
- ✅ The `workflow_id` field is properly used for AMC operations
- ✅ Truncated IDs are correctly rejected
- ✅ Error messages provide clear diagnostics

## Impact
- Fixes workflow execution failures
- Prevents data loss from ID truncation
- Improves error diagnostics
- Maintains backward compatibility

## Files Changed
1. `/root/amazon-helper/amc_manager/services/amc_execution_service.py` - Fixed ID handling
2. `/root/amazon-helper/scripts/test_workflow_execution_fix.py` - Added test verification

## Next Steps
No further action required. The fix has been tested and verified to work correctly.