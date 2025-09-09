# Execution Tracking Fixes for report_data_weeks

## Summary
Fixed the execution tracking system for `report_data_weeks` table to properly link data collection weeks with their corresponding workflow executions.

## Collection ID Referenced
- **Collection ID**: `db8bf63b-d49b-4c25-8db0-2b1441f5cb95`

## Issues Fixed

### 1. Execution ID Not Being Stored (Initial Issue)
**Problem**: The `execution_id` column existed in the schema but wasn't being populated when workflows executed.

**Solution**: 
- Modified `reporting_database_service.py` to accept and store `execution_id` and `amc_execution_id`
- Updated `historical_collection_service.py` to pass execution IDs to the database service

### 2. Async Execution Handling
**Problem**: AMC executions are asynchronous - they return immediately with status 'pending' and complete later. The system wasn't handling this properly.

**Solution**:
- Store `execution_id` immediately when execution starts (status: pending/running)
- Let the background poller (`execution_status_poller.py`) update the status when execution completes
- Fixed `get_execution_status()` to return the internal UUID for foreign key reference

### 3. Schema Cache Issues
**Problem**: Supabase PostgREST schema cache wasn't recognizing new columns (`started_at`, `completed_at`, `amc_execution_id`, etc.)

**Solution**:
- Added backward compatibility with fallback logic for missing columns
- Created migration script (`006_fix_report_data_weeks_columns.sql`) to ensure columns exist
- Added graceful degradation when columns aren't available

### 4. Column Name Mismatch
**Problem**: Code was using `row_count` but the database column is named `record_count`

**Solution**:
- Fixed line 204 in `execution_status_poller.py` to use correct column name:
```python
if 'row_count' in execution_data:
    update_data['record_count'] = execution_data['row_count']
```

## Files Modified

1. **amc_manager/services/reporting_database_service.py**
   - Added execution tracking parameters to `update_week_status()`
   - Added fallback logic for schema compatibility

2. **amc_manager/services/historical_collection_service.py**
   - Modified to handle async AMC executions
   - Now passes execution IDs to database service

3. **amc_manager/services/amc_execution_service.py**
   - Fixed `get_execution_status()` to return internal UUID

4. **amc_manager/services/execution_status_poller.py**
   - Added `_update_report_week_status()` method
   - Fixed column name from `row_count` to `record_count`

5. **scripts/migrations/006_fix_report_data_weeks_columns.sql**
   - Migration to add missing columns safely

## Commits
- Initial fix: `ea1bd94`
- Async handling: `aa37925`
- Backward compatibility: `2ba483e`
- Record count fix: `81bc91c`

## Current Status
✅ The execution tracking system is now fully functional:
- Execution IDs are properly stored when workflows execute
- Async AMC executions are handled correctly (pending → running → completed)
- Background poller updates week status when executions complete
- Correct column names are used for all updates

## Testing the Fix
To verify the fixes work for collection `db8bf63b-d49b-4c25-8db0-2b1441f5cb95`:

1. New executions from this collection should now properly store `execution_id`
2. The background poller will update status from pending → running → completed
3. When executions complete, `record_count` will be populated
4. Full data lineage is maintained from collection → week → execution

## Notes
- The fixes are backward compatible and won't affect existing data
- Old records without execution_id will continue to work
- New records will have full execution tracking
- The system gracefully handles schema cache issues