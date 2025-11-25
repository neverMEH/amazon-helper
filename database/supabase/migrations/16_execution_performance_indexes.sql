-- Performance indexes for faster execution queries
-- These indexes support the optimized JOIN queries in amc_executions.py

-- Index on workflow_executions for faster workflow_id lookups
-- Used in: list_all_stored_executions, list_stored_executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id
ON workflow_executions(workflow_id);

-- Composite index for common query pattern: workflow_id + started_at (descending)
-- Used for: recent executions queries with ORDER BY started_at DESC
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_started
ON workflow_executions(workflow_id, started_at DESC);

-- Index on workflow_executions for status filtering
-- Used for: finding pending/running executions for smart polling
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status
ON workflow_executions(status);

-- Index on workflow_executions for amc_execution_id lookups
-- Used for: looking up execution by AMC execution ID
CREATE INDEX IF NOT EXISTS idx_workflow_executions_amc_execution_id
ON workflow_executions(amc_execution_id);

-- Index on workflow_executions for user_id lookups
-- Used for: filtering executions by user in stats endpoint
CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_id
ON workflow_executions(user_id);

-- Composite index for user + started_at (for recent executions count in stats)
CREATE INDEX IF NOT EXISTS idx_workflow_executions_user_started
ON workflow_executions(user_id, started_at DESC);

-- Index on workflows for user_id lookups
-- Used in: all workflow queries filter by user
CREATE INDEX IF NOT EXISTS idx_workflows_user_id
ON workflows(user_id);

-- Index on amc_accounts for user_id lookups
-- Used in: get_user_instances, stats endpoint
CREATE INDEX IF NOT EXISTS idx_amc_accounts_user_id
ON amc_accounts(user_id);

-- Index on campaigns for instance_id lookups
-- Used in: stats endpoint, campaign list queries
CREATE INDEX IF NOT EXISTS idx_campaigns_instance_id
ON campaigns(instance_id);

-- Analyze tables to update statistics after adding indexes
ANALYZE workflow_executions;
ANALYZE workflows;
ANALYZE amc_accounts;
ANALYZE campaigns;
