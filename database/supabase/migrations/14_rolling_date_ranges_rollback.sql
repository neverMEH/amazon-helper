-- Rollback: Remove added columns from workflow_schedules
-- Date: 2025-10-15

-- Remove all columns added in migration 14
ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS user_id,
DROP COLUMN IF EXISTS name,
DROP COLUMN IF EXISTS description,
DROP COLUMN IF EXISTS schedule_type,
DROP COLUMN IF EXISTS day_of_week,
DROP COLUMN IF EXISTS day_of_month,
DROP COLUMN IF EXISTS lookback_days,
DROP COLUMN IF EXISTS date_range_type,
DROP COLUMN IF EXISTS window_size_days,
DROP COLUMN IF EXISTS auto_pause_on_failure,
DROP COLUMN IF EXISTS failure_threshold,
DROP COLUMN IF EXISTS consecutive_failures,
DROP COLUMN IF EXISTS execution_history_limit;
