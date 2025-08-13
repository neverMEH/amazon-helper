#!/usr/bin/env python3
"""Test AMC instances with exact Postman format"""

import json
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def refresh_token():
    """Refresh the access token"""
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

def test_exact_postman_request(access_token):
    """Test with exact Postman format"""
    
    print("\n🔍 Testing Exact Postman Format")
    print("="*60)
    
    # Exact URL from Postman
    url = "https://advertising-api.amazon.com/amc/instances?nextToken="
    
    # Common headers that might be used
    headers_variations = [
        {
            # Basic headers
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        {
            # With additional headers that might be required
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Amazon-Advertising-API-Scope': 'profile',  # Generic scope
        },
        {
            # With user agent
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PostmanRuntime/7.32.1'
        }
    ]
    
    for idx, headers in enumerate(headers_variations):
        print(f"\n📍 Attempt {idx + 1}:")
        print(f"   Headers: {list(headers.keys())}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS!")
                
                # Check if it has the expected structure
                if 'instances' in data:
                    instances = data['instances']
                    print(f"   Found {len(instances)} instances")
                    
                    # Save the response
                    with open('amc_instances_success.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    # Display instances
                    for i, instance in enumerate(instances[:3]):
                        print(f"\n   Instance {i+1}:")
                        print(f"     ID: {instance.get('instanceId')}")
                        print(f"     Name: {instance.get('instanceName')}")
                        print(f"     Type: {instance.get('instanceType')}")
                        print(f"     Customer: {instance.get('customerCanonicalName')}")
                        print(f"     Entities: {instance.get('entities')}")
                    
                    # Save working headers
                    with open('working_headers.json', 'w') as f:
                        json.dump({
                            'headers': headers,
                            'url': url,
                            'note': 'These headers successfully retrieved AMC instances'
                        }, f, indent=2)
                    
                    return True
                else:
                    print(f"   Unexpected response structure: {list(data.keys())}")
                    
            elif response.status_code == 401:
                print(f"   Unauthorized - token might be invalid")
                print(f"   Response: {response.text[:100]}")
            elif response.status_code == 403:
                print(f"   Forbidden - might need different permissions")
                print(f"   Response: {response.text[:100]}")
            else:
                print(f"   Response: {response.text[:100] if response.text else 'No details'}")
                
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    # Also try without the nextToken parameter
    print("\n📍 Testing without nextToken parameter:")
    url_no_param = "https://advertising-api.amazon.com/amc/instances"
    
    try:
        response = requests.get(url_no_param, headers=headers_variations[0])
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Works without nextToken too!")
            data = response.json()
            if 'instances' in data:
                print(f"   Found {len(data['instances'])} instances")
                
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    return False

def main():
    print("AMC Instances API Test - Exact Postman Format")
    print("============================================")
    
    # Refresh token first
    access_token = refresh_token()
    if not access_token:
        print("\n❌ Failed to get valid token")
        return
    
    # Test with exact Postman format
    success = test_exact_postman_request(access_token)
    
    print("\n\n" + "="*60)
    print("📋 Summary")
    print("="*60)
    
    if success:
        print("\n✅ Successfully retrieved AMC instances!")
        print("\n📁 Check these files:")
        print("- amc_instances_success.json - Full response with instances")
        print("- working_headers.json - Headers that worked")
    else:
        print("\n❌ Could not retrieve instances")
        print("\n🔍 We need the exact headers from Postman:")
        print("1. In Postman, go to the Headers tab")
        print("2. Share all headers (you can redact token values)")
        print("3. Especially look for:")
        print("   - Amazon-Advertising-API-* headers")
        print("   - Any X-Amz-* headers")
        print("   - Profile or Scope headers")

if __name__ == "__main__":
    main()