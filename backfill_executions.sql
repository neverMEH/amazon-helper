-- Backfill script to queue existing completed executions for Snowflake sync
-- This script will find all completed executions from the last 7 days
-- and queue them for universal Snowflake sync

-- First, let's see what completed executions we have
SELECT 
    'Completed executions in last 7 days' as info,
    COUNT(*) as count
FROM workflow_executions we
WHERE we.status = 'completed' 
  AND we.created_at >= NOW() - INTERVAL '7 days'
  AND we.result_rows IS NOT NULL 
  AND we.result_total_rows > 0;

-- Show some sample executions
SELECT 
    'Sample completed executions' as info,
    we.execution_id,
    we.workflow_id,
    we.status,
    we.result_total_rows,
    we.created_at,
    w.name as workflow_name,
    u.email as user_email
FROM workflow_executions we
JOIN workflows w ON w.id = we.workflow_id
JOIN users u ON u.id = w.user_id
WHERE we.status = 'completed' 
  AND we.created_at >= NOW() - INTERVAL '7 days'
  AND we.result_rows IS NOT NULL 
  AND we.result_total_rows > 0
ORDER BY we.created_at DESC
LIMIT 5;

-- Check which executions are already queued
SELECT 
    'Already queued executions' as info,
    COUNT(*) as count
FROM snowflake_sync_queue ssq
JOIN workflow_executions we ON we.execution_id = ssq.execution_id
WHERE we.status = 'completed' 
  AND we.created_at >= NOW() - INTERVAL '7 days';

-- Queue new executions for sync
-- This will insert executions that aren't already queued
INSERT INTO snowflake_sync_queue (execution_id, user_id, status)
SELECT DISTINCT
    we.execution_id,
    w.user_id,
    'pending'::VARCHAR(50)
FROM workflow_executions we
JOIN workflows w ON w.id = we.workflow_id
WHERE we.status = 'completed' 
  AND we.created_at >= NOW() - INTERVAL '7 days'
  AND we.result_rows IS NOT NULL 
  AND we.result_total_rows > 0
  AND NOT EXISTS (
      SELECT 1 FROM snowflake_sync_queue ssq 
      WHERE ssq.execution_id = we.execution_id
  );

-- Show the results
SELECT 
    'Backfill completed' as info,
    COUNT(*) as newly_queued_executions
FROM snowflake_sync_queue ssq
WHERE ssq.status = 'pending'
  AND ssq.created_at >= NOW() - INTERVAL '1 minute';

-- Show current queue status
SELECT 
    'Current sync queue status' as info,
    status,
    COUNT(*) as count
FROM snowflake_sync_queue
GROUP BY status
ORDER BY status;

-- Show users who have Snowflake configurations (these will actually sync)
SELECT 
    'Users with Snowflake configs' as info,
    COUNT(DISTINCT sc.user_id) as users_with_snowflake,
    COUNT(DISTINCT ssq.user_id) as users_in_queue
FROM snowflake_configurations sc
FULL OUTER JOIN snowflake_sync_queue ssq ON ssq.user_id = sc.user_id
WHERE ssq.status = 'pending' OR sc.user_id IS NOT NULL;
