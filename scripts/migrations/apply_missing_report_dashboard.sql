
-- Create collection_report_configs table
CREATE TABLE IF NOT EXISTS public.collection_report_configs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    config_name text NOT NULL,
    chart_configs jsonb NOT NULL DEFAULT '{}',
    default_view text DEFAULT 'trending' CHECK (default_view IN ('trending', 'comparison', 'aggregate')),
    default_weeks_shown int4 DEFAULT 12 CHECK (default_weeks_shown > 0 AND default_weeks_shown <= 52),
    saved_comparisons jsonb DEFAULT '[]',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(collection_id, user_id, config_name)
);


-- Create collection_report_snapshots table
CREATE TABLE IF NOT EXISTS public.collection_report_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id text UNIQUE NOT NULL,
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
    snapshot_name text NOT NULL,
    snapshot_data jsonb NOT NULL,
    week_range jsonb NOT NULL,
    comparison_settings jsonb DEFAULT NULL,
    chart_images jsonb DEFAULT NULL,
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz DEFAULT NULL,
    is_public boolean DEFAULT false,
    access_count int4 DEFAULT 0
);


-- Add columns to report_data_collections
ALTER TABLE report_data_collections 
ADD COLUMN IF NOT EXISTS report_metadata jsonb DEFAULT NULL,
ADD COLUMN IF NOT EXISTS last_report_generated_at timestamptz DEFAULT NULL;


-- Add column to report_data_weeks
ALTER TABLE report_data_weeks
ADD COLUMN IF NOT EXISTS summary_stats jsonb DEFAULT NULL;


-- Create indexes
CREATE INDEX IF NOT EXISTS idx_report_configs_user_collection 
ON collection_report_configs(user_id, collection_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_snapshots_public 
ON collection_report_snapshots(snapshot_id, is_public) 
WHERE is_public = true;

CREATE INDEX IF NOT EXISTS idx_week_summary_stats 
ON report_data_weeks USING gin(summary_stats)
WHERE summary_stats IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collection_weeks_summary 
ON report_data_weeks(collection_id, week_start_date) 
WHERE status = 'succeeded' AND summary_stats IS NOT NULL;


-- Enable RLS
ALTER TABLE collection_report_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_report_snapshots ENABLE ROW LEVEL SECURITY;


-- Create RLS policies for collection_report_configs
CREATE POLICY "Users can view their own report configs"
ON collection_report_configs FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own report configs"
ON collection_report_configs FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own report configs"
ON collection_report_configs FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own report configs"
ON collection_report_configs FOR DELETE
USING (auth.uid() = user_id);


-- Create RLS policies for collection_report_snapshots
CREATE POLICY "Users can view their own snapshots or public snapshots"
ON collection_report_snapshots FOR SELECT
USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users can create their own snapshots"
ON collection_report_snapshots FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own snapshots"
ON collection_report_snapshots FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own snapshots"
ON collection_report_snapshots FOR DELETE
USING (auth.uid() = user_id);


-- Create summary view
CREATE OR REPLACE VIEW collection_report_summary AS
SELECT 
    c.id as collection_id,
    c.collection_id as external_id,
    c.workflow_id,
    c.user_id,
    c.collection_type,
    c.target_weeks,
    c.weeks_completed,
    c.progress_percentage,
    c.status as collection_status,
    c.report_metadata,
    c.last_report_generated_at,
    COUNT(DISTINCT w.id) FILTER (WHERE w.status = 'succeeded') as successful_weeks,
    COUNT(DISTINCT w.id) as total_weeks,
    MIN(w.week_start_date) as earliest_week,
    MAX(w.week_start_date) as latest_week,
    SUM(w.record_count) as total_records,
    AVG(w.execution_time_seconds) as avg_execution_time
FROM report_data_collections c
LEFT JOIN report_data_weeks w ON c.id = w.collection_id
GROUP BY c.id, c.collection_id, c.workflow_id, c.user_id, 
         c.collection_type, c.target_weeks, c.weeks_completed, 
         c.progress_percentage, c.status, c.report_metadata, 
         c.last_report_generated_at;

-- Grant permissions
GRANT SELECT ON collection_report_summary TO authenticated;


-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON collection_report_configs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON collection_report_snapshots TO authenticated;