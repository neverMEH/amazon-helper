# Fixes Log - RecomAMP Project

> Last Updated: 2025-08-26
> Version: 1.0.0

This log maintains a comprehensive record of all problems solved and fixes implemented in the RecomAMP project. Each entry provides the solution pattern for future reference.

## Critical Fixes Reference

### Token Management Issues

#### Fix ID: TOKEN-001
**Date**: 2025-08-21  
**Commit**: `c8147c9`  
**Problem**: Schedule executor using incorrect token refresh method  
**Symptoms**: 403 errors during scheduled workflow execution  
**Root Cause**: Called `refresh_token()` instead of `refresh_access_token()` in TokenService  
**Solution**: Changed method call in `schedule_executor.py` line 156  
**Files**: `amc_manager/services/schedule_executor.py`  
**Pattern**: Always use `refresh_access_token()` for token refresh operations  
**Prevention**: Added to CLAUDE.md critical gotchas list  

#### Fix ID: TOKEN-002
**Date**: Previous  
**Problem**: Token decryption failures after FERNET_KEY changes  
**Symptoms**: "Failed to decrypt token" errors  
**Root Cause**: FERNET_KEY environment variable changed, existing tokens encrypted with old key  
**Solution**: Users must re-authenticate to generate new encrypted tokens  
**Files**: `amc_manager/services/token_service.py`  
**Pattern**: FERNET_KEY changes require user re-authentication  
**Prevention**: Document FERNET_KEY consistency requirements  

### AMC API Integration Issues

#### Fix ID: AMC-001
**Date**: Previous  
**Problem**: Empty query results from AMC despite valid queries  
**Symptoms**: Queries return no data when data should exist  
**Root Cause**: Date format with timezone suffix ('Z') causes AMC to return empty results  
**Solution**: Use format `2025-07-15T00:00:00` without timezone suffix  
**Files**: Date parameter handling throughout application  
**Pattern**: AMC requires dates without timezone information  
**Prevention**: Validate date format before AMC API calls  

#### Fix ID: AMC-002
**Date**: Previous  
**Problem**: 403 Forbidden errors on AMC API calls  
**Symptoms**: Valid authenticated requests returning 403  
**Root Cause**: Using internal UUID instead of AMC instance_id  
**Solution**: Always use `instance_id` field for AMC API calls, not internal `id` UUID  
**Files**: All AMC API service methods  
**Pattern**: AMC APIs require actual AMC instance identifiers  
**Prevention**: ID field reference guide in CLAUDE.md  

#### Fix ID: AMC-003
**Date**: Previous  
**Problem**: Workflow execution status not updating  
**Symptoms**: Executions stuck in "running" status indefinitely  
**Root Cause**: Using workflow execution internal UUID instead of amc_execution_id for AMC API calls  
**Solution**: Use `amc_execution_id` field for all AMC status check operations  
**Files**: `workflow_execution_service.py`, `execution_poller.py`  
**Pattern**: Always use AMC-provided IDs for AMC API operations  
**Prevention**: Consistent ID field naming conventions  

### Database Connection Issues

#### Fix ID: DB-001
**Date**: Previous  
**Problem**: Intermittent database connection failures  
**Symptoms**: Random "connection closed" errors during operations  
**Root Cause**: Network instability with Supabase without proper retry logic  
**Solution**: Implemented `@with_connection_retry` decorator for all database operations  
**Files**: `database_service.py`, all service classes  
**Pattern**: All database operations must include connection retry logic  
**Prevention**: DatabaseService base class enforces retry pattern  

### Frontend Integration Issues

#### Fix ID: FRONTEND-001
**Date**: Previous  
**Problem**: Monaco Editor not rendering properly  
**Symptoms**: Editor appears as empty/blank or very small  
**Root Cause**: Monaco Editor requires pixel-based heights, not percentage heights  
**Solution**: Always specify height as pixels (e.g., "400px")  
**Files**: `SQLEditor.tsx`, `QueryBuilder.tsx`  
**Pattern**: Monaco Editor components must use pixel heights  
**Prevention**: Component validation for height prop format  

#### Fix ID: FRONTEND-002
**Date**: Previous  
**Problem**: React Query cache invalidation not working  
**Symptoms**: Stale data persists after mutations  
**Root Cause**: Inconsistent query key structures breaking cache relationships  
**Solution**: Standardized query key formats (e.g., ['dataSource', schemaId])  
**Files**: Query service hooks, mutation handlers  
**Pattern**: Consistent query key structures required for cache invalidation  
**Prevention**: Query key validation utilities  

### Schedule Execution Issues

#### Fix ID: SCHEDULE-001
**Date**: 2025-08-21  
**Problem**: Schedules executing repeatedly in rapid succession  
**Symptoms**: Multiple executions within minutes instead of scheduled intervals  
**Root Cause**: Next run time not updated after execution start  
**Solution**: Added 5-minute deduplication window and immediate next_run updates  
**Files**: `schedule_executor.py`  
**Pattern**: Update next_run immediately after execution start  
**Prevention**: Deduplication logic prevents rapid re-execution  

#### Fix ID: SCHEDULE-002
**Date**: 2025-08-26
**Problem**: Schedule sched_d69097bad1cf executing 8 times at 6:00 AM EST instead of once
**Symptoms**: Single scheduled execution at 6:00 AM triggers 8 executions within minutes
**Root Cause**: 
  1. Race condition with 2-minute buffer window in `get_due_schedules`
  2. Non-atomic schedule claiming allows multiple processes to execute same schedule
  3. Deduplication check happens AFTER schedule is already claimed
**Solution**: 
  1. Implemented atomic `_atomic_claim_schedule` method with optimistic locking
  2. Reduced buffer window from 2 minutes to 30 seconds  
  3. Added double-check on both `last_run_at` and `schedule_runs` table
  4. Implemented retry logic (max 3 attempts) for API errors only
**Files**: `schedule_executor_service_fixed.py`
**Pattern**: 
  - Atomic database operations for distributed locking
  - Optimistic locking pattern: `UPDATE ... WHERE last_run_at = old_value`
  - Tight time windows for schedule claiming (30 seconds max)
**Prevention**: 
  - Always use atomic operations for resource claiming
  - Update state BEFORE executing, not after
  - Implement proper distributed locking for concurrent processes  

#### Fix ID: SCHEDULE-002
**Date**: Previous  
**Problem**: Scheduled workflows not executing  
**Symptoms**: Due schedules remain unexecuted  
**Root Cause**: Timezone calculation errors in CRON expression evaluation  
**Solution**: Proper timezone conversion using croniter with user timezone  
**Files**: `schedule_service.py`, `schedule_executor.py`  
**Pattern**: Always consider user timezone for schedule calculations  
**Prevention**: Timezone validation in schedule creation  

## Solution Patterns Reference

### Error Handling Patterns
```python
# Token refresh with retry
@with_connection_retry
async def refresh_user_token(self, user_id: str):
    return await self.token_service.refresh_access_token(user_id)

# AMC API with proper ID usage
result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance.instance_id,  # Use AMC ID, not UUID!
    user_id=user_id,
    entity_id=entity_id,
)

# Database operations with retry
@with_connection_retry  
async def get_workflow(self, workflow_id: str):
    return self.client.table('workflows').select().eq('id', workflow_id).execute()
```

### Frontend Patterns
```typescript
// Monaco Editor height specification
<SQLEditor height="400px" />  // ✓ Correct
<SQLEditor height="100%" />   // ✗ May fail

// Consistent React Query keys
const queryKey = ['dataSource', schemaId];  // ✓ Standard format
const queryKey = ['data-source', id];       // ✗ Breaks cache relationships
```

### Date Handling Patterns
```python
# AMC-compatible date format
date_str = '2025-07-15T00:00:00'    # ✓ Correct
date_str = '2025-07-15T00:00:00Z'   # ✗ Causes empty results

# Timezone-aware scheduling
next_run = croniter(cron_expr, user_tz.localize(datetime.now())).get_next(datetime)
```

## Prevention Strategies

1. **ID Field Validation**: Validate ID types before API calls
2. **Date Format Validation**: Ensure AMC-compatible date formats
3. **Connection Retry**: Always use retry decorators for database operations  
4. **Token Refresh**: Implement proper token refresh error handling
5. **Cache Key Consistency**: Standardize React Query key structures
6. **Editor Configuration**: Validate Monaco Editor height specifications
7. **Schedule Deduplication**: Implement execution windows to prevent rapid repeats

## Future Fix Categories

- **Performance Optimizations**: Database query improvements, caching strategies
- **Security Enhancements**: Token encryption, API security patterns
- **User Experience**: Loading states, error handling, feedback mechanisms
- **Integration Reliability**: AMC API resilience, webhook handling
- **Monitoring & Alerting**: Error detection, performance tracking

## Usage Guidelines

1. **Before fixing similar issues**: Search this log for existing patterns
2. **After implementing fixes**: Add detailed entry with solution pattern
3. **When reviewing code**: Reference these patterns for consistency
4. **During onboarding**: Use as training material for common issues
5. **For documentation**: Reference fix IDs in code comments

**Remember**: Every fix here represents institutional knowledge that prevents repeating the same debugging process.