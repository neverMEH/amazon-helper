#!/usr/bin/env python3
"""Test workflow execution"""

import requests
import json

# Login
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Try to execute a workflow
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 30}

print(f'Executing workflow {workflow_id}...')
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)

print(f'Status: {resp.status_code}')
if resp.status_code != 200:
    print(f'Error: {resp.text}')
else:
    print(f'Success: {resp.json()}')