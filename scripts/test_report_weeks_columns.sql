-- Quick test to verify report_data_weeks columns
-- Run this in Supabase SQL Editor after migration

-- 1. Show all columns in the table
SELECT 
    column_name AS "Column",
    data_type AS "Type",
    CASE 
        WHEN is_nullable = 'YES' THEN 'NULL' 
        ELSE 'NOT NULL' 
    END AS "Nullable",
    CASE 
        WHEN column_name IN ('execution_id', 'amc_execution_id', 'started_at', 'completed_at', 'record_count')
        THEN '✅ Required'
        ELSE ''
    END AS "Status"
FROM information_schema.columns
WHERE table_name = 'report_data_weeks'
ORDER BY ordinal_position;

-- 2. Test if we can insert/update with the new columns
-- This will verify the schema cache is updated
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Try to use the new columns in an update (won't actually update anything)
    UPDATE report_data_weeks 
    SET 
        execution_id = NULL,
        amc_execution_id = 'test',
        started_at = NOW(),
        completed_at = NOW(),
        record_count = 0
    WHERE id = '00000000-0000-0000-0000-000000000000'::UUID;
    
    RAISE NOTICE '✅ All columns are accessible for updates';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ Error accessing columns: %', SQLERRM;
END $$;

-- 3. Show any existing data with execution tracking
SELECT 
    id,
    week_start_date,
    week_end_date,
    status,
    execution_id,
    amc_execution_id,
    record_count,
    started_at,
    completed_at
FROM report_data_weeks
WHERE execution_id IS NOT NULL
   OR amc_execution_id IS NOT NULL
LIMIT 5;