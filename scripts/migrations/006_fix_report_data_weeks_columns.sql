-- Migration to ensure report_data_weeks has all required columns
-- Run this in Supabase SQL Editor to fix column issues

BEGIN;

-- Check and add missing columns to report_data_weeks
DO $$
BEGIN
    -- Add execution_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'execution_id'
    ) THEN
        ALTER TABLE report_data_weeks 
        ADD COLUMN execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL;
        RAISE NOTICE 'Added execution_id column';
    ELSE
        RAISE NOTICE 'execution_id column already exists';
    END IF;

    -- Add amc_execution_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'amc_execution_id'
    ) THEN
        ALTER TABLE report_data_weeks 
        ADD COLUMN amc_execution_id VARCHAR(255);
        RAISE NOTICE 'Added amc_execution_id column';
    ELSE
        RAISE NOTICE 'amc_execution_id column already exists';
    END IF;

    -- Add started_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'started_at'
    ) THEN
        ALTER TABLE report_data_weeks 
        ADD COLUMN started_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added started_at column';
    ELSE
        RAISE NOTICE 'started_at column already exists';
    END IF;

    -- Add completed_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'completed_at'
    ) THEN
        ALTER TABLE report_data_weeks 
        ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added completed_at column';
    ELSE
        RAISE NOTICE 'completed_at column already exists';
    END IF;

    -- Add record_count column if it doesn't exist (some schemas might have row_count instead)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'record_count'
    ) THEN
        -- Check if row_count exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'report_data_weeks' 
            AND column_name = 'row_count'
        ) THEN
            -- Rename row_count to record_count for consistency
            ALTER TABLE report_data_weeks 
            RENAME COLUMN row_count TO record_count;
            RAISE NOTICE 'Renamed row_count to record_count';
        ELSE
            -- Add record_count column
            ALTER TABLE report_data_weeks 
            ADD COLUMN record_count INTEGER;
            RAISE NOTICE 'Added record_count column';
        END IF;
    ELSE
        RAISE NOTICE 'record_count column already exists';
    END IF;

    -- Add execution_time_seconds if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'execution_time_seconds'
    ) THEN
        ALTER TABLE report_data_weeks 
        ADD COLUMN execution_time_seconds INTEGER;
        RAISE NOTICE 'Added execution_time_seconds column';
    END IF;

    -- Ensure data_checksum has correct size
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'data_checksum'
        AND character_maximum_length < 64
    ) THEN
        ALTER TABLE report_data_weeks 
        ALTER COLUMN data_checksum TYPE VARCHAR(64);
        RAISE NOTICE 'Updated data_checksum column size';
    END IF;

END $$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_report_weeks_execution_id 
    ON report_data_weeks(execution_id) 
    WHERE execution_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_report_weeks_status_running 
    ON report_data_weeks(status) 
    WHERE status = 'running';

-- Verify the changes
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'report_data_weeks'
    AND column_name IN (
        'execution_id', 
        'amc_execution_id', 
        'started_at', 
        'completed_at',
        'record_count',
        'execution_time_seconds'
    );
    
    IF col_count >= 6 THEN
        RAISE NOTICE '✅ All required columns are present';
    ELSE
        RAISE WARNING '⚠️ Only % of 6 required columns found', col_count;
    END IF;
END $$;

-- Display current table structure
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'report_data_weeks'
ORDER BY ordinal_position;

COMMIT;

-- After running this migration, the schema cache will automatically refresh
-- Wait about 60 seconds before testing the application again