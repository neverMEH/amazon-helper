#!/usr/bin/env python3
"""Validate and manage Amazon OAuth tokens"""

import os
import sys
import json
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.services.token_service import token_service
from amc_manager.services.db_service import db_service
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


async def validate_tokens_from_file(token_file: str = "tokens.json"):
    """Validate tokens from a JSON file"""
    print(f"\nValidating tokens from {token_file}")
    print("=" * 50)
    
    # Check if file exists
    if not os.path.exists(token_file):
        print(f"✗ Token file not found: {token_file}")
        print("\nTo create a token file:")
        print("1. Run the OAuth flow to get tokens")
        print("2. Save them to tokens.json in this format:")
        print(json.dumps({
            "access_token": "Atza|...",
            "refresh_token": "Atzr|...",
            "token_type": "bearer",
            "expires_in": 3600
        }, indent=2))
        return None
    
    # Load tokens
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing token file: {e}")
        return None
    
    # Extract tokens
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    
    if not access_token:
        print("✗ No access token found in file")
        return None
    
    print(f"✓ Found access token: {access_token[:20]}...")
    if refresh_token:
        print(f"✓ Found refresh token: {refresh_token[:20]}...")
    
    # Validate access token
    print("\nValidating access token...")
    is_valid, error = await token_service.validate_token(access_token)
    
    if is_valid:
        print("✓ Access token is valid!")
        
        # Get profiles
        print("\nFetching advertising profiles...")
        profiles = await token_service.get_user_profiles(access_token)
        
        if profiles:
            print(f"✓ Found {len(profiles)} profiles:")
            for profile in profiles[:5]:  # Show first 5
                print(f"  - {profile.get('profileId')}: {profile.get('accountInfo', {}).get('name')} ({profile.get('countryCode')})")
        
        return token_data
    else:
        print(f"✗ Access token is invalid: {error}")
        
        if refresh_token and "expired" in error.lower():
            print("\nAttempting to refresh token...")
            new_tokens = await token_service.refresh_access_token(refresh_token)
            
            if new_tokens:
                print("✓ Successfully refreshed token!")
                
                # Save new tokens
                with open(token_file, 'w') as f:
                    json.dump(new_tokens, f, indent=2)
                print(f"✓ Updated tokens saved to {token_file}")
                
                return new_tokens
            else:
                print("✗ Failed to refresh token")
                print("\nYou need to re-authenticate:")
                print("1. Run the OAuth flow again")
                print("2. Update tokens.json with new tokens")
        
        return None


async def store_tokens_for_user(email: str = "nick@nevermeh.com"):
    """Store tokens in database for a user"""
    print(f"\nStoring tokens for user: {email}")
    print("=" * 50)
    
    # Get user
    user = await db_service.get_user_by_email(email)
    if not user:
        print(f"✗ User not found: {email}")
        return
    
    print(f"✓ Found user: {user['name']} (ID: {user['id']})")
    
    # Validate tokens first
    token_data = await validate_tokens_from_file()
    if not token_data:
        print("✗ No valid tokens to store")
        return
    
    # Store tokens
    print("\nStoring encrypted tokens in database...")
    success = await token_service.store_user_tokens(user['id'], token_data)
    
    if success:
        print("✓ Tokens stored successfully!")
        
        # Test retrieval
        print("\nTesting token retrieval...")
        retrieved_token = await token_service.get_valid_token(user['id'])
        
        if retrieved_token:
            print("✓ Successfully retrieved valid token from database")
            print(f"  Token: {retrieved_token[:20]}...")
        else:
            print("✗ Failed to retrieve token")
    else:
        print("✗ Failed to store tokens")


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and manage Amazon OAuth tokens")
    parser.add_argument('--file', default='tokens.json', help='Token file path')
    parser.add_argument('--store', action='store_true', help='Store tokens in database')
    parser.add_argument('--email', default='nick@nevermeh.com', help='User email for storing tokens')
    
    args = parser.parse_args()
    
    print("Amazon OAuth Token Validator")
    print("=" * 50)
    
    # Validate tokens
    token_data = await validate_tokens_from_file(args.file)
    
    # Store in database if requested
    if args.store and token_data:
        await store_tokens_for_user(args.email)
    
    print("\n✅ Token validation completed!")


if __name__ == "__main__":
    asyncio.run(main())