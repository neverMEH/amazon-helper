#!/usr/bin/env python
"""
Direct Snowflake Configuration Fix
This script directly updates the database without needing the API server
"""

import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def fix_snowflake_configuration():
    """Fix Snowflake configuration directly in the database"""
    
    print("Direct Snowflake Configuration Fix")
    print("=" * 40)
    
    # Your Snowflake credentials from the config file
    snowflake_config = {
        'account_identifier': 'MUMZYBN-CN28961',
        'warehouse': 'AMC_WH',
        'database': 'AMC_DB',
        'schema': 'PUBLIC',
        'role': 'AMC_DB_OWNER_ROLE',
        'username': 'NICK_PADILLA',
        'password': '6O[B%Vke@>6xB8IYcBCG'
    }
    
    print("Updating Snowflake configuration with:")
    for key, value in snowflake_config.items():
        if key != 'password':
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {'*' * len(value)}")
    print()
    
    try:
        from amc_manager.core.supabase_client import SupabaseManager
        
        print("Connecting to Supabase...")
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Check existing configurations
        print("Checking existing Snowflake configurations...")
        response = client.table('snowflake_configurations').select('*').execute()
        
        if response.data:
            print(f"Found {len(response.data)} existing configuration(s)")
            
            # Find active configuration
            active_config = None
            for config in response.data:
                if config.get('is_active'):
                    active_config = config
                    break
            
            if active_config:
                print(f"Updating active configuration: {active_config['id']}")
                
                # Update the configuration
                update_data = {
                    'account_identifier': snowflake_config['account_identifier'],
                    'warehouse': snowflake_config['warehouse'],
                    'database': snowflake_config['database'],
                    'schema': snowflake_config['schema'],
                    'role': snowflake_config['role'],
                    'username': snowflake_config['username'],
                    'password_encrypted': snowflake_config['password'],  # Store as plain text for now
                    'is_active': True
                }
                
                update_response = client.table('snowflake_configurations')\
                    .update(update_data)\
                    .eq('id', active_config['id'])\
                    .execute()
                
                if update_response.data:
                    print("✅ Snowflake configuration updated successfully!")
                else:
                    print("❌ Failed to update Snowflake configuration")
            else:
                print("No active configuration found, creating new one...")
                
                # Get first user ID (you might need to adjust this)
                users_response = client.table('users').select('id').limit(1).execute()
                if users_response.data:
                    user_id = users_response.data[0]['id']
                    
                    config_record = {
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'account_identifier': snowflake_config['account_identifier'],
                        'warehouse': snowflake_config['warehouse'],
                        'database': snowflake_config['database'],
                        'schema': snowflake_config['schema'],
                        'role': snowflake_config['role'],
                        'username': snowflake_config['username'],
                        'password_encrypted': snowflake_config['password'],
                        'is_active': True
                    }
                    
                    create_response = client.table('snowflake_configurations').insert(config_record).execute()
                    
                    if create_response.data:
                        print("✅ Snowflake configuration created successfully!")
                    else:
                        print("❌ Failed to create Snowflake configuration")
                else:
                    print("❌ No users found in database")
        else:
            print("No existing configurations found, creating new one...")
            
            # Get first user ID
            users_response = client.table('users').select('id').limit(1).execute()
            if users_response.data:
                user_id = users_response.data[0]['id']
                
                config_record = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'account_identifier': snowflake_config['account_identifier'],
                    'warehouse': snowflake_config['warehouse'],
                    'database': snowflake_config['database'],
                    'schema': snowflake_config['schema'],
                    'role': snowflake_config['role'],
                    'username': snowflake_config['username'],
                    'password_encrypted': snowflake_config['password'],
                    'is_active': True
                }
                
                create_response = client.table('snowflake_configurations').insert(config_record).execute()
                
                if create_response.data:
                    print("✅ Snowflake configuration created successfully!")
                else:
                    print("❌ Failed to create Snowflake configuration")
            else:
                print("❌ No users found in database")
        
        # Check the specific execution
        print("\nChecking execution Snowflake status...")
        execution_id = "3ee03ec3-419b-4e98-9c52-6bc8b9018e0f"
        
        exec_response = client.table('workflow_executions')\
            .select('*')\
            .eq('execution_id', execution_id)\
            .execute()
        
        if exec_response.data:
            execution = exec_response.data[0]
            print(f"Execution {execution_id}:")
            print(f"  Snowflake enabled: {execution.get('snowflake_enabled')}")
            print(f"  Snowflake status: {execution.get('snowflake_status')}")
            print(f"  Snowflake table: {execution.get('snowflake_table_name')}")
            print(f"  Snowflake schema: {execution.get('snowflake_schema_name')}")
            print(f"  Snowflake error: {execution.get('snowflake_error_message')}")
            print(f"  Snowflake row count: {execution.get('snowflake_row_count')}")
            
            if execution.get('snowflake_enabled') and execution.get('snowflake_status') == 'failed':
                print("\n⚠️  This execution had Snowflake enabled but failed!")
                print("The failure was likely due to the incorrect credentials we just fixed.")
                print("You can now:")
                print("1. Rerun this execution to test the fixed credentials")
                print("2. Create a new execution with Snowflake enabled")
        else:
            print(f"❌ Execution {execution_id} not found")
        
        print("\n" + "=" * 40)
        print("SNOWFLAKE CONFIGURATION FIX COMPLETE")
        print("=" * 40)
        print("Next steps:")
        print("1. Start the API server: ./start_services.sh")
        print("2. Test Snowflake connection in the application")
        print("3. Create a new report with Snowflake enabled")
        print("4. Check execution details for Snowflake status")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_snowflake_configuration()
