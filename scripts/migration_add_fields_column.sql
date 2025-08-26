
-- Add fields column to amc_data_sources table
ALTER TABLE public.amc_data_sources 
ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN public.amc_data_sources.fields IS 'Array of field definitions for this data source schema';

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_amc_data_sources_fields ON public.amc_data_sources USING GIN (fields);
