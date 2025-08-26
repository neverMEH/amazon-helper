#!/usr/bin/env python
"""Fetch account/advertiser IDs from Amazon API to use as entity_id"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.token_service import TokenService
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry
import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fetch_account_entity_ids():
    """Fetch account/advertiser IDs from Amazon API"""
    db = SupabaseManager().get_client()
    token_service = TokenService()
    
    # Get a user with valid tokens
    users = db.table('users').select('*').execute()
    
    for user in users.data:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        
        try:
            # Get valid access token
            access_token = await token_service.get_valid_token(user_id)
            if not access_token:
                print(f"No valid token for user {email}")
                continue
            
            print(f"\n=== User: {email} ===")
            
            # Get profiles using the existing method
            profiles = await token_service.get_user_profiles(access_token)
            
            if profiles:
                print(f"Found {len(profiles)} profiles:")
                for profile in profiles:
                    profile_id = profile.get('profileId')
                    account_id = profile.get('accountId')
                    marketplace = profile.get('countryCode')
                    account_type = profile.get('accountInfo', {}).get('type', 'Unknown')
                    account_name = profile.get('accountInfo', {}).get('name', 'Unknown')
                    
                    print(f"  Profile ID: {profile_id}")
                    print(f"  Account ID: {account_id}")
                    print(f"  Account Name: {account_name}")
                    print(f"  Marketplace: {marketplace}")
                    print(f"  Type: {account_type}")
                    
                    # The profileId is what we need as entity_id for AMC API calls
                    entity_id = str(profile_id)
                    print(f"  --> Entity ID for AMC: {entity_id}")
                    print()
                    
                    # Update AMC instances that belong to this account
                    # We'll need to match based on account name or other criteria
                    
            else:
                print("No profiles found for this user")
            
        except Exception as e:
            print(f"Error processing user {email}: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_account_entity_ids())