#!/usr/bin/env python3
"""
Script to fix token encryption issues by clearing invalid tokens.

This script addresses the issue where tokens were encrypted with a different
FERNET_KEY and can no longer be decrypted. It clears the auth_tokens for
affected users, forcing them to re-authenticate.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.config.settings import settings
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def check_and_fix_tokens():
    """Check all users' tokens and clear invalid ones."""
    
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Get the current Fernet key
    fernet_key = settings.fernet_key
    if not fernet_key:
        logger.error("No FERNET_KEY found in environment!")
        logger.error("Please set FERNET_KEY in your .env file")
        return
    
    logger.info(f"Using FERNET_KEY: {fernet_key[:10]}...")
    
    try:
        fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)
    except Exception as e:
        logger.error(f"Invalid FERNET_KEY format: {e}")
        return
    
    # Get all users with auth_tokens
    response = client.table('users').select('id, email, auth_tokens').not_.is_('auth_tokens', 'null').execute()
    
    if not response.data:
        logger.info("No users with auth tokens found")
        return
    
    logger.info(f"Found {len(response.data)} users with auth tokens")
    
    invalid_count = 0
    valid_count = 0
    cleared_count = 0
    
    for user in response.data:
        user_id = user['id']
        email = user.get('email', 'Unknown')
        auth_tokens = user.get('auth_tokens')
        
        if not auth_tokens or not isinstance(auth_tokens, dict):
            logger.warning(f"User {email}: No valid auth_tokens structure")
            continue
        
        access_token = auth_tokens.get('access_token')
        if not access_token:
            logger.warning(f"User {email}: No access_token found")
            continue
        
        # Try to decrypt the token
        try:
            decrypted = fernet.decrypt(access_token.encode()).decode()
            if decrypted.startswith('Atza|'):
                logger.info(f"✓ User {email}: Token is valid and decryptable")
                valid_count += 1
            else:
                logger.warning(f"User {email}: Decrypted token doesn't look like Amazon token")
                invalid_count += 1
        except Exception as e:
            logger.error(f"✗ User {email}: Cannot decrypt token - {str(e)[:50]}")
            invalid_count += 1
            
            # Clear the invalid tokens
            try:
                clear_response = client.table('users').update({'auth_tokens': None}).eq('id', user_id).execute()
                if clear_response.data:
                    logger.info(f"  → Cleared invalid tokens for {email}")
                    cleared_count += 1
                else:
                    logger.error(f"  → Failed to clear tokens for {email}")
            except Exception as clear_error:
                logger.error(f"  → Error clearing tokens for {email}: {clear_error}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total users with tokens: {len(response.data)}")
    logger.info(f"Valid tokens: {valid_count}")
    logger.info(f"Invalid tokens: {invalid_count}")
    logger.info(f"Tokens cleared: {cleared_count}")
    
    if cleared_count > 0:
        logger.info("\n⚠️  Users with cleared tokens will need to re-authenticate")
        logger.info("They should go to their Profile page and click 'Re-authenticate with Amazon'")


if __name__ == "__main__":
    print("Token Encryption Fix Script")
    print("="*60)
    print("This script will check all users' tokens and clear any that")
    print("cannot be decrypted with the current FERNET_KEY.")
    print()
    
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted")
        sys.exit(0)
    
    check_and_fix_tokens()