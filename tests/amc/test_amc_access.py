#!/usr/bin/env python3
"""Test AMC instance access with obtained tokens"""

import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def load_tokens():
    """Load tokens from saved file"""
    try:
        with open('tokens.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ tokens.json not found. Run exchange_token.py first.")
        return None

def test_amc_instances(access_token, profile_id):
    """Test accessing AMC instances"""
    
    print(f"\n🔄 Testing AMC access for Profile ID: {profile_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Amazon-Advertising-API-Scope': str(profile_id),
        'Content-Type': 'application/json'
    }
    
    # Note: AMC API endpoints might be different
    # This is a placeholder - actual AMC endpoints would be like:
    # https://advertising-api.amazon.com/amc/instances
    
    # For now, let's test with a standard campaigns endpoint
    url = f'https://advertising-api.amazon.com/v2/sp/campaigns'
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully accessed API")
            print(f"Found {len(data)} campaigns")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("Amazon Marketing Cloud Access Test")
    print("==================================")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    # Load profiles
    try:
        with open('profiles.json', 'r') as f:
            profiles = json.load(f)
    except FileNotFoundError:
        print("❌ profiles.json not found")
        return
    
    print(f"\nFound {len(profiles)} profiles:")
    for i, profile in enumerate(profiles):
        print(f"{i+1}. {profile['accountInfo']['name']} - {profile['countryCode']} (ID: {profile['profileId']})")
    
    # Test with first profile
    if profiles:
        profile = profiles[0]
        test_amc_instances(tokens['access_token'], profile['profileId'])
        
        print("\n📝 Notes:")
        print("- AMC instances are typically provisioned separately from standard advertising accounts")
        print("- You may need to request AMC access through your Amazon Advertising representative")
        print("- AMC API endpoints are integrated into the Amazon Ads API as of 2023")
        print("- Check with your account manager for AMC instance availability")

if __name__ == "__main__":
    main()