#!/usr/bin/env python3
"""Execute Build Guides migration using Supabase client"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

# SQL statements to execute - split into individual statements
SQL_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS build_guides (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        guide_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        short_description TEXT,
        tags JSONB DEFAULT '[]',
        icon TEXT,
        difficulty_level TEXT DEFAULT 'intermediate',
        estimated_time_minutes INTEGER DEFAULT 30,
        prerequisites JSONB DEFAULT '[]',
        is_published BOOLEAN DEFAULT false,
        display_order INTEGER DEFAULT 0,
        created_by UUID REFERENCES users(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    
    """CREATE TABLE IF NOT EXISTS build_guide_sections (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
        section_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content_markdown TEXT,
        display_order INTEGER NOT NULL,
        is_collapsible BOOLEAN DEFAULT true,
        default_expanded BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(guide_id, section_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS build_guide_queries (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
        query_template_id UUID REFERENCES query_templates(id),
        title TEXT NOT NULL,
        description TEXT,
        sql_query TEXT NOT NULL,
        parameters_schema JSONB DEFAULT '{}',
        default_parameters JSONB DEFAULT '{}',
        display_order INTEGER NOT NULL,
        query_type TEXT DEFAULT 'main_analysis',
        expected_columns JSONB,
        interpretation_notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    
    """CREATE TABLE IF NOT EXISTS build_guide_examples (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        guide_query_id UUID REFERENCES build_guide_queries(id) ON DELETE CASCADE,
        example_name TEXT NOT NULL,
        sample_data JSONB NOT NULL,
        interpretation_markdown TEXT,
        insights JSONB DEFAULT '[]',
        display_order INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )""",
    
    """CREATE TABLE IF NOT EXISTS build_guide_metrics (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
        metric_name TEXT NOT NULL,
        display_name TEXT NOT NULL,
        definition TEXT NOT NULL,
        metric_type TEXT DEFAULT 'metric',
        display_order INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(guide_id, metric_name)
    )""",
    
    """CREATE TABLE IF NOT EXISTS user_guide_progress (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'not_started',
        current_section TEXT,
        completed_sections JSONB DEFAULT '[]',
        executed_queries JSONB DEFAULT '[]',
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        progress_percentage INTEGER DEFAULT 0,
        UNIQUE(user_id, guide_id)
    )""",
    
    """CREATE TABLE IF NOT EXISTS user_guide_favorites (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(user_id, guide_id)
    )"""
]

# Index statements
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_guides_published ON build_guides(is_published)",
    "CREATE INDEX IF NOT EXISTS idx_guides_category ON build_guides(category)",
    "CREATE INDEX IF NOT EXISTS idx_guides_display_order ON build_guides(display_order)",
    "CREATE INDEX IF NOT EXISTS idx_guide_sections_guide ON build_guide_sections(guide_id)",
    "CREATE INDEX IF NOT EXISTS idx_guide_sections_order ON build_guide_sections(guide_id, display_order)",
    "CREATE INDEX IF NOT EXISTS idx_guide_queries_guide ON build_guide_queries(guide_id)",
    "CREATE INDEX IF NOT EXISTS idx_guide_queries_order ON build_guide_queries(guide_id, display_order)",
    "CREATE INDEX IF NOT EXISTS idx_guide_examples_query ON build_guide_examples(guide_query_id)",
    "CREATE INDEX IF NOT EXISTS idx_guide_metrics_guide ON build_guide_metrics(guide_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_progress ON user_guide_progress(user_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_user_progress_guide ON user_guide_progress(guide_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_user_favorites ON user_guide_favorites(user_id)"
]

def execute_migration():
    """Execute the Build Guides migration"""
    try:
        # Note: Supabase Python client doesn't support raw SQL execution directly
        # We'll need to use the postgrest-py client or execute through RPC
        
        # For now, let's verify the tables don't exist and report what needs to be done
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Try to query the build_guides table to see if it exists
        try:
            result = client.table('build_guides').select('count').limit(1).execute()
            logger.info("✅ Build Guides tables already exist in database!")
            return True
        except Exception as e:
            if 'relation "public.build_guides" does not exist' in str(e):
                logger.info("Build Guides tables do not exist yet.")
            else:
                logger.error(f"Error checking tables: {e}")
        
        # Generate the full SQL script
        full_sql = "-- Build Guides Migration\n\n"
        
        # Add table creation statements
        for i, stmt in enumerate(SQL_STATEMENTS, 1):
            full_sql += f"-- Table {i}/{len(SQL_STATEMENTS)}\n"
            full_sql += stmt + ";\n\n"
        
        # Add index creation statements
        full_sql += "-- Create indexes\n"
        for stmt in INDEX_STATEMENTS:
            full_sql += stmt + ";\n"
        
        # Add trigger function
        full_sql += """
-- Add updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers
DROP TRIGGER IF EXISTS update_build_guides_updated_at ON build_guides;
CREATE TRIGGER update_build_guides_updated_at BEFORE UPDATE ON build_guides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_build_guide_sections_updated_at ON build_guide_sections;
CREATE TRIGGER update_build_guide_sections_updated_at BEFORE UPDATE ON build_guide_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_build_guide_queries_updated_at ON build_guide_queries;
CREATE TRIGGER update_build_guide_queries_updated_at BEFORE UPDATE ON build_guide_queries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_build_guide_examples_updated_at ON build_guide_examples;
CREATE TRIGGER update_build_guide_examples_updated_at BEFORE UPDATE ON build_guide_examples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
        
        # Save to file
        output_path = Path(__file__).parent / 'build_guides_migration_full.sql'
        with open(output_path, 'w') as f:
            f.write(full_sql)
        
        print("\n" + "="*60)
        print("📋 MANUAL STEP REQUIRED")
        print("="*60)
        print("\nThe Build Guides tables need to be created in Supabase.")
        print("\n📝 Option 1: Supabase Dashboard (Recommended)")
        print("1. Go to your Supabase project dashboard")
        print("2. Navigate to SQL Editor")
        print(f"3. Copy the contents of: {output_path}")
        print("4. Paste into the SQL Editor")
        print("5. Click 'Run' to execute the migration")
        
        print("\n🔧 Option 2: Supabase CLI")
        print(f"supabase db push --file {output_path}")
        
        print("\n✅ After running the migration, the Build Guides feature will be ready!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to execute migration: {e}")
        return False

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)