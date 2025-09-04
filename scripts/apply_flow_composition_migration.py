#!/usr/bin/env python3
"""
Apply Visual Query Flow Builder database migration
Creates tables for flow composition functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def apply_migration(supabase: Client, migration_file: str) -> bool:
    """Apply SQL migration file to Supabase database"""
    
    # Read migration file
    migration_path = Path(__file__).parent / 'migrations' / migration_file
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        sql_content = f.read()
    
    # Remove the migration history insert at the end (Supabase doesn't have this table yet)
    sql_statements = sql_content.split('-- MIGRATION METADATA')[0]
    
    try:
        # Execute migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use the REST API or run via psql
        print(f"📋 Migration SQL prepared: {migration_file}")
        print(f"⚠️  Please execute the following SQL in Supabase SQL Editor:")
        print(f"    Path: {migration_path}")
        print()
        print("Or run via command line:")
        print(f"psql $DATABASE_URL < {migration_path}")
        print()
        
        # Verify connection
        response = supabase.table('users').select('id').limit(1).execute()
        print("✅ Successfully connected to Supabase")
        
        # Check if tables already exist
        try:
            response = supabase.table('template_flow_compositions').select('id').limit(1).execute()
            print("⚠️  Warning: template_flow_compositions table already exists")
            return True
        except Exception:
            print("✅ Table template_flow_compositions does not exist yet - ready for migration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False


def verify_migration(supabase: Client) -> bool:
    """Verify that migration was successful"""
    
    tables_to_check = [
        'template_flow_compositions',
        'template_flow_nodes', 
        'template_flow_connections',
        'user_composition_favorites',
        'template_flow_composition_executions'
    ]
    
    print("\n🔍 Verifying migration...")
    all_exist = True
    
    for table in tables_to_check:
        try:
            response = supabase.table(table).select('id').limit(1).execute()
            print(f"  ✅ Table {table} exists")
        except Exception as e:
            print(f"  ❌ Table {table} not found")
            all_exist = False
    
    # Check if workflow_executions has new columns
    try:
        response = supabase.table('workflow_executions').select('composition_execution_id').limit(1).execute()
        print(f"  ✅ Column composition_execution_id exists in workflow_executions")
    except Exception:
        print(f"  ⚠️  Column composition_execution_id not added to workflow_executions yet")
    
    # Check if workflow_schedules has new columns
    try:
        response = supabase.table('workflow_schedules').select('composition_id').limit(1).execute()
        print(f"  ✅ Column composition_id exists in workflow_schedules")
    except Exception:
        print(f"  ⚠️  Column composition_id not added to workflow_schedules yet")
    
    return all_exist


def main():
    """Main execution"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        print("   Please check your .env file")
        return 1
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    print("🚀 Visual Query Flow Builder - Database Migration")
    print("=" * 50)
    
    # Apply migration
    migration_file = '002_create_flow_composition_tables.sql'
    success = apply_migration(supabase, migration_file)
    
    if success:
        print("\n" + "=" * 50)
        print("📝 Next Steps:")
        print("1. Copy the SQL from the migration file")
        print(f"2. Open Supabase SQL Editor: {supabase_url.replace('.supabase.co', '.supabase.com/project/').replace('https://', 'https://app.')}/sql")
        print("3. Paste and execute the SQL")
        print("4. Run this script again to verify")
        
        # Try to verify if tables exist
        verify_migration(supabase)
    else:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())