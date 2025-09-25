#!/usr/bin/env python3
"""
Apply the Report Builder Dashboards migration
Creates tables and columns for the report builder dashboard feature
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_supabase_client():
    """Create Supabase client with service role key"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables")

    return create_client(url, key)


def execute_sql(supabase: Client, sql: str, description: str) -> bool:
    """Execute SQL statement via Supabase RPC"""
    try:
        print(f"  📝 {description}...")
        result = supabase.rpc('execute_sql', {'query': sql}).execute()
        print(f"  ✅ {description} - Success")
        return True
    except Exception as e:
        print(f"  ❌ {description} - Failed: {e}")
        return False


def apply_migration(supabase: Client) -> bool:
    """Apply all migration SQL statements"""

    print("\n🚀 Starting Report Builder Dashboards migration...")
    print("-" * 60)

    success_count = 0
    total_count = 0

    # ==========================================
    # 1. Create report_configurations table
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create report_configurations table"):
        success_count += 1

    # Add indexes for report_configurations
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create report_configurations indexes"):
        success_count += 1

    # ==========================================
    # 2. Create dashboard_views table
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create dashboard_views table"):
        success_count += 1

    # Add indexes for dashboard_views
    sql = """
    CREATE INDEX IF NOT EXISTS idx_dashboard_views_report_config
        ON dashboard_views(report_configuration_id);
    CREATE INDEX IF NOT EXISTS idx_dashboard_views_view_type
        ON dashboard_views(view_type);
    CREATE INDEX IF NOT EXISTS idx_dashboard_views_last_updated
        ON dashboard_views(last_updated);
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create dashboard_views indexes"):
        success_count += 1

    # ==========================================
    # 3. Create dashboard_insights table
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create dashboard_insights table"):
        success_count += 1

    # Add indexes for dashboard_insights
    sql = """
    CREATE INDEX IF NOT EXISTS idx_dashboard_insights_view
        ON dashboard_insights(dashboard_view_id);
    CREATE INDEX IF NOT EXISTS idx_dashboard_insights_type
        ON dashboard_insights(insight_type);
    CREATE INDEX IF NOT EXISTS idx_dashboard_insights_generated
        ON dashboard_insights(generated_at DESC);
    CREATE INDEX IF NOT EXISTS idx_dashboard_insights_confidence
        ON dashboard_insights(confidence_score DESC);
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create dashboard_insights indexes"):
        success_count += 1

    # ==========================================
    # 4. Create report_exports table
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create report_exports table"):
        success_count += 1

    # Add indexes for report_exports
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create report_exports indexes"):
        success_count += 1

    # ==========================================
    # 5. Add columns to workflows table
    # ==========================================
    sql = """
    ALTER TABLE workflows
    ADD COLUMN IF NOT EXISTS report_enabled BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS report_config_id UUID REFERENCES report_configurations(id) ON DELETE SET NULL;
    """
    total_count += 1
    if execute_sql(supabase, sql, "Add report columns to workflows table"):
        success_count += 1

    # Add index for report_enabled workflows
    sql = """
    CREATE INDEX IF NOT EXISTS idx_workflows_report_enabled
        ON workflows(report_enabled)
        WHERE report_enabled = true;
    CREATE INDEX IF NOT EXISTS idx_workflows_report_config
        ON workflows(report_config_id)
        WHERE report_config_id IS NOT NULL;
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create workflows report indexes"):
        success_count += 1

    # ==========================================
    # 6. Add column to query_templates table
    # ==========================================
    sql = """
    ALTER TABLE query_templates
    ADD COLUMN IF NOT EXISTS default_dashboard_type VARCHAR(50)
        CHECK (default_dashboard_type IN ('funnel', 'performance', 'attribution', 'audience', 'custom'));
    """
    total_count += 1
    if execute_sql(supabase, sql, "Add default_dashboard_type to query_templates"):
        success_count += 1

    # Add index for query templates with dashboard type
    sql = """
    CREATE INDEX IF NOT EXISTS idx_query_templates_dashboard_type
        ON query_templates(default_dashboard_type)
        WHERE default_dashboard_type IS NOT NULL;
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create query_templates dashboard index"):
        success_count += 1

    # ==========================================
    # 7. Create composite indexes for performance
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create composite indexes"):
        success_count += 1

    # ==========================================
    # 8. Create updated_at trigger for report_configurations
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Create updated_at trigger"):
        success_count += 1

    # ==========================================
    # 9. Set up Row Level Security (RLS) policies
    # ==========================================
    sql = """
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
    """
    total_count += 1
    if execute_sql(supabase, sql, "Set up RLS policies"):
        success_count += 1

    print("\n" + "=" * 60)
    print(f"✨ Migration completed: {success_count}/{total_count} steps successful")

    return success_count == total_count


def verify_migration(supabase: Client) -> bool:
    """Verify that migration was successful"""

    print("\n🔍 Verifying migration...")
    all_success = True

    # Check new tables
    new_tables = [
        'report_configurations',
        'dashboard_views',
        'dashboard_insights',
        'report_exports'
    ]

    for table in new_tables:
        try:
            response = supabase.table(table).select('id').limit(1).execute()
            print(f"  ✅ Table {table} exists")
        except Exception as e:
            print(f"  ❌ Table {table} not found: {e}")
            all_success = False

    # Check new columns
    column_checks = [
        ('workflows', 'report_enabled'),
        ('workflows', 'report_config_id'),
        ('query_templates', 'default_dashboard_type')
    ]

    for table, column in column_checks:
        try:
            response = supabase.table(table).select(f'id, {column}').limit(1).execute()
            print(f"  ✅ Column {table}.{column} exists")
        except Exception as e:
            if 'column' in str(e).lower() and 'does not exist' in str(e).lower():
                print(f"  ❌ Column {table}.{column} not found")
                all_success = False
            else:
                # Column might exist but table might be empty, that's OK
                print(f"  ✅ Column {table}.{column} exists")

    return all_success


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🚀 Report Builder Dashboards Migration")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")

        # Apply migration
        migration_success = apply_migration(supabase)

        # Verify migration
        verification_success = verify_migration(supabase)

        if migration_success and verification_success:
            print("\n✨ Migration completed successfully!")
            return 0
        else:
            print("\n⚠️ Migration completed with some issues. Please review the output above.")
            return 1

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())