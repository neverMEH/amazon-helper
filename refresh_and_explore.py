#!/usr/bin/env python3
"""Refresh token and explore AMC accounts/instances relationship"""

import json
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def refresh_access_token():
    """Refresh the access token using the refresh token"""
    
    print("🔄 Refreshing access token...")
    
    # Load current tokens
    try:
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ tokens.json not found")
        return None
    
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        print("❌ No refresh token found")
        return None
    
    # Refresh the token
    token_url = 'https://api.amazon.com/auth/o2/token'
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': os.getenv('AMAZON_CLIENT_ID'),
        'client_secret': os.getenv('AMAZON_CLIENT_SECRET')
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            new_tokens = response.json()
            new_tokens['refresh_token'] = refresh_token  # Preserve refresh token
            new_tokens['obtained_at'] = time.time()
            
            # Save new tokens
            with open('tokens.json', 'w') as f:
                json.dump(new_tokens, f, indent=2)
            
            print("✅ Token refreshed successfully!")
            return new_tokens['access_token']
        else:
            print(f"❌ Failed to refresh token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error refreshing token: {e}")
        return None

def explore_amc_hierarchy(access_token):
    """Explore the AMC account hierarchy"""
    
    print("\n🔍 Exploring AMC Hierarchy")
    print("="*60)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # First, get AMC accounts again
    print("\n1️⃣ Getting AMC Accounts:")
    url = 'https://advertising-api.amazon.com/amc/accounts'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            accounts_data = response.json()
            amc_accounts = accounts_data.get('amcAccounts', [])
            print(f"✅ Found {len(amc_accounts)} AMC accounts")
            
            for account in amc_accounts:
                print(f"\n📦 Account: {account['accountName']}")
                print(f"   ID: {account['accountId']}")
                print(f"   Marketplace: {account['marketplaceId']}")
                
                # Try to get more details about each account
                explore_account_details(access_token, account)
                
        else:
            print(f"❌ Failed to get AMC accounts: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def explore_account_details(access_token, account):
    """Try different approaches to get account details"""
    
    account_id = account['accountId']
    account_name = account['accountName']
    
    print(f"\n   🔍 Exploring {account_name} in detail:")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json'
    }
    
    # Try AMC instances with POST method and body
    print("\n   📍 Trying POST with entityId in body:")
    url = 'https://advertising-api.amazon.com/amc/instances'
    
    body_variations = [
        {'entityId': account_id},
        {'accountId': account_id},
        {'amcAccountId': account_id},
        {'filter': {'entityId': account_id}},
        {'filters': {'entityId': account_id}}
    ]
    
    for body in body_variations:
        try:
            response = requests.post(url, headers=headers, json=body)
            print(f"      Body: {body}")
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Success!")
                
                filename = f"amc_instances_{account_id}_POST.json"
                with open(filename, 'w') as f:
                    json.dump({
                        'account': account,
                        'request_body': body,
                        'response': data
                    }, f, indent=2)
                print(f"      💾 Saved to: {filename}")
                return data
            elif response.status_code in [400, 403]:
                error = response.json() if response.text else {}
                print(f"      Error: {error.get('details', response.text)[:100]}")
                
        except Exception as e:
            print(f"      Exception: {str(e)[:50]}")
    
    # Try with different URL patterns
    print("\n   📍 Trying different URL patterns:")
    url_patterns = [
        f'https://advertising-api.amazon.com/amc/instances?accountId={account_id}',
        f'https://advertising-api.amazon.com/amc/instances?amcAccountId={account_id}',
        f'https://advertising-api.amazon.com/amc/instances?filter.entityId={account_id}',
        f'https://advertising-api.amazon.com/amc/accounts/{account_id}/instances',
    ]
    
    for url in url_patterns:
        try:
            response = requests.get(url, headers=headers)
            print(f"      URL: {url.split('?')[1] if '?' in url else url.split('/')[-2:]}")
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Success!")
                
                filename = f"amc_instances_{account_id}_success.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"      💾 Saved to: {filename}")
                return data
                
        except Exception as e:
            print(f"      Error: {str(e)[:30]}")

def main():
    print("AMC Account Exploration with Token Refresh")
    print("=========================================")
    
    # Refresh token first
    access_token = refresh_access_token()
    if not access_token:
        print("\n❌ Failed to refresh token. You may need to re-authenticate.")
        return
    
    # Explore AMC hierarchy
    explore_amc_hierarchy(access_token)
    
    print("\n\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print("\n💡 Key Points:")
    print("1. We successfully got AMC accounts")
    print("2. The instances endpoint is still problematic")
    print("3. Check any created JSON files for successful responses")
    print("\n🔍 The issue might be:")
    print("1. AMC instances require a different API endpoint entirely")
    print("2. The entityId parameter has a specific format we haven't found")
    print("3. Additional permissions or scopes are needed")
    print("4. The UI uses internal APIs not exposed publicly")

if __name__ == "__main__":
    main()