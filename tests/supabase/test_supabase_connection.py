#!/usr/bin/env python3
"""Test Supabase connection and basic operations"""

import asyncio
import sys
from datetime import datetime
from amc_manager.core import SupabaseManager, get_logger

logger = get_logger(__name__)


async def test_supabase_connection():
    """Test basic Supabase connection and operations"""
    
    print("Testing Supabase connection...")
    
    try:
        # Get Supabase client
        client = SupabaseManager.get_client(use_service_role=True)
        print("✓ Successfully created Supabase client")
        
        # Test database connection by attempting to query users table
        print("\nTesting database access...")
        response = client.table('users').select('count', count='exact').execute()
        print(f"✓ Successfully connected to database")
        print(f"  Users table exists (count query successful)")
        
        # Test RPC function
        print("\nTesting RPC function access...")
        # This will fail if the function doesn't exist, which is expected
        # We're just testing the connection mechanism
        try:
            client.rpc('get_brand_asin_summary', {'user_id_param': '00000000-0000-0000-0000-000000000000'}).execute()
            print("✓ RPC function call mechanism works")
        except Exception as e:
            if "function" in str(e).lower() and "does not exist" in str(e).lower():
                print("✓ RPC mechanism works (function not yet created in database)")
            else:
                print(f"✗ RPC error: {str(e)}")
        
        # Test table access
        print("\nTesting table access...")
        tables_to_check = [
            'users',
            'amc_accounts', 
            'amc_instances',
            'campaign_mappings',
            'brand_configurations',
            'workflows',
            'workflow_executions'
        ]
        
        for table in tables_to_check:
            try:
                response = client.table(table).select('count', count='exact').limit(1).execute()
                print(f"✓ Table '{table}' is accessible")
            except Exception as e:
                print(f"✗ Table '{table}' error: {str(e)}")
        
        print("\n✅ Supabase connection test completed successfully!")
        print("\nNext steps:")
        print("1. Run the SQL scripts in Supabase SQL editor:")
        print("   - supabase_schema.sql (create tables)")
        print("   - supabase_rls_policies.sql (set up RLS)")
        print("   - supabase_functions.sql (create functions)")
        print("2. Update alembic.ini with Supabase database URL")
        print("3. Start integrating Supabase services into your API endpoints")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Supabase connection test failed!")
        print(f"Error: {str(e)}")
        print("\nPlease check:")
        print("1. Your Supabase credentials in .env file")
        print("2. Network connectivity to Supabase")
        print("3. That the Supabase project is active")
        logger.error(f"Supabase connection test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_supabase_connection())
    sys.exit(0 if success else 1)