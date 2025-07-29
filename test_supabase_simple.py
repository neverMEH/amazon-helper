#!/usr/bin/env python3
"""Simple Supabase connection test"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("Testing Supabase connection...")
print(f"URL: {SUPABASE_URL}")

try:
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✓ Successfully created Supabase client")
    
    # Test database connection
    print("\nTesting database access...")
    
    # Check tables
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
            response = supabase.table(table).select('count', count='exact').limit(1).execute()
            print(f"✓ Table '{table}' exists and is accessible")
        except Exception as e:
            print(f"✗ Table '{table}' error: {str(e)}")
    
    print("\n✅ Supabase connection test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Supabase connection test failed!")
    print(f"Error: {str(e)}")