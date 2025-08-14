-- Add field_count, example_count, and complexity columns to amc_data_sources table

-- Add field_count column
ALTER TABLE amc_data_sources 
ADD COLUMN IF NOT EXISTS field_count INTEGER DEFAULT 0;

-- Add example_count column
ALTER TABLE amc_data_sources 
ADD COLUMN IF NOT EXISTS example_count INTEGER DEFAULT 0;

-- Add complexity column with check constraint
ALTER TABLE amc_data_sources 
ADD COLUMN IF NOT EXISTS complexity TEXT DEFAULT 'simple'
CHECK (complexity IN ('simple', 'medium', 'complex'));

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_amc_data_sources_field_count ON amc_data_sources(field_count);
CREATE INDEX IF NOT EXISTS idx_amc_data_sources_complexity ON amc_data_sources(complexity);

-- Update existing rows with calculated counts
UPDATE amc_data_sources ds
SET 
    field_count = COALESCE((
        SELECT COUNT(*) 
        FROM amc_schema_fields f 
        WHERE f.data_source_id = ds.id
    ), 0),
    example_count = COALESCE((
        SELECT COUNT(*) 
        FROM amc_query_examples e 
        WHERE e.data_source_id = ds.id
    ), 0);

-- Update complexity based on field count
UPDATE amc_data_sources
SET complexity = CASE
    WHEN field_count < 20 THEN 'simple'
    WHEN field_count < 50 THEN 'medium'
    ELSE 'complex'
END;