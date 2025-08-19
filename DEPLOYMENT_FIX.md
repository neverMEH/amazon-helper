# Deployment Fix Required

## Issue
The application is failing to start with the error:
```
ImportError: cannot import name 'get_supabase_client' from 'amc_manager.core.supabase_client'
```

## Root Cause
The schedule executor service was using an incorrect import that doesn't exist in the codebase.

## Fix Applied (Commit: ff2714f)
Changed imports in two files:

### 1. `/amc_manager/services/schedule_executor_service.py`
- **OLD**: `from ..core.supabase_client import get_supabase_client`
- **NEW**: `from ..core.supabase_client import SupabaseManager`

- **OLD**: `self.db = get_supabase_client()`
- **NEW**: `self.db = SupabaseManager.get_client()`

### 2. `/amc_manager/api/supabase/schedule_endpoints.py`
- **OLD**: `from ...core.supabase_client import get_supabase_client`
- **NEW**: `from ...core.supabase_client import SupabaseManager`

- **OLD**: `db = get_supabase_client()`
- **NEW**: `db = SupabaseManager.get_client()`

## Deployment Steps

### Option 1: Pull Latest Changes
```bash
git pull origin main
# Latest commit should be: ff2714f
```

### Option 2: Quick Temporary Fix (if can't redeploy immediately)
Comment out the schedule executor import in `main_supabase.py` temporarily:

```python
# Line 26 in main_supabase.py
# from amc_manager.services.schedule_executor_service import get_schedule_executor

# In the lifespan function, comment out:
# schedule_executor = get_schedule_executor()
# asyncio.create_task(schedule_executor.start())
# await schedule_executor.stop()
```

This will allow the app to start without the scheduling feature until you can deploy the fix.

### Option 3: Manual Fix
If you need to fix manually in the deployed environment:

1. Edit `/app/amc_manager/services/schedule_executor_service.py`
2. Change line 10 from:
   ```python
   from ..core.supabase_client import get_supabase_client
   ```
   to:
   ```python
   from ..core.supabase_client import SupabaseManager
   ```

3. Change line ~25 from:
   ```python
   self.db = get_supabase_client()
   ```
   to:
   ```python
   self.db = SupabaseManager.get_client()
   ```

4. Apply similar changes to `/app/amc_manager/api/supabase/schedule_endpoints.py`

## Verification
After deployment, the application should start without import errors and you should see:
- Schedule executor service starting in the logs
- No ImportError messages
- The `/schedules` route accessible in the frontend

## Related Commits
- `ff2714f` - fix: Correct Supabase client imports in schedule services
- `2a828ce` - fix: Resolve TypeScript build errors in schedule components
- `60a787c` - feat: Add comprehensive workflow scheduling system