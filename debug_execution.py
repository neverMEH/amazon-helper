#!/usr/bin/env python3
"""Debug execution to see where results are lost"""

import requests
import json
import time

# Login
print("1. Logging in...")
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute a workflow
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 7}

print(f'\n2. Executing workflow {workflow_id}...')
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)

execution = resp.json()
execution_id = execution['execution_id']
print(f'Started execution: {execution_id}')

# Wait for completion
print('\n3. Waiting for completion...')
for i in range(10):
    resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/status', 
                        headers=headers)
    status = resp.json()
    print(f'  Status: {status["status"]} (Progress: {status.get("progress", 0)}%)')
    
    if status['status'] in ['completed', 'failed']:
        break
    time.sleep(1)

print('\n4. Checking database directly...')
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Get the execution from database
result = supabase.table('workflow_executions').select('*').eq('execution_id', execution_id).execute()
if result.data:
    exec_data = result.data[0]
    print(f'\nDatabase record for {execution_id}:')
    print(f'  Status: {exec_data["status"]}')
    print(f'  Row count: {exec_data["row_count"]}')
    print(f'  Result columns: {exec_data.get("result_columns")}')
    print(f'  Result rows: {exec_data.get("result_rows")}')
    print(f'  Result total rows: {exec_data.get("result_total_rows")}')
    print(f'  Query runtime: {exec_data.get("query_runtime_seconds")}')
    
    # Check if these fields have any non-null values
    result_fields = ['result_columns', 'result_rows', 'result_total_rows', 
                     'query_runtime_seconds', 'data_scanned_gb', 'cost_estimate_usd']
    
    non_null = [f for f in result_fields if exec_data.get(f) is not None]
    print(f'\n  Non-null result fields: {non_null}')

# Also check via API
print('\n5. Checking via API results endpoint...')
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                    headers=headers)
print(f'  API Status: {resp.status_code}')
if resp.status_code == 200:
    api_results = resp.json()
    print(f'  API Results: {json.dumps(api_results, indent=2)}')