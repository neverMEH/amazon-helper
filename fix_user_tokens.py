#!/usr/bin/env python3
"""
Script to check and potentially fix user token issues
"""
import os
import sys
import json
from datetime import datetime

# Add the project to path
sys.path.insert(0, '/root/amazon-helper')

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.token_service import TokenService

def main():
    # Initialize Supabase client
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Check specific user
    user_id = 'fe841586-7807-48b1-8808-02877834fce0'
    
    print(f"Checking user {user_id}...")
    
    # Get user data
    result = client.table('users').select('*').eq('id', user_id).execute()
    
    if not result.data:
        print(f"User {user_id} not found")
        return
    
    user = result.data[0]
    print(f"User email: {user['email']}")
    
    # Check auth_tokens field
    auth_tokens = user.get('auth_tokens')
    
    if not auth_tokens:
        print("User has NO auth_tokens field at all")
        return
    
    # Parse if string
    if isinstance(auth_tokens, str):
        try:
            auth_tokens = json.loads(auth_tokens)
        except:
            print(f"Failed to parse auth_tokens JSON: {auth_tokens[:50]}...")
            return
    
    print(f"Auth tokens keys: {list(auth_tokens.keys())}")
    
    # Try to decrypt
    token_service = TokenService()
    
    if 'access_token' in auth_tokens:
        try:
            decrypted = token_service.decrypt_token(auth_tokens['access_token'])
            print(f"✓ Successfully decrypted access_token (length: {len(decrypted)})")
        except Exception as e:
            print(f"✗ Failed to decrypt access_token: {e}")
            print(f"  Encrypted token first 20 chars: {auth_tokens['access_token'][:20]}")
            
            # Clear the invalid tokens
            print("\nClearing invalid tokens...")
            update_result = client.table('users').update({
                'auth_tokens': None
            }).eq('id', user_id).execute()
            
            if update_result.data:
                print("✓ Cleared invalid tokens. User needs to re-authenticate.")
            else:
                print("✗ Failed to clear tokens")
    else:
        print("No access_token in auth_tokens")
    
    # Check for any schedules owned by this user
    schedules_result = client.table('workflow_schedules').select('id, name').eq('user_id', user_id).execute()
    if schedules_result.data:
        print(f"\nUser has {len(schedules_result.data)} schedules:")
        for schedule in schedules_result.data:
            print(f"  - {schedule['name']} (ID: {schedule['id']})")

if __name__ == '__main__':
    main()