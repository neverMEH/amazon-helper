-- Check what columns exist in the report_data_aggregates table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'report_data_aggregates'
ORDER BY ordinal_position;