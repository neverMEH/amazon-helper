#!/usr/bin/env python3
"""Create test tokens for development"""

import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sample tokens (expired, for testing only)
sample_tokens = {
    "access_token": "Atza|IwEBIKnJV2Dt-example-access-token",
    "refresh_token": "Atzr|IwEBIH7Lkq0z-example-refresh-token",
    "token_type": "bearer",
    "expires_in": 3600
}

print("Creating test tokens.json file...")
print("=" * 50)
print("\nNOTE: These are sample tokens for testing.")
print("You'll need real tokens from Amazon OAuth flow for production use.")
print("\nTo get real tokens:")
print("1. Set up OAuth app in Amazon Advertising Console")
print("2. Run the OAuth flow to get authorization code")
print("3. Exchange code for tokens using scripts/exchange_token.py")
print("\nFor now, creating tokens.json with test data...")

with open('tokens.json', 'w') as f:
    json.dump(sample_tokens, f, indent=2)

print("\n✓ Created tokens.json")
print("\nNext steps:")
print("1. Replace with real tokens when available")
print("2. Run: python scripts/validate_tokens.py --store")