-- Rollback: Remove Snowflake configuration fields from workflow_schedules
-- Created: 2025-10-22

-- Drop index
DROP INDEX IF EXISTS idx_schedules_snowflake_enabled;

-- Remove Snowflake configuration columns
ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS snowflake_schema_name;

ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS snowflake_table_name;

ALTER TABLE workflow_schedules
DROP COLUMN IF EXISTS snowflake_enabled;

-- Verify rollback
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'workflow_schedules'
        AND column_name IN ('snowflake_enabled', 'snowflake_table_name', 'snowflake_schema_name')
    ) THEN
        RAISE NOTICE 'Snowflake columns successfully removed from workflow_schedules';
    ELSE
        RAISE EXCEPTION 'Failed to remove Snowflake columns from workflow_schedules';
    END IF;
END $$;
