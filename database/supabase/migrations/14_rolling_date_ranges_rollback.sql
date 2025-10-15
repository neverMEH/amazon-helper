-- Rollback: Remove rolling date range support from workflow_schedules
-- Date: 2025-10-15

-- Remove rolling date range columns
ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS lookback_days,
DROP COLUMN IF EXISTS date_range_type,
DROP COLUMN IF EXISTS window_size_days;
