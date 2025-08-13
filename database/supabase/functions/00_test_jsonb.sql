-- Test JSONB operators for Supabase
-- Run these queries to verify JSONB operations are working correctly

-- Test 1: Check if a JSONB array contains a specific value
-- This should return true
SELECT '["user1", "user2", "user3"]'::jsonb ? 'user2';

-- Test 2: Check if a JSONB array does NOT contain a value
-- This should return false
SELECT '["user1", "user2", "user3"]'::jsonb ? 'user4';

-- Test 3: Simulate the shared_with_users check
-- Replace 'test-user-id' with an actual UUID
SELECT 
    '["123e4567-e89b-12d3-a456-426614174000", "987fcdeb-51a2-43f1-b456-426614174001"]'::jsonb ? '123e4567-e89b-12d3-a456-426614174000'::text AS user_is_shared;

-- Test 4: Extract text array from JSONB (for the campaign ASINs)
SELECT jsonb_array_elements_text('["B001", "B002", "B003"]'::jsonb) AS asin;

-- Test 5: Check if any element from one JSONB array exists in another
-- This is useful for finding campaigns with matching ASINs
WITH test_data AS (
    SELECT 
        '["B001", "B002", "B003"]'::jsonb AS campaign_asins,
        ARRAY['B002', 'B004'] AS search_asins
)
SELECT 
    campaign_asins,
    search_asins,
    campaign_asins ?| search_asins AS has_matching_asin
FROM test_data;

-- Test 6: Intersection of JSONB array with text array
-- This shows which ASINs match
WITH test_data AS (
    SELECT 
        '["B001", "B002", "B003"]'::jsonb AS campaign_asins,
        ARRAY['B002', 'B004'] AS search_asins
)
SELECT 
    ARRAY(
        SELECT jsonb_array_elements_text(campaign_asins) 
        INTERSECT 
        SELECT unnest(search_asins)
    ) AS matching_asins
FROM test_data;