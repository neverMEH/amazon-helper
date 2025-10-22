-- Migration: Add Snowflake configuration fields to workflow_schedules
-- Created: 2025-10-22
-- Purpose: Enable schedules to automatically upload execution results to Snowflake

-- Add Snowflake configuration columns to workflow_schedules
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS snowflake_enabled BOOLEAN DEFAULT FALSE;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS snowflake_table_name TEXT;

ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS snowflake_schema_name TEXT;

-- Add comments for documentation
COMMENT ON COLUMN workflow_schedules.snowflake_enabled IS 'Whether to automatically upload execution results to Snowflake';
COMMENT ON COLUMN workflow_schedules.snowflake_table_name IS 'Target Snowflake table name for result uploads';
COMMENT ON COLUMN workflow_schedules.snowflake_schema_name IS 'Target Snowflake schema name (optional, uses user default if not specified)';

-- Create index for filtering schedules with Snowflake enabled
CREATE INDEX IF NOT EXISTS idx_schedules_snowflake_enabled ON workflow_schedules(snowflake_enabled) WHERE snowflake_enabled = TRUE;

-- Verify changes
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_schedules'
        AND column_name IN ('snowflake_enabled', 'snowflake_table_name', 'snowflake_schema_name')
    ) THEN
        RAISE NOTICE 'Snowflake columns successfully added to workflow_schedules';
    ELSE
        RAISE EXCEPTION 'Failed to add Snowflake columns to workflow_schedules';
    END IF;
END $$;
