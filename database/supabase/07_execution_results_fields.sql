-- Add execution results fields to workflow_executions table

-- Add result storage columns to workflow_executions
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS result_columns JSONB,
ADD COLUMN IF NOT EXISTS result_rows JSONB,
ADD COLUMN IF NOT EXISTS result_total_rows INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS result_sample_size INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS query_runtime_seconds NUMERIC,
ADD COLUMN IF NOT EXISTS data_scanned_gb NUMERIC,
ADD COLUMN IF NOT EXISTS cost_estimate_usd NUMERIC;

-- Add index on execution_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_id 
ON workflow_executions(execution_id);

-- Add index on workflow_id and created_at for listing executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_created 
ON workflow_executions(workflow_id, created_at DESC);

-- Update RLS policies to allow users to read their execution results
DROP POLICY IF EXISTS "Users can view their workflow execution results" ON workflow_executions;

CREATE POLICY "Users can view their workflow execution results" ON workflow_executions
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM workflows 
        WHERE workflows.id = workflow_executions.workflow_id 
        AND workflows.user_id = auth.uid()
    )
);