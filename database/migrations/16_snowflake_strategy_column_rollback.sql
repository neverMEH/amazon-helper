-- Rollback: Remove snowflake_strategy and snowflake_attempt_count columns
-- Author: Claude Code
-- Date: 2025-11-19
-- Purpose: Rollback Snowflake strategy and retry tracking enhancements

-- Drop performance index
DROP INDEX IF EXISTS idx_workflow_executions_snowflake_retry;

-- Remove retry attempt counter from workflow_executions
ALTER TABLE workflow_executions
DROP COLUMN IF EXISTS snowflake_attempt_count;

-- Remove strategy column from workflow_schedules
ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS snowflake_strategy;

-- Update table statistics
ANALYZE workflow_schedules;
ANALYZE workflow_executions;
