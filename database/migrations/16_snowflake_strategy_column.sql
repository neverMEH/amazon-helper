-- Add snowflake_strategy column to workflow_schedules
-- Add snowflake_attempt_count column to workflow_executions
-- Author: Claude Code
-- Date: 2025-11-19
-- Purpose: Enhance Snowflake upload with strategy selection and retry tracking

-- Add strategy column to workflow_schedules
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS snowflake_strategy VARCHAR(20) DEFAULT 'upsert'
CHECK (snowflake_strategy IN ('upsert', 'append', 'replace', 'create_new'));

-- Add retry attempt counter to workflow_executions
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS snowflake_attempt_count INTEGER DEFAULT 0;

-- Performance index for finding failed uploads that need retry
CREATE INDEX IF NOT EXISTS idx_workflow_executions_snowflake_retry
ON workflow_executions(snowflake_status, snowflake_attempt_count)
WHERE snowflake_status = 'failed' AND snowflake_attempt_count < 3;

-- Update table statistics for query planner
ANALYZE workflow_schedules;
ANALYZE workflow_executions;

-- Add helpful comment
COMMENT ON COLUMN workflow_schedules.snowflake_strategy IS 'Upload strategy: upsert (merge with deduplication), append (insert all), replace (truncate and load), create_new (new timestamped table)';
COMMENT ON COLUMN workflow_executions.snowflake_attempt_count IS 'Number of Snowflake upload retry attempts (max 3)';
