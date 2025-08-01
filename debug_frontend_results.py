#!/usr/bin/env python3
"""Debug frontend results issue"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Login
login_url = "http://localhost:8001/api/auth/login"
login_params = {"email": "nick@nevermeh.com"}

print("1. Logging in...")
response = requests.post(login_url, params=login_params)
if response.status_code != 200:
    print(f"Login failed: {response.status_code}")
    exit(1)

token = response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in successfully")

# Get a workflow
print("\n2. Getting a workflow...")
workflows_url = "http://localhost:8001/api/workflows"
response = requests.get(workflows_url, headers=headers)
workflows = response.json()

if not workflows or not isinstance(workflows, list):
    print(f"No workflows found or unexpected response: {workflows}")
    exit(1)

workflow = workflows[0]
print(f"✓ Using workflow: {workflow['name']} ({workflow['workflow_id']})")

# Execute it
print("\n3. Executing workflow...")
execute_url = f"http://localhost:8001/api/workflows/{workflow['workflow_id']}/execute"
execute_data = {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}
response = requests.post(execute_url, json=execute_data, headers=headers)
if response.status_code != 200:
    print(f"Execution failed: {response.status_code}")
    print(response.text)
    exit(1)

execution = response.json()
execution_id = execution['execution_id']
print(f"✓ Execution started: {execution_id}")

# Poll for completion
print("\n4. Waiting for completion...")
status_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/status"
for i in range(30):
    response = requests.get(status_url, headers=headers)
    status = response.json()
    print(f"  Status: {status['status']} (progress: {status['progress']}%)")
    
    if status['status'] in ['completed', 'failed']:
        break
    time.sleep(1)

if status['status'] != 'completed':
    print("✗ Execution did not complete successfully")
    exit(1)

print("✓ Execution completed")

# Get details
print("\n5. Getting execution details...")
detail_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/detail"
response = requests.get(detail_url, headers=headers)
details = response.json()
print(f"✓ Details retrieved: {list(details.keys())}")

# Get results
print("\n6. Getting execution results...")
results_url = f"http://localhost:8001/api/workflows/executions/{execution_id}/results"
response = requests.get(results_url, headers=headers)
if response.status_code == 200:
    results = response.json()
    print(f"✓ Results retrieved:")
    print(f"  - Columns: {len(results.get('columns', []))}")
    print(f"  - Rows: {len(results.get('rows', []))}")
    print(f"  - Total rows: {results.get('total_rows', 0)}")
else:
    print(f"✗ Failed to get results: {response.status_code}")
    print(response.text)

print("\n7. Summary:")
print(f"  - Execution ID: {execution_id}")
print(f"  - Use this in the UI to check if results show")
print(f"  - Direct results URL: http://localhost:8001/api/workflows/executions/{execution_id}/results")