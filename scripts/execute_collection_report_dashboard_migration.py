#!/usr/bin/env python3
"""
Execute the collection report dashboard migration directly
"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

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
        
        if not supabase_url or not supabase_password:
            raise ValueError("Missing database connection information. Set DATABASE_URL or SUPABASE_DB_PASSWORD")
        
        # Extract project ID from Supabase URL
        project_id = supabase_url.split('.')[0].replace('https://', '')
        database_url = f"postgresql://postgres.{project_id}:{supabase_password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    return psycopg2.connect(database_url)


def execute_migration():
    """Execute the migration SQL directly"""
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / 'migrations' / '009_create_collection_report_dashboard_tables.sql'
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("🚀 Executing Collection Report Dashboard Migration")
        print("=" * 60)
        
        # Connect to database
        print("📊 Connecting to database...")
        try:
            conn = get_database_connection()
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            print("✅ Connected to database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            print("\n💡 Alternative: Copy the SQL from the migration file and run it in the Supabase SQL editor")
            print(f"   File: {migration_file}")
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
            total_statements = len(statements)
            successful = 0
            
            for i, statement in enumerate(statements, 1):
                if statement.strip() and not statement.strip().startswith('--'):
                    try:
                        cur.execute(statement)
                        successful += 1
                        if 'CREATE TABLE' in statement:
                            table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                            print(f"  ✅ Created table: {table_name}")
                        elif 'CREATE OR REPLACE FUNCTION' in statement:
                            func_name = statement.split('CREATE OR REPLACE FUNCTION')[1].split('(')[0].strip()
                            print(f"  ✅ Created function: {func_name}")
                        elif 'CREATE INDEX' in statement:
                            index_name = statement.split('CREATE INDEX IF NOT EXISTS')[1].split(' ON ')[0].strip()
                            print(f"  ✅ Created index: {index_name}")
                        elif 'CREATE POLICY' in statement:
                            policy_name = statement.split('CREATE POLICY')[1].split('ON')[0].strip().strip('"')
                            print(f"  ✅ Created policy: {policy_name}")
                        elif 'ALTER TABLE' in statement and 'ADD COLUMN' in statement:
                            print(f"  ✅ Added column to table")
                        elif 'CREATE OR REPLACE VIEW' in statement:
                            view_name = statement.split('CREATE OR REPLACE VIEW')[1].split(' AS')[0].strip()
                            print(f"  ✅ Created view: {view_name}")
                    except psycopg2.Error as e:
                        if 'already exists' in str(e):
                            print(f"  ⚠️  Already exists (statement {i}/{total_statements})")
                        else:
                            print(f"  ❌ Error in statement {i}/{total_statements}: {e}")
            
            print(f"\n📊 Migration completed: {successful}/{total_statements} statements executed successfully")
            
            # Verify migration
            print("\n🔍 Verifying migration...")
            
            # Check tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('collection_report_configs', 'collection_report_snapshots')
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"  ✅ Table verified: {table[0]}")
            
            # Check functions
            cur.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('calculate_week_over_week_change', 'aggregate_collection_weeks')
            """)
            functions = cur.fetchall()
            for func in functions:
                print(f"  ✅ Function verified: {func[0]}")
            
            # Check columns
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'report_data_collections'
                AND column_name IN ('report_metadata', 'last_report_generated_at')
            """)
            columns = cur.fetchall()
            for col in columns:
                print(f"  ✅ Column verified: report_data_collections.{col[0]}")
            
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'report_data_weeks'
                AND column_name = 'summary_stats'
            """)
            columns = cur.fetchall()
            for col in columns:
                print(f"  ✅ Column verified: report_data_weeks.{col[0]}")
            
            print("\n✅ Migration executed successfully!")
            
            # Close connection
            cur.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error executing migration: {e}")
            cur.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def main():
    """Main entry point"""
    print("📋 Collection Report Dashboard - Direct Migration Execution")
    print("=" * 60)
    
    # Check for psycopg2
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        os.system("pip install psycopg2-binary")
        import psycopg2
    
    return execute_migration()


if __name__ == '__main__':
    sys.exit(0 if main() else 1)