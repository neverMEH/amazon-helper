#!/usr/bin/env python3
"""Test AMC instances with nextToken parameter"""

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

def test_with_pagination(access_token):
    """Test instances endpoint with nextToken parameter"""
    
    print("🔍 Testing AMC Instances with nextToken Parameter")
    print("="*60)
    
    # Possible base URLs
    base_urls = [
        'https://advertising-api.amazon.com',
        'https://amc-api.amazon.com',  # Possible dedicated AMC domain
        'https://advertising-api-na.amazon.com',  # Regional endpoint
        'https://advertising-api-eu.amazon.com',
        'https://api.advertising.amazon.com',
    ]
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': os.getenv('AMAZON_CLIENT_ID'),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Test each base URL
    for base_url in base_urls:
        print(f"\n📍 Testing base URL: {base_url}")
        
        # Try with empty nextToken (initial request)
        url = f"{base_url}/amc/instances?nextToken="
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS! Base URL is: {base_url}")
                
                if 'instances' in data:
                    print(f"   Found {len(data['instances'])} instances")
                    
                    # Save the working configuration
                    config = {
                        'api_url': base_url,
                        'endpoint': '/amc/instances',
                        'headers_used': list(headers.keys()),
                        'supports_pagination': 'nextToken' in data
                    }
                    
                    with open('working_amc_config.json', 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    with open('amc_instances_response.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    display_instances(data.get('instances', []))
                    
                    # Check for pagination
                    if 'nextToken' in data and data['nextToken']:
                        print(f"\n   📄 More results available. NextToken: {data['nextToken'][:20]}...")
                    
                    return base_url
                    
            elif response.status_code == 404:
                print(f"   Not found at this URL")
            elif response.status_code == 401:
                print(f"   Unauthorized - might be correct URL but token issue")
            else:
                print(f"   Response: {response.text[:100] if response.text else 'No details'}")
                
        except requests.exceptions.Timeout:
            print(f"   Timeout - URL might not exist")
        except requests.exceptions.ConnectionError:
            print(f"   Connection error - URL might not exist")
        except Exception as e:
            print(f"   Error: {str(e)[:50]}")
    
    # Also test without nextToken parameter
    print("\n\n📍 Testing without nextToken parameter:")
    url = "https://advertising-api.amazon.com/amc/instances"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Works without nextToken too!")
            if 'instances' in data:
                print(f"Found {len(data['instances'])} instances")
        else:
            print(f"Response: {response.text[:100] if response.text else 'No details'}")
            
    except Exception as e:
        print(f"Error: {str(e)[:50]}")

def display_instances(instances):
    """Display instances based on Postman structure"""
    if not instances:
        print("   No instances to display")
        return
        
    print("\n   📊 AMC Instances:")
    for idx, instance in enumerate(instances[:3]):  # Show first 3
        print(f"\n   Instance {idx + 1}:")
        print(f"     Instance ID: {instance.get('instanceId', 'N/A')}")
        print(f"     Instance Name: {instance.get('instanceName', 'N/A')}")
        print(f"     Instance Type: {instance.get('instanceType', 'N/A')}")
        print(f"     Customer: {instance.get('customerCanonicalName', 'N/A')}")
        print(f"     Status: {instance.get('creationStatus', 'N/A')}")
        print(f"     Created: {instance.get('creationDatetime', 'N/A')}")
        print(f"     S3 Bucket: {instance.get('s3BucketName', 'N/A')}")
        print(f"     API Endpoint: {instance.get('apiEndpoint', 'N/A')}")
        
        # Show entities if present
        entities = instance.get('entities', [])
        if entities:
            if isinstance(entities, list):
                print(f"     Entities: {', '.join(entities[:3])}{'...' if len(entities) > 3 else ''}")
            else:
                print(f"     Entities: {entities}")

def main():
    print("AMC Instances API Test with Pagination")
    print("=====================================")
    print("Testing with nextToken parameter as shown in Postman\n")
    
    # Load tokens
    tokens = load_tokens()
    if not tokens:
        print("❌ No tokens found")
        return
        
    access_token = tokens.get('access_token')
    if not access_token:
        print("❌ No access token found")
        return
    
    # Test with pagination
    working_url = test_with_pagination(access_token)
    
    print("\n\n" + "="*60)
    print("📋 Summary")
    print("="*60)
    
    if working_url:
        print(f"\n✅ Found working base URL: {working_url}")
        print("\n💡 Next steps:")
        print("1. Check 'working_amc_config.json' for the configuration")
        print("2. Check 'amc_instances_response.json' for the full response")
        print("3. Update the application to use the correct base URL")
    else:
        print("\n❓ Still need the exact base URL from Postman")
        print("\nIn Postman:")
        print("1. Check Environments → Look for 'api_url' variable")
        print("2. Or hover over {{api_url}} in the request")
        print("3. Or click 'Code' → 'cURL' to see the full request")

if __name__ == "__main__":
    main()