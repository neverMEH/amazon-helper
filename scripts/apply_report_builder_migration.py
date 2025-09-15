"""
Migration script for AMC Report Builder database schema
Replaces workflow-based system with direct ad-hoc execution model
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase: Client = create_client(url, key)


def run_migration(sql: str, description: str) -> bool:
    """Execute a migration SQL statement"""
    try:
        print(f"Running: {description}...")
        result = supabase.rpc('execute_sql', {'query': sql}).execute()
        print(f"✓ {description} completed")
        return True
    except Exception as e:
        print(f"✗ {description} failed: {str(e)}")
        return False


def main():
    """Run all migrations for Report Builder"""
    print("\n" + "="*60)
    print("AMC REPORT BUILDER - DATABASE MIGRATION")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    print("-"*60)

    migrations = []
    success_count = 0

    # 1. Extend query_templates table with report columns
    migrations.append(("""
        ALTER TABLE query_templates
        ADD COLUMN IF NOT EXISTS report_type TEXT,
        ADD COLUMN IF NOT EXISTS report_config JSONB DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS ui_schema JSONB DEFAULT '{}'::jsonb;
    """, "Extend query_templates with report columns"))

    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_query_templates_report_type
        ON query_templates(report_type)
        WHERE report_type IS NOT NULL;
    """, "Create index on query_templates.report_type"))

    # 2. Create report_definitions table
    migrations.append(("""
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
    """, "Create report_definitions table"))

    # Create indexes for report_definitions
    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_report_definitions_owner ON report_definitions(owner_id);
        CREATE INDEX IF NOT EXISTS idx_report_definitions_instance ON report_definitions(instance_id);
        CREATE INDEX IF NOT EXISTS idx_report_definitions_template ON report_definitions(template_id);
        CREATE INDEX IF NOT EXISTS idx_report_definitions_active ON report_definitions(is_active) WHERE is_active = TRUE;
    """, "Create indexes for report_definitions"))

    # 3. Create report_executions table
    migrations.append(("""
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
    """, "Create report_executions table"))

    # Create indexes for report_executions
    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_report_executions_report ON report_executions(report_id);
        CREATE INDEX IF NOT EXISTS idx_report_executions_status ON report_executions(status);
        CREATE INDEX IF NOT EXISTS idx_report_executions_started ON report_executions(started_at DESC);
        CREATE INDEX IF NOT EXISTS idx_report_executions_amc_id ON report_executions(amc_execution_id) WHERE amc_execution_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_report_exec_composite ON report_executions(report_id, status, started_at DESC);
    """, "Create indexes for report_executions"))

    # 4. Create report_schedules table
    migrations.append(("""
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
    """, "Create report_schedules table"))

    # Create indexes for report_schedules
    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run_at)
        WHERE is_active = TRUE AND is_paused = FALSE;
        CREATE INDEX IF NOT EXISTS idx_report_schedules_report ON report_schedules(report_id);
        CREATE INDEX IF NOT EXISTS idx_report_schedule_composite ON report_schedules(is_active, is_paused, next_run_at)
        WHERE is_active = TRUE;
    """, "Create indexes for report_schedules"))

    # Add foreign key constraint for schedule_id in report_executions
    migrations.append(("""
        ALTER TABLE report_executions
        ADD CONSTRAINT fk_report_executions_schedule
        FOREIGN KEY (schedule_id) REFERENCES report_schedules(id) ON DELETE SET NULL;
    """, "Add foreign key for report_executions.schedule_id"))

    # 5. Create dashboard_favorites table
    migrations.append(("""
        CREATE TABLE IF NOT EXISTS dashboard_favorites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ DEFAULT now(),
            UNIQUE(dashboard_id, user_id)
        );
    """, "Create dashboard_favorites table"))

    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_dashboard_favorites_user ON dashboard_favorites(user_id);
    """, "Create index for dashboard_favorites"))

    # 6. Modify report_data_collections for report backfills
    migrations.append(("""
        ALTER TABLE report_data_collections
        ADD COLUMN IF NOT EXISTS report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
        ADD COLUMN IF NOT EXISTS segment_type TEXT DEFAULT 'weekly' CHECK (segment_type IN ('daily', 'weekly', 'monthly', 'quarterly')),
        ADD COLUMN IF NOT EXISTS max_lookback_days INTEGER DEFAULT 365 CHECK (max_lookback_days <= 365);
    """, "Extend report_data_collections for report backfills"))

    migrations.append(("""
        CREATE INDEX IF NOT EXISTS idx_collections_report ON report_data_collections(report_id)
        WHERE report_id IS NOT NULL;
    """, "Create index for report_data_collections.report_id"))

    # Add foreign key constraint for collection_id in report_executions
    migrations.append(("""
        ALTER TABLE report_executions
        ADD CONSTRAINT fk_report_executions_collection
        FOREIGN KEY (collection_id) REFERENCES report_data_collections(id) ON DELETE SET NULL;
    """, "Add foreign key for report_executions.collection_id"))

    # 7. Create report_runs_overview view
    migrations.append(("""
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
    """, "Create report_runs_overview view"))

    # 8. Archive existing workflow tables
    migrations.append(("""
        CREATE TABLE IF NOT EXISTS archived_workflows AS
        SELECT * FROM workflows;
    """, "Archive workflows table"))

    migrations.append(("""
        CREATE TABLE IF NOT EXISTS archived_workflow_executions AS
        SELECT * FROM workflow_executions;
    """, "Archive workflow_executions table"))

    migrations.append(("""
        CREATE TABLE IF NOT EXISTS archived_workflow_schedules AS
        SELECT * FROM workflow_schedules;
    """, "Archive workflow_schedules table"))

    # Add deprecation comments
    migrations.append(("""
        COMMENT ON TABLE workflows IS 'DEPRECATED: Replaced by report_definitions. Archived data available in archived_workflows.';
        COMMENT ON TABLE workflow_executions IS 'DEPRECATED: Replaced by report_executions. Archived data available in archived_workflow_executions.';
        COMMENT ON TABLE workflow_schedules IS 'DEPRECATED: Replaced by report_schedules. Archived data available in archived_workflow_schedules.';
    """, "Add deprecation comments to workflow tables"))

    # 9. Create update trigger for timestamps
    migrations.append(("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """, "Create update_updated_at_column function"))

    migrations.append(("""
        CREATE TRIGGER update_report_definitions_updated_at
        BEFORE UPDATE ON report_definitions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """, "Create trigger for report_definitions.updated_at"))

    migrations.append(("""
        CREATE TRIGGER update_report_executions_updated_at
        BEFORE UPDATE ON report_executions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """, "Create trigger for report_executions.updated_at"))

    migrations.append(("""
        CREATE TRIGGER update_report_schedules_updated_at
        BEFORE UPDATE ON report_schedules
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """, "Create trigger for report_schedules.updated_at"))

    # 10. Create helper functions for the view
    migrations.append(("""
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
    """, "Create get_report_runs_overview function"))

    # Helper functions for testing
    migrations.append(("""
        CREATE OR REPLACE FUNCTION get_database_tables(schema_name TEXT DEFAULT 'public')
        RETURNS TABLE (table_name TEXT) AS $$
        BEGIN
            RETURN QUERY
            SELECT tablename::TEXT FROM pg_tables WHERE schemaname = schema_name;
        END;
        $$ LANGUAGE plpgsql;
    """, "Create get_database_tables helper function"))

    migrations.append(("""
        CREATE OR REPLACE FUNCTION get_table_comment(table_name TEXT)
        RETURNS TABLE (comment TEXT) AS $$
        BEGIN
            RETURN QUERY
            SELECT obj_description(c.oid)::TEXT
            FROM pg_class c
            WHERE c.relname = table_name AND c.relkind = 'r';
        END;
        $$ LANGUAGE plpgsql;
    """, "Create get_table_comment helper function"))

    migrations.append(("""
        CREATE OR REPLACE FUNCTION get_table_indexes(schema_name TEXT DEFAULT 'public')
        RETURNS TABLE (index_name TEXT) AS $$
        BEGIN
            RETURN QUERY
            SELECT indexname::TEXT FROM pg_indexes WHERE schemaname = schema_name;
        END;
        $$ LANGUAGE plpgsql;
    """, "Create get_table_indexes helper function"))

    # Execute all migrations
    for sql, description in migrations:
        if run_migration(sql, description):
            success_count += 1

    # Summary
    print("-"*60)
    print(f"Migration completed at: {datetime.now().isoformat()}")
    print(f"Results: {success_count}/{len(migrations)} migrations successful")

    if success_count == len(migrations):
        print("✓ All migrations completed successfully!")
        return 0
    else:
        print(f"⚠ {len(migrations) - success_count} migrations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())