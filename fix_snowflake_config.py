#!/usr/bin/env python
"""
Check Snowflake configuration and fix execution issues
"""

import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def check_execution_snowflake_status():
    """Check if the specific execution had Snowflake enabled"""
    
    print("Checking execution Snowflake status...")
    print("=" * 40)
    
    try:
        from amc_manager.core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Check the specific execution
        execution_id = "3ee03ec3-419b-4e98-9c52-6bc8b9018e0f"
        
        response = client.table('workflow_executions')\
            .select('*')\
            .eq('execution_id', execution_id)\
            .execute()
        
        if response.data:
            execution = response.data[0]
            print(f"Found execution: {execution_id}")
            print(f"Snowflake enabled: {execution.get('snowflake_enabled')}")
            print(f"Snowflake status: {execution.get('snowflake_status')}")
            print(f"Snowflake table: {execution.get('snowflake_table_name')}")
            print(f"Snowflake schema: {execution.get('snowflake_schema_name')}")
            print(f"Snowflake error: {execution.get('snowflake_error_message')}")
            print(f"Snowflake row count: {execution.get('snowflake_row_count')}")
            print(f"Snowflake uploaded at: {execution.get('snowflake_uploaded_at')}")
            
            return execution
        else:
            print(f"❌ Execution {execution_id} not found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking execution: {e}")
        return None

def check_snowflake_configurations():
    """Check all Snowflake configurations"""
    
    print("\nChecking Snowflake configurations...")
    print("=" * 40)
    
    try:
        from amc_manager.core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client(use_service_role=True)
        
        response = client.table('snowflake_configurations').select('*').execute()
        
        print(f"Found {len(response.data)} Snowflake configurations:")
        
        for i, config in enumerate(response.data):
            print(f"\nConfiguration {i+1}:")
            print(f"  ID: {config.get('id')}")
            print(f"  User: {config.get('user_id')}")
            print(f"  Active: {config.get('is_active')}")
            print(f"  Account: {config.get('account_identifier')}")
            print(f"  Warehouse: {config.get('warehouse')}")
            print(f"  Database: {config.get('database')}")
            print(f"  Schema: {config.get('schema')}")
            print(f"  Username: {config.get('username')}")
            print(f"  Role: {config.get('role')}")
            print(f"  Has Password: {'Yes' if config.get('password_encrypted') else 'No'}")
            print(f"  Has Private Key: {'Yes' if config.get('private_key_encrypted') else 'No'}")
        
        return response.data
        
    except Exception as e:
        print(f"❌ Error checking configurations: {e}")
        return []

def update_snowflake_config_with_new_credentials():
    """Update Snowflake configuration with the provided credentials"""
    
    print("\nUpdating Snowflake configuration...")
    print("=" * 40)
    
    # Your Snowflake credentials from the config file
    new_config = {
        'account': 'MUMZYBN-CN28961',
        'user': 'NICK_PADILLA',
        'password': '6O[B%Vke@>6xB8IYcBCG',
        'role': 'AMC_DB_OWNER_ROLE',
        'warehouse': 'AMC_WH',
        'database': 'AMC_DB',
        'schema': 'PUBLIC'
    }
    
    try:
        from amc_manager.core.supabase_client import SupabaseManager
        
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get all configurations
        configs = client.table('snowflake_configurations').select('*').execute().data
        
        if not configs:
            print("❌ No Snowflake configurations found!")
            print("You need to create a Snowflake configuration first.")
            return False
        
        # Find the active configuration to update
        active_config = None
        for config in configs:
            if config.get('is_active'):
                active_config = config
                break
        
        if not active_config:
            print("❌ No active Snowflake configuration found!")
            return False
        
        print(f"Updating configuration: {active_config['id']}")
        
        # Update the configuration with new credentials
        update_data = {
            'account_identifier': new_config['account'],
            'warehouse': new_config['warehouse'],
            'database': new_config['database'],
            'schema': new_config['schema'],
            'role': new_config['role'],
            'username': new_config['user'],
            'password_encrypted': new_config['password'],  # Store as plain text for now
            'is_active': True
        }
        
        response = client.table('snowflake_configurations')\
            .update(update_data)\
            .eq('id', active_config['id'])\
            .execute()
        
        if response.data:
            print("✅ Snowflake configuration updated successfully!")
            print("New credentials:")
            print(f"  Account: {new_config['account']}")
            print(f"  Warehouse: {new_config['warehouse']}")
            print(f"  Database: {new_config['database']}")
            print(f"  Schema: {new_config['schema']}")
            print(f"  Username: {new_config['user']}")
            print(f"  Role: {new_config['role']}")
            return True
        else:
            print("❌ Failed to update Snowflake configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False

def test_snowflake_connection():
    """Test the Snowflake connection"""
    
    print("\nTesting Snowflake connection...")
    print("=" * 40)
    
    try:
        from amc_manager.services.snowflake_service import SnowflakeService
        
        snowflake_service = SnowflakeService()
        
        # Get the updated configuration
        configs = snowflake_service.get_user_snowflake_config("dummy_user_id")  # We'll get the first active one
        
        if not configs:
            print("❌ No Snowflake configuration found!")
            return False
        
        # Test connection
        result = snowflake_service.test_connection(configs)
        
        if result.get('success'):
            print("✅ Snowflake connection test successful!")
            print(f"Connection details: {result.get('details', 'N/A')}")
            return True
        else:
            print(f"❌ Snowflake connection test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

if __name__ == "__main__":
    print("SNOWFLAKE CONFIGURATION DIAGNOSTIC")
    print("=" * 50)
    
    # Check the specific execution
    execution = check_execution_snowflake_status()
    
    # Check current configurations
    configs = check_snowflake_configurations()
    
    # Update configuration with new credentials
    if configs:
        success = update_snowflake_config_with_new_credentials()
        if success:
            # Test the connection
            test_snowflake_connection()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 50)
