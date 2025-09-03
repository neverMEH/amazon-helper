-- Query Flow Templates Database Migration
-- Created: 2025-09-03
-- Description: Creates all tables required for the Query Flow Templates feature

-- 1. Main templates table
CREATE TABLE IF NOT EXISTS query_flow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    sql_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_count INTEGER DEFAULT 0,
    avg_execution_time_ms INTEGER,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT template_id_format CHECK (template_id ~ '^[a-z0-9_]+$')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_flow_templates_category ON query_flow_templates(category);
CREATE INDEX IF NOT EXISTS idx_query_flow_templates_is_active ON query_flow_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_query_flow_templates_tags ON query_flow_templates USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_query_flow_templates_created_by ON query_flow_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_query_flow_templates_execution_count ON query_flow_templates(execution_count DESC);

-- 2. Template parameters table
CREATE TABLE IF NOT EXISTS template_parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    parameter_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    parameter_type VARCHAR(50) NOT NULL, -- 'date', 'date_range', 'string', 'number', 'boolean', 'campaign_list', 'asin_list', 'string_list'
    required BOOLEAN DEFAULT false,
    default_value JSONB,
    validation_rules JSONB DEFAULT '{}'::jsonb,
    ui_component VARCHAR(100) NOT NULL, -- Component name to use in UI
    ui_config JSONB DEFAULT '{}'::jsonb, -- UI-specific configuration
    dependencies JSONB DEFAULT '[]'::jsonb, -- Other parameters this depends on
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, parameter_name),
    CONSTRAINT parameter_type_check CHECK (
        parameter_type IN ('date', 'date_range', 'string', 'number', 'boolean', 'campaign_list', 'asin_list', 'string_list')
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_parameters_template_id ON template_parameters(template_id);
CREATE INDEX IF NOT EXISTS idx_template_parameters_order ON template_parameters(template_id, order_index);

-- 3. Template chart configurations table
CREATE TABLE IF NOT EXISTS template_chart_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    chart_name VARCHAR(255) NOT NULL,
    chart_type VARCHAR(50) NOT NULL, -- 'line', 'bar', 'pie', 'scatter', 'table', 'heatmap', 'funnel'
    chart_config JSONB NOT NULL DEFAULT '{}'::jsonb, -- Chart.js or recharts configuration
    data_mapping JSONB NOT NULL DEFAULT '{}'::jsonb, -- How to map SQL results to chart data
    is_default BOOLEAN DEFAULT false,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, chart_name),
    CONSTRAINT chart_type_check CHECK (
        chart_type IN ('line', 'bar', 'pie', 'scatter', 'table', 'heatmap', 'funnel', 'area', 'combo')
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_chart_configs_template_id ON template_chart_configs(template_id);
CREATE INDEX IF NOT EXISTS idx_template_chart_configs_order ON template_chart_configs(template_id, order_index);
CREATE INDEX IF NOT EXISTS idx_template_chart_configs_default ON template_chart_configs(template_id, is_default);

-- 4. Template executions table
CREATE TABLE IF NOT EXISTS template_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    instance_id UUID NOT NULL REFERENCES amc_instances(id),
    parameters_used JSONB NOT NULL, -- Actual parameter values used
    workflow_id UUID REFERENCES workflows(id), -- Generated workflow
    execution_id UUID REFERENCES workflow_executions(id), -- AMC execution
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    result_summary JSONB, -- Summary statistics of results
    execution_time_ms INTEGER,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT status_check CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'cancelled')
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_executions_template_id ON template_executions(template_id);
CREATE INDEX IF NOT EXISTS idx_template_executions_user_id ON template_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_template_executions_instance_id ON template_executions(instance_id);
CREATE INDEX IF NOT EXISTS idx_template_executions_status ON template_executions(status);
CREATE INDEX IF NOT EXISTS idx_template_executions_created_at ON template_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_template_executions_workflow_id ON template_executions(workflow_id);

-- 5. User template favorites table
CREATE TABLE IF NOT EXISTS user_template_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, template_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_template_favorites_user_id ON user_template_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_template_favorites_template_id ON user_template_favorites(template_id);

-- 6. Template ratings and reviews table
CREATE TABLE IF NOT EXISTS template_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_flow_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL,
    review TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(template_id, user_id),
    CONSTRAINT rating_range CHECK (rating >= 1 AND rating <= 5)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_ratings_template_id ON template_ratings(template_id);
CREATE INDEX IF NOT EXISTS idx_template_ratings_user_id ON template_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_template_ratings_rating ON template_ratings(rating);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
DROP TRIGGER IF EXISTS update_query_flow_templates_updated_at ON query_flow_templates;
CREATE TRIGGER update_query_flow_templates_updated_at 
    BEFORE UPDATE ON query_flow_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_template_parameters_updated_at ON template_parameters;
CREATE TRIGGER update_template_parameters_updated_at 
    BEFORE UPDATE ON template_parameters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_template_chart_configs_updated_at ON template_chart_configs;
CREATE TRIGGER update_template_chart_configs_updated_at 
    BEFORE UPDATE ON template_chart_configs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_template_ratings_updated_at ON template_ratings;
CREATE TRIGGER update_template_ratings_updated_at 
    BEFORE UPDATE ON template_ratings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for template statistics
CREATE OR REPLACE VIEW template_statistics AS
SELECT 
    t.id,
    t.template_id,
    t.name,
    t.category,
    t.execution_count,
    t.avg_execution_time_ms,
    COUNT(DISTINCT f.user_id) as favorite_count,
    AVG(r.rating) as avg_rating,
    COUNT(DISTINCT r.user_id) as rating_count,
    COUNT(DISTINCT e.user_id) as unique_users,
    MAX(e.created_at) as last_executed_at
FROM query_flow_templates t
LEFT JOIN user_template_favorites f ON t.id = f.template_id
LEFT JOIN template_ratings r ON t.id = r.template_id
LEFT JOIN template_executions e ON t.id = e.template_id AND e.status = 'completed'
GROUP BY t.id, t.template_id, t.name, t.category, t.execution_count, t.avg_execution_time_ms;

-- Add RLS policies (Row Level Security)
ALTER TABLE query_flow_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_parameters ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_chart_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_template_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_ratings ENABLE ROW LEVEL SECURITY;

-- Templates are public to read, only admins can write
CREATE POLICY "Templates are viewable by all authenticated users" 
    ON query_flow_templates FOR SELECT 
    USING (is_public = true OR created_by = auth.uid());

CREATE POLICY "Templates can be created by authenticated users" 
    ON query_flow_templates FOR INSERT 
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Templates can be updated by creators" 
    ON query_flow_templates FOR UPDATE 
    USING (auth.uid() = created_by);

-- Template parameters follow template visibility
CREATE POLICY "Template parameters are viewable with templates" 
    ON template_parameters FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM query_flow_templates t 
            WHERE t.id = template_parameters.template_id 
            AND (t.is_public = true OR t.created_by = auth.uid())
        )
    );

CREATE POLICY "Template parameters can be managed by template creators" 
    ON template_parameters FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM query_flow_templates t 
            WHERE t.id = template_parameters.template_id 
            AND t.created_by = auth.uid()
        )
    );

-- Chart configs follow template visibility
CREATE POLICY "Chart configs are viewable with templates" 
    ON template_chart_configs FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM query_flow_templates t 
            WHERE t.id = template_chart_configs.template_id 
            AND (t.is_public = true OR t.created_by = auth.uid())
        )
    );

CREATE POLICY "Chart configs can be managed by template creators" 
    ON template_chart_configs FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM query_flow_templates t 
            WHERE t.id = template_chart_configs.template_id 
            AND t.created_by = auth.uid()
        )
    );

-- Users can only see their own executions
CREATE POLICY "Users can view own executions" 
    ON template_executions FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own executions" 
    ON template_executions FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own executions" 
    ON template_executions FOR UPDATE 
    USING (auth.uid() = user_id);

-- Users can manage their own favorites
CREATE POLICY "Users can view own favorites" 
    ON user_template_favorites FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own favorites" 
    ON user_template_favorites FOR ALL 
    USING (auth.uid() = user_id);

-- Ratings are public to read, users can manage their own
CREATE POLICY "Ratings are viewable by all" 
    ON template_ratings FOR SELECT 
    USING (true);

CREATE POLICY "Users can manage own ratings" 
    ON template_ratings FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own ratings" 
    ON template_ratings FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own ratings" 
    ON template_ratings FOR DELETE 
    USING (auth.uid() = user_id);

-- Grant permissions for authenticated users
GRANT SELECT ON query_flow_templates TO authenticated;
GRANT INSERT, UPDATE ON query_flow_templates TO authenticated;
GRANT SELECT ON template_parameters TO authenticated;
GRANT SELECT ON template_chart_configs TO authenticated;
GRANT ALL ON template_executions TO authenticated;
GRANT ALL ON user_template_favorites TO authenticated;
GRANT ALL ON template_ratings TO authenticated;
GRANT SELECT ON template_statistics TO authenticated;

-- Comments for documentation
COMMENT ON TABLE query_flow_templates IS 'Stores parameterized SQL query templates with visualization configurations';
COMMENT ON TABLE template_parameters IS 'Defines parameters for each template with validation rules and UI configuration';
COMMENT ON TABLE template_chart_configs IS 'Stores chart visualization configurations for each template';
COMMENT ON TABLE template_executions IS 'Tracks execution history of templates with parameter values and results';
COMMENT ON TABLE user_template_favorites IS 'Stores user favorite templates for quick access';
COMMENT ON TABLE template_ratings IS 'Stores user ratings and reviews for templates';
COMMENT ON VIEW template_statistics IS 'Aggregated statistics view for template usage and popularity';