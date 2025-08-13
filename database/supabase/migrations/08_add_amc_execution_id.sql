-- Add amc_execution_id column to workflow_executions table
-- This stores the AMC execution ID returned by Amazon for tracking

ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS amc_execution_id TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_workflow_executions_amc_execution_id 
ON workflow_executions(amc_execution_id);

-- Add comment
COMMENT ON COLUMN workflow_executions.amc_execution_id IS 'AMC execution ID returned by Amazon API';