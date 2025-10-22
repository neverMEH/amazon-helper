# Schedule Token Refresh & Snowflake Upload Fixes

**Date**: 2025-10-22
**Status**: ✅ Implementation Complete - Pending Migration

## Issues Fixed

### Issue 1: Token Refresh Failures in Scheduled Executions

**Problem**: Schedules were failing with generic error: "Failed to refresh token (after 1 attempts)"

**Root Cause**:
- Token refresh had no retry logic
- Error messages were generic and didn't indicate the specific failure reason
- No distinction between temporary errors (network issues) and permanent errors (expired refresh token)

**Solution Implemented**:

1. **Enhanced Token Service** ([token_service.py:108-212](amc_manager/services/token_service.py))
   - Added retry logic with exponential backoff (max 3 attempts)
   - Differentiated error types:
     - `400/401`: Invalid/expired refresh token → No retry, user must re-authenticate
     - `500/502/503/504`: Server errors → Retry with backoff (5s, 10s, 20s)
     - `429`: Rate limiting → Retry with longer backoff (10s, 20s, 40s)
     - Timeout/Connection errors → Retry with backoff
   - Detailed error logging showing exact failure reason and HTTP status codes

2. **Improved Schedule Executor Token Check** ([schedule_executor_service.py:483-587](amc_manager/services/schedule_executor_service.py))
   - Added user email to logs for easier debugging
   - Validates token structure before attempting refresh
   - Provides detailed error messages explaining:
     - Why token refresh failed
     - What the user needs to do (e.g., re-authenticate)
     - Whether it's a temporary or permanent failure
   - Checks token expiry time and logs remaining validity

**Expected Outcome**:
- Transient errors (network issues, server errors) will be automatically retried
- Permanent errors (expired refresh token) will show clear message: "User needs to re-authenticate via Amazon OAuth"
- Logs will show exactly which attempt failed and why

---

### Issue 2: Schedules Not Uploading to Snowflake

**Problem**: Scheduled executions never uploaded results to Snowflake, even though ad-hoc executions did

**Root Cause**:
- `workflow_schedules` table had NO Snowflake configuration fields
- Schedule creation endpoints didn't accept Snowflake settings
- Schedule executor didn't pass Snowflake config to the execution service
- No way to persist Snowflake preferences for recurring schedule runs

**Solution Implemented**:

1. **Database Schema Migration** ([15_add_snowflake_to_schedules.sql](database/supabase/migrations/15_add_snowflake_to_schedules.sql))
   - Added 3 new fields to `workflow_schedules`:
     - `snowflake_enabled` (BOOLEAN, default FALSE)
     - `snowflake_table_name` (TEXT, nullable)
     - `snowflake_schema_name` (TEXT, nullable)
   - Added index for filtering schedules with Snowflake enabled
   - Rollback script provided for safe reversibility

2. **API Schema Updates** ([schedule_endpoints.py:22-103](amc_manager/api/supabase/schedule_endpoints.py))
   - Updated `ScheduleCreatePreset` model with Snowflake fields
   - Updated `ScheduleCreateCustom` model with Snowflake fields
   - Updated `ScheduleUpdate` model with Snowflake fields
   - Updated `ScheduleResponse` model to return Snowflake config
   - All changes backward compatible (optional fields)

3. **Schedule Service Updates** ([enhanced_schedule_service.py:39-126](amc_manager/services/enhanced_schedule_service.py))
   - `create_schedule_from_preset()` now accepts Snowflake parameters
   - Stores Snowflake configuration in database when creating schedules

4. **Schedule Executor Updates** ([schedule_executor_service.py:689-760](amc_manager/services/schedule_executor_service.py))
   - `execute_workflow()` method now accepts optional `schedule` parameter
   - Extracts Snowflake config from schedule:
     - `snowflake_enabled`
     - `snowflake_table_name`
     - `snowflake_schema_name`
   - Passes Snowflake config to `amc_execution_service.execute_workflow()`
   - Logs Snowflake upload status for debugging

**Expected Outcome**:
- Schedules can now be configured with Snowflake upload settings during creation
- Scheduled executions will automatically upload to Snowflake (just like ad-hoc executions)
- Snowflake uploads use UPSERT to prevent duplicate data
- Each schedule run uploads to the same table (enables time-series analysis)

---

## Files Modified

### Backend Services
1. `amc_manager/services/token_service.py` - Enhanced retry logic and error handling
2. `amc_manager/services/schedule_executor_service.py` - Improved token validation + Snowflake config passing
3. `amc_manager/services/enhanced_schedule_service.py` - Accept and store Snowflake config
4. `amc_manager/api/supabase/schedule_endpoints.py` - Updated Pydantic schemas

### Database Migrations
1. `database/supabase/migrations/15_add_snowflake_to_schedules.sql` - Add Snowflake fields
2. `database/supabase/migrations/15_add_snowflake_to_schedules_rollback.sql` - Rollback migration

### Documentation
1. `.agent-os/features/schedule-fixes-2025-10-22.md` - This document

---

## How to Apply Changes

### Step 1: Apply Database Migration

**Option A: Via Supabase SQL Editor** (Recommended)
```sql
-- Copy contents of database/supabase/migrations/15_add_snowflake_to_schedules.sql
-- Paste into Supabase SQL Editor
-- Run the migration
```

**Option B: Via psql CLI**
```bash
psql -d postgres -f database/supabase/migrations/15_add_snowflake_to_schedules.sql
```

**Verify Migration**:
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'workflow_schedules'
  AND column_name IN ('snowflake_enabled', 'snowflake_table_name', 'snowflake_schema_name');
```

Expected output:
```
column_name            | data_type | is_nullable
-----------------------+-----------+-------------
snowflake_enabled      | boolean   | YES
snowflake_table_name   | text      | YES
snowflake_schema_name  | text      | YES
```

### Step 2: Restart Backend Service

```bash
# Restart the FastAPI backend to load new code
# If using systemd:
sudo systemctl restart recomamp

# If running manually:
# Stop the current process (Ctrl+C)
python main_supabase.py
```

### Step 3: Test Token Refresh

1. Find a schedule that previously failed with token errors
2. Check the execution history log for detailed error messages
3. If error says "refresh token is invalid or expired", user needs to re-authenticate
4. If error shows "Amazon API server error 503", it should now automatically retry

### Step 4: Test Snowflake Upload

1. **Ensure Snowflake is configured**: User must have an active Snowflake configuration in `snowflake_configurations` table
2. **Create a test schedule** with Snowflake enabled:
   ```json
   {
     "preset_type": "daily",
     "name": "Test Snowflake Schedule",
     "snowflake_enabled": true,
     "snowflake_table_name": "test_schedule_results",
     "snowflake_schema_name": null
   }
   ```
3. **Run the schedule** (either wait for next scheduled run or use "Run Now")
4. **Verify in execution logs**:
   - Should see: `Snowflake upload enabled for schedule sched_xxxx. Table: test_schedule_results`
   - Should see: `Successfully uploaded X rows to Snowflake table`
5. **Verify in Snowflake**:
   ```sql
   SELECT COUNT(*), MIN(uploaded_at), MAX(uploaded_at)
   FROM your_database.your_schema.test_schedule_results;
   ```

---

## Rollback Instructions

If issues occur, rollback the database migration:

```bash
psql -d postgres -f database/supabase/migrations/15_add_snowflake_to_schedules_rollback.sql
```

Then revert the code changes:
```bash
git checkout HEAD~1 -- amc_manager/services/token_service.py
git checkout HEAD~1 -- amc_manager/services/schedule_executor_service.py
git checkout HEAD~1 -- amc_manager/services/enhanced_schedule_service.py
git checkout HEAD~1 -- amc_manager/api/supabase/schedule_endpoints.py
```

---

## Testing Checklist

- [ ] Apply database migration successfully
- [ ] Restart backend service
- [ ] Create new schedule with Snowflake enabled
- [ ] Verify schedule stores Snowflake config in database
- [ ] Run schedule and verify execution creates with Snowflake fields
- [ ] Check execution monitor uploads to Snowflake
- [ ] Verify data appears in Snowflake table
- [ ] Test token refresh with expired token (should see detailed error)
- [ ] Test token refresh with network error (should see retry attempts)

---

## Benefits

### Token Refresh Improvements
- ✅ Automatic retry for transient errors (no manual intervention needed)
- ✅ Clear error messages indicating exact failure reason
- ✅ Distinguishes between user action required vs. temporary issues
- ✅ Better debugging with detailed logs

### Snowflake Upload for Schedules
- ✅ Scheduled executions now upload to Snowflake automatically
- ✅ Consistent data storage for both ad-hoc and scheduled runs
- ✅ Time-series data accumulation in same table
- ✅ UPSERT prevents duplicate data on re-runs
- ✅ No manual export needed after schedule executions

---

## Related Documentation

- [Token Service](amc_manager/services/token_service.py) - OAuth token management
- [Schedule Executor Service](amc_manager/services/schedule_executor_service.py) - Background schedule runner
- [Execution Monitor Service](amc_manager/services/execution_monitor_service.py) - Polls AMC API and triggers Snowflake upload
- [Snowflake Service](amc_manager/services/snowflake_service.py) - UPSERT logic for data warehouse
- [CLAUDE.md](CLAUDE.md#recent-critical-fixes) - Update with this fix entry
