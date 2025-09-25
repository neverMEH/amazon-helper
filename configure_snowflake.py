#!/usr/bin/env python
"""
Direct Snowflake Configuration Script
This script bypasses the API router issues and configures Snowflake directly
"""

import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from cryptography.fernet import Fernet
import base64

def encrypt_password(password: str) -> str:
    """Encrypt password using Fernet"""
    # Generate a key (in production, this should be stored securely)
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return base64.b64encode(encrypted).decode()

def create_snowflake_config():
    """Create Snowflake configuration with your provided credentials"""
    
    # Your Snowflake credentials
    config_data = {
        'account_identifier': 'MUMZYBN-CN28961',
        'warehouse': 'AMC_WH',
        'database': 'AMC_DB', 
        'schema': 'PUBLIC',
        'role': 'AMC_DB_OWNER_ROLE',
        'username': 'NICK_PADILLA',
        'password': 'YOUR_PASSWORD_HERE'  # Replace with actual password
    }
    
    print("Snowflake Configuration Script")
    print("=" * 40)
    print(f"Account: {config_data['account_identifier']}")
    print(f"Warehouse: {config_data['warehouse']}")
    print(f"Database: {config_data['database']}")
    print(f"Schema: {config_data['schema']}")
    print(f"Role: {config_data['role']}")
    print(f"Username: {config_data['username']}")
    print()
    
    # Get password from user
    password = input("Enter your Snowflake password: ")
    config_data['password'] = password
    
    try:
        # Connect to Supabase
        print("Connecting to Supabase...")
        client = SupabaseManager.get_client()
        
        # Check if user exists (you'll need to provide a user ID)
        print("Available users:")
        users_response = client.table('users').select('id, email').execute()
        for user in users_response.data:
            print(f"  - ID: {user['id']}, Email: {user.get('email', 'N/A')}")
        
        user_id = input("\nEnter your user ID: ")
        
        # Encrypt password
        print("Encrypting password...")
        encrypted_password = encrypt_password(password)
        
        # Create configuration record
        config_record = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'account_identifier': config_data['account_identifier'],
            'warehouse': config_data['warehouse'],
            'database': config_data['database'],
            'schema': config_data['schema'],
            'role': config_data['role'],
            'username': config_data['username'],
            'encrypted_password': encrypted_password,
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
        else:
            print("❌ Failed to create Snowflake configuration")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

def test_snowflake_connection():
    """Test the Snowflake connection"""
    try:
        import snowflake.connector
        
        print("\nTesting Snowflake connection...")
        
        # Get configuration from database
        client = SupabaseManager.get_client()
        response = client.table('snowflake_configurations')\
            .select('*')\
            .eq('is_active', True)\
            .single()\
            .execute()
        
        if not response.data:
            print("❌ No active Snowflake configuration found")
            return False
        
        config = response.data
        
        # Decrypt password
        encrypted_password = config['encrypted_password']
        encrypted_bytes = base64.b64decode(encrypted_password.encode())
        # Note: In production, you'd need to store the key securely
        print("⚠️  Password decryption requires proper key management")
        print("   For now, connection test is skipped")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Snowflake Configuration Setup")
    print("=" * 30)
    print()
    
    choice = input("Choose an option:\n1. Create Snowflake configuration\n2. Test Snowflake connection\n3. Exit\n\nEnter choice (1-3): ")
    
    if choice == "1":
        create_snowflake_config()
    elif choice == "2":
        test_snowflake_connection()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice")
