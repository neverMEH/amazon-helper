-- Migration: Add AMC workflow tracking columns
-- Description: Adds columns to track AMC workflow synchronization and execution modes

-- Add AMC workflow tracking columns to workflows table
ALTER TABLE workflows
ADD COLUMN IF NOT EXISTS amc_workflow_id TEXT,
ADD COLUMN IF NOT EXISTS is_synced_to_amc BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS amc_sync_status TEXT DEFAULT 'not_synced',
ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP WITH TIME ZONE;

-- Add constraint for amc_sync_status values
ALTER TABLE workflows
DROP CONSTRAINT IF EXISTS check_amc_sync_status;

ALTER TABLE workflows
ADD CONSTRAINT check_amc_sync_status 
CHECK (amc_sync_status IN ('not_synced', 'syncing', 'synced', 'sync_failed'));

-- Add index for AMC workflow lookups
CREATE INDEX IF NOT EXISTS idx_workflows_amc_workflow_id 
ON workflows(amc_workflow_id)
WHERE amc_workflow_id IS NOT NULL;

-- Add execution mode tracking to workflow_executions table
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS execution_mode TEXT DEFAULT 'ad_hoc',
ADD COLUMN IF NOT EXISTS amc_workflow_id TEXT;

-- Add constraint to ensure valid execution modes
ALTER TABLE workflow_executions
DROP CONSTRAINT IF EXISTS check_execution_mode;

ALTER TABLE workflow_executions
ADD CONSTRAINT check_execution_mode 
CHECK (execution_mode IN ('ad_hoc', 'saved_workflow'));

-- Update existing executions to be marked as ad_hoc
UPDATE workflow_executions 
SET execution_mode = 'ad_hoc' 
WHERE execution_mode IS NULL;

-- Add index for execution mode queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_mode 
ON workflow_executions(execution_mode);

-- Add comment documentation
COMMENT ON COLUMN workflows.amc_workflow_id IS 'The workflow ID assigned by AMC when the workflow is synced';
COMMENT ON COLUMN workflows.is_synced_to_amc IS 'Whether this workflow has been created in AMC';
COMMENT ON COLUMN workflows.amc_sync_status IS 'Current synchronization status with AMC';
COMMENT ON COLUMN workflows.last_synced_at IS 'Timestamp of last successful sync with AMC';
COMMENT ON COLUMN workflow_executions.execution_mode IS 'Whether this execution used ad_hoc query or saved_workflow';
COMMENT ON COLUMN workflow_executions.amc_workflow_id IS 'The AMC workflow ID used for saved_workflow executions';