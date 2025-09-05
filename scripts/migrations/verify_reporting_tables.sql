-- Verification Script for Reporting Tables
-- Run this to check the current state of your database

-- 1. Check which tables exist
SELECT 
    'Tables Check' as check_type,
    table_name,
    CASE 
        WHEN table_name IS NOT NULL THEN '✅ Exists'
        ELSE '❌ Missing'
    END as status
FROM (
    VALUES 
        ('dashboards'),
        ('dashboard_widgets'),
        ('report_data_collections'),
        ('report_data_weeks'),
        ('report_data_aggregates'),
        ('ai_insights'),
        ('dashboard_shares')
) AS required(table_name)
LEFT JOIN information_schema.tables ist 
    ON ist.table_name = required.table_name
    AND ist.table_schema = 'public'
ORDER BY required.table_name;

-- 2. Check for any existing data
SELECT 
    'Data Check' as check_type,
    'report_data_collections' as table_name,
    COUNT(*) as row_count
FROM report_data_collections
UNION ALL
SELECT 
    'Data Check',
    'report_data_weeks',
    COUNT(*)
FROM report_data_weeks
UNION ALL
SELECT 
    'Data Check',
    'dashboards',
    COUNT(*)
FROM dashboards;

-- 3. Check if triggers exist
SELECT 
    'Trigger Check' as check_type,
    trigger_name,
    event_object_table as table_name,
    '✅ Exists' as status
FROM information_schema.triggers
WHERE trigger_name LIKE 'update_%_updated_at'
AND event_object_schema = 'public'
ORDER BY trigger_name;

-- 4. Check indexes
SELECT 
    'Index Check' as check_type,
    indexname,
    tablename,
    '✅ Exists' as status
FROM pg_indexes
WHERE schemaname = 'public'
AND (
    indexname LIKE 'idx_dashboards%'
    OR indexname LIKE 'idx_dashboard_widgets%'
    OR indexname LIKE 'idx_collections%'
    OR indexname LIKE 'idx_weeks%'
    OR indexname LIKE 'idx_aggregates%'
    OR indexname LIKE 'idx_insights%'
    OR indexname LIKE 'idx_shares%'
)
ORDER BY indexname;