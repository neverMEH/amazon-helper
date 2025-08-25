-- Add lookback_days column to workflow_schedules table
-- This allows users to configure a custom lookback window for scheduled workflows

-- Add the column if it doesn't exist
ALTER TABLE workflow_schedules 
ADD COLUMN IF NOT EXISTS lookback_days INTEGER DEFAULT 1;

-- Add a comment to document the column
COMMENT ON COLUMN workflow_schedules.lookback_days IS 'Number of days to look back for data when executing the scheduled workflow';

-- Update existing schedules to set appropriate lookback_days based on their interval
UPDATE workflow_schedules 
SET lookback_days = CASE
    WHEN interval_days IS NOT NULL THEN interval_days
    WHEN schedule_type = 'weekly' THEN 7
    WHEN schedule_type = 'monthly' THEN 30
    ELSE 1  -- Daily or other
END
WHERE lookback_days IS NULL OR lookback_days = 1;

-- Verify the migration
SELECT 
    'Migration completed successfully!' as message,
    COUNT(*) as schedules_updated
FROM workflow_schedules
WHERE lookback_days IS NOT NULL;