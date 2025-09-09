-- Force complete all running weeks for a specific collection
-- Use this if executions are stuck and you need to mark them as completed

-- REPLACE THIS WITH YOUR COLLECTION ID
DO $$
DECLARE
    collection_uuid UUID := '51e6816e-b5bf-40d8-a44e-16d1707c4145';
    updated_count INTEGER;
BEGIN
    -- Update all running weeks to completed for this collection
    UPDATE report_data_weeks
    SET 
        status = 'completed',
        completed_at = NOW(),
        updated_at = NOW()
    WHERE 
        collection_id = collection_uuid
        AND status = 'running';
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    RAISE NOTICE 'Updated % weeks from running to completed', updated_count;
END $$;

-- Verify the results
SELECT 
    status,
    COUNT(*) as count
FROM report_data_weeks
WHERE collection_id = '51e6816e-b5bf-40d8-a44e-16d1707c4145'
GROUP BY status
ORDER BY status;