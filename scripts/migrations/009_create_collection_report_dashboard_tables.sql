-- Migration: Collection Report Dashboard Schema
-- Date: 2025-09-10
-- Description: Adds tables and functions for collection report dashboard feature

-- ============================================
-- 1. CREATE NEW TABLES
-- ============================================

-- Table: collection_report_configs
-- Stores saved report configurations and preferences for collections
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

-- Table: collection_report_snapshots
-- Stores generated report snapshots for sharing and historical reference
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

-- ============================================
-- 2. ADD COLUMNS TO EXISTING TABLES
-- ============================================

-- Add columns to report_data_collections
ALTER TABLE report_data_collections 
ADD COLUMN IF NOT EXISTS report_metadata jsonb DEFAULT NULL,
ADD COLUMN IF NOT EXISTS last_report_generated_at timestamptz DEFAULT NULL;

-- Add columns to report_data_weeks
ALTER TABLE report_data_weeks
ADD COLUMN IF NOT EXISTS summary_stats jsonb DEFAULT NULL;

-- ============================================
-- 3. CREATE INDEXES
-- ============================================

-- Indexes for collection_report_configs
CREATE INDEX IF NOT EXISTS idx_report_configs_user_collection 
ON collection_report_configs(user_id, collection_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_report_configs_collection 
ON collection_report_configs(collection_id);

-- Indexes for collection_report_snapshots
CREATE INDEX IF NOT EXISTS idx_snapshots_public 
ON collection_report_snapshots(snapshot_id, is_public) 
WHERE is_public = true;

CREATE INDEX IF NOT EXISTS idx_snapshots_user 
ON collection_report_snapshots(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_snapshots_collection 
ON collection_report_snapshots(collection_id);

-- Indexes for report_data_collections metadata
CREATE INDEX IF NOT EXISTS idx_collections_metadata 
ON report_data_collections(id) 
WHERE report_metadata IS NOT NULL;

-- Indexes for report_data_weeks summary stats
CREATE INDEX IF NOT EXISTS idx_week_summary_stats 
ON report_data_weeks USING gin(summary_stats)
WHERE summary_stats IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collection_weeks_summary 
ON report_data_weeks(collection_id, week_start_date) 
WHERE status = 'succeeded' AND summary_stats IS NOT NULL;

-- Index for workflow_executions to optimize report queries
CREATE INDEX IF NOT EXISTS idx_execution_results_optimized
ON workflow_executions(id, status)
WHERE status = 'SUCCEEDED' AND result_rows IS NOT NULL;

-- ============================================
-- 4. CREATE FUNCTIONS
-- ============================================

-- Function: calculate_week_over_week_change
-- Calculates the change between two weeks for a specific metric
CREATE OR REPLACE FUNCTION calculate_week_over_week_change(
    p_collection_id uuid,
    p_metric text,
    p_week1_start date,
    p_week2_start date
) RETURNS jsonb AS $$
DECLARE
    week1_value numeric;
    week2_value numeric;
    change_value numeric;
    change_percent numeric;
BEGIN
    -- Get week 1 value
    SELECT SUM((elem->>p_metric)::numeric)
    INTO week1_value
    FROM report_data_weeks w
    JOIN workflow_executions e ON w.workflow_execution_id = e.id,
    jsonb_array_elements(e.result_rows) elem
    WHERE w.collection_id = p_collection_id
    AND w.week_start_date = p_week1_start
    AND w.status = 'succeeded';
    
    -- Get week 2 value
    SELECT SUM((elem->>p_metric)::numeric)
    INTO week2_value
    FROM report_data_weeks w
    JOIN workflow_executions e ON w.workflow_execution_id = e.id,
    jsonb_array_elements(e.result_rows) elem
    WHERE w.collection_id = p_collection_id
    AND w.week_start_date = p_week2_start
    AND w.status = 'succeeded';
    
    -- Handle null values
    week1_value := COALESCE(week1_value, 0);
    week2_value := COALESCE(week2_value, 0);
    
    -- Calculate changes
    change_value := week2_value - week1_value;
    IF week1_value != 0 THEN
        change_percent := ROUND((change_value / week1_value) * 100, 2);
    ELSE
        change_percent := NULL;
    END IF;
    
    RETURN jsonb_build_object(
        'week1_value', week1_value,
        'week2_value', week2_value,
        'change_value', change_value,
        'change_percent', change_percent
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: aggregate_collection_weeks
-- Aggregates data across multiple weeks with different aggregation types
CREATE OR REPLACE FUNCTION aggregate_collection_weeks(
    p_collection_id uuid,
    p_start_date date,
    p_end_date date,
    p_aggregation_type text DEFAULT 'sum'
) RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
    -- Validate aggregation type
    IF p_aggregation_type NOT IN ('sum', 'avg', 'min', 'max') THEN
        RAISE EXCEPTION 'Invalid aggregation type: %. Must be sum, avg, min, or max', p_aggregation_type;
    END IF;
    
    WITH week_data AS (
        SELECT 
            elem,
            e.result_columns
        FROM report_data_weeks w
        JOIN workflow_executions e ON w.workflow_execution_id = e.id,
        jsonb_array_elements(e.result_rows) elem
        WHERE w.collection_id = p_collection_id
        AND w.week_start_date >= p_start_date
        AND w.week_start_date <= p_end_date
        AND w.status = 'succeeded'
    ),
    metrics AS (
        SELECT DISTINCT jsonb_object_keys(elem) as metric_name
        FROM week_data
        WHERE jsonb_typeof(elem) = 'object'
    ),
    aggregated AS (
        SELECT 
            metric_name,
            CASE p_aggregation_type
                WHEN 'sum' THEN SUM((elem->>metric_name)::numeric)
                WHEN 'avg' THEN AVG((elem->>metric_name)::numeric)
                WHEN 'min' THEN MIN((elem->>metric_name)::numeric)
                WHEN 'max' THEN MAX((elem->>metric_name)::numeric)
            END as value
        FROM metrics
        CROSS JOIN week_data
        WHERE elem ? metric_name
        AND (elem->>metric_name) ~ '^[0-9]+\.?[0-9]*$'  -- Only numeric values
        GROUP BY metric_name
    )
    SELECT jsonb_object_agg(metric_name, ROUND(value, 2))
    INTO result
    FROM aggregated
    WHERE value IS NOT NULL;
    
    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: update_updated_at_timestamp
-- Automatically updates the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. CREATE TRIGGERS
-- ============================================

-- Trigger for collection_report_configs updated_at
DROP TRIGGER IF EXISTS update_collection_report_configs_updated_at ON collection_report_configs;
CREATE TRIGGER update_collection_report_configs_updated_at
    BEFORE UPDATE ON collection_report_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_timestamp();

-- ============================================
-- 6. ENABLE ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on new tables
ALTER TABLE collection_report_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_report_snapshots ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 7. CREATE RLS POLICIES
-- ============================================

-- Policies for collection_report_configs
DROP POLICY IF EXISTS "Users can view their own report configs" ON collection_report_configs;
CREATE POLICY "Users can view their own report configs"
ON collection_report_configs
FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create their own report configs" ON collection_report_configs;
CREATE POLICY "Users can create their own report configs"
ON collection_report_configs
FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own report configs" ON collection_report_configs;
CREATE POLICY "Users can update their own report configs"
ON collection_report_configs
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own report configs" ON collection_report_configs;
CREATE POLICY "Users can delete their own report configs"
ON collection_report_configs
FOR DELETE
USING (auth.uid() = user_id);

-- Policies for collection_report_snapshots
DROP POLICY IF EXISTS "Users can view their own snapshots or public snapshots" ON collection_report_snapshots;
CREATE POLICY "Users can view their own snapshots or public snapshots"
ON collection_report_snapshots
FOR SELECT
USING (auth.uid() = user_id OR is_public = true);

DROP POLICY IF EXISTS "Users can create their own snapshots" ON collection_report_snapshots;
CREATE POLICY "Users can create their own snapshots"
ON collection_report_snapshots
FOR INSERT
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own snapshots" ON collection_report_snapshots;
CREATE POLICY "Users can update their own snapshots"
ON collection_report_snapshots
FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own snapshots" ON collection_report_snapshots;
CREATE POLICY "Users can delete their own snapshots"
ON collection_report_snapshots
FOR DELETE
USING (auth.uid() = user_id);

-- ============================================
-- 8. GRANT PERMISSIONS
-- ============================================

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON collection_report_configs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON collection_report_snapshots TO authenticated;

-- Grant permissions to service role
GRANT ALL ON collection_report_configs TO service_role;
GRANT ALL ON collection_report_snapshots TO service_role;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION calculate_week_over_week_change TO authenticated;
GRANT EXECUTE ON FUNCTION aggregate_collection_weeks TO authenticated;
GRANT EXECUTE ON FUNCTION update_updated_at_timestamp TO authenticated;

-- ============================================
-- 9. CREATE HELPER VIEW (Optional)
-- ============================================

-- View for easy access to collection report data
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

-- Grant permissions on view
GRANT SELECT ON collection_report_summary TO authenticated;

-- ============================================
-- 10. ADD COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE collection_report_configs IS 'Stores user-defined report dashboard configurations for collections';
COMMENT ON TABLE collection_report_snapshots IS 'Stores shareable snapshots of report dashboards with data';
COMMENT ON COLUMN report_data_collections.report_metadata IS 'Cached metadata about available KPIs and data types';
COMMENT ON COLUMN report_data_collections.last_report_generated_at IS 'Timestamp of last report dashboard generation';
COMMENT ON COLUMN report_data_weeks.summary_stats IS 'Pre-calculated summary statistics for performance';
COMMENT ON FUNCTION calculate_week_over_week_change IS 'Calculates percentage and absolute change between two weeks for a metric';
COMMENT ON FUNCTION aggregate_collection_weeks IS 'Aggregates metrics across multiple weeks using sum, avg, min, or max';

-- ============================================
-- Migration Complete
-- ============================================