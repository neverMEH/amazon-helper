-- Simple Check Script for Reporting Tables
-- Run each section separately if needed

-- =====================================
-- SECTION 1: Check which tables exist
-- =====================================
SELECT 
    required.table_name as "Table Name",
    CASE 
        WHEN ist.table_name IS NOT NULL THEN '✅ Exists'
        ELSE '❌ Missing'
    END as "Status"
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

-- =====================================
-- SECTION 2: Check if tables have data
-- =====================================
-- Run these one by one if the tables exist:

-- Check dashboards
SELECT 'dashboards' as table_name, COUNT(*) as row_count FROM dashboards;

-- Check report_data_collections  
SELECT 'report_data_collections' as table_name, COUNT(*) as row_count FROM report_data_collections;

-- Check report_data_weeks
SELECT 'report_data_weeks' as table_name, COUNT(*) as row_count FROM report_data_weeks;

-- =====================================
-- SECTION 3: Check triggers
-- =====================================
SELECT 
    trigger_name,
    event_object_table as table_name
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND trigger_name LIKE 'update_%_updated_at'
ORDER BY trigger_name;

-- =====================================
-- SECTION 4: Check indexes
-- =====================================
SELECT 
    indexname as "Index Name",
    tablename as "Table"
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename IN (
    'dashboards',
    'dashboard_widgets', 
    'report_data_collections',
    'report_data_weeks',
    'report_data_aggregates',
    'ai_insights',
    'dashboard_shares'
)
ORDER BY tablename, indexname;