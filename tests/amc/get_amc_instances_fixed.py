#!/usr/bin/env python3
"""Get AMC instances with proper entityId handling"""

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

def get_amc_instances(access_token, account_id, account_name):
    """Get AMC instances for a specific AMC account"""
    
    print(f"\n🔍 Getting instances for: {account_name}")
    print(f"   Account ID: {account_id}")
    
    # Try different approaches
    approaches = [
        {
            'name': 'Query Parameter',
            'url': f'https://advertising-api.amazon.com/amc/instances?entityId={account_id}',
            'headers': {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Header-based entityId',
            'url': 'https://advertising-api.amazon.com/amc/instances',
            'headers': {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'Amazon-Advertising-API-Scope': account_id,  # Try entityId as scope
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Custom Header',
            'url': 'https://advertising-api.amazon.com/amc/instances',
            'headers': {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'Amazon-Advertising-API-EntityId': account_id,  # Custom header
                'Content-Type': 'application/json'
            }
        }
    ]
    
    for approach in approaches:
        print(f"\n   Trying: {approach['name']}")
        
        try:
            response = requests.get(approach['url'], headers=approach['headers'])
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                instances = data.get('amcInstances', data)  # Handle different response formats
                
                if isinstance(instances, list) and len(instances) > 0:
                    print(f"   ✅ Success! Found {len(instances)} instances")
                    
                    # Save this specific response
                    filename = f"amc_instances_{account_id}.json"
                    with open(filename, 'w') as f:
                        json.dump({
                            'account': {'id': account_id, 'name': account_name},
                            'approach': approach['name'],
                            'instances': instances
                        }, f, indent=2)
                    print(f"   💾 Saved to {filename}")
                    
                    return instances
                else:
                    print(f"   ⚠️  Empty response or no instances")
                    
            elif response.status_code == 400:
                error_detail = response.json().get('details', response.text)
                print(f"   Error: {error_detail}")
            else:
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"   Exception: {str(e)[:50]}")
    
    return []

def test_direct_instance_access(access_token):
    """Try accessing instances without entityId to see the error message"""
    
    print("\n🔍 Testing direct instance access (for error details)")
    
    url = 'https://advertising-api.amazon.com/amc/instances'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Try POST to see if it gives more info
        print("\n🔍 Testing POST (to see required fields)")
        response = requests.post(url, headers=headers, json={})
        print(f"POST Status: {response.status_code}")
        print(f"POST Response: {response.text[:200]}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Amazon Marketing Cloud Instances Discovery (Fixed)")
    print("=================================================")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # First, test direct access to understand the API better
    test_direct_instance_access(access_token)
    
    # Load AMC accounts
    try:
        with open('amc_accounts.json', 'r') as f:
            data = json.load(f)
            amc_accounts = data.get('amcAccounts', [])
    except FileNotFoundError:
        print("❌ amc_accounts.json not found")
        return
    
    print(f"\n📋 Processing {len(amc_accounts)} AMC accounts:")
    
    # Get instances for each account
    all_instances = []
    for account in amc_accounts:
        instances = get_amc_instances(
            access_token, 
            account['accountId'], 
            account['accountName']
        )
        
        if instances:
            all_instances.append({
                'account': account,
                'instances': instances
            })
    
    print("\n" + "="*50)
    print("📊 Summary")
    print("="*50)
    
    if all_instances:
        total_instances = sum(len(item['instances']) for item in all_instances)
        print(f"✅ Found {total_instances} total instances across {len(all_instances)} accounts")
        
        for item in all_instances:
            account = item['account']
            instances = item['instances']
            print(f"\n{account['accountName']}:")
            for inst in instances:
                print(f"  - Instance: {inst.get('instanceId', 'Unknown ID')}")
    else:
        print("❌ No instances found")
        print("\n💡 Troubleshooting tips:")
        print("1. Check if you're accessing AMC through the correct UI/console")
        print("2. Use browser dev tools to capture the exact API calls")
        print("3. The entityId parameter format might be different")
        print("4. There might be additional required headers or parameters")

if __name__ == "__main__":
    main()