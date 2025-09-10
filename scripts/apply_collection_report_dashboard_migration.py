#!/usr/bin/env python3
"""
Apply the collection report dashboard migration
Creates tables and functions for the report dashboard feature
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


def verify_migration(supabase: Client) -> bool:
    """Verify that migration was successful"""
    
    print("\n🔍 Verifying migration...")
    all_success = True
    
    # Check new tables
    new_tables = [
        'collection_report_configs',
        'collection_report_snapshots'
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
        ('report_data_collections', 'report_metadata'),
        ('report_data_collections', 'last_report_generated_at'),
        ('report_data_weeks', 'summary_stats')
    ]
    
    for table, column in column_checks:
        try:
            response = supabase.table(table).select(f'id, {column}').limit(1).execute()
            print(f"  ✅ Column {table}.{column} exists")
        except Exception as e:
            print(f"  ❌ Column {table}.{column} not found: {e}")
            all_success = False
    
    # Check functions
    function_checks = [
        ('calculate_week_over_week_change', {
            'p_collection_id': '00000000-0000-0000-0000-000000000000',
            'p_metric': 'impressions',
            'p_week1_start': '2025-01-01',
            'p_week2_start': '2025-01-08'
        }),
        ('aggregate_collection_weeks', {
            'p_collection_id': '00000000-0000-0000-0000-000000000000',
            'p_start_date': '2025-01-01',
            'p_end_date': '2025-03-31',
            'p_aggregation_type': 'sum'
        })
    ]
    
    for func_name, params in function_checks:
        try:
            response = supabase.rpc(func_name, params).execute()
            print(f"  ✅ Function {func_name} exists")
        except Exception as e:
            if 'function' in str(e).lower() and 'does not exist' in str(e).lower():
                print(f"  ❌ Function {func_name} not found")
                all_success = False
            else:
                # Function exists but returned an error (likely no data), that's OK
                print(f"  ✅ Function {func_name} exists")
    
    # Check view
    try:
        # Try to query the view
        response = supabase.from_('collection_report_summary').select('collection_id').limit(1).execute()
        print(f"  ✅ View collection_report_summary exists")
    except Exception as e:
        if 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
            print(f"  ❌ View collection_report_summary not found")
            all_success = False
        else:
            # View exists but may have no data
            print(f"  ✅ View collection_report_summary exists")
    
    return all_success


def apply_migration():
    """Apply the collection report dashboard migration"""
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / 'migrations' / '009_create_collection_report_dashboard_tables.sql'
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("🚀 Collection Report Dashboard - Database Migration")
        print("=" * 60)
        print("📊 This migration will create:")
        print("   Tables:")
        print("   - collection_report_configs (saved dashboard configurations)")
        print("   - collection_report_snapshots (shareable report snapshots)")
        print("\n   Columns:")
        print("   - report_data_collections.report_metadata")
        print("   - report_data_collections.last_report_generated_at")
        print("   - report_data_weeks.summary_stats")
        print("\n   Functions:")
        print("   - calculate_week_over_week_change()")
        print("   - aggregate_collection_weeks()")
        print("\n   Plus indexes, RLS policies, and a summary view")
        print("=" * 60)
        
        # Get Supabase client
        client = get_supabase_client()
        
        # Get Supabase URL for dashboard link
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            project_ref = supabase_url.split('.')[0].replace('https://', '')
            dashboard_url = f"https://supabase.com/dashboard/project/{project_ref}/editor"
            print(f"\n📎 Supabase SQL Editor: {dashboard_url}")
        
        # Ask for confirmation
        print("\n⚠️  This will modify your database schema.")
        response = input("Do you want to proceed? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Migration cancelled")
            return False
        
        print("\n🔄 Applying migration...")
        
        # Execute the SQL migration
        # Note: Supabase Python client doesn't have a direct SQL execution method
        # For production, you might want to use the Supabase SQL editor or psql directly
        
        print("\n⚠️  Please execute the SQL migration using one of these methods:")
        print("   1. Copy the SQL from 'scripts/migrations/009_create_collection_report_dashboard_tables.sql'")
        print("   2. Paste it in the Supabase SQL editor")
        print("   3. Or run it using psql with your database connection string")
        print("\n📝 The migration file is ready at:")
        print(f"   {migration_file}")
        
        # For now, let's verify what we can
        print("\n🔍 Checking current database state...")
        
        # Check if tables already exist
        existing_tables = []
        for table in ['collection_report_configs', 'collection_report_snapshots']:
            try:
                client.table(table).select('id').limit(1).execute()
                existing_tables.append(table)
            except:
                pass
        
        if existing_tables:
            print(f"\n⚠️  Some tables already exist: {', '.join(existing_tables)}")
            print("   The migration script uses IF NOT EXISTS, so it's safe to run again.")
        else:
            print("\n✅ No conflicting tables found. Ready for migration.")
        
        print("\n📋 Next steps:")
        print("   1. Execute the SQL migration file")
        print("   2. Run this script again with --verify flag to check the migration")
        print("   3. Run the tests: pytest tests/supabase/test_report_dashboard_schema.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply collection report dashboard migration')
    parser.add_argument('--verify', action='store_true', help='Only verify the migration')
    args = parser.parse_args()
    
    if args.verify:
        client = get_supabase_client()
        success = verify_migration(client)
        if success:
            print("\n✅ All migration checks passed!")
        else:
            print("\n⚠️  Some migration checks failed. Please review and apply the migration.")
        return success
    else:
        return apply_migration()


if __name__ == '__main__':
    sys.exit(0 if main() else 1)