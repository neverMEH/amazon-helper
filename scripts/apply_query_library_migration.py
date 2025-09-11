#!/usr/bin/env python3
"""
Apply the Query Library database migration
Creates enhanced query templates schema with parameters, reports, and instances
"""
import os
import sys
from pathlib import Path

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


def apply_query_templates_enhancements(supabase: Client):
    """Enhance the query_templates table with new columns"""
    
    print("\n📝 Enhancing query_templates table...")
    
    # Check if columns already exist
    try:
        result = supabase.table('query_templates').select('id, report_config').limit(1).execute()
        print("  ⚠️  Enhanced columns already exist, skipping...")
        return
    except:
        pass  # Columns don't exist, proceed with migration
    
    # SQL to add new columns to query_templates
    sql = """
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
    
    -- Add comment
    COMMENT ON COLUMN query_templates.report_config IS 'Dashboard configuration for auto-generation';
    COMMENT ON COLUMN query_templates.version IS 'Template version number for tracking changes';
    COMMENT ON COLUMN query_templates.parent_template_id IS 'Reference to parent template if forked';
    COMMENT ON COLUMN query_templates.execution_count IS 'Number of times template has been executed';
    """
    
    try:
        supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("  ✅ query_templates table enhanced successfully")
    except Exception as e:
        print(f"  ❌ Failed to enhance query_templates: {e}")
        raise


def create_query_template_parameters_table(supabase: Client):
    """Create the query_template_parameters table"""
    
    print("\n📝 Creating query_template_parameters table...")
    
    # Check if table already exists
    try:
        result = supabase.table('query_template_parameters').select('id').limit(1).execute()
        print("  ⚠️  Table already exists, skipping...")
        return
    except:
        pass  # Table doesn't exist, proceed with creation
    
    sql = """
    -- Create query_template_parameters table
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
    CREATE INDEX idx_template_parameters_template 
    ON query_template_parameters(template_id);
    
    CREATE INDEX idx_template_parameters_order 
    ON query_template_parameters(template_id, display_order);
    
    -- Enable RLS
    ALTER TABLE query_template_parameters ENABLE ROW LEVEL SECURITY;
    
    -- Create RLS policies
    CREATE POLICY "Users can view parameters for public templates or their own"
    ON query_template_parameters FOR SELECT
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid() OR is_public = true
        )
    );
    
    CREATE POLICY "Users can manage parameters for their own templates"
    ON query_template_parameters FOR ALL
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid()
        )
    );
    
    -- Add comments
    COMMENT ON TABLE query_template_parameters IS 'Structured parameter definitions for query templates';
    COMMENT ON COLUMN query_template_parameters.parameter_type IS 'Type of parameter for validation and UI component selection';
    COMMENT ON COLUMN query_template_parameters.validation_rules IS 'JSON Schema validation rules for the parameter';
    COMMENT ON COLUMN query_template_parameters.ui_config IS 'UI component configuration and hints';
    """
    
    try:
        supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("  ✅ query_template_parameters table created successfully")
    except Exception as e:
        print(f"  ❌ Failed to create query_template_parameters: {e}")
        raise


def create_query_template_reports_table(supabase: Client):
    """Create the query_template_reports table"""
    
    print("\n📝 Creating query_template_reports table...")
    
    # Check if table already exists
    try:
        result = supabase.table('query_template_reports').select('id').limit(1).execute()
        print("  ⚠️  Table already exists, skipping...")
        return
    except:
        pass  # Table doesn't exist, proceed with creation
    
    sql = """
    -- Create query_template_reports table
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
    CREATE INDEX idx_template_reports_template 
    ON query_template_reports(template_id);
    
    -- Enable RLS
    ALTER TABLE query_template_reports ENABLE ROW LEVEL SECURITY;
    
    -- Create RLS policies
    CREATE POLICY "Users can view reports for public templates or their own"
    ON query_template_reports FOR SELECT
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid() OR is_public = true
        )
    );
    
    CREATE POLICY "Users can manage reports for their own templates"
    ON query_template_reports FOR ALL
    USING (
        template_id IN (
            SELECT id FROM query_templates 
            WHERE user_id = auth.uid()
        )
    );
    
    -- Add comments
    COMMENT ON TABLE query_template_reports IS 'Dashboard and report configurations for query templates';
    COMMENT ON COLUMN query_template_reports.dashboard_config IS 'Widget layouts and configurations for dashboard';
    COMMENT ON COLUMN query_template_reports.field_mappings IS 'Maps query result fields to dashboard widgets';
    """
    
    try:
        supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("  ✅ query_template_reports table created successfully")
    except Exception as e:
        print(f"  ❌ Failed to create query_template_reports: {e}")
        raise


def create_query_template_instances_table(supabase: Client):
    """Create the query_template_instances table"""
    
    print("\n📝 Creating query_template_instances table...")
    
    # Check if table already exists
    try:
        result = supabase.table('query_template_instances').select('id').limit(1).execute()
        print("  ⚠️  Table already exists, skipping...")
        return
    except:
        pass  # Table doesn't exist, proceed with creation
    
    sql = """
    -- Create query_template_instances table
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
    CREATE INDEX idx_template_instances_user 
    ON query_template_instances(user_id, is_favorite DESC, last_executed_at DESC);
    
    CREATE INDEX idx_template_instances_template 
    ON query_template_instances(template_id);
    
    -- Enable RLS
    ALTER TABLE query_template_instances ENABLE ROW LEVEL SECURITY;
    
    -- Create RLS policies
    CREATE POLICY "Users can view their own instances"
    ON query_template_instances FOR SELECT
    USING (user_id = auth.uid());
    
    CREATE POLICY "Users can manage their own instances"
    ON query_template_instances FOR ALL
    USING (user_id = auth.uid());
    
    -- Add comments
    COMMENT ON TABLE query_template_instances IS 'Saved parameter sets for query templates';
    COMMENT ON COLUMN query_template_instances.saved_parameters IS 'User-saved parameter values for quick re-execution';
    COMMENT ON COLUMN query_template_instances.is_favorite IS 'Mark frequently used instances as favorites';
    """
    
    try:
        supabase.rpc('exec_sql', {'sql': sql}).execute()
        print("  ✅ query_template_instances table created successfully")
    except Exception as e:
        print(f"  ❌ Failed to create query_template_instances: {e}")
        raise


def migrate_existing_templates(supabase: Client):
    """Migrate existing templates to populate parameter definitions"""
    
    print("\n🔄 Migrating existing templates...")
    
    try:
        # Get all existing templates
        templates = supabase.table('query_templates').select('*').execute()
        
        if not templates.data:
            print("  ℹ️  No existing templates to migrate")
            return
        
        migrated_count = 0
        for template in templates.data:
            # Check if parameters already exist for this template
            existing_params = supabase.table('query_template_parameters')\
                .select('id')\
                .eq('template_id', template['id'])\
                .execute()
            
            if existing_params.data:
                continue  # Skip if parameters already exist
            
            # Extract parameters from parameters_schema if it exists
            if template.get('parameters_schema') and template['parameters_schema'].get('properties'):
                properties = template['parameters_schema']['properties']
                order = 1
                
                for param_name, param_schema in properties.items():
                    # Infer parameter type
                    param_type = 'string'  # Default
                    if 'asin' in param_name.lower():
                        param_type = 'asin_list'
                    elif 'campaign' in param_name.lower():
                        param_type = 'campaign_list'
                    elif 'date' in param_name.lower():
                        param_type = 'date_range'
                    elif param_schema.get('type') == 'number':
                        param_type = 'number'
                    elif param_schema.get('type') == 'boolean':
                        param_type = 'boolean'
                    
                    # Create parameter definition
                    param_data = {
                        'template_id': template['id'],
                        'parameter_name': param_name,
                        'parameter_type': param_type,
                        'display_name': param_schema.get('title', param_name),
                        'description': param_schema.get('description'),
                        'required': param_name in template['parameters_schema'].get('required', []),
                        'default_value': param_schema.get('default'),
                        'display_order': order
                    }
                    
                    try:
                        supabase.table('query_template_parameters').insert(param_data).execute()
                        order += 1
                    except Exception as e:
                        print(f"  ⚠️  Failed to migrate parameter {param_name}: {e}")
                
                migrated_count += 1
        
        print(f"  ✅ Migrated {migrated_count} templates")
        
    except Exception as e:
        print(f"  ⚠️  Migration warning: {e}")


def verify_migration(supabase: Client) -> bool:
    """Verify that migration was successful"""
    
    print("\n🔍 Verifying migration...")
    all_success = True
    
    # Check enhanced columns in query_templates
    column_checks = [
        ('query_templates', 'report_config'),
        ('query_templates', 'version'),
        ('query_templates', 'parent_template_id'),
        ('query_templates', 'execution_count')
    ]
    
    for table, column in column_checks:
        try:
            response = supabase.table(table).select(f'id, {column}').limit(1).execute()
            print(f"  ✅ Column {table}.{column} exists")
        except Exception as e:
            print(f"  ❌ Column {table}.{column} not found: {e}")
            all_success = False
    
    # Check new tables
    new_tables = [
        'query_template_parameters',
        'query_template_reports',
        'query_template_instances'
    ]
    
    for table in new_tables:
        try:
            response = supabase.table(table).select('id').limit(1).execute()
            print(f"  ✅ Table {table} exists")
        except Exception as e:
            print(f"  ❌ Table {table} not found: {e}")
            all_success = False
    
    return all_success


def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 Query Library Database Migration")
    print("=" * 60)
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Apply migrations in order
        apply_query_templates_enhancements(supabase)
        create_query_template_parameters_table(supabase)
        create_query_template_reports_table(supabase)
        create_query_template_instances_table(supabase)
        
        # Migrate existing data
        migrate_existing_templates(supabase)
        
        # Verify migration
        success = verify_migration(supabase)
        
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n⚠️  Migration completed with warnings. Please review the output above.")
        
        print("\n📊 Next steps:")
        print("  1. Run the test suite: pytest tests/supabase/test_query_library_schema.py -v")
        print("  2. Update backend services to use new schema")
        print("  3. Implement frontend components")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()