-- Add AMC sync tracking columns to workflows table
ALTER TABLE workflows 
ADD COLUMN IF NOT EXISTS amc_workflow_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS is_synced_to_amc BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS amc_sync_status VARCHAR(50) DEFAULT 'not_synced',
ADD COLUMN IF NOT EXISTS amc_synced_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS amc_last_updated_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_amc_workflow_id 
ON workflows(amc_workflow_id) 
WHERE amc_workflow_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workflows_is_synced_to_amc 
ON workflows(is_synced_to_amc) 
WHERE is_synced_to_amc = TRUE;

-- Add comments for documentation
COMMENT ON COLUMN workflows.amc_workflow_id IS 'AMC workflow ID when synced to Amazon Marketing Cloud';
COMMENT ON COLUMN workflows.is_synced_to_amc IS 'Whether this workflow is synced to AMC';
COMMENT ON COLUMN workflows.amc_sync_status IS 'Status of AMC sync: not_synced, syncing, synced, failed';
COMMENT ON COLUMN workflows.amc_synced_at IS 'Timestamp when workflow was first synced to AMC';
COMMENT ON COLUMN workflows.amc_last_updated_at IS 'Timestamp when workflow was last updated in AMC';