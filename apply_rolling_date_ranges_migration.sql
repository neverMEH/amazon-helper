-- Apply Rolling Date Ranges Migration
-- Run this SQL script in your Supabase SQL Editor or via psql

-- Migration: Add rolling date range support to workflow_schedules
-- Date: 2025-10-15
-- Description: Adds columns for configuring rolling date ranges in scheduled workflows

BEGIN;

-- Add lookback_days column (number of days to look back for data)
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS lookback_days INTEGER
CHECK (lookback_days IS NULL OR (lookback_days >= 1 AND lookback_days <= 365));

-- Add date_range_type column (rolling or fixed)
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS date_range_type VARCHAR(10)
CHECK (date_range_type IS NULL OR date_range_type IN ('rolling', 'fixed'));

-- Add window_size_days column (explicit window size, alias for lookback_days)
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS window_size_days INTEGER
CHECK (window_size_days IS NULL OR (window_size_days >= 1 AND window_size_days <= 365));

-- Add comment explaining these columns
COMMENT ON COLUMN workflow_schedules.lookback_days IS 'Number of days to look back for data (1-365)';
COMMENT ON COLUMN workflow_schedules.date_range_type IS 'How date range is calculated: rolling (advances with each execution) or fixed (always same window relative to execution date)';
COMMENT ON COLUMN workflow_schedules.window_size_days IS 'Explicit window size for clarity (alias for lookback_days)';

COMMIT;

-- Verify the migration
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'workflow_schedules'
    AND column_name IN ('lookback_days', 'date_range_type', 'window_size_days')
ORDER BY column_name;
