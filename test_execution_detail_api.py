#!/usr/bin/env python3
"""Test what the execution detail API returns"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Login
login_url = "http://localhost:8001/api/auth/login"
login_params = {"email": "nick@nevermeh.com"}

response = requests.post(login_url, params=login_params)
token = response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Use a known execution ID
execution_id = "exec_1807e240"

# Get execution detail (what the modal uses)
print("1. Testing /executions/{id}/detail endpoint:")
detail_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/detail"
response = requests.get(detail_url, headers=headers)

if response.status_code == 200:
    detail = response.json()
    print(f"✓ Detail endpoint returned: {list(detail.keys())}")
    
    # Check if result fields are in detail response
    result_fields = ['result_columns', 'result_rows', 'result_total_rows']
    for field in result_fields:
        if field in detail:
            print(f"  ✓ {field} is in detail response")
        else:
            print(f"  ✗ {field} is NOT in detail response")
else:
    print(f"✗ Failed: {response.status_code}")

# Get execution results (separate endpoint)
print("\n2. Testing /executions/{id}/results endpoint:")
results_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/results"
response = requests.get(results_url, headers=headers)

if response.status_code == 200:
    results = response.json()
    print(f"✓ Results endpoint returned:")
    print(f"  - Columns: {len(results.get('columns', []))}")
    print(f"  - Rows: {len(results.get('rows', []))}")
    print(f"  - Total rows: {results.get('total_rows', 0)}")
else:
    print(f"✗ Failed: {response.status_code}")