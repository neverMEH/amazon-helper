#!/usr/bin/env python3
"""Test AMC instances based on Postman response structure"""

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

def refresh_token_if_needed():
    """Refresh token if expired"""
    tokens = load_tokens()
    if not tokens:
        return None
        
    # Simple refresh
    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        return None
        
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
            new_tokens['refresh_token'] = refresh_token
            
            with open('tokens.json', 'w') as f:
                json.dump(new_tokens, f, indent=2)
                
            print("✅ Token refreshed")
            return new_tokens['access_token']
    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        
    return None

def test_instances_endpoint_variations(access_token):
    """Test variations based on Postman structure"""
    
    print("🔍 Testing AMC Instances Endpoint Variations")
    print("Based on Postman response structure showing 'instances' array")
    print("="*60)
    
    # Load AMC accounts
    try:
        with open('amc_accounts.json', 'r') as f:
            data = json.load(f)
            amc_accounts = data.get('amcAccounts', [])
    except:
        print("❌ No AMC accounts found. Run previous scripts first.")
        return
    
    # Common headers
    base_headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test different endpoint patterns that might return the instances structure
    test_configs = [
        {
            'name': 'Standard instances endpoint',
            'url': 'https://advertising-api.amazon.com/amc/instances',
            'method': 'GET',
            'headers': base_headers
        },
        {
            'name': 'With X-Amz-* headers',
            'url': 'https://advertising-api.amazon.com/amc/instances',
            'method': 'GET',
            'headers': {
                **base_headers,
                'X-Amz-Date': '20250729T000000Z',
                'X-Amz-Target': 'AmazonMarketingCloud.GetInstances'
            }
        },
        {
            'name': 'V2 endpoint',
            'url': 'https://advertising-api.amazon.com/v2/amc/instances',
            'method': 'GET',
            'headers': base_headers
        },
        {
            'name': 'Management endpoint',
            'url': 'https://advertising-api.amazon.com/amc/management/instances',
            'method': 'GET',
            'headers': base_headers
        }
    ]
    
    # Test each configuration with different entity formats
    for config in test_configs:
        print(f"\n📍 Testing: {config['name']}")
        print(f"   URL: {config['url']}")
        
        # Test without parameters first
        print("\n   Without parameters:")
        try:
            response = requests.request(
                method=config['method'],
                url=config['url'],
                headers=config['headers']
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'instances' in data:
                    print(f"   ✅ SUCCESS! Found {len(data['instances'])} instances")
                    save_instances_response(data, 'instances_success.json')
                    display_instances(data['instances'])
                    return data
                else:
                    print(f"   Response structure: {list(data.keys())}")
                    
        except Exception as e:
            print(f"   Error: {str(e)[:50]}")
        
        # Test with entity parameters
        for account in amc_accounts:
            entity_id = account['accountId']
            print(f"\n   With entity {entity_id}:")
            
            # Try as query parameter
            test_url = f"{config['url']}?entityId={entity_id}"
            try:
                response = requests.get(test_url, headers=config['headers'])
                if response.status_code == 200:
                    data = response.json()
                    if 'instances' in data:
                        print(f"   ✅ SUCCESS with entityId parameter!")
                        save_instances_response(data, f'instances_{entity_id}.json')
                        display_instances(data['instances'])
                        return data
                elif response.status_code != 400:
                    print(f"   Status: {response.status_code}")
            except:
                pass

def display_instances(instances):
    """Display instances in a formatted way"""
    print("\n   📊 Instance Details:")
    for idx, instance in enumerate(instances):
        print(f"\n   Instance {idx + 1}:")
        print(f"     ID: {instance.get('instanceId', 'N/A')}")
        print(f"     Name: {instance.get('instanceName', 'N/A')}")
        print(f"     Type: {instance.get('instanceType', 'N/A')}")
        print(f"     Customer: {instance.get('customerCanonicalName', 'N/A')}")
        print(f"     Status: {instance.get('creationStatus', 'N/A')}")
        print(f"     S3 Bucket: {instance.get('s3BucketName', 'N/A')}")
        print(f"     API Endpoint: {instance.get('apiEndpoint', 'N/A')}")
        
        entities = instance.get('entities', [])
        if entities:
            print(f"     Entities: {', '.join(entities) if isinstance(entities, list) else entities}")

def save_instances_response(data, filename):
    """Save successful response"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"   💾 Saved to: {filename}")
    
    # Also create a summary
    if 'instances' in data:
        summary = {
            'total_instances': len(data['instances']),
            'instances': [
                {
                    'id': inst.get('instanceId'),
                    'name': inst.get('instanceName'),
                    'type': inst.get('instanceType'),
                    'entities': inst.get('entities', [])
                }
                for inst in data['instances']
            ]
        }
        
        with open('instances_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

def main():
    print("AMC Instances Test Based on Postman Structure")
    print("=============================================\n")
    
    # Get fresh token
    print("🔄 Ensuring valid token...")
    access_token = refresh_token_if_needed()
    if not access_token:
        tokens = load_tokens()
        access_token = tokens.get('access_token') if tokens else None
        
    if not access_token:
        print("❌ No valid token available")
        return
    
    # Test variations
    test_instances_endpoint_variations(access_token)
    
    print("\n\n" + "="*60)
    print("📋 Summary")
    print("="*60)
    print("\n🔍 What we learned from Postman:")
    print("1. The response has an 'instances' array")
    print("2. Each instance has detailed properties")
    print("3. Instances have 'entities' field (might link to our ENTITY IDs)")
    print("\n❓ Still need from you:")
    print("1. The exact URL Postman is using")
    print("2. All headers from the Postman request")
    print("3. Any query parameters or body")
    print("\nYou can find these in Postman's request details or")
    print("export as cURL (Code button → cURL)")

if __name__ == "__main__":
    main()