#!/usr/bin/env python
"""
Direct Snowflake Configuration Script
"""

import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def create_snowflake_config():
    """Create Snowflake configuration with your provided credentials"""
    
    print("Snowflake Configuration Setup")
    print("=" * 30)
    print()
    print("Your Snowflake credentials:")
    print("Account: MUMZYBN-CN28961")
    print("Warehouse: AMC_WH")
    print("Database: AMC_DB")
    print("Schema: PUBLIC")
    print("Role: AMC_DB_OWNER_ROLE")
    print("Username: NICK_PADILLA")
    print("Password: A&JLove12182124!")
    print()
    
    try:
        # Import Supabase client
        from amc_manager.core.supabase_client import SupabaseManager
        
        print("Connecting to Supabase...")
        client = SupabaseManager.get_client()
        
        # Check if user exists
        print("Available users:")
        users_response = client.table('users').select('id, email').execute()
        for user in users_response.data:
            print(f"  - ID: {user['id']}, Email: {user.get('email', 'N/A')}")
        
        if not users_response.data:
            print("❌ No users found in the database")
            return False
        
        # Use the first user for now (you can change this)
        user_id = users_response.data[0]['id']
        print(f"\nUsing user ID: {user_id}")
        
        # Create configuration record
        config_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'account_identifier': 'MUMZYBN-CN28961',
            'warehouse': 'AMC_WH',
            'database': 'AMC_DB',
            'schema': 'PUBLIC',
            'role': 'AMC_DB_OWNER_ROLE',
            'username': 'NICK_PADILLA',
            'encrypted_password': 'A&JLove12182124!',  # Store as plain text for now
            'is_active': True
        }
        
        print("Creating Snowflake configuration...")
        
        # Insert into database
        response = client.table('snowflake_configurations').insert(config_record).execute()
        
        if response.data:
            print("✅ Snowflake configuration created successfully!")
            print(f"Configuration ID: {response.data[0]['id']}")
            print()
            print("You can now use Snowflake integration in the Report Builder!")
            print("When creating reports, you'll see a 'Data Storage Options' section")
            print("where you can enable Snowflake storage.")
            return True
        else:
            print("❌ Failed to create Snowflake configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_snowflake_config()
    if success:
        print("\n🎉 Snowflake configuration complete!")
    else:
        print("\n❌ Configuration failed. Please check the error messages above.")
