#!/usr/bin/env python3
"""Script to exchange authorization code for access tokens"""

import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def exchange_code_for_token(auth_code):
    """Exchange authorization code for access and refresh tokens"""
    
    client_id = os.getenv('AMAZON_CLIENT_ID')
    client_secret = os.getenv('AMAZON_CLIENT_SECRET')
    redirect_uri = os.getenv('AMAZON_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing required credentials in .env file")
        return None
    
    # Amazon token endpoint
    token_url = 'https://api.amazon.com/auth/o2/token'
    
    # Prepare the request
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print("🔄 Exchanging authorization code for tokens...")
    
    try:
        response = requests.post(token_url, data=data, headers=headers)
        
        if response.status_code == 200:
            tokens = response.json()
            print("✅ Successfully obtained tokens!")
            
            # Save tokens to a file for testing
            with open('tokens.json', 'w') as f:
                json.dump(tokens, f, indent=2)
            
            print("\nTokens saved to tokens.json")
            print(f"Access Token: {tokens.get('access_token', '')[:50]}...")
            print(f"Refresh Token: {tokens.get('refresh_token', '')[:50]}...")
            print(f"Expires in: {tokens.get('expires_in')} seconds")
            
            return tokens
        else:
            print(f"❌ Failed to exchange code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        return None


def test_api_access(access_token):
    """Test API access with the obtained token"""
    
    print("\n🔄 Testing API access with token...")
    
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
            print(f"✅ Successfully retrieved {len(profiles)} profiles:")
            
            # Save profiles for reference
            with open('profiles.json', 'w') as f:
                json.dump(profiles, f, indent=2)
            
            print("\nProfiles saved to profiles.json")
            
            for i, profile in enumerate(profiles[:5]):  # Show first 5
                print(f"\nProfile {i+1}:")
                print(f"  Profile ID: {profile.get('profileId')}")
                print(f"  Country: {profile.get('countryCode')}")
                print(f"  Currency: {profile.get('currencyCode')}")
                print(f"  Type: {profile.get('accountInfo', {}).get('type')}")
                print(f"  Name: {profile.get('accountInfo', {}).get('name')}")
                
            return profiles
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to make API request: {e}")
        return None


if __name__ == "__main__":
    print("Amazon Advertising API Token Exchange")
    print("=====================================\n")
    
    # The authorization code you received
    auth_code = "ANTYQOzYKvyjIFlQFnYG"
    
    print(f"Using authorization code: {auth_code}")
    
    # Exchange code for tokens
    tokens = exchange_code_for_token(auth_code)
    
    if tokens and 'access_token' in tokens:
        # Test API access
        test_api_access(tokens['access_token'])
        
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Check tokens.json for your access and refresh tokens")
        print("2. Check profiles.json for your advertising profiles")
        print("3. Use the Profile ID(s) to make AMC API calls")
    else:
        print("\n❌ Failed to obtain tokens")
        print("\nPossible issues:")
        print("1. The authorization code may have expired (they're only valid for a short time)")
        print("2. The code may have already been used (they can only be used once)")
        print("3. Check that your redirect_uri matches exactly what's configured in Amazon")
        print("\nTry going through the OAuth flow again to get a fresh code")