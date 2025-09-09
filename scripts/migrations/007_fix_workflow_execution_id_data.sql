-- Migration to fix workflow_execution_id column data
-- The execution_id column has the data, but workflow_execution_id is empty
-- This migration copies the data and ensures both columns work

BEGIN;

-- First, let's see the current state
DO $$
DECLARE
    total_records INTEGER;
    records_with_execution_id INTEGER;
    records_with_workflow_execution_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_records FROM report_data_weeks;
    SELECT COUNT(*) INTO records_with_execution_id FROM report_data_weeks WHERE execution_id IS NOT NULL;
    SELECT COUNT(*) INTO records_with_workflow_execution_id FROM report_data_weeks WHERE workflow_execution_id IS NOT NULL;
    
    RAISE NOTICE 'Total records: %', total_records;
    RAISE NOTICE 'Records with execution_id: %', records_with_execution_id;
    RAISE NOTICE 'Records with workflow_execution_id: %', records_with_workflow_execution_id;
END $$;

-- Copy execution_id to workflow_execution_id where it's missing
UPDATE report_data_weeks
SET workflow_execution_id = execution_id
WHERE execution_id IS NOT NULL 
  AND workflow_execution_id IS NULL;

-- Verify the update
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO updated_count 
    FROM report_data_weeks 
    WHERE workflow_execution_id IS NOT NULL;
    
    RAISE NOTICE '✅ Updated workflow_execution_id for % records', updated_count;
END $$;

-- Create a trigger to keep both columns in sync going forward
-- This ensures backward compatibility
CREATE OR REPLACE FUNCTION sync_execution_id_columns()
RETURNS TRIGGER AS $$
BEGIN
    -- If execution_id is set but workflow_execution_id is not, copy it
    IF NEW.execution_id IS NOT NULL AND NEW.workflow_execution_id IS NULL THEN
        NEW.workflow_execution_id := NEW.execution_id;
    -- If workflow_execution_id is set but execution_id is not, copy it
    ELSIF NEW.workflow_execution_id IS NOT NULL AND NEW.execution_id IS NULL THEN
        NEW.execution_id := NEW.workflow_execution_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if it exists
DROP TRIGGER IF EXISTS sync_execution_ids ON report_data_weeks;

-- Create trigger for both INSERT and UPDATE
CREATE TRIGGER sync_execution_ids
BEFORE INSERT OR UPDATE ON report_data_weeks
FOR EACH ROW
EXECUTE FUNCTION sync_execution_id_columns();

-- Test the trigger with a sample update
DO $$
DECLARE
    test_id UUID;
BEGIN
    -- Get a record to test with
    SELECT id INTO test_id FROM report_data_weeks WHERE execution_id IS NOT NULL LIMIT 1;
    
    IF test_id IS NOT NULL THEN
        -- This should trigger the sync
        UPDATE report_data_weeks 
        SET updated_at = NOW() 
        WHERE id = test_id;
        
        RAISE NOTICE '✅ Trigger test completed';
    END IF;
END $$;

-- Final verification
SELECT 
    COUNT(*) AS total_records,
    COUNT(execution_id) AS with_execution_id,
    COUNT(workflow_execution_id) AS with_workflow_execution_id,
    COUNT(CASE WHEN execution_id = workflow_execution_id THEN 1 END) AS matching_ids
FROM report_data_weeks;

COMMIT;

-- Note: After running this migration, both columns will be populated
-- The trigger ensures future inserts/updates keep them in sync