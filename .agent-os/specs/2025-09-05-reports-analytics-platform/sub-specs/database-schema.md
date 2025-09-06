# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-05-reports-analytics-platform/spec.md

> Created: 2025-09-05
> Version: 1.0.0

## Schema Changes

### New Tables for Reporting Platform

```sql
-- Dashboard configurations and metadata
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id VARCHAR(255) NOT NULL UNIQUE, -- Human-readable ID like "dash_xxxxx"
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(100), -- 'performance', 'attribution', 'audience', 'custom'
    layout_config JSONB NOT NULL DEFAULT '{}', -- Widget positions and configurations
    filter_config JSONB DEFAULT '{}', -- Default filters and settings
    is_public BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual dashboard widgets
CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    widget_id VARCHAR(255) NOT NULL,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(100) NOT NULL, -- 'chart', 'table', 'metric_card', 'text'
    chart_type VARCHAR(100), -- 'line', 'bar', 'pie', 'scatter', 'area'
    title VARCHAR(255) NOT NULL,
    data_source JSONB NOT NULL, -- Workflow IDs, metrics, filters
    display_config JSONB DEFAULT '{}', -- Styling, axis labels, colors
    position_config JSONB NOT NULL, -- x, y, width, height
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dashboard_id, widget_id)
);

-- Historical data collection for reports
CREATE TABLE report_data_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id VARCHAR(255) NOT NULL UNIQUE, -- Human-readable ID
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    collection_type VARCHAR(100) NOT NULL, -- 'backfill', 'weekly_update'
    target_weeks INTEGER NOT NULL, -- Number of weeks to collect
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'paused'
    progress_percentage INTEGER DEFAULT 0,
    weeks_completed INTEGER DEFAULT 0,
    error_message TEXT,
    configuration JSONB DEFAULT '{}', -- Collection parameters and settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual week collection results
CREATE TABLE report_data_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES report_data_collections(id) ON DELETE CASCADE,
    workflow_execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    execution_date TIMESTAMP WITH TIME ZONE,
    row_count INTEGER,
    data_checksum VARCHAR(255), -- For duplicate detection
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(collection_id, week_start_date)
);

-- Aggregated reporting data for fast dashboard queries
CREATE TABLE report_data_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    aggregation_type VARCHAR(100) NOT NULL, -- 'weekly', 'monthly', 'quarterly'
    aggregation_key VARCHAR(255) NOT NULL, -- Date or period identifier
    metrics JSONB NOT NULL, -- Pre-computed metrics and KPIs
    dimensions JSONB DEFAULT '{}', -- Campaign IDs, ASINs, etc.
    data_date DATE NOT NULL,
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workflow_id, instance_id, aggregation_type, aggregation_key, data_date)
);

-- AI conversation history and insights
CREATE TABLE ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    data_context JSONB DEFAULT '{}', -- Relevant data context provided to AI
    confidence_score DECIMAL(3,2), -- AI confidence in the response
    insight_type VARCHAR(100), -- 'trend_analysis', 'anomaly_detection', 'optimization'
    related_metrics JSONB DEFAULT '{}', -- Metrics referenced in the insight
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dashboard sharing and permissions
CREATE TABLE dashboard_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    shared_by_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(50) DEFAULT 'view', -- 'view', 'edit'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(dashboard_id, shared_with_user_id)
);
```

### Indexes for Performance

```sql
-- Dashboard queries
CREATE INDEX idx_dashboards_user_id ON dashboards(user_id);
CREATE INDEX idx_dashboards_template_type ON dashboards(template_type);
CREATE INDEX idx_dashboards_is_public ON dashboards(is_public) WHERE is_public = true;

-- Widget queries
CREATE INDEX idx_dashboard_widgets_dashboard_id ON dashboard_widgets(dashboard_id);
CREATE INDEX idx_dashboard_widgets_type ON dashboard_widgets(widget_type);

-- Data collection queries
CREATE INDEX idx_report_collections_workflow_id ON report_data_collections(workflow_id);
CREATE INDEX idx_report_collections_instance_id ON report_data_collections(instance_id);
CREATE INDEX idx_report_collections_status ON report_data_collections(status);
CREATE INDEX idx_report_collections_user_id ON report_data_collections(user_id);

-- Week data queries
CREATE INDEX idx_report_weeks_collection_id ON report_data_weeks(collection_id);
CREATE INDEX idx_report_weeks_date_range ON report_data_weeks(week_start_date, week_end_date);
CREATE INDEX idx_report_weeks_status ON report_data_weeks(status);

-- Aggregate data queries (most critical for dashboard performance)
CREATE INDEX idx_report_aggregates_workflow_instance ON report_data_aggregates(workflow_id, instance_id);
CREATE INDEX idx_report_aggregates_type_date ON report_data_aggregates(aggregation_type, data_date);
CREATE INDEX idx_report_aggregates_key_date ON report_data_aggregates(aggregation_key, data_date);

-- AI insights queries
CREATE INDEX idx_ai_insights_user_id ON ai_insights(user_id);
CREATE INDEX idx_ai_insights_dashboard_id ON ai_insights(dashboard_id);
CREATE INDEX idx_ai_insights_created_at ON ai_insights(created_at);
CREATE INDEX idx_ai_insights_type ON ai_insights(insight_type);

-- Dashboard sharing
CREATE INDEX idx_dashboard_shares_shared_with ON dashboard_shares(shared_with_user_id);
```

### Foreign Key Constraints and Triggers

```sql
-- Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_widgets_updated_at BEFORE UPDATE ON dashboard_widgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_collections_updated_at BEFORE UPDATE ON report_data_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_weeks_updated_at BEFORE UPDATE ON report_data_weeks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_aggregates_updated_at BEFORE UPDATE ON report_data_aggregates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Migrations

### Migration Script: 001_create_reporting_tables.sql

```sql
-- Run this migration to add the reporting platform tables
-- This extends the existing AMC platform with reporting capabilities

BEGIN;

-- Add tables in dependency order
-- (Include all CREATE TABLE statements from above)

-- Add indexes
-- (Include all CREATE INDEX statements from above)

-- Add triggers
-- (Include all trigger statements from above)

-- Verify table creation
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'dashboards', 
    'dashboard_widgets', 
    'report_data_collections',
    'report_data_weeks',
    'report_data_aggregates',
    'ai_insights',
    'dashboard_shares'
);

COMMIT;
```

## Rationale

### Data Collection Strategy
- **Separate collection tracking** allows for robust progress monitoring and error recovery during 52-week backfill operations
- **Week-level granularity** provides flexibility for partial re-runs and detailed error tracking
- **Checksum-based duplicate detection** prevents data duplication during overlapping collection periods

### Aggregation Strategy
- **Pre-computed aggregates** enable fast dashboard loading for common time-based queries
- **Multiple aggregation levels** support different dashboard zoom levels without real-time computation
- **JSONB storage** provides flexibility for different metric types while maintaining query performance

### Dashboard Architecture
- **Separate widget storage** allows for complex dashboard layouts and individual widget configurations
- **Template system** enables quick dashboard creation for common AMC use cases
- **JSONB configuration** provides flexibility for different chart types and customizations

### AI Integration
- **Conversation history** enables learning from user interactions and improving insights over time
- **Context tracking** ensures AI responses are relevant to specific data and timeframes
- **Confidence scoring** allows UI to indicate reliability of AI-generated insights

### Performance Considerations
- **Strategic indexing** optimized for dashboard queries and data collection operations
- **Date-based partitioning** potential for large datasets (can be added later)
- **Aggregate tables** reduce complex real-time calculations for dashboard rendering