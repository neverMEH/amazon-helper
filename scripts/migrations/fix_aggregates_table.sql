-- Fix report_data_aggregates table column names
-- This script handles the case where the table exists with wrong column names

-- First, check what columns currently exist
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'report_data_aggregates'
ORDER BY ordinal_position;

-- If the table has the wrong columns (date_range_start, date_range_end),
-- we need to rename them or recreate the table

-- Option 1: Rename columns if they exist with wrong names
DO $$
BEGIN
    -- Check if old column names exist
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_aggregates' 
        AND column_name = 'date_range_start'
    ) THEN
        ALTER TABLE report_data_aggregates 
        RENAME COLUMN date_range_start TO date_start;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_aggregates' 
        AND column_name = 'date_range_end'
    ) THEN
        ALTER TABLE report_data_aggregates 
        RENAME COLUMN date_range_end TO date_end;
    END IF;
END $$;

-- Option 2: If the table doesn't exist or is empty, drop and recreate
-- ONLY run this if you're sure there's no data you need to keep!

/*
DROP TABLE IF EXISTS report_data_aggregates CASCADE;

CREATE TABLE report_data_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    aggregation_type VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL,
    dimensions JSONB DEFAULT '{}',
    data_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_aggregate UNIQUE(workflow_id, instance_id, date_start, date_end, aggregation_type)
);

-- Create indexes
CREATE INDEX idx_aggregates_workflow_instance ON report_data_aggregates(workflow_id, instance_id);
CREATE INDEX idx_aggregates_dates ON report_data_aggregates(date_start, date_end);
*/

-- Verify the final structure
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'report_data_aggregates'
ORDER BY ordinal_position;