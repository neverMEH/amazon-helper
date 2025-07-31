#!/usr/bin/env python3
"""Test real AMC execution"""

import os
import requests
import json

# Enable real AMC API
os.environ['AMC_USE_REAL_API'] = 'true'

print("🚀 Testing Real AMC Execution")
print("="*50)

# Login
print("\n1. Logging in...")
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})

if resp.status_code != 200:
    print(f"❌ Login failed: {resp.text}")
    exit(1)

token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}
print("✓ Logged in successfully")

# Check if user has Amazon token
print("\n2. Checking Amazon OAuth token...")
# This would be checked server-side during execution

# Execute a simple workflow
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 7}

print(f'\n3. Executing workflow {workflow_id} with REAL AMC API...')
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)

if resp.status_code != 200:
    print(f'❌ Execution failed: {resp.text}')
    exit(1)

execution = resp.json()
execution_id = execution['execution_id']
print(f'✓ Started execution: {execution_id}')

# Check status
print('\n4. Monitoring execution status...')
import time

for i in range(30):  # Check for up to 5 minutes
    resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/status', 
                        headers=headers)
    
    if resp.status_code == 200:
        status = resp.json()
        print(f'   Status: {status["status"]} (Progress: {status.get("progress", 0)}%)')
        
        if status['status'] == 'completed':
            print('\n✅ Execution completed successfully!')
            print(f'   Rows: {status.get("row_count", 0)}')
            break
        elif status['status'] == 'failed':
            print(f'\n❌ Execution failed: {status.get("error_message", "Unknown error")}')
            break
    
    time.sleep(10)  # Wait 10 seconds between checks

# Get results
print('\n5. Fetching results...')
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                    headers=headers)

if resp.status_code == 200:
    results = resp.json()
    print(f'✓ Retrieved {results["total_rows"]} rows')
    
    if results['columns']:
        print('\nColumns:', [col['name'] for col in results['columns']])
    
    if results['execution_details']:
        print('\nExecution Details:')
        details = results['execution_details']
        print(f'  Runtime: {details.get("query_runtime_seconds")}s')
        print(f'  Data Scanned: {details.get("data_scanned_gb")} GB')
        print(f'  Cost: ${details.get("cost_estimate_usd", 0):.4f}')

print('\n' + '='*50)
print('🎉 Real AMC execution test complete!')
print('\nNOTE: If execution failed with "No valid Amazon OAuth token"')
print('      the user needs to authenticate with Amazon first.')