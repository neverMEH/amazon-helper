#!/usr/bin/env python3
"""Check for AMC instances across all profiles"""

import json
import requests
import os
from dotenv import load_dotenv
import time

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

def check_amc_for_profile(access_token, profile):
    """Check AMC access for a specific profile"""
    
    profile_id = profile['profileId']
    name = profile['accountInfo']['name']
    account_type = profile['accountInfo']['type']
    
    print(f"\n🔍 Checking: {name} ({account_type}) - Profile: {profile_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Amazon-Advertising-API-Scope': str(profile_id),
        'Content-Type': 'application/json'
    }
    
    # Try different potential AMC endpoints
    amc_endpoints = [
        # Potential AMC instance endpoints
        'https://advertising-api.amazon.com/amc/instances',
        'https://advertising-api.amazon.com/v1/amc/instances',
        'https://advertising-api.amazon.com/data-provider/amc/instances',
        
        # DSP endpoints (AMC often associated with DSP)
        'https://advertising-api.amazon.com/dsp/accounts',
        'https://advertising-api.amazon.com/v2/dsp/accounts',
    ]
    
    amc_found = False
    
    for endpoint in amc_endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ Success at: {endpoint}")
                data = response.json()
                print(f"  📊 Response: {json.dumps(data, indent=2)[:200]}...")
                amc_found = True
                
                # Save successful response
                filename = f"amc_response_{profile_id}.json"
                with open(filename, 'w') as f:
                    json.dump({
                        'profile': profile,
                        'endpoint': endpoint,
                        'response': data
                    }, f, indent=2)
                print(f"  💾 Saved to: {filename}")
                
            elif response.status_code == 403:
                print(f"  🚫 Access denied: {endpoint}")
            elif response.status_code == 404:
                # Skip 404s as they're expected for non-existent endpoints
                pass
            else:
                print(f"  ❓ {response.status_code} at: {endpoint}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout: {endpoint}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}...")
        
        # Rate limiting
        time.sleep(0.5)
    
    if not amc_found:
        print(f"  ℹ️  No AMC endpoints found for this profile")
    
    return amc_found

def main():
    print("Amazon Marketing Cloud Instance Discovery")
    print("=========================================")
    
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
    
    print(f"\n📋 Checking {len(profiles)} profiles for AMC access...")
    
    # Prioritize agency accounts
    agency_profiles = [p for p in profiles if p['accountInfo']['type'] == 'agency']
    seller_profiles = [p for p in profiles if p['accountInfo']['type'] == 'seller']
    
    profiles_with_amc = []
    
    # Check agency accounts first
    if agency_profiles:
        print("\n🏢 Checking AGENCY accounts (more likely to have AMC):")
        for profile in agency_profiles:
            if check_amc_for_profile(tokens['access_token'], profile):
                profiles_with_amc.append(profile)
    
    # Then check seller accounts
    print("\n🏪 Checking SELLER accounts:")
    for profile in seller_profiles[:3]:  # Check first 3 to avoid rate limits
        if check_amc_for_profile(tokens['access_token'], profile):
            profiles_with_amc.append(profile)
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    
    if profiles_with_amc:
        print(f"\n✅ Found {len(profiles_with_amc)} profiles with potential AMC access:")
        for p in profiles_with_amc:
            print(f"  - {p['accountInfo']['name']} ({p['accountInfo']['type']})")
    else:
        print("\n❌ No AMC instances found in checked profiles")
        print("\n💡 This is normal if:")
        print("  - AMC instances haven't been provisioned for your accounts")
        print("  - AMC access requires separate approval from your account manager")
        print("  - The API endpoints for AMC might be different than tested")
    
    print("\n📝 Next steps:")
    print("  1. Contact your Amazon Advertising account manager about AMC access")
    print("  2. Agency accounts (neverMEH, SparkX) are more likely to have AMC")
    print("  3. Check any saved response files for more details")

if __name__ == "__main__":
    main()