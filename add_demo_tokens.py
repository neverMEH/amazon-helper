#!/usr/bin/env python3
"""
Add demo Amazon OAuth tokens for testing
This is for development only - in production, users must go through proper OAuth flow
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amc_manager.services.token_service import token_service
from amc_manager.services.db_service import db_service
from amc_manager.services.token_refresh_service import token_refresh_service

async def add_demo_tokens(email: str = "nick@nevermeh.com"):
    """Add demo tokens for a user"""
    
    print(f"\n=== Adding Demo Tokens for {email} ===\n")
    
    # Get user
    user = await db_service.get_user_by_email(email)
    if not user:
        print(f"Error: User {email} not found")
        return
    
    user_id = user['id']
    print(f"Found user: {user_id}")
    
    # Create demo tokens (these are not real tokens, just for testing)
    # In production, these would come from Amazon OAuth
    demo_tokens = {
        'access_token': 'Atza|IwEBIDEMO_ACCESS_TOKEN_FOR_TESTING_ONLY_NOT_REAL',
        'refresh_token': 'Atzr|IwEBIDEMO_REFRESH_TOKEN_FOR_TESTING_ONLY_NOT_REAL',
        'token_type': 'bearer',
        'expires_in': 3600  # 1 hour
    }
    
    print("\nStoring demo tokens...")
    success = await token_service.store_user_tokens(user_id, demo_tokens)
    
    if success:
        print("✓ Demo tokens stored successfully")
        
        # Add user to token refresh tracking
        token_refresh_service.add_user(user_id)
        print("✓ Added user to token refresh tracking")
        
        # Verify tokens were stored correctly
        user = await db_service.get_user_by_id(user_id)
        if user and user.get('auth_tokens'):
            print("\nVerifying stored tokens:")
            auth_tokens = user['auth_tokens']
            print(f"  - Has access token: {'access_token' in auth_tokens}")
            print(f"  - Has refresh token: {'refresh_token' in auth_tokens}")
            print(f"  - Expires at: {auth_tokens.get('expires_at')}")
            
            # Test decryption
            try:
                decrypted = token_service.decrypt_token(auth_tokens['access_token'])
                print(f"  - Token decryption works: {decrypted.startswith('Atza|')}")
            except Exception as e:
                print(f"  - Token decryption failed: {e}")
        else:
            print("Error: Tokens not found after storing")
    else:
        print("Error: Failed to store demo tokens")
    
    print("\n=== Complete ===\n")
    print("NOTE: These are demo tokens for testing only.")
    print("For real AMC API access, you must authenticate through Amazon OAuth.")

if __name__ == "__main__":
    import sys
    email = sys.argv[1] if len(sys.argv) > 1 else "nick@nevermeh.com"
    asyncio.run(add_demo_tokens(email))