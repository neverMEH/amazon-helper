#!/usr/bin/env python3
"""Simple test for Supabase connection"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Get credentials
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"Supabase URL: {url}")
print(f"Key present: {'Yes' if key else 'No'}")

try:
    # Create client
    supabase = create_client(url, key)
    print("✓ Successfully created Supabase client")
    
    # Try a simple query
    response = supabase.table('users').select('*').limit(1).execute()
    print("✓ Successfully queried database")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()