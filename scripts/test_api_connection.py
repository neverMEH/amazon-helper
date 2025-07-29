#!/usr/bin/env python3
"""Test script to verify Amazon Advertising API credentials and connection"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.auth import AmazonAuthManager
from amc_manager.core.api_client import AMCAPIClient


def test_credentials():
    """Test if credentials are properly configured"""
    print("Testing Amazon Advertising API Credentials...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'AMAZON_CLIENT_ID',
        'AMAZON_CLIENT_SECRET',
        'AMAZON_REDIRECT_URI',
        'AMAZON_SCOPE'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive values
            if 'SECRET' in var:
                display_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n✗ Missing required variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file")
        return False
    
    print("\n✓ All required credentials are configured")
    return True


def test_oauth_url():
    """Test OAuth URL generation"""
    print("\nTesting OAuth URL Generation...")
    print("=" * 50)
    
    try:
        auth_manager = AmazonAuthManager()
        auth_url, state = auth_manager.get_authorization_url()
        
        print(f"✓ Authorization URL generated successfully")
        print(f"  URL: {auth_url[:100]}...")
        print(f"  State: {state}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to generate authorization URL: {e}")
        return False


def test_profile_access(access_token: str):
    """Test API access with a token (if available)"""
    print("\nTesting API Access...")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json'
    }
    
    # Test getting profiles
    url = 'https://advertising-api.amazon.com/v2/profiles'
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            profiles = response.json()
            print(f"✓ Successfully retrieved {len(profiles)} profiles:")
            
            for profile in profiles[:5]:  # Show first 5 profiles
                print(f"  - Profile ID: {profile.get('profileId')}")
                print(f"    Country: {profile.get('countryCode')}")
                print(f"    Currency: {profile.get('currencyCode')}")
                print(f"    Type: {profile.get('accountInfo', {}).get('type')}")
                print()
                
            return True
        else:
            print(f"✗ API request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to make API request: {e}")
        return False


def main():
    """Run all tests"""
    print("Amazon Advertising API Connection Test")
    print("=====================================\n")
    
    # Test 1: Check credentials
    if not test_credentials():
        print("\n⚠️  Please configure your credentials first")
        return
    
    # Test 2: Generate OAuth URL
    if not test_oauth_url():
        print("\n⚠️  Failed to initialize OAuth")
        return
    
    print("\n" + "=" * 50)
    print("Basic configuration tests passed!")
    print("\nNext steps:")
    print("1. Start the application: python main.py")
    print("2. Navigate to: http://localhost:8000/api/auth/login")
    print("3. Complete the OAuth flow to get access tokens")
    print("4. The application will then have full API access")
    
    # Optional: Test with existing token
    existing_token = os.getenv('TEST_ACCESS_TOKEN')
    if existing_token:
        print("\n" + "=" * 50)
        print("Found TEST_ACCESS_TOKEN, testing API access...")
        test_profile_access(existing_token)


if __name__ == "__main__":
    main()