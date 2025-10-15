-- Migration: Add missing columns to workflow_schedules
-- Date: 2025-10-15
-- Description: Adds columns for schedule configuration, date ranges, and failure handling

-- Add schedule configuration columns
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS name TEXT;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS schedule_type TEXT DEFAULT 'cron';

-- Add day-specific scheduling columns
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS day_of_week INTEGER CHECK (day_of_week IS NULL OR (day_of_week >= 0 AND day_of_week <= 6));

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS day_of_month INTEGER CHECK (day_of_month IS NULL OR (day_of_month >= 1 AND day_of_month <= 31));

-- Add rolling date range columns
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS lookback_days INTEGER CHECK (lookback_days IS NULL OR (lookback_days >= 1 AND lookback_days <= 365));

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS date_range_type VARCHAR(10) CHECK (date_range_type IS NULL OR date_range_type IN ('rolling', 'fixed'));

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS window_size_days INTEGER CHECK (window_size_days IS NULL OR (window_size_days >= 1 AND window_size_days <= 365));

-- Add failure handling columns
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS auto_pause_on_failure BOOLEAN DEFAULT false;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS failure_threshold INTEGER DEFAULT 3;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS execution_history_limit INTEGER DEFAULT 30;

-- Add comments explaining key columns
COMMENT ON COLUMN workflow_schedules.day_of_week IS 'Day of week for weekly schedules: 0=Sunday, 1=Monday, ..., 6=Saturday';
COMMENT ON COLUMN workflow_schedules.day_of_month IS 'Day of month for monthly schedules: 1-31';
COMMENT ON COLUMN workflow_schedules.lookback_days IS 'Number of days to look back for data (1-365)';
COMMENT ON COLUMN workflow_schedules.date_range_type IS 'How date range is calculated: rolling (advances with each execution) or fixed (always same window relative to execution date)';
COMMENT ON COLUMN workflow_schedules.window_size_days IS 'Explicit window size for clarity (alias for lookback_days)';
COMMENT ON COLUMN workflow_schedules.auto_pause_on_failure IS 'Automatically pause schedule after reaching failure threshold';
COMMENT ON COLUMN workflow_schedules.failure_threshold IS 'Number of consecutive failures before auto-pausing';
COMMENT ON COLUMN workflow_schedules.consecutive_failures IS 'Current count of consecutive failures';

-- Update existing schedules to have NULL for these new fields (backward compatible)
-- No update needed since ALTER TABLE with IF NOT EXISTS will add columns with NULL default
