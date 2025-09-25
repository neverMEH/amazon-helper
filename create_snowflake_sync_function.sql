-- Manual function creation script
-- Run this if the function doesn't exist or needs to be recreated

-- Manual function recreation script
-- Run this if you need to recreate the function and trigger

-- Drop the trigger first (since it depends on the function)
DROP TRIGGER IF EXISTS trigger_queue_universal_snowflake_sync ON workflow_executions;

-- Drop the function
DROP FUNCTION IF EXISTS queue_execution_for_universal_snowflake_sync();

-- Create the function
CREATE OR REPLACE FUNCTION queue_execution_for_universal_snowflake_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Only queue completed executions with results
    IF NEW.status = 'completed' 
       AND NEW.result_rows IS NOT NULL 
       AND NEW.result_total_rows > 0
       AND NOT EXISTS (
           SELECT 1 FROM snowflake_sync_queue 
           WHERE execution_id = NEW.execution_id
       ) THEN
        
        -- Get user_id from workflow
        INSERT INTO snowflake_sync_queue (execution_id, user_id)
        SELECT NEW.execution_id, w.user_id
        FROM workflows w
        WHERE w.id = NEW.workflow_id;
        
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger if it doesn't exist
DROP TRIGGER IF EXISTS trigger_queue_universal_snowflake_sync ON workflow_executions;

CREATE TRIGGER trigger_queue_universal_snowflake_sync
    AFTER UPDATE ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION queue_execution_for_universal_snowflake_sync();

-- Verify the function was created
SELECT 
    'Function created successfully' as status,
    proname as function_name,
    prokind as function_type
FROM pg_proc 
WHERE proname = 'queue_execution_for_universal_snowflake_sync';

-- Verify the trigger was created
SELECT 
    'Trigger created successfully' as status,
    tgname as trigger_name,
    tgrelid::regclass as table_name
FROM pg_trigger 
WHERE tgname = 'trigger_queue_universal_snowflake_sync';
