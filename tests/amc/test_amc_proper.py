#!/usr/bin/env python3
"""Test AMC access with corrected endpoints and headers"""

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
        print("❌ tokens.json not found")
        return None

def test_amc_accounts(access_token):
    """Test AMC accounts endpoint (different from instances)"""
    
    print("\n🔍 Testing AMC Accounts Endpoint")
    print("="*50)
    
    # AMC accounts endpoint (not profile-specific)
    url = 'https://advertising-api.amazon.com/amc/accounts'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    print(f"URL: {url}")
    print(f"Headers: {json.dumps({k: v[:50]+'...' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} AMC accounts")
            with open('amc_accounts.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("💾 Saved to amc_accounts.json")
            return data
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None

def test_amc_instances_without_marketplace(access_token, profile_id=None):
    """Test AMC instances without marketplace ID header"""
    
    print("\n🔍 Testing AMC Instances (No Marketplace ID)")
    print("="*50)
    
    url = 'https://advertising-api.amazon.com/amc/instances'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json'
    }
    
    # Only add profile ID if provided
    if profile_id:
        headers['Amazon-Advertising-API-Scope'] = str(profile_id)
        print(f"Using Profile ID: {profile_id}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found AMC instances")
            return data
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None

def test_data_provider_endpoints(access_token):
    """Test data provider endpoints which might have AMC"""
    
    print("\n🔍 Testing Data Provider Endpoints")
    print("="*50)
    
    endpoints = [
        '/data-provider/accounts',
        '/data-provider/instances',
        '/dp/accounts',  # Alternative shorter path
        '/dp/instances'
    ]
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json'
    }
    
    for endpoint in endpoints:
        url = f'https://advertising-api.amazon.com{endpoint}'
        print(f"\nTrying: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Success at {endpoint}!")
                data = response.json()
                filename = f"response_{endpoint.replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"💾 Saved to {filename}")
                
        except Exception as e:
            print(f"Error: {str(e)[:50]}")

def check_token_scopes(access_token):
    """Decode JWT token to check scopes (if possible)"""
    
    print("\n🔍 Checking Token Information")
    print("="*50)
    
    # Try to decode JWT (without verification)
    try:
        import base64
        import json
        
        # JWT tokens have 3 parts separated by dots
        parts = access_token.split('.')
        if len(parts) == 3:
            # Decode the payload (middle part)
            # Add padding if needed
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            decoded = base64.b64decode(payload)
            token_data = json.loads(decoded)
            
            print("Token payload (partial):")
            for key in ['scope', 'scopes', 'aud', 'iss', 'exp']:
                if key in token_data:
                    print(f"  {key}: {token_data[key]}")
                    
    except Exception as e:
        print(f"Could not decode token: {e}")

def main():
    print("Amazon Marketing Cloud API Access Test (Corrected)")
    print("=================================================")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # Check token information
    check_token_scopes(access_token)
    
    # Test AMC accounts (not profile-specific)
    amc_accounts = test_amc_accounts(access_token)
    
    # Test AMC instances without marketplace
    test_amc_instances_without_marketplace(access_token)
    
    # Test with specific profiles (agency accounts)
    print("\n🏢 Testing with Agency Profiles:")
    agency_profiles = [
        3810822089931808,  # neverMEH: US
        3335273396303954   # SparkX-US Clean Boss
    ]
    
    for profile_id in agency_profiles:
        test_amc_instances_without_marketplace(access_token, profile_id)
    
    # Test data provider endpoints
    test_data_provider_endpoints(access_token)
    
    print("\n" + "="*50)
    print("📝 Summary")
    print("="*50)
    print("\nIf you're seeing AMC instances through the UI but not API:")
    print("1. The UI might use different endpoints or authentication")
    print("2. Check if you need different OAuth scopes (not just 'advertising::campaign_management')")
    print("3. AMC might require a separate API client or application type")
    print("4. Try accessing through the Amazon Ads Console to see the exact API calls")
    print("\n💡 Next steps:")
    print("1. Check any successful response files created")
    print("2. Use browser developer tools to inspect API calls when viewing AMC in the UI")
    print("3. Contact Amazon support about the specific AMC API endpoints and requirements")

if __name__ == "__main__":
    main()