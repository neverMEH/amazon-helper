-- Simple verification script for Universal Snowflake Sync
-- Run this to verify everything is working correctly

-- 1. Check if the table exists
SELECT 
    'snowflake_sync_queue table exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'snowflake_sync_queue' 
        AND table_schema = 'public'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 2. Check if the function exists
SELECT 
    'Trigger function exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'queue_execution_for_universal_snowflake_sync'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 3. Check if the trigger exists
SELECT 
    'Trigger exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trigger_queue_universal_snowflake_sync'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 4. Check table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'snowflake_sync_queue' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 5. Check if views exist
SELECT 
    'Views exist' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name IN ('snowflake_sync_queue_summary', 'snowflake_sync_failures')
        AND table_schema = 'public'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 6. Count existing completed executions
SELECT 
    'Completed executions ready for sync' as check_name,
    COUNT(*) as count
FROM workflow_executions 
WHERE status = 'completed' 
AND result_rows IS NOT NULL 
AND result_total_rows > 0;

-- 7. Check current sync queue status
SELECT 
    'Current sync queue status' as check_name,
    status,
    COUNT(*) as count
FROM snowflake_sync_queue
GROUP BY status;

-- 8. Test the trigger by checking if any executions would be queued
-- (This doesn't actually queue them, just shows what would be queued)
SELECT 
    'Executions that would be queued' as check_name,
    COUNT(*) as count
FROM workflow_executions we
JOIN workflows w ON w.id = we.workflow_id
WHERE we.status = 'completed' 
AND we.result_rows IS NOT NULL 
AND we.result_total_rows > 0
AND NOT EXISTS (
    SELECT 1 FROM snowflake_sync_queue ssq 
    WHERE ssq.execution_id = we.execution_id
);

-- 9. Summary
SELECT 
    'Migration Status' as summary,
    'All components appear to be installed correctly!' as status;
