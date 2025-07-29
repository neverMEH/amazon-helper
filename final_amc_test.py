#!/usr/bin/env python3
"""Final AMC test combining what worked before"""

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

def get_amc_accounts_and_instances(access_token):
    """Get AMC accounts and then try to get instances"""
    
    print("🔍 Step 1: Get AMC Accounts (this worked before)")
    print("="*60)
    
    # Use the exact headers that worked before - NO profile scope
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Get AMC accounts (this worked)
    url = 'https://advertising-api.amazon.com/amc/accounts'
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            amc_accounts = data.get('amcAccounts', [])
            print(f"✅ Found {len(amc_accounts)} AMC accounts:")
            
            for account in amc_accounts:
                print(f"\n📦 {account['accountName']}")
                print(f"   ID: {account['accountId']}")
                print(f"   Marketplace: {account['marketplaceId']}")
            
            # Now try to get instances with the exact entityId format
            print("\n\n🔍 Step 2: Try to get instances")
            print("="*60)
            
            for account in amc_accounts:
                test_instances_multiple_ways(headers, account)
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_instances_multiple_ways(headers, account):
    """Try every possible way to get instances"""
    
    account_id = account['accountId']
    account_name = account['accountName']
    
    print(f"\n📦 Testing for {account_name} ({account_id})")
    
    # Method 1: Direct query parameter with exact case
    print("\n   Method 1: Query parameter 'entityId'")
    url = f'https://advertising-api.amazon.com/amc/instances?entityId={account_id}'
    response = requests.get(url, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code != 200:
        print(f"   Response: {response.text[:100]}")
    
    # Method 2: Try with different parameter names
    param_names = ['entity_id', 'entity-id', 'accountId', 'account_id', 'amcAccountId']
    print("\n   Method 2: Alternative parameter names")
    for param in param_names:
        url = f'https://advertising-api.amazon.com/amc/instances?{param}={account_id}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"   ✅ Success with parameter: {param}")
            save_response(response.json(), f"instances_{account_id}_{param}.json")
            return
        elif response.status_code != 400:
            print(f"   {param}: Status {response.status_code}")
    
    # Method 3: POST with body
    print("\n   Method 3: POST with entityId in body")
    url = 'https://advertising-api.amazon.com/amc/instances'
    
    # Try exact format from error message
    body = {'entityId': account_id}
    response = requests.post(url, headers=headers, json=body)
    print(f"   Status: {response.status_code}")
    print(f"   Body sent: {body}")
    if response.status_code != 200:
        print(f"   Response: {response.text[:100]}")
    
    # Method 4: Try URL path instead of parameter
    print("\n   Method 4: Account ID in URL path")
    test_urls = [
        f'https://advertising-api.amazon.com/amc/accounts/{account_id}/instances',
        f'https://advertising-api.amazon.com/amc/entities/{account_id}/instances',
        f'https://advertising-api.amazon.com/amc/instances/{account_id}'
    ]
    
    for test_url in test_urls:
        response = requests.get(test_url, headers=headers)
        url_part = test_url.split('.com')[1]
        if response.status_code == 200:
            print(f"   ✅ Success with: {url_part}")
            save_response(response.json(), f"instances_{account_id}_path.json")
            return
        else:
            print(f"   {url_part}: Status {response.status_code}")

def save_response(data, filename):
    """Save successful response"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   💾 Saved to: {filename}")

def main():
    print("Final AMC API Test")
    print("==================")
    print("Testing what worked before and trying all variations\n")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # Get accounts and test instances
    get_amc_accounts_and_instances(access_token)
    
    print("\n\n" + "="*60)
    print("📊 Final Analysis")
    print("="*60)
    print("\n✅ What works:")
    print("- GET /amc/accounts returns your AMC accounts")
    print("- No profile scope needed for this endpoint")
    print("\n❌ What doesn't work:")
    print("- GET /amc/instances with entityId parameter")
    print("- The API keeps saying 'entityId provided is null'")
    print("\n🤔 Possible reasons:")
    print("1. The instances endpoint might not be publicly available")
    print("2. It might require additional permissions or a different OAuth scope")
    print("3. The entityId format might be different than what we're sending")
    print("4. AMC instances might be accessed through a completely different API")
    print("\n💡 Recommendation:")
    print("Use browser DevTools to capture the exact API call when viewing AMC instances in the UI")

if __name__ == "__main__":
    main()