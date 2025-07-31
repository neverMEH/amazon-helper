#!/usr/bin/env python3
"""Test execution detail functionality"""

import requests
import json
import time

# Login
print("1. Logging in...")
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute a workflow to create a test execution
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 7, 'brand': 'TestBrand'}

print(f'\n2. Creating test execution...')
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)

if resp.status_code != 200:
    print(f'Error: {resp.text}')
    exit(1)

execution = resp.json()
execution_id = execution['execution_id']
print(f'Created execution: {execution_id}')

# Wait for completion
print('\n3. Waiting for completion...')
time.sleep(5)

# Get execution detail
print('\n4. Fetching execution detail...')
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/detail', 
                    headers=headers)

if resp.status_code != 200:
    print(f'Error: {resp.text}')
    exit(1)

detail = resp.json()
print(f'\nExecution Detail:')
print(f'  Execution ID: {detail["execution_id"]}')
print(f'  Workflow: {detail.get("workflow_name", "Unknown")}')
print(f'  Status: {detail["status"]}')
print(f'  Progress: {detail["progress"]}%')
print(f'  Started: {detail.get("started_at", "N/A")}')
print(f'  Completed: {detail.get("completed_at", "N/A")}')
print(f'  Duration: {detail.get("duration_seconds", "N/A")}s')
print(f'  Rows: {detail.get("row_count", 0)}')
print(f'  Triggered By: {detail["triggered_by"]}')

if detail.get('execution_parameters'):
    print(f'\n  Parameters:')
    for key, value in detail['execution_parameters'].items():
        print(f'    {key}: {value}')

if detail.get('error_message'):
    print(f'\n  Error: {detail["error_message"]}')

if detail.get('output_location'):
    print(f'\n  Output Location: {detail["output_location"]}')
    if detail.get('size_bytes'):
        print(f'  Size: {detail["size_bytes"] / 1024:.2f} KB')

print('\n✓ Execution detail functionality is working!')
print('\nIn the UI, you can now:')
print('1. Go to any workflow detail page')
print('2. Click on the "Executions" tab')
print('3. Click on any execution row to see full details')
print('4. View parameters, results, and download CSV')