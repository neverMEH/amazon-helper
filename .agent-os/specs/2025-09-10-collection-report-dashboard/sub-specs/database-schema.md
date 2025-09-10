# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-10-collection-report-dashboard/spec.md

> Created: 2025-09-10
> Version: 1.0.0

## Schema Changes

### New Tables

#### `collection_report_configs`
Stores saved report configurations and preferences for collections.

```sql
CREATE TABLE public.collection_report_configs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    config_name text NOT NULL,
    chart_configs jsonb NOT NULL, -- Chart type preferences per KPI
    default_view text DEFAULT 'trending', -- 'trending', 'comparison', 'aggregate'
    default_weeks_shown int4 DEFAULT 12, -- Number of weeks to show by default
    saved_comparisons jsonb NULL, -- Saved week comparison sets
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(collection_id, user_id, config_name)
);

-- Example chart_configs JSONB:
-- {
--   "impressions": {"type": "line", "color": "#3B82F6"},
--   "clicks": {"type": "bar", "color": "#10B981"},
--   "spend": {"type": "area", "color": "#F59E0B"},
--   "ctr": {"type": "line", "color": "#8B5CF6", "yAxisId": "right"}
-- }
```

#### `collection_report_snapshots`
Stores generated report snapshots for sharing and historical reference.

```sql
CREATE TABLE public.collection_report_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id text UNIQUE NOT NULL,
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    snapshot_name text NOT NULL,
    snapshot_data jsonb NOT NULL, -- Complete dashboard state and data
    week_range jsonb NOT NULL, -- {"start": "2025-01-01", "end": "2025-03-31"}
    comparison_settings jsonb NULL, -- Comparison configuration if applicable
    chart_images jsonb NULL, -- Base64 encoded chart images for export
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz NULL,
    is_public boolean DEFAULT false,
    access_count int4 DEFAULT 0
);

-- Index for public snapshot access
CREATE INDEX idx_snapshots_public ON collection_report_snapshots(snapshot_id, is_public) 
WHERE is_public = true AND expires_at > now();
```

### New Columns for Existing Tables

#### `report_data_collections` table additions:
```sql
ALTER TABLE report_data_collections 
ADD COLUMN report_metadata jsonb NULL, -- Cached KPI column metadata
ADD COLUMN last_report_generated_at timestamptz NULL;

-- Example report_metadata:
-- {
--   "available_kpis": ["impressions", "clicks", "spend", "conversions"],
--   "data_types": {"impressions": "integer", "spend": "numeric"},
--   "aggregatable": ["impressions", "clicks", "spend"],
--   "date_columns": ["report_date", "week_start"]
-- }
```

#### `report_data_weeks` table additions:
```sql
ALTER TABLE report_data_weeks
ADD COLUMN summary_stats jsonb NULL; -- Pre-calculated aggregates for performance

-- Example summary_stats:
-- {
--   "total_impressions": 1500000,
--   "total_clicks": 22500,
--   "total_spend": 4567.89,
--   "avg_ctr": 0.015,
--   "row_count": 1250
-- }
```

### New Indexes

```sql
-- Optimize collection report queries
CREATE INDEX idx_collection_weeks_summary 
ON report_data_weeks(collection_id, week_start_date) 
WHERE status = 'succeeded' AND summary_stats IS NOT NULL;

-- Speed up KPI metadata lookups
CREATE INDEX idx_collections_metadata 
ON report_data_collections(id) 
WHERE report_metadata IS NOT NULL;

-- Improve config retrieval
CREATE INDEX idx_report_configs_user_collection 
ON collection_report_configs(user_id, collection_id, updated_at DESC);

-- JSONB indexing for summary stats
CREATE INDEX idx_week_summary_stats 
ON report_data_weeks USING gin(summary_stats);

-- Optimize workflow execution result queries
CREATE INDEX idx_execution_results_optimized
ON workflow_executions(id, status)
WHERE status = 'SUCCEEDED' AND result_rows IS NOT NULL;
```

### New Materialized View (Optional for Performance)

```sql
CREATE MATERIALIZED VIEW collection_week_aggregates AS
SELECT 
    c.id as collection_id,
    c.collection_id as external_id,
    w.week_start_date,
    w.week_end_date,
    w.status,
    e.result_columns,
    jsonb_agg(e.result_rows) as aggregated_rows,
    COUNT(DISTINCT e.id) as execution_count,
    SUM(e.result_total_rows) as total_rows,
    AVG(e.query_runtime_seconds) as avg_runtime
FROM report_data_collections c
JOIN report_data_weeks w ON c.id = w.collection_id
LEFT JOIN workflow_executions e ON w.workflow_execution_id = e.id
WHERE w.status = 'succeeded'
GROUP BY c.id, c.collection_id, w.week_start_date, w.week_end_date, w.status, e.result_columns;

-- Index for fast lookups
CREATE UNIQUE INDEX idx_collection_week_agg 
ON collection_week_aggregates(collection_id, week_start_date);

-- Refresh strategy
CREATE OR REPLACE FUNCTION refresh_collection_aggregates()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY collection_week_aggregates;
END;
$$ LANGUAGE plpgsql;
```

### Database Functions

#### Function to calculate week-over-week changes
```sql
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
    
    -- Calculate changes
    change_value := week2_value - week1_value;
    IF week1_value != 0 THEN
        change_percent := (change_value / week1_value) * 100;
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
$$ LANGUAGE plpgsql;
```

#### Function to aggregate multi-week data
```sql
CREATE OR REPLACE FUNCTION aggregate_collection_weeks(
    p_collection_id uuid,
    p_start_date date,
    p_end_date date,
    p_aggregation_type text DEFAULT 'sum' -- 'sum', 'avg', 'min', 'max'
) RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
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
    )
    SELECT jsonb_object_agg(
        metric_name,
        CASE p_aggregation_type
            WHEN 'sum' THEN (SELECT SUM((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'avg' THEN (SELECT AVG((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'min' THEN (SELECT MIN((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'max' THEN (SELECT MAX((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
        END
    ) INTO result
    FROM metrics;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

### Migration Script

```sql
-- Migration to add report dashboard schema changes
BEGIN;

-- Create new tables
CREATE TABLE IF NOT EXISTS public.collection_report_configs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    config_name text NOT NULL,
    chart_configs jsonb NOT NULL,
    default_view text DEFAULT 'trending',
    default_weeks_shown int4 DEFAULT 12,
    saved_comparisons jsonb NULL,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now(),
    UNIQUE(collection_id, user_id, config_name)
);

CREATE TABLE IF NOT EXISTS public.collection_report_snapshots (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id text UNIQUE NOT NULL,
    collection_id uuid REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    snapshot_name text NOT NULL,
    snapshot_data jsonb NOT NULL,
    week_range jsonb NOT NULL,
    comparison_settings jsonb NULL,
    chart_images jsonb NULL,
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz NULL,
    is_public boolean DEFAULT false,
    access_count int4 DEFAULT 0
);

-- Add columns to existing tables
ALTER TABLE report_data_collections 
ADD COLUMN IF NOT EXISTS report_metadata jsonb NULL,
ADD COLUMN IF NOT EXISTS last_report_generated_at timestamptz NULL;

ALTER TABLE report_data_weeks
ADD COLUMN IF NOT EXISTS summary_stats jsonb NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_collection_weeks_summary 
ON report_data_weeks(collection_id, week_start_date) 
WHERE status = 'succeeded' AND summary_stats IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_collections_metadata 
ON report_data_collections(id) 
WHERE report_metadata IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_report_configs_user_collection 
ON collection_report_configs(user_id, collection_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_week_summary_stats 
ON report_data_weeks USING gin(summary_stats);

CREATE INDEX IF NOT EXISTS idx_execution_results_optimized
ON workflow_executions(id, status)
WHERE status = 'SUCCEEDED' AND result_rows IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_snapshots_public 
ON collection_report_snapshots(snapshot_id, is_public) 
WHERE is_public = true AND expires_at > now();

-- Create functions
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
    
    -- Calculate changes
    change_value := week2_value - week1_value;
    IF week1_value != 0 THEN
        change_percent := (change_value / week1_value) * 100;
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
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION aggregate_collection_weeks(
    p_collection_id uuid,
    p_start_date date,
    p_end_date date,
    p_aggregation_type text DEFAULT 'sum'
) RETURNS jsonb AS $$
DECLARE
    result jsonb;
BEGIN
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
    )
    SELECT jsonb_object_agg(
        metric_name,
        CASE p_aggregation_type
            WHEN 'sum' THEN (SELECT SUM((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'avg' THEN (SELECT AVG((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'min' THEN (SELECT MIN((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
            WHEN 'max' THEN (SELECT MAX((elem->>metric_name)::numeric) FROM week_data WHERE elem ? metric_name)
        END
    ) INTO result
    FROM metrics;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Add RLS policies
ALTER TABLE collection_report_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_report_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own report configs"
ON collection_report_configs
FOR ALL
USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own snapshots"
ON collection_report_snapshots
FOR ALL
USING (auth.uid() = user_id OR is_public = true);

COMMIT;
```

## Rationale

### New Tables
- **collection_report_configs**: Allows users to save dashboard preferences and custom views per collection
- **collection_report_snapshots**: Enables sharing and exporting of report states with data

### Column Additions
- **report_metadata**: Caches KPI information to avoid repeated JSONB parsing
- **summary_stats**: Pre-calculates common aggregations for performance

### Indexes
- Optimized for common query patterns: week ranges, successful executions, JSONB searches
- Partial indexes reduce index size while maintaining query performance

### Functions
- Database-level calculations reduce data transfer and improve performance
- Reusable logic for common operations like week-over-week changes

### Performance Considerations
- Materialized view option for frequently accessed aggregations
- JSONB indexing for efficient metric queries
- Summary statistics caching to avoid repeated calculations