-- Verification Script for Instance Templates Migration
-- Run these queries in Supabase SQL Editor AFTER applying the migration
-- to verify everything was created correctly

-- ============================================================================
-- 1. Verify Table Creation
-- ============================================================================

SELECT
    'Table exists: instance_templates' as check_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'instance_templates'
        ) THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status;

-- ============================================================================
-- 2. Verify All Columns Exist
-- ============================================================================

SELECT
    'Column structure' as check_name,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'instance_templates'
        ) = 10 THEN 'PASS ✓ (10 columns)'
        ELSE 'FAIL ✗'
    END as status;

-- List all columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'instance_templates'
ORDER BY ordinal_position;

-- ============================================================================
-- 3. Verify Indexes
-- ============================================================================

SELECT
    'Indexes created' as check_name,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE tablename = 'instance_templates'
        ) >= 4 THEN 'PASS ✓ (4+ indexes)'
        ELSE 'FAIL ✗'
    END as status;

-- List all indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'instance_templates'
ORDER BY indexname;

-- ============================================================================
-- 4. Verify RLS is Enabled
-- ============================================================================

SELECT
    'RLS enabled' as check_name,
    CASE
        WHEN (
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = 'instance_templates'
        ) = true THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status;

-- ============================================================================
-- 5. Verify RLS Policies
-- ============================================================================

SELECT
    'RLS policies' as check_name,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM pg_policies
            WHERE tablename = 'instance_templates'
        ) = 4 THEN 'PASS ✓ (4 policies)'
        ELSE 'FAIL ✗'
    END as status;

-- List all policies
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'instance_templates'
ORDER BY policyname;

-- ============================================================================
-- 6. Verify Foreign Key Constraints
-- ============================================================================

SELECT
    'Foreign key constraints' as check_name,
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_name = 'instance_templates'
            AND constraint_type = 'FOREIGN KEY'
        ) = 2 THEN 'PASS ✓ (2 FKs)'
        ELSE 'FAIL ✗'
    END as status;

-- List all foreign key constraints
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name = 'instance_templates'
ORDER BY tc.constraint_name;

-- ============================================================================
-- 7. Verify Triggers
-- ============================================================================

SELECT
    'Auto-update trigger' as check_name,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM information_schema.triggers
            WHERE event_object_table = 'instance_templates'
            AND trigger_name = 'update_instance_templates_updated_at'
        ) THEN 'PASS ✓'
        ELSE 'FAIL ✗'
    END as status;

-- List all triggers
SELECT trigger_name, event_manipulation, action_statement
FROM information_schema.triggers
WHERE event_object_table = 'instance_templates'
ORDER BY trigger_name;

-- ============================================================================
-- 8. Test RLS Policies (INSERT/SELECT)
-- ============================================================================
-- NOTE: These tests will only work if you're logged in as a user
-- and have valid instance_id and user_id values

-- Test INSERT (should succeed for current user)
-- Replace the UUIDs below with actual values from your database
/*
INSERT INTO instance_templates (
    template_id,
    name,
    description,
    sql_query,
    instance_id,
    user_id
) VALUES (
    'tpl_inst_test123',
    'Test Template',
    'This is a test template for RLS verification',
    'SELECT * FROM campaigns LIMIT 10',
    'YOUR_INSTANCE_ID_HERE',  -- Replace with actual instance UUID
    auth.uid()  -- Current user's ID
);

-- Test SELECT (should only see own templates)
SELECT * FROM instance_templates
WHERE template_id = 'tpl_inst_test123';

-- Test UPDATE (should succeed for own templates)
UPDATE instance_templates
SET name = 'Updated Test Template'
WHERE template_id = 'tpl_inst_test123';

-- Test DELETE (should succeed for own templates)
DELETE FROM instance_templates
WHERE template_id = 'tpl_inst_test123';
*/

-- ============================================================================
-- 9. Test CASCADE Delete
-- ============================================================================
-- This test verifies that deleting an instance or user cascades to templates
-- WARNING: Only run if you have test data you're willing to delete!

/*
-- First, check how many templates exist for a test instance
SELECT COUNT(*) as template_count
FROM instance_templates
WHERE instance_id = 'YOUR_TEST_INSTANCE_ID';

-- Delete the instance (this should cascade to templates)
-- DELETE FROM amc_instances WHERE id = 'YOUR_TEST_INSTANCE_ID';

-- Verify templates were also deleted
SELECT COUNT(*) as template_count_after_delete
FROM instance_templates
WHERE instance_id = 'YOUR_TEST_INSTANCE_ID';
-- Should return 0
*/

-- ============================================================================
-- Summary
-- ============================================================================

SELECT
    'Migration Verification Summary' as info,
    'All checks should show PASS ✓' as expected_result;
