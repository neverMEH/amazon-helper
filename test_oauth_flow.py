#!/usr/bin/env python3
"""Test the Amazon OAuth flow implementation"""

import asyncio
import os
from dotenv import load_dotenv

from amc_manager.services.token_service import token_service
from amc_manager.services.db_service import db_service
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

load_dotenv()

async def test_oauth_flow():
    """Test the OAuth flow components"""
    
    print("\n=== Testing Amazon OAuth Flow ===\n")
    
    # 1. Check OAuth configuration
    print("1. Checking OAuth configuration...")
    client_id = os.getenv('AMAZON_CLIENT_ID')
    client_secret = os.getenv('AMAZON_CLIENT_SECRET')
    redirect_uri = os.getenv('AMAZON_REDIRECT_URI', 'http://localhost:8001/api/auth/amazon/callback')
    
    if not client_id or not client_secret:
        print("❌ Missing AMAZON_CLIENT_ID or AMAZON_CLIENT_SECRET in environment")
        return
    
    print(f"✓ Client ID: {client_id[:10]}...")
    print(f"✓ Redirect URI: {redirect_uri}")
    
    # 2. Test token storage
    print("\n2. Testing token storage...")
    import uuid
    test_user_id = str(uuid.uuid4())
    
    # Create test user
    test_user = await db_service.create_user({
        "id": test_user_id,
        "email": f"test-{test_user_id[:8]}@example.com",
        "name": "Test User"
    })
    
    if test_user:
        print(f"✓ Created test user: {test_user['email']}")
    else:
        print("❌ Failed to create test user")
        return
    
    # 3. Store test tokens
    print("\n3. Testing token encryption and storage...")
    test_tokens = {
        "access_token": "test-access-token-12345",
        "refresh_token": "test-refresh-token-67890",
        "token_type": "bearer",
        "expires_in": 3600
    }
    
    success = await token_service.store_user_tokens(test_user_id, test_tokens)
    if success:
        print("✓ Tokens stored successfully")
    else:
        print("❌ Failed to store tokens")
        return
    
    # 4. Retrieve tokens
    print("\n4. Testing token retrieval...")
    retrieved_token = await token_service.get_valid_token(test_user_id)
    if retrieved_token:
        print(f"✓ Retrieved token: {retrieved_token[:20]}...")
    else:
        print("❌ Failed to retrieve token")
    
    # 5. Check user with tokens
    print("\n5. Checking user record...")
    user_with_tokens = await db_service.get_user_by_id(test_user_id)
    if user_with_tokens and user_with_tokens.get('auth_tokens'):
        print("✓ User has auth_tokens field")
        print(f"  - Token type: {user_with_tokens['auth_tokens'].get('token_type')}")
        print(f"  - Expires at: {user_with_tokens['auth_tokens'].get('expires_at')}")
    else:
        print("❌ User missing auth_tokens")
    
    # Cleanup
    print("\n6. Cleaning up...")
    try:
        client = db_service.client
        client.table('users').delete().eq('id', test_user_id).execute()
        print("✓ Test user deleted")
    except Exception as e:
        print(f"⚠️  Failed to delete test user: {e}")
    
    print("\n=== OAuth Flow Test Complete ===")
    
    print("\nNext steps:")
    print("1. Set up OAuth app in Amazon Advertising Console")
    print("2. Update AMAZON_CLIENT_ID and AMAZON_CLIENT_SECRET in .env")
    print("3. Start the backend server: python main_supabase.py")
    print("4. Navigate to: http://localhost:8001/api/auth/amazon/login")
    print("5. Complete the OAuth flow")
    print("6. Check that tokens are stored in the user record")

if __name__ == "__main__":
    asyncio.run(test_oauth_flow())