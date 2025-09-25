-- Verification script for Universal Snowflake Sync migration
-- Run this in your Supabase SQL editor to verify the migration was successful

-- 1. Check if the snowflake_sync_queue table exists and has correct structure
SELECT 
    'snowflake_sync_queue table exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'snowflake_sync_queue' 
        AND table_schema = 'public'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 2. Check table columns
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'snowflake_sync_queue' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 3. Check indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'snowflake_sync_queue';

-- 4. Check constraints
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conrelid = 'snowflake_sync_queue'::regclass;

-- 5. Check if the trigger function exists
SELECT 
    'Trigger function exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'queue_execution_for_universal_snowflake_sync'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 6. Check if the trigger exists
SELECT 
    'Trigger exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trigger_queue_universal_snowflake_sync'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 7. Check if views exist
SELECT 
    'Views exist' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_name IN ('snowflake_sync_queue_summary', 'snowflake_sync_failures')
        AND table_schema = 'public'
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 8. Check RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE tablename = 'snowflake_sync_queue';

-- 9. Test the trigger function (simpler check)
SELECT 
    'Trigger function exists' as check_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'queue_execution_for_universal_snowflake_sync'
        AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    ) THEN 'PASS' ELSE 'FAIL' END as status;

-- 10. Count existing completed executions that could be synced
SELECT 
    'Existing executions ready for sync' as check_name,
    COUNT(*) as count
FROM workflow_executions 
WHERE status = 'completed' 
AND result_rows IS NOT NULL 
AND result_total_rows > 0;

-- 11. Check if any executions are already in the sync queue
SELECT 
    'Executions in sync queue' as check_name,
    COUNT(*) as count
FROM snowflake_sync_queue;

-- 12. Summary
SELECT 
    'Migration Summary' as summary,
    'All checks completed - see results above' as details;
