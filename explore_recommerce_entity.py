#!/usr/bin/env python3
"""Explore Recommerce Brands entity to find all associated account IDs"""

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

def explore_entity(access_token, entity_id, entity_name):
    """Explore various endpoints for a specific entity"""
    
    print(f"\n🔍 Exploring Entity: {entity_name}")
    print(f"   Entity ID: {entity_id}")
    print("="*60)
    
    # Base headers
    base_headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Try various endpoints that might give us more information
    endpoints_to_try = [
        # Direct entity endpoints
        f'/amc/accounts/{entity_id}',
        f'/amc/entities/{entity_id}',
        f'/entities/{entity_id}',
        f'/entity/{entity_id}',
        
        # Account-related endpoints
        f'/amc/accounts/{entity_id}/profiles',
        f'/amc/accounts/{entity_id}/advertisers',
        f'/amc/accounts/{entity_id}/users',
        f'/amc/accounts/{entity_id}/permissions',
        
        # Instance endpoints with entity in path
        f'/amc/accounts/{entity_id}/instances',
        f'/amc/entities/{entity_id}/instances',
        
        # Data provider endpoints
        f'/data-provider/entities/{entity_id}',
        f'/dp/entities/{entity_id}',
        
        # Profile associations
        f'/profiles?entityId={entity_id}',
        f'/v2/profiles?entityId={entity_id}',
        
        # DSP associations (AMC often linked with DSP)
        f'/dsp/advertisers?entityId={entity_id}',
        f'/v2/dsp/advertisers?entityId={entity_id}',
    ]
    
    results = []
    
    for endpoint in endpoints_to_try:
        url = f'https://advertising-api.amazon.com{endpoint}'
        print(f"\n📍 Trying: {endpoint}")
        
        # Try with base headers
        try:
            response = requests.get(url, headers=base_headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                print(f"   Response preview: {json.dumps(data, indent=2)[:200]}...")
                
                # Save successful response
                filename = f"entity_response_{endpoint.replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump({
                        'entity': {'id': entity_id, 'name': entity_name},
                        'endpoint': endpoint,
                        'response': data
                    }, f, indent=2)
                print(f"   💾 Saved to: {filename}")
                
                results.append({
                    'endpoint': endpoint,
                    'status': 'success',
                    'data': data
                })
                
            elif response.status_code in [400, 403, 404]:
                error_msg = response.json().get('details', response.text) if response.text else 'No details'
                print(f"   ❌ {error_msg[:100]}")
            else:
                print(f"   ⚠️  Unexpected response")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout")
        except Exception as e:
            print(f"   💥 Error: {str(e)[:50]}")
    
    # Try with entity ID as different header types
    print("\n\n🔄 Trying with Entity ID in headers:")
    header_variations = [
        {'Amazon-Advertising-API-Scope': entity_id},
        {'Amazon-Advertising-API-EntityId': entity_id},
        {'X-Amz-Account-Id': entity_id},
        {'Amazon-Account-Id': entity_id},
    ]
    
    for headers_update in header_variations:
        headers = base_headers.copy()
        headers.update(headers_update)
        header_name = list(headers_update.keys())[0]
        
        print(f"\n📍 Testing /amc/instances with {header_name}")
        
        try:
            response = requests.get(
                'https://advertising-api.amazon.com/amc/instances',
                headers=headers,
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success with {header_name}!")
                
                filename = f"instances_with_{header_name.replace('-', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"   💾 Saved to: {filename}")
                
        except Exception as e:
            print(f"   Error: {str(e)[:50]}")
    
    return results

def get_all_profiles_for_accounts():
    """Check if any advertising profiles are linked to the AMC accounts"""
    
    print("\n\n🔍 Checking profile associations")
    print("="*60)
    
    tokens = load_tokens()
    if not tokens:
        return
    
    # Load regular advertising profiles
    try:
        with open('profiles.json', 'r') as f:
            profiles = json.load(f)
    except:
        print("❌ profiles.json not found")
        return
    
    # Check for matching account IDs
    amc_account_ids = ['ENTITYEJZCBSCBH4HZ', 'ENTITY277TBI8OBF435']
    
    print("\n📊 Checking for profile matches:")
    for profile in profiles:
        account_id = profile['accountInfo'].get('id', '')
        if any(amc_id in account_id for amc_id in amc_account_ids):
            print(f"\n🔗 Potential match found!")
            print(f"   Profile: {profile['profileId']}")
            print(f"   Name: {profile['accountInfo']['name']}")
            print(f"   Account ID: {account_id}")

def main():
    print("Recommerce Brands Entity Exploration")
    print("====================================")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # Focus on Recommerce Brands entity
    entity_id = 'ENTITYEJZCBSCBH4HZ'
    entity_name = 'Recommerce Brands'
    
    # Explore the entity
    results = explore_entity(access_token, entity_id, entity_name)
    
    # Check profile associations
    get_all_profiles_for_accounts()
    
    # Summary
    print("\n\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    successful_endpoints = [r for r in results if r['status'] == 'success']
    if successful_endpoints:
        print(f"\n✅ Found {len(successful_endpoints)} successful endpoints:")
        for result in successful_endpoints:
            print(f"   - {result['endpoint']}")
    
    print("\n💡 Key Insights:")
    print("1. AMC entities (ENTITY...) are different from profile IDs")
    print("2. They may contain multiple advertiser accounts")
    print("3. Check any saved response files for account details")
    
    print("\n📝 Next Steps:")
    print("1. Review any successful response files created")
    print("2. Look for account IDs, profile IDs, or advertiser IDs in the responses")
    print("3. Try using any discovered IDs to access AMC instances")

if __name__ == "__main__":
    main()