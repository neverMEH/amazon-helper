-- Check the structure of dashboard_shares table if it exists
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'dashboard_shares'
ORDER BY ordinal_position;