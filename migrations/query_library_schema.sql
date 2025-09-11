-- Query Library Database Migration
-- This migration enhances the query templates system with parameters, reports, and instances

-- ============================================================================
-- STEP 1: Enhance query_templates table
-- ============================================================================

-- Add new columns to query_templates table
ALTER TABLE public.query_templates
ADD COLUMN IF NOT EXISTS report_config JSONB,
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS parent_template_id UUID REFERENCES query_templates(id),
ADD COLUMN IF NOT EXISTS execution_count INTEGER DEFAULT 0;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_query_templates_parent 
ON query_templates(parent_template_id);

CREATE INDEX IF NOT EXISTS idx_query_templates_usage 
ON query_templates(execution_count DESC, created_at DESC);

-- Add comments
COMMENT ON COLUMN query_templates.report_config IS 'Dashboard configuration for auto-generation';
COMMENT ON COLUMN query_templates.version IS 'Template version number for tracking changes';
COMMENT ON COLUMN query_templates.parent_template_id IS 'Reference to parent template if forked';
COMMENT ON COLUMN query_templates.execution_count IS 'Number of times template has been executed';

-- ============================================================================
-- STEP 2: Create query_template_parameters table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.query_template_parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    parameter_name TEXT NOT NULL,
    parameter_type TEXT NOT NULL CHECK (parameter_type IN (
        'asin_list', 'campaign_list', 'date_range', 'date_expression',
        'campaign_filter', 'threshold_numeric', 'percentage', 'enum_select',
        'string', 'number', 'boolean', 'string_list', 'mapped_from_node'
    )),
    display_name TEXT NOT NULL,
    description TEXT,
    required BOOLEAN DEFAULT true,
    default_value JSONB,
    validation_rules JSONB,
    ui_config JSONB,
    display_order INTEGER,
    group_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(template_id, parameter_name)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_parameters_template 
ON query_template_parameters(template_id);

CREATE INDEX IF NOT EXISTS idx_template_parameters_order 
ON query_template_parameters(template_id, display_order);

-- Enable RLS
ALTER TABLE query_template_parameters ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
DO $$ BEGIN
    CREATE POLICY "Users can view parameters for public templates or their own"
    ON query_template_parameters FOR SELECT
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid() OR is_public = true
        )
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can manage parameters for their own templates"
    ON query_template_parameters FOR ALL
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid()
        )
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Add comments
COMMENT ON TABLE query_template_parameters IS 'Structured parameter definitions for query templates';
COMMENT ON COLUMN query_template_parameters.parameter_type IS 'Type of parameter for validation and UI component selection';
COMMENT ON COLUMN query_template_parameters.validation_rules IS 'JSON Schema validation rules for the parameter';
COMMENT ON COLUMN query_template_parameters.ui_config IS 'UI component configuration and hints';
COMMENT ON COLUMN query_template_parameters.display_order IS 'Order in which parameters appear in UI';
COMMENT ON COLUMN query_template_parameters.group_name IS 'Group parameters together in UI sections';

-- ============================================================================
-- STEP 3: Create query_template_reports table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.query_template_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    report_name TEXT NOT NULL,
    dashboard_config JSONB NOT NULL,
    field_mappings JSONB NOT NULL,
    default_filters JSONB,
    widget_order JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_reports_template 
ON query_template_reports(template_id);

-- Enable RLS
ALTER TABLE query_template_reports ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
DO $$ BEGIN
    CREATE POLICY "Users can view reports for public templates or their own"
    ON query_template_reports FOR SELECT
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid() OR is_public = true
        )
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can manage reports for their own templates"
    ON query_template_reports FOR ALL
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid()
        )
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Add comments
COMMENT ON TABLE query_template_reports IS 'Dashboard and report configurations for query templates';
COMMENT ON COLUMN query_template_reports.dashboard_config IS 'Widget layouts and configurations for dashboard';
COMMENT ON COLUMN query_template_reports.field_mappings IS 'Maps query result fields to dashboard widgets';
COMMENT ON COLUMN query_template_reports.default_filters IS 'Default filter settings for the report';
COMMENT ON COLUMN query_template_reports.widget_order IS 'Display order of widgets in the dashboard';

-- ============================================================================
-- STEP 4: Create query_template_instances table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.query_template_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    instance_name TEXT NOT NULL,
    saved_parameters JSONB NOT NULL,
    is_favorite BOOLEAN DEFAULT false,
    last_executed_at TIMESTAMPTZ,
    execution_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_template_instances_user 
ON query_template_instances(user_id, is_favorite DESC, last_executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_template_instances_template 
ON query_template_instances(template_id);

CREATE INDEX IF NOT EXISTS idx_template_instances_favorites
ON query_template_instances(user_id, is_favorite) WHERE is_favorite = true;

-- Enable RLS
ALTER TABLE query_template_instances ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
DO $$ BEGIN
    CREATE POLICY "Users can view their own instances"
    ON query_template_instances FOR SELECT
    USING (user_id = auth.uid());
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE POLICY "Users can manage their own instances"
    ON query_template_instances FOR ALL
    USING (user_id = auth.uid());
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Add comments
COMMENT ON TABLE query_template_instances IS 'Saved parameter sets for query templates';
COMMENT ON COLUMN query_template_instances.saved_parameters IS 'User-saved parameter values for quick re-execution';
COMMENT ON COLUMN query_template_instances.is_favorite IS 'Mark frequently used instances as favorites';
COMMENT ON COLUMN query_template_instances.last_executed_at IS 'Last time this instance was executed';
COMMENT ON COLUMN query_template_instances.execution_count IS 'Number of times this instance has been executed';

-- ============================================================================
-- STEP 5: Create helper functions
-- ============================================================================

-- Function to increment template execution count
CREATE OR REPLACE FUNCTION increment_template_execution_count(p_template_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE query_templates
    SET execution_count = execution_count + 1
    WHERE id = p_template_id;
END;
$$ LANGUAGE plpgsql;

-- Function to increment instance execution count and update last executed
CREATE OR REPLACE FUNCTION increment_instance_execution_count(p_instance_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE query_template_instances
    SET 
        execution_count = execution_count + 1,
        last_executed_at = now()
    WHERE id = p_instance_id;
END;
$$ LANGUAGE plpgsql;

-- Function to fork a template
CREATE OR REPLACE FUNCTION fork_query_template(
    p_template_id UUID,
    p_user_id UUID,
    p_new_name TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_new_template_id UUID;
    v_original_template RECORD;
BEGIN
    -- Get original template
    SELECT * INTO v_original_template
    FROM query_templates
    WHERE id = p_template_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Template not found: %', p_template_id;
    END IF;
    
    -- Create new template
    INSERT INTO query_templates (
        template_id,
        name,
        description,
        category,
        sql_template,
        parameters_schema,
        default_parameters,
        report_config,
        user_id,
        is_public,
        parent_template_id,
        version
    )
    VALUES (
        'tpl_' || substr(gen_random_uuid()::text, 1, 12),
        COALESCE(p_new_name, v_original_template.name || ' (Fork)'),
        v_original_template.description,
        v_original_template.category,
        v_original_template.sql_template,
        v_original_template.parameters_schema,
        v_original_template.default_parameters,
        v_original_template.report_config,
        p_user_id,
        false,  -- Forks are private by default
        p_template_id,
        1  -- New version starts at 1
    )
    RETURNING id INTO v_new_template_id;
    
    -- Copy parameters
    INSERT INTO query_template_parameters (
        template_id,
        parameter_name,
        parameter_type,
        display_name,
        description,
        required,
        default_value,
        validation_rules,
        ui_config,
        display_order,
        group_name
    )
    SELECT 
        v_new_template_id,
        parameter_name,
        parameter_type,
        display_name,
        description,
        required,
        default_value,
        validation_rules,
        ui_config,
        display_order,
        group_name
    FROM query_template_parameters
    WHERE template_id = p_template_id;
    
    -- Copy reports
    INSERT INTO query_template_reports (
        template_id,
        report_name,
        dashboard_config,
        field_mappings,
        default_filters,
        widget_order
    )
    SELECT 
        v_new_template_id,
        report_name,
        dashboard_config,
        field_mappings,
        default_filters,
        widget_order
    FROM query_template_reports
    WHERE template_id = p_template_id;
    
    RETURN v_new_template_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 6: Create triggers for updated_at timestamps
-- ============================================================================

-- Create trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for new tables
DROP TRIGGER IF EXISTS update_query_template_parameters_updated_at ON query_template_parameters;
CREATE TRIGGER update_query_template_parameters_updated_at
    BEFORE UPDATE ON query_template_parameters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_query_template_reports_updated_at ON query_template_reports;
CREATE TRIGGER update_query_template_reports_updated_at
    BEFORE UPDATE ON query_template_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_query_template_instances_updated_at ON query_template_instances;
CREATE TRIGGER update_query_template_instances_updated_at
    BEFORE UPDATE ON query_template_instances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- STEP 7: Grant permissions
-- ============================================================================

-- Grant permissions on new tables
GRANT ALL ON query_template_parameters TO authenticated;
GRANT ALL ON query_template_reports TO authenticated;
GRANT ALL ON query_template_instances TO authenticated;

-- Grant permissions on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION increment_template_execution_count(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION increment_instance_execution_count(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION fork_query_template(UUID, UUID, TEXT) TO authenticated;

-- ============================================================================
-- Migration complete!
-- ============================================================================