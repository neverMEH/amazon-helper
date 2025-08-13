#!/usr/bin/env python3
"""Test AMC with correct approach based on latest research"""

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

def load_profiles():
    """Load advertising profiles"""
    try:
        with open('profiles.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ profiles.json not found")
        return None

def test_amc_with_profile_scope(access_token, profile_id, profile_name):
    """Test AMC access using profile ID as scope"""
    
    print(f"\n🔍 Testing with Profile: {profile_name} (ID: {profile_id})")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Amazon-Advertising-API-Scope': str(profile_id),  # Use profile ID as scope
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test AMC endpoints with profile scope
    endpoints = [
        '/amc/accounts',
        '/amc/instances',
        '/amc/advertisers',
        '/amc/users'
    ]
    
    for endpoint in endpoints:
        url = f'https://advertising-api.amazon.com{endpoint}'
        print(f"\n   📍 {endpoint}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Success!")
                
                # Save response
                filename = f"amc_{profile_id}_{endpoint.replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump({
                        'profile': {'id': profile_id, 'name': profile_name},
                        'endpoint': endpoint,
                        'response': data
                    }, f, indent=2)
                print(f"      💾 Saved to: {filename}")
                
                # If we got accounts, try to get instances for each
                if endpoint == '/amc/accounts' and 'amcAccounts' in data:
                    for account in data['amcAccounts']:
                        test_instances_for_account(headers, account)
                        
            elif response.status_code == 400:
                error = response.json() if response.text else {}
                print(f"      Error: {error.get('details', 'Unknown')}")
            elif response.status_code == 403:
                print(f"      Access denied - this profile may not have AMC access")
                
        except Exception as e:
            print(f"      Exception: {str(e)[:50]}")

def test_instances_for_account(headers, account):
    """Test getting instances for a specific AMC account"""
    
    account_id = account['accountId']
    account_name = account['accountName']
    
    print(f"\n      🔸 Getting instances for {account_name}")
    
    # Try different parameter formats
    test_params = [
        {'entityId': account_id},
        {'accountId': account_id},
        {'amcAccountId': account_id}
    ]
    
    for params in test_params:
        url = 'https://advertising-api.amazon.com/amc/instances'
        
        try:
            response = requests.get(url, headers=headers, params=params)
            param_key = list(params.keys())[0]
            
            if response.status_code == 200:
                data = response.json()
                print(f"         ✅ Success with {param_key}!")
                
                filename = f"instances_{account_id}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                return data
            elif response.status_code == 400:
                # Only print if different from "entityId null" error
                error = response.json() if response.text else {}
                if 'null' not in error.get('details', ''):
                    print(f"         {param_key}: {error.get('details', '')[:50]}")
                    
        except Exception:
            pass

def main():
    print("AMC API Test with Profile-Based Scope")
    print("=====================================")
    print("Using profiles as scope based on AMC API documentation\n")
    
    # Load tokens and profiles
    tokens = load_tokens()
    if not tokens:
        return
        
    profiles = load_profiles()
    if not profiles:
        return
    
    access_token = tokens.get('access_token')
    
    # First, test which profiles have AMC access
    print("🔍 Testing profiles for AMC access:")
    
    # Prioritize testing with agency profiles and specific seller profiles
    priority_profiles = [
        # Agency profiles (more likely to have AMC)
        {'profileId': 3810822089931808, 'name': 'neverMEH: US', 'type': 'agency'},
        {'profileId': 3335273396303954, 'name': 'SparkX-US Clean Boss', 'type': 'agency'},
        
        # US seller profiles
        {'profileId': 149933231819265, 'name': 'Dirty Labs - US', 'type': 'seller'},
        {'profileId': 1595982706516623, 'name': 'Planetary Design - US', 'type': 'seller'},
    ]
    
    # Test priority profiles
    for profile_info in priority_profiles:
        test_amc_with_profile_scope(
            access_token,
            profile_info['profileId'],
            f"{profile_info['name']} ({profile_info['type']})"
        )
    
    print("\n\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print("\n💡 Key Approach:")
    print("1. Use advertising profile ID as the API scope")
    print("2. Agency profiles are more likely to have AMC access")
    print("3. Check /amc/accounts first to see which profiles have AMC")
    print("4. Then use the returned account IDs to get instances")
    print("\n📝 Check any JSON files created for successful responses")

if __name__ == "__main__":
    main()