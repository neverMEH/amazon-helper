-- ============================================================
-- AMC REPORT BUILDER - DATABASE MIGRATION
-- ============================================================
-- This migration replaces the workflow-based system with
-- direct ad-hoc execution model for AMC queries
-- ============================================================

-- 1. Extend query_templates table with report columns
ALTER TABLE query_templates
ADD COLUMN IF NOT EXISTS report_type TEXT,
ADD COLUMN IF NOT EXISTS report_config JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS ui_schema JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_query_templates_report_type
ON query_templates(report_type)
WHERE report_type IS NOT NULL;

-- 2. Create report_definitions table
CREATE TABLE IF NOT EXISTS report_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    template_id UUID REFERENCES query_templates(id) ON DELETE RESTRICT,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    frequency TEXT NOT NULL DEFAULT 'once' CHECK (frequency IN ('once', 'daily', 'weekly', 'monthly', 'quarterly')),
    timezone TEXT NOT NULL DEFAULT 'UTC',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    last_execution_id UUID,
    execution_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for report_definitions
CREATE INDEX IF NOT EXISTS idx_report_definitions_owner ON report_definitions(owner_id);
CREATE INDEX IF NOT EXISTS idx_report_definitions_instance ON report_definitions(instance_id);
CREATE INDEX IF NOT EXISTS idx_report_definitions_template ON report_definitions(template_id);
CREATE INDEX IF NOT EXISTS idx_report_definitions_active ON report_definitions(is_active) WHERE is_active = TRUE;

-- 3. Create report_executions table
CREATE TABLE IF NOT EXISTS report_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id TEXT UNIQUE NOT NULL,
    report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
    template_id UUID REFERENCES query_templates(id) ON DELETE SET NULL,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    triggered_by TEXT NOT NULL CHECK (triggered_by IN ('manual', 'schedule', 'backfill', 'api')),
    schedule_id UUID,
    collection_id UUID,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    amc_execution_id TEXT,
    output_location TEXT,
    row_count INTEGER,
    size_bytes BIGINT,
    error_message TEXT,
    parameters_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    time_window_start TIMESTAMPTZ,
    time_window_end TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for report_executions
CREATE INDEX IF NOT EXISTS idx_report_executions_report ON report_executions(report_id);
CREATE INDEX IF NOT EXISTS idx_report_executions_status ON report_executions(status);
CREATE INDEX IF NOT EXISTS idx_report_executions_started ON report_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_executions_amc_id ON report_executions(amc_execution_id) WHERE amc_execution_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_report_exec_composite ON report_executions(report_id, status, started_at DESC);

-- 4. Create report_schedules table
CREATE TABLE IF NOT EXISTS report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id TEXT UNIQUE NOT NULL,
    report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
    schedule_type TEXT NOT NULL CHECK (schedule_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'custom')),
    cron_expression TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    default_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_paused BOOLEAN NOT NULL DEFAULT FALSE,
    last_run_at TIMESTAMPTZ,
    last_run_status TEXT,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(report_id, is_active) WHERE is_active = TRUE
);

-- Create indexes for report_schedules
CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run_at)
WHERE is_active = TRUE AND is_paused = FALSE;
CREATE INDEX IF NOT EXISTS idx_report_schedules_report ON report_schedules(report_id);
CREATE INDEX IF NOT EXISTS idx_report_schedule_composite ON report_schedules(is_active, is_paused, next_run_at)
WHERE is_active = TRUE;

-- Add foreign key constraint for schedule_id in report_executions
ALTER TABLE report_executions
ADD CONSTRAINT fk_report_executions_schedule
FOREIGN KEY (schedule_id) REFERENCES report_schedules(id) ON DELETE SET NULL;

-- 5. Create dashboard_favorites table
CREATE TABLE IF NOT EXISTS dashboard_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(dashboard_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_favorites_user ON dashboard_favorites(user_id);

-- 6. Modify report_data_collections for report backfills
ALTER TABLE report_data_collections
ADD COLUMN IF NOT EXISTS report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS segment_type TEXT DEFAULT 'weekly' CHECK (segment_type IN ('daily', 'weekly', 'monthly', 'quarterly')),
ADD COLUMN IF NOT EXISTS max_lookback_days INTEGER DEFAULT 365 CHECK (max_lookback_days <= 365);

CREATE INDEX IF NOT EXISTS idx_collections_report ON report_data_collections(report_id)
WHERE report_id IS NOT NULL;

-- Add foreign key constraint for collection_id in report_executions
ALTER TABLE report_executions
ADD CONSTRAINT fk_report_executions_collection
FOREIGN KEY (collection_id) REFERENCES report_data_collections(id) ON DELETE SET NULL;

-- 7. Create report_runs_overview view
CREATE OR REPLACE VIEW report_runs_overview AS
SELECT
    rd.id AS report_uuid,
    rd.report_id,
    rd.name,
    rd.description,
    rd.instance_id,
    ai.instance_id AS amc_instance_id,
    ai.instance_name,
    rd.owner_id,
    u.email AS owner_email,
    qt.name AS template_name,
    qt.report_type,
    rd.is_active,
    rd.frequency,
    CASE
        WHEN rs.is_paused THEN 'paused'
        WHEN rd.is_active THEN 'active'
        ELSE 'inactive'
    END AS state,
    re.status AS latest_status,
    re.started_at AS last_run_at,
    re.completed_at AS last_completed_at,
    rs.next_run_at,
    rd.execution_count,
    rd.created_at,
    rd.updated_at,
    EXISTS(
        SELECT 1 FROM dashboard_favorites df
        WHERE df.dashboard_id = rd.dashboard_id
        AND df.user_id = rd.owner_id
    ) AS is_favorite
FROM report_definitions rd
LEFT JOIN query_templates qt ON qt.id = rd.template_id
LEFT JOIN amc_instances ai ON ai.id = rd.instance_id
LEFT JOIN users u ON u.id = rd.owner_id
LEFT JOIN LATERAL (
    SELECT * FROM report_executions re2
    WHERE re2.report_id = rd.id
    ORDER BY re2.started_at DESC NULLS LAST
    LIMIT 1
) re ON TRUE
LEFT JOIN report_schedules rs ON rs.report_id = rd.id AND rs.is_active = TRUE
ORDER BY rd.created_at DESC;

-- 8. Archive existing workflow tables (only if they exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflows') THEN
        CREATE TABLE IF NOT EXISTS archived_workflows AS
        SELECT * FROM workflows;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_executions') THEN
        CREATE TABLE IF NOT EXISTS archived_workflow_executions AS
        SELECT * FROM workflow_executions;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_schedules') THEN
        CREATE TABLE IF NOT EXISTS archived_workflow_schedules AS
        SELECT * FROM workflow_schedules;
    END IF;
END $$;

-- Add deprecation comments
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflows') THEN
        COMMENT ON TABLE workflows IS 'DEPRECATED: Replaced by report_definitions. Archived data available in archived_workflows.';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_executions') THEN
        COMMENT ON TABLE workflow_executions IS 'DEPRECATED: Replaced by report_executions. Archived data available in archived_workflow_executions.';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'workflow_schedules') THEN
        COMMENT ON TABLE workflow_schedules IS 'DEPRECATED: Replaced by report_schedules. Archived data available in archived_workflow_schedules.';
    END IF;
END $$;

-- 9. Create update trigger for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_report_definitions_updated_at ON report_definitions;
CREATE TRIGGER update_report_definitions_updated_at
BEFORE UPDATE ON report_definitions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_executions_updated_at ON report_executions;
CREATE TRIGGER update_report_executions_updated_at
BEFORE UPDATE ON report_executions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_schedules_updated_at ON report_schedules;
CREATE TRIGGER update_report_schedules_updated_at
BEFORE UPDATE ON report_schedules
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. Create helper functions for the view
CREATE OR REPLACE FUNCTION get_report_runs_overview(filter_report_id UUID DEFAULT NULL)
RETURNS TABLE (
    report_uuid UUID,
    report_id TEXT,
    name TEXT,
    description TEXT,
    instance_id UUID,
    amc_instance_id TEXT,
    instance_name TEXT,
    owner_id UUID,
    owner_email TEXT,
    template_name TEXT,
    report_type TEXT,
    is_active BOOLEAN,
    frequency TEXT,
    state TEXT,
    latest_status TEXT,
    last_run_at TIMESTAMPTZ,
    last_completed_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    execution_count INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    is_favorite BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM report_runs_overview
    WHERE filter_report_id IS NULL OR report_runs_overview.report_uuid = filter_report_id;
END;
$$ LANGUAGE plpgsql;

-- Helper functions for testing
CREATE OR REPLACE FUNCTION get_database_tables(schema_name TEXT DEFAULT 'public')
RETURNS TABLE (table_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT tablename::TEXT FROM pg_tables WHERE schemaname = schema_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_table_comment(table_name TEXT)
RETURNS TABLE (comment TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT obj_description(c.oid)::TEXT
    FROM pg_class c
    WHERE c.relname = table_name AND c.relkind = 'r';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_table_indexes(schema_name TEXT DEFAULT 'public')
RETURNS TABLE (index_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT indexname::TEXT FROM pg_indexes WHERE schemaname = schema_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
-- To run this migration:
-- 1. Open Supabase Dashboard
-- 2. Go to SQL Editor
-- 3. Paste this entire script
-- 4. Click "Run"
-- ============================================================