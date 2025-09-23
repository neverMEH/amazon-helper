# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-23-report-builder-dashboards/spec.md

> Created: 2025-09-23
> Version: 1.0.0

## Schema Changes

### New Tables

#### report_configurations
Stores report enablement and configuration for queries
```sql
CREATE TABLE report_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    query_template_id UUID REFERENCES query_templates(id) ON DELETE SET NULL,
    enabled BOOLEAN DEFAULT false,
    dashboard_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    visualization_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    UNIQUE(workflow_id),
    INDEX idx_report_configs_enabled (enabled),
    INDEX idx_report_configs_workflow (workflow_id)
);
```

#### dashboard_views
Stores generated dashboard instances with processed data
```sql
CREATE TABLE dashboard_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_configuration_id UUID NOT NULL REFERENCES report_configurations(id) ON DELETE CASCADE,
    workflow_id UUID NOT NULL REFERENCES workflows(id),
    execution_ids UUID[] NOT NULL,
    data_start_date DATE NOT NULL,
    data_end_date DATE NOT NULL,
    processed_data JSONB NOT NULL,
    charts_config JSONB NOT NULL,
    metrics_summary JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_dashboard_views_config (report_configuration_id),
    INDEX idx_dashboard_views_dates (data_start_date, data_end_date),
    INDEX idx_dashboard_views_workflow (workflow_id)
);
```

#### dashboard_insights
AI-generated insights for dashboards
```sql
CREATE TABLE dashboard_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_view_id UUID NOT NULL REFERENCES dashboard_views(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    insight_text TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    data_points JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(50),

    INDEX idx_insights_dashboard (dashboard_view_id),
    INDEX idx_insights_type (insight_type)
);
```

#### report_exports
Tracks exported reports for retrieval
```sql
CREATE TABLE report_exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_view_id UUID NOT NULL REFERENCES dashboard_views(id) ON DELETE CASCADE,
    export_format VARCHAR(20) NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes INTEGER,
    exported_by UUID REFERENCES users(id),
    exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_exports_dashboard (dashboard_view_id),
    INDEX idx_exports_user (exported_by)
);
```

### Modified Tables

#### workflows
Add column for report enablement tracking
```sql
ALTER TABLE workflows
ADD COLUMN report_enabled BOOLEAN DEFAULT false,
ADD COLUMN report_config_id UUID REFERENCES report_configurations(id);

CREATE INDEX idx_workflows_report_enabled ON workflows(report_enabled) WHERE report_enabled = true;
```

#### query_templates
Add default dashboard configuration
```sql
ALTER TABLE query_templates
ADD COLUMN default_dashboard_type VARCHAR(50),
ADD COLUMN default_visualization_config JSONB;
```

#### workflow_executions
Add flag for dashboard processing status
```sql
ALTER TABLE workflow_executions
ADD COLUMN dashboard_processed BOOLEAN DEFAULT false,
ADD COLUMN dashboard_processing_error TEXT;

CREATE INDEX idx_executions_dashboard_pending
ON workflow_executions(workflow_id, dashboard_processed)
WHERE dashboard_processed = false AND status = 'SUCCEEDED';
```

## Indexes and Constraints

### Performance Indexes
```sql
-- Composite index for finding report-enabled workflows with executions
CREATE INDEX idx_report_workflow_executions
ON workflow_executions(workflow_id, created_at DESC)
WHERE status = 'SUCCEEDED';

-- Index for dashboard data retrieval
CREATE INDEX idx_dashboard_data_lookup
ON dashboard_views(workflow_id, data_end_date DESC);

-- Index for insight aggregation
CREATE INDEX idx_insights_aggregation
ON dashboard_insights(dashboard_view_id, insight_type);
```

### Check Constraints
```sql
-- Ensure valid dashboard types
ALTER TABLE report_configurations
ADD CONSTRAINT chk_dashboard_type
CHECK (dashboard_type IN ('standard', 'funnel', 'comparison', 'custom'));

-- Ensure valid export formats
ALTER TABLE report_exports
ADD CONSTRAINT chk_export_format
CHECK (export_format IN ('pdf', 'png', 'csv', 'xlsx'));

-- Ensure date range validity
ALTER TABLE dashboard_views
ADD CONSTRAINT chk_date_range
CHECK (data_end_date >= data_start_date);
```

## Migration Strategy

1. **Phase 1**: Create new tables with no foreign key constraints
2. **Phase 2**: Add columns to existing tables
3. **Phase 3**: Backfill report_enabled flag based on existing data patterns
4. **Phase 4**: Add foreign key constraints and indexes
5. **Phase 5**: Enable Row Level Security policies

## Data Retention

- Dashboard views: Keep for 90 days, then archive to cold storage
- Insights: Keep for 180 days
- Exports: Delete files after 30 days, keep metadata for 1 year
- Report configurations: Retain indefinitely while workflow exists