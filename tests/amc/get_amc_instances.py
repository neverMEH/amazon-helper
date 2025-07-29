#!/usr/bin/env python3
"""Get AMC instances for discovered AMC accounts"""

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

def get_amc_instances(access_token, account_id):
    """Get AMC instances for a specific AMC account"""
    
    print(f"\n🔍 Getting instances for AMC Account: {account_id}")
    
    # The endpoint requires the entityId (AMC account ID)
    url = f'https://advertising-api.amazon.com/amc/instances?entityId={account_id}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            instances = data.get('amcInstances', [])
            print(f"✅ Found {len(instances)} AMC instances")
            
            for instance in instances:
                print(f"\n  Instance ID: {instance.get('instanceId')}")
                print(f"  Name: {instance.get('instanceName')}")
                print(f"  Region: {instance.get('region')}")
                print(f"  Status: {instance.get('status')}")
                print(f"  Created: {instance.get('createdTime')}")
                
            return instances
        else:
            print(f"Error: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return []

def main():
    print("Amazon Marketing Cloud Instances Discovery")
    print("=========================================")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # Load AMC accounts
    try:
        with open('amc_accounts.json', 'r') as f:
            data = json.load(f)
            amc_accounts = data.get('amcAccounts', [])
    except FileNotFoundError:
        print("❌ amc_accounts.json not found")
        return
    
    print(f"\n📋 Found {len(amc_accounts)} AMC accounts:")
    for account in amc_accounts:
        print(f"  - {account['accountName']} ({account['accountId']})")
    
    # Get instances for each account
    all_instances = []
    for account in amc_accounts:
        instances = get_amc_instances(access_token, account['accountId'])
        if instances:
            all_instances.extend([{
                'account': account,
                'instances': instances
            }])
    
    # Save all instances
    if all_instances:
        with open('amc_instances.json', 'w') as f:
            json.dump({
                'amcAccounts': amc_accounts,
                'instancesByAccount': all_instances
            }, f, indent=2)
        print("\n💾 Saved all instances to amc_instances.json")
    
    print("\n" + "="*50)
    print("📊 Summary")
    print("="*50)
    print(f"Total AMC Accounts: {len(amc_accounts)}")
    print(f"Total Instances Found: {sum(len(item['instances']) for item in all_instances)}")
    
    print("\n✅ Success! Your AMC instances have been discovered.")
    print("\nThe key insight was that:")
    print("1. AMC accounts are accessed via /amc/accounts (not profile-specific)")
    print("2. AMC instances require the entityId parameter (the AMC account ID)")
    print("3. These are separate from your advertising profiles")

if __name__ == "__main__":
    main()