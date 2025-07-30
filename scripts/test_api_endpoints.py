#!/usr/bin/env python3
"""Test the API endpoints"""

import requests
import json

API_BASE = "http://localhost:8001"

def test_health():
    """Test health endpoints"""
    print("\n1. Testing health endpoints...")
    
    # Root endpoint
    response = requests.get(f"{API_BASE}/")
    print(f"   GET / - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
    
    # Health check
    response = requests.get(f"{API_BASE}/api/health")
    print(f"   GET /api/health - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")

def test_auth():
    """Test authentication"""
    print("\n2. Testing authentication...")
    
    # Login
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        params={"email": "nick@nevermeh.com"}
    )
    print(f"   POST /api/auth/login - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   User: {data['user']['email']}")
        print(f"   Token: {data['access_token'][:20]}...")
        return data['access_token']
    return None

def test_authenticated_endpoints(token):
    """Test endpoints that require authentication"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n3. Testing authenticated endpoints...")
    
    # Get current user
    response = requests.get(f"{API_BASE}/api/auth/me", headers=headers)
    print(f"   GET /api/auth/me - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   User: {response.json()}")
    
    # List instances
    response = requests.get(f"{API_BASE}/api/instances", headers=headers)
    print(f"\n   GET /api/instances - Status: {response.status_code}")
    if response.status_code == 200:
        instances = response.json()
        print(f"   Found {len(instances)} instances")
        if instances:
            print(f"   First instance: {instances[0]['instance_name']}")
    
    # List workflows
    response = requests.get(f"{API_BASE}/api/workflows", headers=headers)
    print(f"\n   GET /api/workflows - Status: {response.status_code}")
    if response.status_code == 200:
        workflows = response.json()
        print(f"   Found {len(workflows)} workflows")
    
    # List campaigns
    response = requests.get(f"{API_BASE}/api/campaigns", headers=headers)
    print(f"\n   GET /api/campaigns - Status: {response.status_code}")
    if response.status_code == 200:
        campaigns = response.json()
        print(f"   Found {len(campaigns)} campaigns")
    
    # List query templates
    response = requests.get(f"{API_BASE}/api/queries/templates", headers=headers)
    print(f"\n   GET /api/queries/templates - Status: {response.status_code}")
    if response.status_code == 200:
        templates = response.json()
        print(f"   Found {len(templates)} query templates")

def main():
    """Run all tests"""
    print("Testing AMC Manager API Endpoints")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test auth and get token
    token = test_auth()
    
    if token:
        # Test authenticated endpoints
        test_authenticated_endpoints(token)
    else:
        print("\n✗ Authentication failed, skipping authenticated endpoints")
    
    print("\n✅ API endpoint tests completed!")

if __name__ == "__main__":
    main()