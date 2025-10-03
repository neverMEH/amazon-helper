#!/usr/bin/env python3
"""
Test script for Instance Parameter Mapping API endpoints
Run this script to verify the mapping endpoints are working correctly
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8001/api"
AUTH_TOKEN = ""  # Set your JWT token here
INSTANCE_ID = ""  # Set your instance UUID here


def test_endpoint(name: str, method: str, url: str, data: Dict[str, Any] = None) -> None:
    """Test an API endpoint and print results"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"Method: {method}")
    print(f"URL: {url}")

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    if data:
        print(f"Payload: {json.dumps(data, indent=2)}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            print(f"Unsupported method: {method}")
            return

        print(f"\nStatus Code: {response.status_code}")

        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")

            # Store useful data for later tests
            if name == "Get Available Brands" and response.status_code == 200:
                if response_data.get('brands'):
                    global test_brand
                    test_brand = response_data['brands'][0]['brand_tag']
                    print(f"\n✓ Stored brand for testing: {test_brand}")

            elif name == "Get Brand ASINs" and response.status_code == 200:
                if response_data.get('asins'):
                    global test_asin
                    test_asin = response_data['asins'][0]['asin']
                    print(f"\n✓ Stored ASIN for testing: {test_asin}")

            elif name == "Get Brand Campaigns" and response.status_code == 200:
                if response_data.get('campaigns'):
                    global test_campaign
                    test_campaign = response_data['campaigns'][0]['campaign_id']
                    print(f"\n✓ Stored campaign for testing: {test_campaign}")

        except json.JSONDecodeError:
            print(f"Response (text): {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR: {e}")


def main():
    global test_brand, test_asin, test_campaign

    # Validate configuration
    if not AUTH_TOKEN:
        print("ERROR: Please set AUTH_TOKEN in the script")
        print("You can get a token by logging into the app and checking localStorage.getItem('token')")
        sys.exit(1)

    if not INSTANCE_ID:
        print("ERROR: Please set INSTANCE_ID in the script")
        print("You can get an instance ID from the instances page URL")
        sys.exit(1)

    print("="*60)
    print("Instance Parameter Mapping API Test Suite")
    print("="*60)
    print(f"API Base: {API_BASE}")
    print(f"Instance ID: {INSTANCE_ID}")
    print("="*60)

    # Test 1: Get Available Brands
    test_endpoint(
        name="Get Available Brands",
        method="GET",
        url=f"{API_BASE}/instances/{INSTANCE_ID}/available-brands"
    )

    # Test 2: Get Current Mappings
    test_endpoint(
        name="Get Current Mappings",
        method="GET",
        url=f"{API_BASE}/instances/{INSTANCE_ID}/mappings"
    )

    # Test 3: Get Brand ASINs (if we have a brand)
    if 'test_brand' in globals():
        test_endpoint(
            name="Get Brand ASINs",
            method="GET",
            url=f"{API_BASE}/instances/{INSTANCE_ID}/brands/{test_brand}/asins?limit=5"
        )

        # Test 4: Get Brand Campaigns
        test_endpoint(
            name="Get Brand Campaigns",
            method="GET",
            url=f"{API_BASE}/instances/{INSTANCE_ID}/brands/{test_brand}/campaigns?limit=5"
        )

        # Test 5: Save Mappings (if we have data)
        if 'test_asin' in globals() or 'test_campaign' in globals():
            payload = {
                "brands": [test_brand],
                "asins_by_brand": {},
                "campaigns_by_brand": {}
            }

            if 'test_asin' in globals():
                payload["asins_by_brand"][test_brand] = [test_asin]

            if 'test_campaign' in globals():
                payload["campaigns_by_brand"][test_brand] = [test_campaign]

            test_endpoint(
                name="Save Mappings",
                method="POST",
                url=f"{API_BASE}/instances/{INSTANCE_ID}/mappings",
                data=payload
            )

            # Test 6: Get Parameter Values
            test_endpoint(
                name="Get Parameter Values",
                method="GET",
                url=f"{API_BASE}/instances/{INSTANCE_ID}/parameter-values"
            )

    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)


if __name__ == "__main__":
    main()
