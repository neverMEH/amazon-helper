#!/usr/bin/env python3
"""Test Amazon OAuth authentication flow with existing tokens"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Amazon API configuration
CLIENT_ID = os.getenv('AMAZON_CLIENT_ID')
BASE_URL = "https://advertising-api.amazon.com"

def load_tokens():
    """Load tokens from tokens.json"""
    print("Loading tokens...")
    with open('tokens.json', 'r') as f:
        return json.load(f)

def test_token_validity(access_token):
    """Test if access token is still valid"""
    print("\nTesting token validity...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': CLIENT_ID,
        'Content-Type': 'application/json'
    }
    
    # Test with profiles endpoint
    url = f"{BASE_URL}/v2/profiles"
    response = requests.get(url, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Token is valid!")
        profiles = response.json()
        print(f"✓ Found {len(profiles)} profiles")
        return True
    elif response.status_code == 401:
        print("✗ Token is expired or invalid")
        return False
    else:
        print(f"✗ Unexpected response: {response.text}")
        return False

def refresh_token(refresh_token):
    """Refresh the access token"""
    print("\nRefreshing access token...")
    
    CLIENT_SECRET = os.getenv('AMAZON_CLIENT_SECRET')
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post('https://api.amazon.com/auth/o2/token', data=data)
    
    if response.status_code == 200:
        print("✓ Token refreshed successfully!")
        new_tokens = response.json()
        
        # Save new tokens
        with open('tokens.json', 'w') as f:
            json.dump(new_tokens, f, indent=2)
        
        return new_tokens['access_token']
    else:
        print(f"✗ Failed to refresh token: {response.text}")
        return None

def test_amc_instance_access(access_token):
    """Test accessing AMC instances"""
    print("\nTesting AMC instance access...")
    
    # Load AMC accounts
    with open('amc_accounts.json', 'r') as f:
        accounts = json.load(f)
    
    for account in accounts['amcAccounts']:
        print(f"\nTesting account: {account['accountName']}")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': CLIENT_ID,
            'Amazon-Advertising-API-MarketplaceId': account['marketplaceId'],
            'Amazon-Advertising-API-AdvertiserId': account['accountId'],  # Critical header!
            'Content-Type': 'application/json'
        }
        
        url = f"{BASE_URL}/amc/reporting/instances"
        response = requests.get(url, headers=headers)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            instance_count = len(data.get('instances', []))
            print(f"  ✓ Successfully accessed AMC instances")
            print(f"  ✓ Found {instance_count} instances")
        else:
            print(f"  ✗ Failed to access instances: {response.text}")

def main():
    """Main test function"""
    print("Testing Amazon OAuth Authentication Flow")
    print("=" * 50)
    
    # Load tokens
    tokens = load_tokens()
    access_token = tokens.get('access_token')
    refresh_token_value = tokens.get('refresh_token')
    
    if not access_token:
        print("✗ No access token found!")
        return
    
    # Test token validity
    if not test_token_validity(access_token):
        # Try to refresh
        if refresh_token_value:
            new_token = refresh_token(refresh_token_value)
            if new_token:
                access_token = new_token
            else:
                print("✗ Failed to refresh token. Manual re-authentication required.")
                return
        else:
            print("✗ No refresh token available.")
            return
    
    # Test AMC instance access
    test_amc_instance_access(access_token)
    
    print("\n✅ Authentication test completed!")

if __name__ == "__main__":
    main()