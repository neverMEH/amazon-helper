-- ============================================================
-- Report Builder Dashboards Migration
-- Creates tables and columns for the report builder dashboard feature
-- ============================================================

-- ==========================================
-- 1. Create report_configurations table
-- ==========================================
CREATE TABLE IF NOT EXISTS report_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    query_template_id UUID REFERENCES query_templates(id) ON DELETE CASCADE,
    dashboard_type VARCHAR(50) CHECK (dashboard_type IN ('funnel', 'performance', 'attribution', 'audience', 'custom')),
    visualization_settings JSONB NOT NULL DEFAULT '{}',
    data_aggregation_settings JSONB NOT NULL DEFAULT '{}',
    export_settings JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workflow_or_template CHECK (
        (workflow_id IS NOT NULL AND query_template_id IS NULL) OR
        (workflow_id IS NULL AND query_template_id IS NOT NULL)
    )
);

-- Add indexes for report_configurations
CREATE INDEX IF NOT EXISTS idx_report_configurations_workflow
    ON report_configurations(workflow_id)
    WHERE workflow_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_report_configurations_template
    ON report_configurations(query_template_id)
    WHERE query_template_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_report_configurations_enabled
    ON report_configurations(is_enabled)
    WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_report_configurations_dashboard_type
    ON report_configurations(dashboard_type);

-- ==========================================
-- 2. Create dashboard_views table
-- ==========================================
CREATE TABLE IF NOT EXISTS dashboard_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_configuration_id UUID NOT NULL REFERENCES report_configurations(id) ON DELETE CASCADE,
    view_name VARCHAR(255) NOT NULL,
    view_type VARCHAR(50) NOT NULL CHECK (view_type IN ('chart', 'table', 'metric_card', 'insight')),
    chart_configurations JSONB NOT NULL DEFAULT '{}',
    filter_settings JSONB NOT NULL DEFAULT '{}',
    layout_settings JSONB NOT NULL DEFAULT '{}',
    processed_data JSONB,
    last_updated TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add indexes for dashboard_views
CREATE INDEX IF NOT EXISTS idx_dashboard_views_report_config
    ON dashboard_views(report_configuration_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_views_view_type
    ON dashboard_views(view_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_views_last_updated
    ON dashboard_views(last_updated);

-- ==========================================
-- 3. Create dashboard_insights table
-- ==========================================
CREATE TABLE IF NOT EXISTS dashboard_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_view_id UUID NOT NULL REFERENCES dashboard_views(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL CHECK (insight_type IN ('trend', 'anomaly', 'recommendation', 'summary', 'comparison')),
    insight_text TEXT NOT NULL,
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    source_data JSONB NOT NULL DEFAULT '{}',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ai_model VARCHAR(100),
    prompt_version VARCHAR(20)
);

-- Add indexes for dashboard_insights
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_view
    ON dashboard_insights(dashboard_view_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_type
    ON dashboard_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_generated
    ON dashboard_insights(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_confidence
    ON dashboard_insights(confidence_score DESC);

-- ==========================================
-- 4. Create report_exports table
-- ==========================================
CREATE TABLE IF NOT EXISTS report_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_configuration_id UUID NOT NULL REFERENCES report_configurations(id) ON DELETE CASCADE,
    export_format VARCHAR(20) NOT NULL CHECK (export_format IN ('pdf', 'png', 'csv', 'excel')),
    file_url TEXT,
    file_size INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    generated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add indexes for report_exports
CREATE INDEX IF NOT EXISTS idx_report_exports_report_config
    ON report_exports(report_configuration_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_user
    ON report_exports(user_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_status
    ON report_exports(status);
CREATE INDEX IF NOT EXISTS idx_report_exports_generated
    ON report_exports(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_exports_expires
    ON report_exports(expires_at)
    WHERE expires_at IS NOT NULL;

-- ==========================================
-- 5. Add columns to workflows table
-- ==========================================
ALTER TABLE workflows
ADD COLUMN IF NOT EXISTS report_enabled BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS report_config_id UUID REFERENCES report_configurations(id) ON DELETE SET NULL;

-- Add index for report_enabled workflows
CREATE INDEX IF NOT EXISTS idx_workflows_report_enabled
    ON workflows(report_enabled)
    WHERE report_enabled = true;
CREATE INDEX IF NOT EXISTS idx_workflows_report_config
    ON workflows(report_config_id)
    WHERE report_config_id IS NOT NULL;

-- ==========================================
-- 6. Add column to query_templates table
-- ==========================================
ALTER TABLE query_templates
ADD COLUMN IF NOT EXISTS default_dashboard_type VARCHAR(50)
    CHECK (default_dashboard_type IN ('funnel', 'performance', 'attribution', 'audience', 'custom'));

-- Add index for query templates with dashboard type
CREATE INDEX IF NOT EXISTS idx_query_templates_dashboard_type
    ON query_templates(default_dashboard_type)
    WHERE default_dashboard_type IS NOT NULL;

-- ==========================================
-- 7. Create composite indexes for performance
-- ==========================================
-- Composite index for finding report configs by workflow and enabled status
CREATE INDEX IF NOT EXISTS idx_report_configs_workflow_enabled
    ON report_configurations(workflow_id, is_enabled)
    WHERE workflow_id IS NOT NULL;

-- Composite index for finding report configs by template and enabled status
CREATE INDEX IF NOT EXISTS idx_report_configs_template_enabled
    ON report_configurations(query_template_id, is_enabled)
    WHERE query_template_id IS NOT NULL;

-- Composite index for dashboard views by config and type
CREATE INDEX IF NOT EXISTS idx_dashboard_views_config_type
    ON dashboard_views(report_configuration_id, view_type);

-- Composite index for insights by view and type
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_view_type
    ON dashboard_insights(dashboard_view_id, insight_type);

-- Composite index for exports by user and status
CREATE INDEX IF NOT EXISTS idx_report_exports_user_status
    ON report_exports(user_id, status);

-- ==========================================
-- 8. Create updated_at trigger for report_configurations
-- ==========================================
-- Create or replace function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for report_configurations
DROP TRIGGER IF EXISTS update_report_configurations_updated_at ON report_configurations;
CREATE TRIGGER update_report_configurations_updated_at
    BEFORE UPDATE ON report_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 9. Set up Row Level Security (RLS) policies
-- ==========================================
-- Enable RLS on all new tables
ALTER TABLE report_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_exports ENABLE ROW LEVEL SECURITY;

-- Policy for report_configurations: users can manage their own workflow reports
CREATE POLICY "Users can view own report configurations" ON report_configurations
    FOR SELECT USING (
        workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
        query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
    );

CREATE POLICY "Users can create own report configurations" ON report_configurations
    FOR INSERT WITH CHECK (
        workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
        query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
    );

CREATE POLICY "Users can update own report configurations" ON report_configurations
    FOR UPDATE USING (
        workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
        query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
    );

CREATE POLICY "Users can delete own report configurations" ON report_configurations
    FOR DELETE USING (
        workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
        query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
    );

-- Policy for dashboard_views: inherit from report_configurations
CREATE POLICY "Users can view dashboard views" ON dashboard_views
    FOR SELECT USING (
        report_configuration_id IN (
            SELECT id FROM report_configurations WHERE
            workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
            query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
        )
    );

CREATE POLICY "Users can manage dashboard views" ON dashboard_views
    FOR ALL USING (
        report_configuration_id IN (
            SELECT id FROM report_configurations WHERE
            workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
            query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
        )
    );

-- Policy for dashboard_insights: inherit from dashboard_views
CREATE POLICY "Users can view dashboard insights" ON dashboard_insights
    FOR SELECT USING (
        dashboard_view_id IN (
            SELECT id FROM dashboard_views WHERE report_configuration_id IN (
                SELECT id FROM report_configurations WHERE
                workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
                query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
            )
        )
    );

CREATE POLICY "Users can manage dashboard insights" ON dashboard_insights
    FOR ALL USING (
        dashboard_view_id IN (
            SELECT id FROM dashboard_views WHERE report_configuration_id IN (
                SELECT id FROM report_configurations WHERE
                workflow_id IN (SELECT id FROM workflows WHERE user_id = auth.uid()) OR
                query_template_id IN (SELECT id FROM query_templates WHERE created_by = auth.uid())
            )
        )
    );

-- Policy for report_exports: users can only manage their own exports
CREATE POLICY "Users can view own report exports" ON report_exports
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create own report exports" ON report_exports
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own report exports" ON report_exports
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete own report exports" ON report_exports
    FOR DELETE USING (user_id = auth.uid());