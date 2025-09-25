-- Migration: Universal Snowflake Sync System
-- Description: Creates sync queue table and trigger for automatic Snowflake syncing of all executions

-- Create table to queue executions for universal Snowflake sync
CREATE TABLE IF NOT EXISTS snowflake_sync_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    execution_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Add indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_snowflake_sync_queue_status 
ON snowflake_sync_queue(status);

CREATE INDEX IF NOT EXISTS idx_snowflake_sync_queue_execution_id 
ON snowflake_sync_queue(execution_id);

CREATE INDEX IF NOT EXISTS idx_snowflake_sync_queue_created_at 
ON snowflake_sync_queue(created_at);

CREATE INDEX IF NOT EXISTS idx_snowflake_sync_queue_user_id 
ON snowflake_sync_queue(user_id);

-- Add constraint for valid status values
ALTER TABLE snowflake_sync_queue
DROP CONSTRAINT IF EXISTS check_sync_queue_status;

ALTER TABLE snowflake_sync_queue
ADD CONSTRAINT check_sync_queue_status 
CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- Add unique constraint to prevent duplicate entries for the same execution
ALTER TABLE snowflake_sync_queue
ADD CONSTRAINT unique_execution_sync 
UNIQUE (execution_id);

-- Add updated_at trigger
CREATE TRIGGER update_snowflake_sync_queue_updated_at 
BEFORE UPDATE ON snowflake_sync_queue
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE snowflake_sync_queue ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own sync queue items" ON snowflake_sync_queue
FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Service role can manage all sync queue items" ON snowflake_sync_queue
FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Function to queue execution for universal Snowflake sync
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

-- Create trigger to automatically queue executions for sync
CREATE TRIGGER trigger_queue_universal_snowflake_sync
    AFTER UPDATE ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION queue_execution_for_universal_snowflake_sync();

-- Add helpful view for sync queue monitoring
CREATE OR REPLACE VIEW snowflake_sync_queue_summary AS
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest_item,
    MAX(created_at) as newest_item,
    AVG(retry_count) as avg_retries
FROM snowflake_sync_queue
GROUP BY status;

-- Add view for failed syncs with details
CREATE OR REPLACE VIEW snowflake_sync_failures AS
SELECT 
    ssq.id,
    ssq.execution_id,
    ssq.user_id,
    ssq.status,
    ssq.retry_count,
    ssq.max_retries,
    ssq.error_message,
    ssq.created_at,
    ssq.updated_at,
    ssq.processed_at,
    we.status as execution_status,
    we.created_at as execution_created_at,
    w.name as workflow_name,
    u.email as user_email
FROM snowflake_sync_queue ssq
JOIN workflow_executions we ON we.execution_id = ssq.execution_id
JOIN workflows w ON w.id = we.workflow_id
JOIN users u ON u.id = ssq.user_id
WHERE ssq.status = 'failed'
ORDER BY ssq.created_at DESC;

-- Grant permissions
GRANT ALL ON snowflake_sync_queue TO authenticated;
GRANT ALL ON snowflake_sync_queue_summary TO authenticated;
GRANT ALL ON snowflake_sync_failures TO authenticated;

-- Add comments for documentation
COMMENT ON TABLE snowflake_sync_queue IS 'Queue for universal Snowflake sync of all workflow executions';
COMMENT ON COLUMN snowflake_sync_queue.execution_id IS 'Reference to workflow_executions.execution_id (unique identifier, not FK)';
COMMENT ON COLUMN snowflake_sync_queue.user_id IS 'User who owns the execution (for Snowflake config lookup)';
COMMENT ON COLUMN snowflake_sync_queue.status IS 'Current sync status: pending, processing, completed, failed';
COMMENT ON COLUMN snowflake_sync_queue.retry_count IS 'Number of retry attempts made';
COMMENT ON COLUMN snowflake_sync_queue.max_retries IS 'Maximum retry attempts before marking as failed';
COMMENT ON COLUMN snowflake_sync_queue.error_message IS 'Error message if sync failed';
COMMENT ON COLUMN snowflake_sync_queue.processed_at IS 'Timestamp when sync was completed or failed';

-- Verify the migration
SELECT 'snowflake_sync_queue table created successfully' as status;
SELECT COUNT(*) as existing_executions FROM workflow_executions WHERE status = 'completed';
