# Troubleshooting Guide

## Common Issues and Solutions

### Frontend Issues

#### 1. TypeScript Compilation Errors

**Error:** `')' expected` or `Declaration or statement expected`
```typescript
// TSX syntax error in ExecutionModal.tsx
```

**Solution:** Ensure React components return a single root element or use Fragments:
```typescript
// Use React Fragment for multiple elements
return (
  <>
    <div className="modal">...</div>
    {showDetail && <DetailModal />}
  </>
);
```

#### 2. Query Builder Not Showing Schema

**Issue:** Schema explorer in query builder is empty or shows old hardcoded tables

**Solution:** 
1. Check that data sources API is working: `GET /api/data-sources`
2. Verify `dataSourceService.listDataSources()` is being called in QueryEditorStep
3. Ensure the backend service has data sources in the database

#### 3. Query Examples Not Populating

**Issue:** Clicking "Use in Query Builder" from data sources doesn't populate the editor

**Solution:**
1. Check sessionStorage is being set in DataSourceDetail:
```javascript
// Browser console
localStorage.getItem('queryBuilderDraft')
```
2. Verify QueryBuilder.tsx has the useEffect hook to load from sessionStorage
3. Ensure sessionStorage is cleared after loading

#### 4. Modal Z-Index Issues

**Issue:** Nested modals appear behind parent modals

**Solution:** Use proper z-index layering:
- Main modal: `z-50`
- Nested modal: `z-60` or higher
- Backdrop: `z-40`

### Backend Issues

#### 1. asyncio.run() Error

**Error:** 
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Cause:** Using `asyncio.run()` inside an async function

**Solution:** Replace `asyncio.run()` with `await`:
```python
# Wrong
async def my_function():
    result = asyncio.run(async_operation())

# Correct
async def my_function():
    result = await async_operation()
```

#### 2. 403 Forbidden on AMC API Calls

**Error:** 
```json
{"code": "403", "details": "Unauthorized request"}
```

**Possible Causes:**
1. Using internal UUID instead of AMC instanceId
2. Missing or incorrect entity ID in headers
3. Expired OAuth tokens

**Solutions:**
1. Use `instanceId` field, not `id`:
```python
# Wrong
instance_id = instance['id']  # UUID

# Correct
instance_id = instance['instanceId']  # AMC ID
```

2. Ensure entity ID is in headers:
```python
headers = {
    'Amazon-Advertising-API-AdvertiserId': entity_id  # Required!
}
```

3. Re-authenticate to refresh tokens

#### 3. Workflow ID Not Found

**Error:** 
```
Workflow with ID wf_e27c2385_b1ed_4bcf_a does not exist
```

**Cause:** Workflow ID being truncated

**Solution:** Use full workflow_id from database, don't truncate:
```python
# Wrong
amc_workflow_id = f"wf_{workflow_id[:20]}"

# Correct
amc_workflow_id = workflow.get('workflow_id')  # Use full ID
```

#### 4. Token Decryption Errors

**Error:**
```
Failed to decrypt token
```

**Cause:** Fernet key changed or tokens encrypted with different key

**Solution:**
1. Clear invalid tokens from database
2. Have users re-authenticate
3. Keep FERNET_KEY environment variable consistent

### Database Issues

#### 1. Supabase Connection Timeout

**Error:**
```
Server disconnected without sending a response
```

**Cause:** Supabase closes idle connections after 30 minutes

**Solution:** Use connection retry decorator:
```python
from functools import wraps

def with_connection_retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "Server disconnected" in str(e):
                # Force reconnection
                SupabaseManager._client = None
                return func(*args, **kwargs)
            raise
    return wrapper
```

#### 2. Migration Not Applied

**Issue:** New database fields not available

**Solution:**
1. Check migrations table: `SELECT * FROM schema_migrations`
2. Apply missing migrations manually
3. Verify Supabase dashboard shows the fields

### Authentication Issues

#### 1. OAuth Redirect Failed

**Error:** Redirect URI mismatch

**Solution:**
1. Check REDIRECT_URI in environment variables
2. Verify Amazon App Console has correct redirect URI
3. Ensure protocol matches (http vs https)

#### 2. Token Refresh Failing

**Issue:** Tokens not refreshing automatically

**Solution:**
1. Check token refresh service is running
2. Verify refresh token is stored and valid
3. Check logs for refresh errors
4. Ensure 15-minute buffer before expiry

### Execution Issues

#### 1. Execution Stuck in Pending

**Issue:** Workflow execution never starts

**Possible Causes:**
1. AMC API not actually being called
2. Invalid workflow ID
3. Missing required parameters

**Solutions:**
1. Check AMC_USE_REAL_API environment variable
2. Verify workflow exists in AMC
3. Check all required parameters are provided

#### 2. No Results Available

**Issue:** Execution completes but no results shown

**Possible Causes:**
1. Query returned empty dataset
2. Results API endpoint failing
3. Date range has no data

**Solutions:**
1. Test query directly in AMC console
2. Check backend logs for API errors
3. Adjust date range (remember 14-day lag)

### Development Environment Issues

#### 1. Port Already in Use

**Error:** 
```
Error: listen EADDRINUSE: address already in use :::5173
```

**Solution:**
```bash
# Find and kill process
lsof -i :5173
kill -9 <PID>

# Or use different port
npm run dev -- --port 5174
```

#### 2. Module Not Found

**Error:** 
```
Module not found: Can't resolve 'date-fns'
```

**Solution:**
```bash
cd frontend
npm install
# or specific package
npm install date-fns
```

### Deployment Issues

#### 1. Railway Build Failing

**Common Causes:**
1. Missing environment variables
2. TypeScript errors
3. Docker build cache issues

**Solutions:**
1. Check all required env vars are set in Railway
2. Run `npm run build` locally first
3. Clear build cache in Railway dashboard

#### 2. Frontend Not Proxying to Backend

**Issue:** API calls failing in production

**Solution:**
1. Verify nginx config in Docker container
2. Check backend is running on correct port
3. Ensure `/api` proxy rules are correct

## Quick Diagnostic Commands

### Frontend
```bash
# Check TypeScript errors
cd frontend && npx tsc --noEmit

# Test build
npm run build

# Check dependencies
npm ls
```

### Backend
```bash
# Test database connection
python scripts/check_supabase_connection.py

# Run specific test
pytest tests/test_api_auth.py -v

# Check service status
curl http://localhost:8001/health
```

### Database
```sql
-- Check user tokens
SELECT id, email, auth_tokens IS NOT NULL as has_tokens FROM users;

-- Check recent executions
SELECT * FROM workflow_executions 
ORDER BY started_at DESC LIMIT 10;

-- Check workflow sync status
SELECT id, name, workflow_id, is_synced_to_amc 
FROM workflows;
```

## Getting Help

1. Check logs: Backend logs, browser console, Supabase logs
2. Review recent changes in git history
3. Test in isolation (single component/endpoint)
4. Check environment variables are set correctly
5. Verify external services (AMC API, Supabase) are accessible

## Useful Log Locations

- **Backend logs**: Console output from `python main_supabase.py`
- **Frontend logs**: Browser Developer Console
- **Supabase logs**: Dashboard → Logs → API logs
- **AMC API logs**: Available in AMC console
- **Docker logs**: `docker logs <container_id>`