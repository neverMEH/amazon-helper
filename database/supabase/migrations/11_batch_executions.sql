-- Migration: Add batch execution support for multi-instance workflow execution
-- This migration adds tables and columns to support running a single workflow across multiple AMC instances

-- Create batch_executions table to track grouped executions
CREATE TABLE IF NOT EXISTS batch_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id TEXT UNIQUE NOT NULL, -- Format: batch_XXXXXXXX
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    name TEXT,
    description TEXT,
    instance_ids JSONB NOT NULL, -- Array of instance UUIDs
    base_parameters JSONB DEFAULT '{}', -- Common parameters for all instances
    instance_parameters JSONB DEFAULT '{}', -- Per-instance parameter overrides
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'partial', 'failed', 'cancelled')),
    total_instances INTEGER NOT NULL,
    completed_instances INTEGER DEFAULT 0,
    failed_instances INTEGER DEFAULT 0,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add columns to workflow_executions for batch support
ALTER TABLE workflow_executions 
ADD COLUMN IF NOT EXISTS batch_execution_id UUID REFERENCES batch_executions(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS target_instance_id UUID REFERENCES amc_instances(id),
ADD COLUMN IF NOT EXISTS is_batch_member BOOLEAN DEFAULT false;

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_batch_executions_workflow_id ON batch_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_batch_executions_status ON batch_executions(status);
CREATE INDEX IF NOT EXISTS idx_batch_executions_user_id ON batch_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_batch_executions_batch_id ON batch_executions(batch_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_batch_id ON workflow_executions(batch_execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_target_instance ON workflow_executions(target_instance_id);

-- Create view for batch execution summary
CREATE OR REPLACE VIEW batch_execution_summary AS
SELECT 
    be.id,
    be.batch_id,
    be.workflow_id,
    be.name,
    be.description,
    be.status,
    be.total_instances,
    be.completed_instances,
    be.failed_instances,
    be.user_id,
    be.started_at,
    be.completed_at,
    be.created_at,
    COUNT(we.id) as total_executions,
    COUNT(CASE WHEN we.status = 'completed' THEN 1 END) as actual_completed,
    COUNT(CASE WHEN we.status = 'failed' THEN 1 END) as actual_failed,
    COUNT(CASE WHEN we.status = 'running' THEN 1 END) as running_count,
    COUNT(CASE WHEN we.status = 'pending' THEN 1 END) as pending_count,
    AVG(we.duration_seconds) as avg_duration_seconds,
    SUM(we.row_count) as total_rows,
    MIN(we.started_at) as first_started_at,
    MAX(we.completed_at) as last_completed_at
FROM batch_executions be
LEFT JOIN workflow_executions we ON we.batch_execution_id = be.id
GROUP BY be.id;

-- Create function to update batch execution status based on child executions
CREATE OR REPLACE FUNCTION update_batch_execution_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the batch execution status based on child execution statuses
    UPDATE batch_executions be
    SET 
        completed_instances = (
            SELECT COUNT(*) FROM workflow_executions 
            WHERE batch_execution_id = NEW.batch_execution_id 
            AND status = 'completed'
        ),
        failed_instances = (
            SELECT COUNT(*) FROM workflow_executions 
            WHERE batch_execution_id = NEW.batch_execution_id 
            AND status = 'failed'
        ),
        status = CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM workflow_executions 
                WHERE batch_execution_id = NEW.batch_execution_id 
                AND status IN ('pending', 'running')
            ) THEN
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM workflow_executions 
                        WHERE batch_execution_id = NEW.batch_execution_id 
                        AND status = 'failed'
                    ) AND EXISTS (
                        SELECT 1 FROM workflow_executions 
                        WHERE batch_execution_id = NEW.batch_execution_id 
                        AND status = 'completed'
                    ) THEN 'partial'
                    WHEN NOT EXISTS (
                        SELECT 1 FROM workflow_executions 
                        WHERE batch_execution_id = NEW.batch_execution_id 
                        AND status = 'failed'
                    ) THEN 'completed'
                    ELSE 'failed'
                END
            WHEN EXISTS (
                SELECT 1 FROM workflow_executions 
                WHERE batch_execution_id = NEW.batch_execution_id 
                AND status = 'running'
            ) THEN 'running'
            ELSE be.status
        END,
        completed_at = CASE
            WHEN NOT EXISTS (
                SELECT 1 FROM workflow_executions 
                WHERE batch_execution_id = NEW.batch_execution_id 
                AND status IN ('pending', 'running')
            ) THEN NOW()
            ELSE be.completed_at
        END,
        started_at = COALESCE(be.started_at, NOW()),
        updated_at = NOW()
    WHERE id = NEW.batch_execution_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update batch execution status
CREATE TRIGGER update_batch_status_on_execution_change
AFTER UPDATE OF status ON workflow_executions
FOR EACH ROW
WHEN (NEW.batch_execution_id IS NOT NULL)
EXECUTE FUNCTION update_batch_execution_status();

-- Add RLS policies for batch_executions
ALTER TABLE batch_executions ENABLE ROW LEVEL SECURITY;

-- Users can view their own batch executions
CREATE POLICY "Users can view own batch executions" ON batch_executions
    FOR SELECT USING (auth.uid() = user_id);

-- Users can create batch executions
CREATE POLICY "Users can create batch executions" ON batch_executions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own batch executions
CREATE POLICY "Users can update own batch executions" ON batch_executions
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own batch executions
CREATE POLICY "Users can delete own batch executions" ON batch_executions
    FOR DELETE USING (auth.uid() = user_id);

-- Grant permissions
GRANT ALL ON batch_executions TO authenticated;
GRANT ALL ON batch_execution_summary TO authenticated;

-- Add function to generate batch ID
CREATE OR REPLACE FUNCTION generate_batch_id()
RETURNS TEXT AS $$
DECLARE
    new_id TEXT;
    exists_count INTEGER;
BEGIN
    LOOP
        -- Generate a random 8-character ID with batch_ prefix
        new_id := 'batch_' || substr(md5(random()::text), 1, 8);
        
        -- Check if this ID already exists
        SELECT COUNT(*) INTO exists_count
        FROM batch_executions
        WHERE batch_id = new_id;
        
        -- If it doesn't exist, we can use it
        EXIT WHEN exists_count = 0;
    END LOOP;
    
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON TABLE batch_executions IS 'Tracks batch execution of workflows across multiple AMC instances';
COMMENT ON COLUMN batch_executions.batch_id IS 'Unique identifier for the batch execution (format: batch_XXXXXXXX)';
COMMENT ON COLUMN batch_executions.instance_ids IS 'Array of AMC instance UUIDs this batch will execute on';
COMMENT ON COLUMN batch_executions.base_parameters IS 'Common parameters applied to all instances';
COMMENT ON COLUMN batch_executions.instance_parameters IS 'Per-instance parameter overrides, keyed by instance UUID';
COMMENT ON COLUMN workflow_executions.batch_execution_id IS 'Reference to parent batch execution if this is part of a batch';
COMMENT ON COLUMN workflow_executions.target_instance_id IS 'The specific instance this execution targets (for batch executions)';
COMMENT ON COLUMN workflow_executions.is_batch_member IS 'Flag indicating if this execution is part of a batch';