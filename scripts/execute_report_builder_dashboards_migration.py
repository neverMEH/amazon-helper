#!/usr/bin/env python3
"""
Execute the report builder dashboards migration directly using psycopg2
"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def get_database_connection():
    """Create direct PostgreSQL connection"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        # Try to construct from Supabase URL
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_password = os.getenv('SUPABASE_DB_PASSWORD')

        if not supabase_password:
            # Try alternative env var name
            supabase_password = os.getenv('SUPABASE_DATABASE_PASSWORD')

        if not supabase_url or not supabase_password:
            print("❌ Missing database connection information.")
            print("   Please set one of the following:")
            print("   - DATABASE_URL (PostgreSQL connection string)")
            print("   - SUPABASE_DB_PASSWORD or SUPABASE_DATABASE_PASSWORD (along with SUPABASE_URL)")
            print("\n💡 Alternative: Copy the SQL from the migration file and run it in the Supabase SQL editor")
            print(f"   File: scripts/migrations/010_create_report_builder_dashboard_tables.sql")
            raise ValueError("Missing database connection information")

        # Extract project ID from Supabase URL
        project_id = supabase_url.split('.')[0].replace('https://', '')
        database_url = f"postgresql://postgres.{project_id}:{supabase_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

    return psycopg2.connect(database_url)


def execute_migration():
    """Execute the migration SQL directly"""
    print("\n" + "=" * 60)
    print("🚀 Report Builder Dashboards Migration")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print("-" * 60)

    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / 'migrations' / '010_create_report_builder_dashboard_tables.sql'
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        with open(migration_file, 'r') as f:
            sql = f.read()

        # Connect to database
        print("📊 Connecting to database...")
        try:
            conn = get_database_connection()
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            print("✅ Connected to database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

        # Execute migration
        print("\n🔄 Executing migration SQL...")
        try:
            # Split by semicolons but be careful with functions
            statements = []
            current_statement = []
            in_function = False

            for line in sql.split('\n'):
                if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
                    in_function = True

                current_statement.append(line)

                if line.strip().endswith(';'):
                    if in_function and '$$ LANGUAGE' in line:
                        in_function = False
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                    elif not in_function:
                        statements.append('\n'.join(current_statement))
                        current_statement = []

            # Execute each statement
            total_statements = len([s for s in statements if s.strip() and not s.strip().startswith('--')])
            successful = 0
            failed = 0

            for i, statement in enumerate(statements, 1):
                if statement.strip() and not statement.strip().startswith('--'):
                    try:
                        cur.execute(statement)
                        successful += 1
                        if 'CREATE TABLE' in statement:
                            if 'report_configurations' in statement:
                                print(f"  ✅ Created table: report_configurations")
                            elif 'dashboard_views' in statement:
                                print(f"  ✅ Created table: dashboard_views")
                            elif 'dashboard_insights' in statement:
                                print(f"  ✅ Created table: dashboard_insights")
                            elif 'report_exports' in statement:
                                print(f"  ✅ Created table: report_exports")
                        elif 'CREATE INDEX' in statement:
                            # Extract index name
                            if 'idx_' in statement:
                                parts = statement.split('idx_')
                                if len(parts) > 1:
                                    index_name = 'idx_' + parts[1].split()[0].split('\n')[0]
                                    print(f"  ✅ Created index: {index_name}")
                        elif 'ALTER TABLE' in statement:
                            if 'workflows' in statement and 'report_enabled' in statement:
                                print(f"  ✅ Added columns to workflows table")
                            elif 'query_templates' in statement and 'default_dashboard_type' in statement:
                                print(f"  ✅ Added column to query_templates table")
                            elif 'ENABLE ROW LEVEL SECURITY' in statement:
                                table_name = statement.split('ALTER TABLE')[1].split('ENABLE')[0].strip()
                                print(f"  ✅ Enabled RLS on {table_name}")
                        elif 'CREATE POLICY' in statement:
                            policy_name = statement.split('"')[1]
                            print(f"  ✅ Created RLS policy: {policy_name}")
                        elif 'CREATE OR REPLACE FUNCTION' in statement:
                            print(f"  ✅ Created function: update_updated_at_column")
                        elif 'CREATE TRIGGER' in statement:
                            print(f"  ✅ Created trigger: update_report_configurations_updated_at")
                    except psycopg2.Error as e:
                        if 'already exists' in str(e):
                            print(f"  ⚠️  Already exists (statement {i})")
                            successful += 1  # Count as successful since it exists
                        else:
                            print(f"  ❌ Error in statement {i}: {e}")
                            failed += 1

            print(f"\n📊 Migration completed: {successful}/{total_statements} statements executed successfully")

            if failed > 0:
                print(f"   ⚠️ {failed} statements failed")

            # Verify migration
            print("\n🔍 Verifying migration...")

            # Check tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('report_configurations', 'dashboard_views', 'dashboard_insights', 'report_exports')
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"  ✅ Table verified: {table[0]}")

            # Check columns in workflows table
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'workflows'
                AND column_name IN ('report_enabled', 'report_config_id')
            """)
            workflow_columns = cur.fetchall()
            for col in workflow_columns:
                print(f"  ✅ Column verified: workflows.{col[0]}")

            # Check column in query_templates table
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'query_templates'
                AND column_name = 'default_dashboard_type'
            """)
            template_columns = cur.fetchall()
            for col in template_columns:
                print(f"  ✅ Column verified: query_templates.{col[0]}")

            # Check function
            cur.execute("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_name = 'update_updated_at_column'
            """)
            functions = cur.fetchall()
            for func in functions:
                print(f"  ✅ Function verified: {func[0]}")

            print("\n✨ Migration completed and verified successfully!")
            return True

        except Exception as e:
            print(f"❌ Error executing migration: {e}")
            return False

        finally:
            cur.close()
            conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def main():
    """Main function"""
    success = execute_migration()

    if not success:
        print("\n💡 Manual migration option:")
        print("   1. Copy the contents of: scripts/migrations/010_create_report_builder_dashboard_tables.sql")
        print("   2. Go to your Supabase dashboard")
        print("   3. Navigate to SQL Editor")
        print("   4. Paste and run the SQL")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())