#!/usr/bin/env python3
"""Working AMC instances retrieval based on cURL from Postman"""

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

def get_amc_instances(access_token, entity_id, marketplace_id="ATVPDKIKX0DER"):
    """Get AMC instances using the correct headers"""
    
    print(f"\n🔍 Getting AMC instances for entity: {entity_id}")
    print("="*60)
    
    # URL with nextToken parameter (can be empty for first request)
    url = "https://advertising-api.amazon.com/amc/instances?nextToken="
    
    # Headers matching the cURL exactly
    headers = {
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-MarketplaceId': marketplace_id,
        'Amazon-Advertising-API-AdvertiserId': entity_id  # This is the key!
    }
    
    print("📤 Request details:")
    print(f"   URL: {url}")
    print(f"   Headers:")
    for key, value in headers.items():
        if key == 'Authorization':
            print(f"     {key}: Bearer xxx...")
        else:
            print(f"     {key}: {value}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            
            if 'instances' in data:
                instances = data['instances']
                print(f"\n🎉 Found {len(instances)} AMC instances!")
                
                # Save the response
                with open(f'amc_instances_{entity_id}.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"💾 Full response saved to: amc_instances_{entity_id}.json")
                
                # Display instances
                print("\n📊 AMC Instances:")
                for idx, instance in enumerate(instances):
                    print(f"\n  Instance {idx + 1}:")
                    print(f"    Instance ID: {instance.get('instanceId')}")
                    print(f"    Instance Name: {instance.get('instanceName')}")
                    print(f"    Instance Type: {instance.get('instanceType')}")
                    print(f"    Customer: {instance.get('customerCanonicalName')}")
                    print(f"    Status: {instance.get('creationStatus')}")
                    print(f"    Created: {instance.get('creationDatetime')}")
                    print(f"    S3 Bucket: {instance.get('s3BucketName')}")
                    print(f"    API Endpoint: {instance.get('apiEndpoint')}")
                    
                    # Show entities
                    entities = instance.get('entities', [])
                    if entities:
                        print(f"    Entities: {', '.join(entities) if isinstance(entities, list) else entities}")
                    
                    # Show optional datasets
                    datasets = instance.get('optionalDatasets', [])
                    if datasets:
                        print(f"    Optional Datasets:")
                        for ds in datasets:
                            print(f"      - {ds.get('label')} (activated: {ds.get('activationTime')})")
                
                # Check for pagination
                if 'nextToken' in data and data['nextToken']:
                    print(f"\n📄 More results available. NextToken: {data['nextToken']}")
                    
                return instances
            else:
                print(f"❌ Unexpected response structure: {list(data.keys())}")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        
    return None

def main():
    print("AMC Instances Retrieval - Working Solution")
    print("=========================================")
    print("Using the correct headers from Postman cURL\n")
    
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
    except:
        print("❌ amc_accounts.json not found")
        return
    
    print(f"📋 Found {len(amc_accounts)} AMC accounts:")
    for account in amc_accounts:
        print(f"  - {account['accountName']} ({account['accountId']})")
    
    # Get instances for each AMC account
    all_instances = []
    for account in amc_accounts:
        instances = get_amc_instances(
            access_token,
            account['accountId'],
            account['marketplaceId']
        )
        
        if instances:
            for inst in instances:
                inst['amc_account'] = account['accountName']
                inst['amc_account_id'] = account['accountId']
            all_instances.extend(instances)
    
    # Save summary
    if all_instances:
        summary = {
            'total_instances': len(all_instances),
            'amc_accounts': amc_accounts,
            'instances_summary': [
                {
                    'instanceId': inst.get('instanceId'),
                    'instanceName': inst.get('instanceName'),
                    'instanceType': inst.get('instanceType'),
                    'entities': inst.get('entities', [])
                }
                for inst in all_instances
            ]
        }
        
        with open('amc_complete_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n💾 Complete summary saved to: amc_complete_summary.json")
    
    print("\n\n" + "="*60)
    print("🎉 SUCCESS!")
    print("="*60)
    print("\n✅ The key was using 'Amazon-Advertising-API-AdvertiserId' header")
    print("   instead of trying to pass entityId as a parameter!")
    print("\n📝 Working format:")
    print("   - Header: Amazon-Advertising-API-AdvertiserId: ENTITY...")
    print("   - Header: Amazon-Advertising-API-MarketplaceId: ATVPDKIKX0DER")
    print("   - URL: /amc/instances?nextToken=")

if __name__ == "__main__":
    main()