#!/usr/bin/env python3
"""
Apply the reporting platform migration
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
    
    tables_to_check = [
        'dashboards',
        'dashboard_widgets', 
        'report_data_collections',
        'report_data_weeks',
        'report_data_aggregates',
        'ai_insights',
        'dashboard_shares'
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
    
    return all_exist

def apply_reporting_migration():
    """Apply the reporting platform migration"""
    try:
        # Read the migration SQL file
        migration_file = Path(__file__).parent / 'migrations' / '003_create_reporting_tables.sql'
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("🚀 Reports & Analytics Platform - Database Migration")
        print("=" * 50)
        print("📚 This migration will create 7 new tables:")
        print("   - dashboards (dashboard configurations)")
        print("   - dashboard_widgets (individual widgets)")
        print("   - report_data_collections (52-week backfill tracking)")
        print("   - report_data_weeks (individual week results)")
        print("   - report_data_aggregates (pre-computed metrics)")
        print("   - ai_insights (AI conversation history)")
        print("   - dashboard_shares (sharing permissions)")
        
        # Get Supabase client
        client = get_supabase_client()
        
        # Get Supabase URL for dashboard link
        supabase_url = os.getenv('SUPABASE_URL')
        sql_editor_url = supabase_url.replace('.supabase.co', '.supabase.com/project/').replace('https://', 'https://app.') + '/sql'
        
        # Check if tables already exist
        existing = verify_migration(client)
        
        if existing:
            print("\n✅ All tables already exist - migration appears to be complete!")
            return True
        
        print("\n" + "=" * 50)
        print("📝 To apply this migration:")
        print("\n1. Use Supabase SQL Editor (Recommended):")
        print(f"   - Open: {sql_editor_url}")
        print("   - Click 'New Query'")
        print(f"   - Copy contents from: {migration_file}")
        print("   - Click 'Run' to execute")
        
        print("\n2. Or use psql directly:")
        print("   psql $DATABASE_URL < scripts/migrations/003_create_reporting_tables.sql")
        
        print("\n3. Then run this script again to verify:")
        print("   python3 scripts/apply_reporting_migration.py")
        
        print("\n📄 Migration file location:")
        print(f"   {migration_file.absolute()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = apply_reporting_migration()
    sys.exit(0 if success else 1)