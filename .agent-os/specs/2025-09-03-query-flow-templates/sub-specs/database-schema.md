# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-03-query-flow-templates/spec.md

> Created: 2025-09-03
> Version: 1.0.0

## Schema Changes

### New Tables

#### query_flow_templates
```sql
CREATE TABLE query_flow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id VARCHAR(255) UNIQUE NOT NULL, -- Human-readable ID like "branded_search_trends"
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    sql_template TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    difficulty_level VARCHAR(20) DEFAULT 'intermediate' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    estimated_runtime_seconds INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_query_flow_templates_category ON query_flow_templates(category);
CREATE INDEX idx_query_flow_templates_tags ON query_flow_templates USING GIN(tags);
CREATE INDEX idx_query_flow_templates_featured ON query_flow_templates(is_featured) WHERE is_featured = true;
```

#### template_parameters
```sql
CREATE TABLE template_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    parameter_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    parameter_type VARCHAR(50) NOT NULL CHECK (parameter_type IN ('string', 'number', 'date', 'date_range', 'array', 'boolean', 'campaign_ids', 'asin_list', 'brand_list')),
    is_required BOOLEAN DEFAULT true,
    default_value TEXT,
    validation_rules JSONB DEFAULT '{}',
    display_order INTEGER DEFAULT 0,
    help_text TEXT,
    depends_on VARCHAR(100), -- Parameter name this depends on
    conditional_value TEXT, -- Value that must match for this parameter to show
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, parameter_name)
);

CREATE INDEX idx_template_parameters_template ON template_parameters(template_id);
CREATE INDEX idx_template_parameters_order ON template_parameters(template_id, display_order);
```

#### template_chart_configs
```sql
CREATE TABLE template_chart_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    chart_id VARCHAR(100) NOT NULL,
    chart_type VARCHAR(50) NOT NULL CHECK (chart_type IN ('line', 'bar', 'pie', 'table', 'scatter', 'area', 'funnel')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    data_mapping JSONB NOT NULL DEFAULT '{}', -- Maps query columns to chart data
    styling JSONB DEFAULT '{}', -- Chart styling configuration
    interactions JSONB DEFAULT '{}', -- Interactive features config
    display_order INTEGER DEFAULT 0,
    is_default_view BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, chart_id)
);

CREATE INDEX idx_template_chart_configs_template ON template_chart_configs(template_id);
CREATE INDEX idx_template_chart_configs_order ON template_chart_configs(template_id, display_order);
```

#### template_executions
```sql
CREATE TABLE template_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id VARCHAR(255) UNIQUE NOT NULL, -- Human-readable ID
    template_id UUID REFERENCES query_flow_templates(id),
    user_id UUID REFERENCES users(id),
    instance_id UUID REFERENCES amc_instances(id),
    parameters JSONB NOT NULL DEFAULT '{}',
    generated_sql TEXT,
    workflow_execution_id UUID REFERENCES workflow_executions(id),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_time_seconds INTEGER,
    result_row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_template_executions_template ON template_executions(template_id);
CREATE INDEX idx_template_executions_user ON template_executions(user_id);
CREATE INDEX idx_template_executions_status ON template_executions(status);
CREATE INDEX idx_template_executions_created ON template_executions(created_at DESC);
```

#### user_template_favorites
```sql
CREATE TABLE user_template_favorites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    template_id UUID REFERENCES query_flow_templates(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, template_id)
);

CREATE INDEX idx_user_template_favorites_user ON user_template_favorites(user_id);
```

#### template_ratings
```sql
CREATE TABLE template_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES query_flow_templates(id),
    user_id UUID REFERENCES users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, user_id)
);

CREATE INDEX idx_template_ratings_template ON template_ratings(template_id);
CREATE INDEX idx_template_ratings_user ON template_ratings(user_id);
```

## Migrations

### Migration 001: Create Query Flow Templates Tables
```sql
-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create all tables in dependency order
-- (SQL from above schema)

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_query_flow_templates_updated_at 
    BEFORE UPDATE ON query_flow_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_template_ratings_updated_at 
    BEFORE UPDATE ON template_ratings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Migration 002: Seed Initial Template Data
```sql
-- Insert Supergoop Branded Search Trend Analysis template
INSERT INTO query_flow_templates (
    template_id,
    name,
    description,
    category,
    sql_template,
    tags,
    difficulty_level,
    estimated_runtime_seconds,
    is_featured
) VALUES (
    'supergoop_branded_search_trends',
    'Supergoop Branded Search Trend Analysis',
    'Analyze search trends and performance for Supergoop branded campaigns over time',
    'Brand Analysis',
    'WITH campaign_performance AS (
        SELECT 
            date_trunc(''{{aggregation_level}}'', report_date) as period,
            campaign_id,
            campaign_name,
            SUM(impressions) as impressions,
            SUM(clicks) as clicks,
            SUM(purchases_14d) as purchases,
            SUM(sales_14d) as sales
        FROM dsp_impressions_with_clicks_and_purchases
        WHERE report_date >= ''{{start_date}}''
            AND report_date <= ''{{end_date}}''
            AND campaign_id IN ({{campaign_ids}})
            AND lower(campaign_name) LIKE ''%supergoog%''
        GROUP BY 1, 2, 3
    )
    SELECT 
        period,
        campaign_name,
        impressions,
        clicks,
        CASE WHEN impressions > 0 THEN (clicks::float / impressions) * 100 ELSE 0 END as ctr,
        purchases,
        sales,
        CASE WHEN clicks > 0 THEN sales / clicks ELSE 0 END as roas
    FROM campaign_performance
    ORDER BY period DESC, sales DESC;',
    ARRAY['supergoog', 'branded', 'trends', 'campaigns'],
    'intermediate',
    120,
    true
);

-- Insert parameters for the template
INSERT INTO template_parameters (template_id, parameter_name, display_name, parameter_type, is_required, default_value, display_order, help_text)
SELECT 
    t.id,
    param.parameter_name,
    param.display_name,
    param.parameter_type,
    param.is_required,
    param.default_value,
    param.display_order,
    param.help_text
FROM query_flow_templates t
CROSS JOIN (
    VALUES
    ('start_date', 'Start Date', 'date', true, '30 days ago', 1, 'Beginning of analysis period'),
    ('end_date', 'End Date', 'date', true, 'yesterday', 2, 'End of analysis period'),
    ('campaign_ids', 'Campaigns', 'campaign_ids', true, null, 3, 'Select branded campaigns to analyze'),
    ('aggregation_level', 'Time Grouping', 'string', true, 'day', 4, 'Group results by day, week, or month')
) AS param(parameter_name, display_name, parameter_type, is_required, default_value, display_order, help_text)
WHERE t.template_id = 'supergoog_branded_search_trends';

-- Insert chart configurations
INSERT INTO template_chart_configs (template_id, chart_id, chart_type, title, data_mapping, display_order, is_default_view)
SELECT 
    t.id,
    chart.chart_id,
    chart.chart_type,
    chart.title,
    chart.data_mapping::jsonb,
    chart.display_order,
    chart.is_default_view
FROM query_flow_templates t
CROSS JOIN (
    VALUES
    ('trend_line', 'line', 'Sales Trend Over Time', '{"x": "period", "y": "sales", "color": "campaign_name"}', 1, true),
    ('performance_table', 'table', 'Campaign Performance Summary', '{"columns": ["campaign_name", "impressions", "clicks", "ctr", "purchases", "sales", "roas"]}', 2, false),
    ('ctr_comparison', 'bar', 'Click-Through Rate by Campaign', '{"x": "campaign_name", "y": "ctr"}', 3, false)
) AS chart(chart_id, chart_type, title, data_mapping, display_order, is_default_view)
WHERE t.template_id = 'supergoop_branded_search_trends';
```

### Migration 003: Update Query Library Integration
```sql
-- Add template_id reference to existing query_templates table (if needed for migration)
ALTER TABLE query_templates ADD COLUMN flow_template_id UUID REFERENCES query_flow_templates(id);

-- Create view for backward compatibility
CREATE VIEW legacy_query_templates AS
SELECT 
    qft.template_id as id,
    qft.name,
    qft.description,
    qft.sql_template as query_text,
    qft.category,
    qft.created_at,
    qft.updated_at
FROM query_flow_templates qft
WHERE qft.is_active = true;
```