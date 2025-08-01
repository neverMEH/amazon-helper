#!/usr/bin/env python3
"""Test API results endpoint"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Login first
login_url = "http://localhost:8001/api/auth/login"
login_params = {"email": "nick@nevermeh.com"}

response = requests.post(login_url, params=login_params)
if response.status_code != 200:
    print(f"Login failed: {response.status_code}")
    print(response.text)
    exit(1)

token = response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Get execution ID from the check
execution_id = "exec_1807e240"

# Test the results endpoint
results_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/results"
print(f"Testing: GET {results_url}")

response = requests.get(results_url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResults found:")
    print(f"- Columns: {len(data.get('columns', []))}")
    print(f"- Rows: {len(data.get('rows', []))}")
    print(f"- Total rows: {data.get('total_rows', 0)}")
    
    if data.get('columns'):
        print("\nColumn names:")
        for col in data['columns']:
            print(f"  - {col['name']} ({col['type']})")
    
    if data.get('rows') and len(data['rows']) > 0:
        print(f"\nFirst row: {data['rows'][0]}")
else:
    print(f"Error: {response.text}")