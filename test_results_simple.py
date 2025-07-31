#!/usr/bin/env python3
"""Simple test to check execution results"""

import requests
import json

# Login
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute
workflow_id = 'wf_path_to_conversion_7cd2651c'
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json={'lookback_days': 30}, headers=headers)
execution = resp.json()
execution_id = execution['execution_id']
print(f'Execution ID: {execution_id}')

# Wait a bit for completion
import time
time.sleep(5)

# Get results
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                    headers=headers)

print(f'\nResults API Response:')
print(f'Status: {resp.status_code}')
print(f'Response: {json.dumps(resp.json(), indent=2)}')