#!/usr/bin/env python3
"""Test AMC Collaboration Instance Management API based on documentation URL pattern"""

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

def test_collaboration_endpoints(access_token):
    """Test AMC Collaboration instance management endpoints"""
    
    print("🔍 Testing AMC Collaboration Instance Management APIs")
    print("="*60)
    
    # Based on the URL pattern, it seems AMC uses "collaboration" terminology
    base_headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Try collaboration-based endpoints
    endpoints_to_test = [
        # Collaboration instances
        '/amc/collaborations',
        '/amc/collaboration/instances',
        '/amc/collaboration-instances',
        '/collaborations',
        '/collaboration/instances',
        
        # With account IDs we found
        '/amc/collaborations?accountId=ENTITYEJZCBSCBH4HZ',
        '/amc/collaborations?accountId=ENTITY277TBI8OBF435',
        
        # Mapping tables (based on deleteCollaborationIdMappingTable)
        '/amc/collaboration/mapping-tables',
        '/amc/collaborations/mapping-tables',
        
        # Try v2 endpoints
        '/v2/amc/collaborations',
        '/v2/collaboration/instances',
    ]
    
    for endpoint in endpoints_to_test:
        url = f'https://advertising-api.amazon.com{endpoint}'
        print(f"\n📍 Testing: {endpoint}")
        
        try:
            response = requests.get(url, headers=base_headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                print(f"   Response preview: {json.dumps(data, indent=2)[:200]}...")
                
                # Save successful response
                filename = f"collaboration_response_{endpoint.replace('/', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"   💾 Saved to: {filename}")
                
            elif response.status_code in [400, 403, 404]:
                error = response.json() if response.text else {}
                print(f"   ❌ {error.get('details', error.get('message', response.text))[:100]}")
                
        except Exception as e:
            print(f"   💥 Error: {str(e)[:50]}")

def test_with_collaboration_headers(access_token):
    """Test with potential collaboration-specific headers"""
    
    print("\n\n🔍 Testing with Collaboration-Specific Headers")
    print("="*60)
    
    # Try with our AMC account IDs in different header positions
    account_ids = ['ENTITYEJZCBSCBH4HZ', 'ENTITY277TBI8OBF435']
    
    for account_id in account_ids:
        print(f"\n📦 Testing with Account: {account_id}")
        
        # Try different header combinations
        header_variations = [
            {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'Amazon-Advertising-API-CollaborationId': account_id,
                'Content-Type': 'application/json'
            },
            {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'X-Amz-Collaboration-Id': account_id,
                'Content-Type': 'application/json'
            },
            {
                'Authorization': f'Bearer {access_token}',
                'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
                'Amazon-Collaboration-Account-Id': account_id,
                'Content-Type': 'application/json'
            }
        ]
        
        for i, headers in enumerate(header_variations):
            header_key = [k for k in headers.keys() if 'Collaboration' in k][0]
            print(f"\n   Attempt {i+1}: Using header '{header_key}'")
            
            # Test different endpoint patterns
            test_urls = [
                'https://advertising-api.amazon.com/amc/instances',
                'https://advertising-api.amazon.com/amc/collaborations',
                'https://advertising-api.amazon.com/collaboration/instances'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, headers=headers)
                    print(f"      {url.split('/')[-2:]}: Status {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"      ✅ SUCCESS! Found data")
                        
                        filename = f"collaboration_success_{account_id}_{i}.json"
                        with open(filename, 'w') as f:
                            json.dump({
                                'account_id': account_id,
                                'headers_used': header_key,
                                'url': url,
                                'response': data
                            }, f, indent=2)
                        print(f"      💾 Saved to: {filename}")
                        return data
                        
                except Exception as e:
                    print(f"      Error: {str(e)[:30]}")

def main():
    print("AMC Collaboration Instance Management API Test")
    print("=============================================")
    print("Based on documentation URL pattern suggesting 'collaboration' terminology\n")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    
    # Test collaboration endpoints
    test_collaboration_endpoints(access_token)
    
    # Test with collaboration-specific headers
    test_with_collaboration_headers(access_token)
    
    print("\n\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print("\n💡 Insights from documentation URL:")
    print("1. AMC uses 'collaboration' terminology for instance management")
    print("2. There's a 'deleteCollaborationIdMappingTable' operation")
    print("3. This suggests instances might be called 'collaborations'")
    print("4. The entityId might actually be a 'collaborationId'")
    print("\n📝 Next Steps:")
    print("1. Check any successful response files")
    print("2. Look for 'collaboration' related endpoints in browser network tab")
    print("3. The AMC instances might be under a completely different API structure")

if __name__ == "__main__":
    main()