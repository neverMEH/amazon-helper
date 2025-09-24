#!/usr/bin/env python
"""
Simple Snowflake Configuration Insert
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from amc_manager.core.supabase_client import SupabaseManager
    import uuid
    
    print("Setting up Snowflake configuration...")
    
    # Connect to Supabase
    client = SupabaseManager.get_client()
    
    # Get first user
    users = client.table('users').select('id').execute()
    if not users.data:
        print("No users found!")
        exit(1)
    
    user_id = users.data[0]['id']
    print(f"Using user ID: {user_id}")
    
    # Create Snowflake configuration
    config = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'account_identifier': 'MUMZYBN-CN28961',
        'warehouse': 'AMC_WH',
        'database': 'AMC_DB',
        'schema': 'PUBLIC',
        'role': 'AMC_DB_OWNER_ROLE',
        'username': 'NICK_PADILLA',
        'encrypted_password': '6O[B%Vke@>6xB8IYcBCG',
        'is_active': True
    }
    
    # Insert configuration
    result = client.table('snowflake_configurations').insert(config).execute()
    
    if result.data:
        print("✅ Snowflake configuration created!")
        print(f"ID: {result.data[0]['id']}")
    else:
        print("❌ Failed to create configuration")
        
except Exception as e:
    print(f"Error: {e}")
