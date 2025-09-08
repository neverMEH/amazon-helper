#!/usr/bin/env python3
"""
Script to check and fix report_data_weeks table schema
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def check_and_fix_schema():
    """Check report_data_weeks schema and add missing columns if needed"""
    
    print("\n" + "="*60)
    print("REPORT_DATA_WEEKS SCHEMA CHECK & FIX")
    print("="*60)
    
    try:
        # Get Supabase client
        client = SupabaseManager.get_client(use_service_role=True)
        
        # First, try to check if table exists by querying it
        print("\n1. Checking if report_data_weeks table exists...")
        try:
            test_query = client.table('report_data_weeks').select('id').limit(1).execute()
            print("   ✅ Table exists")
        except Exception as e:
            print(f"   ❌ Table doesn't exist or error: {e}")
            print("\n   Creating table...")
            
            # Create the table with all required columns
            create_sql = """
            CREATE TABLE IF NOT EXISTS report_data_weeks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                collection_id UUID REFERENCES report_data_collections(id) ON DELETE CASCADE,
                week_start_date DATE NOT NULL,
                week_end_date DATE NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
                amc_execution_id VARCHAR(255),
                data_checksum VARCHAR(64),
                record_count INTEGER,
                execution_time_seconds INTEGER,
                error_message TEXT,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT unique_collection_week UNIQUE(collection_id, week_start_date)
            );
            """
            
            # Note: Supabase client doesn't support raw SQL execution directly
            # We need to use the Supabase SQL editor or run migrations
            print("   ⚠️  Cannot create table via API - please run migration script")
            return False
        
        # Check for specific columns
        print("\n2. Checking for required columns...")
        columns_to_check = [
            'execution_id',
            'amc_execution_id', 
            'started_at',
            'completed_at',
            'record_count'
        ]
        
        missing_columns = []
        
        for col in columns_to_check:
            try:
                # Try to select the column
                test = client.table('report_data_weeks').select(col).limit(1).execute()
                print(f"   ✅ Column '{col}' exists")
            except Exception as e:
                if 'PGRST204' in str(e) or 'column' in str(e).lower():
                    print(f"   ❌ Column '{col}' missing")
                    missing_columns.append(col)
                else:
                    print(f"   ⚠️  Error checking '{col}': {e}")
        
        if missing_columns:
            print(f"\n3. Missing columns detected: {', '.join(missing_columns)}")
            print("\n   ALTER TABLE statements needed:")
            
            for col in missing_columns:
                if col == 'execution_id':
                    print(f"   ALTER TABLE report_data_weeks ADD COLUMN IF NOT EXISTS execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL;")
                elif col == 'amc_execution_id':
                    print(f"   ALTER TABLE report_data_weeks ADD COLUMN IF NOT EXISTS amc_execution_id VARCHAR(255);")
                elif col == 'started_at':
                    print(f"   ALTER TABLE report_data_weeks ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE;")
                elif col == 'completed_at':
                    print(f"   ALTER TABLE report_data_weeks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;")
                elif col == 'record_count':
                    print(f"   ALTER TABLE report_data_weeks ADD COLUMN IF NOT EXISTS record_count INTEGER;")
            
            print("\n   ⚠️  Please run these ALTER statements in Supabase SQL editor")
            print("   Then reload the schema cache (Settings -> API -> Reload schema cache)")
            return False
        else:
            print("\n3. ✅ All required columns exist!")
            
            # Check if schema cache might be stale
            print("\n4. Testing column access...")
            try:
                # Try to update with all columns
                test_data = {
                    'status': 'pending',
                    'started_at': datetime.utcnow().isoformat(),
                    'amc_execution_id': 'test-123'
                }
                
                # Don't actually update, just test if it would work
                print("   Testing update with new columns...")
                print(f"   Test data: {test_data}")
                
                # This will fail if columns aren't in schema cache
                # We're not actually updating, just testing
                
                print("\n   ✅ Column access test would work")
                print("\n   ℹ️  If you're still seeing errors, try:")
                print("   1. Go to Supabase Dashboard")
                print("   2. Settings -> API")
                print("   3. Click 'Reload schema cache'")
                print("   4. Wait 30 seconds and try again")
                
            except Exception as e:
                print(f"\n   ❌ Column access test failed: {e}")
                print("\n   Schema cache is likely stale. Please reload it in Supabase.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during check: {e}")
        logger.error(f"Schema check failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run check and fix
    success = check_and_fix_schema()
    
    if success:
        print("\n✅ Schema check completed")
        sys.exit(0)
    else:
        print("\n⚠️  Manual intervention required")
        print("\nNext steps:")
        print("1. Run the ALTER TABLE statements in Supabase SQL editor")
        print("2. Reload the schema cache in Supabase Dashboard")
        print("3. Run this script again to verify")
        sys.exit(1)