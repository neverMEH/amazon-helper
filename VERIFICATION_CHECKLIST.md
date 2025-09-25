# Universal Snowflake Sync Integration Verification Checklist

## ✅ Database Migration Verification

Run the SQL verification script in your Supabase SQL editor:
```sql
-- Copy and paste the contents of verify_snowflake_sync_migration.sql
```

Expected results:
- [ ] `snowflake_sync_queue` table exists
- [ ] All required columns are present (id, execution_id, user_id, status, etc.)
- [ ] Indexes are created
- [ ] Constraints are in place (status check, unique execution_id)
- [ ] Trigger function exists
- [ ] Trigger is attached to workflow_executions table
- [ ] Views exist (snowflake_sync_queue_summary, snowflake_sync_failures)
- [ ] RLS policies are configured

## ✅ Service Integration Verification

### 1. Check Main Application Integration
Verify that the service is imported and started in `main_supabase.py`:
- [ ] Import statement: `from amc_manager.services.universal_snowflake_sync_service import universal_snowflake_sync_service`
- [ ] Service start: `asyncio.create_task(universal_snowflake_sync_service.start())`
- [ ] Service stop: `await universal_snowflake_sync_service.stop()`

### 2. Check API Endpoints Integration
Verify that the monitoring API is registered:
- [ ] Import: `from amc_manager.api.snowflake_sync_monitoring import router as snowflake_sync_router`
- [ ] Router registration: `app.include_router(snowflake_sync_router, prefix="/api", tags=["Snowflake Sync"])`

## ✅ Manual Testing Steps

### 1. Start the Application
```bash
# Use your preferred method to start the application
# This could be through your IDE, start_services.sh, or directly
python main_supabase.py
```

### 2. Test API Endpoints
Once the application is running, test these endpoints:

```bash
# Get sync statistics
curl -X GET "http://localhost:8000/api/snowflake-sync/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get sync queue
curl -X GET "http://localhost:8000/api/snowflake-sync/queue" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get failed syncs
curl -X GET "http://localhost:8000/api/snowflake-sync/failed" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Test Trigger Functionality
1. [ ] Complete a workflow execution (or find an existing completed one)
2. [ ] Check if it appears in the sync queue:
   ```sql
   SELECT * FROM snowflake_sync_queue 
   WHERE execution_id = 'your_execution_id';
   ```
3. [ ] Verify the trigger fired by checking the queue

### 4. Test Snowflake Configuration
1. [ ] Ensure you have a Snowflake configuration in `snowflake_configurations` table
2. [ ] Check that the sync service processes items for users with configs
3. [ ] Verify that users without configs are skipped

## ✅ Expected Behavior

### Normal Operation
- [ ] Completed executions are automatically queued for sync
- [ ] Background service processes queue every 30 seconds
- [ ] Only users with Snowflake configs get their data synced
- [ ] Failed syncs are retried up to 3 times
- [ ] Sync status is updated in both queue and execution records

### Monitoring
- [ ] API endpoints return sync statistics
- [ ] Failed syncs can be viewed and retried
- [ ] Queue status is trackable
- [ ] Individual execution sync status is available

## ✅ Troubleshooting

### Common Issues
1. **No executions in queue**: Check if executions have `result_rows` and `result_total_rows > 0`
2. **Sync not processing**: Verify Snowflake configuration exists for the user
3. **API errors**: Check authentication and user permissions
4. **Service not starting**: Check logs for import errors or missing dependencies

### Debug Queries
```sql
-- Check sync queue status
SELECT status, COUNT(*) FROM snowflake_sync_queue GROUP BY status;

-- Check recent executions
SELECT execution_id, status, result_total_rows, created_at 
FROM workflow_executions 
WHERE status = 'completed' 
ORDER BY created_at DESC 
LIMIT 10;

-- Check user Snowflake configs
SELECT user_id, account_identifier, is_active 
FROM snowflake_configurations 
WHERE is_active = true;
```

## ✅ Success Criteria

The integration is successful when:
- [ ] Database migration completed without errors
- [ ] Service starts with the main application
- [ ] API endpoints are accessible
- [ ] Completed executions are automatically queued
- [ ] Background service processes the queue
- [ ] Users with Snowflake configs get their data synced
- [ ] Monitoring and management tools work correctly

## Next Steps After Verification

1. **Monitor the system** for a few days to ensure stable operation
2. **Set up alerts** for failed syncs if needed
3. **Configure Snowflake credentials** for users who want data syncing
4. **Train users** on the new monitoring endpoints
5. **Document any custom configurations** or modifications made

---

**Note**: If you encounter any issues during verification, check the application logs and database for error messages. The system is designed to be resilient and will retry failed operations automatically.
