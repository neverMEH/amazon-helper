#!/usr/bin/env python3
"""Test workflow execution with status polling and result download"""

import requests
import json
import time

# Login
print("1. Logging in...")
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Execute workflow
workflow_id = 'wf_path_to_conversion_7cd2651c'
params = {'lookback_days': 30}

print(f'\n2. Executing workflow {workflow_id}...')
resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                     json=params, headers=headers)

if resp.status_code != 200:
    print(f'Error: {resp.text}')
    exit(1)

execution = resp.json()
execution_id = execution['execution_id']
print(f'Started execution: {execution_id}')

# Poll for status
print('\n3. Polling for status...')
while True:
    resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/status', 
                        headers=headers)
    
    if resp.status_code != 200:
        print(f'Error getting status: {resp.text}')
        break
        
    status = resp.json()
    print(f'Status: {status["status"]} (Progress: {status.get("progress", 0)}%)')
    
    if status['status'] == 'completed':
        print(f'✓ Execution completed successfully!')
        print(f'  - Rows: {status.get("row_count", 0)}')
        duration = status.get("duration_seconds")
        if duration:
            print(f'  - Duration: {duration:.2f}s')
        break
    elif status['status'] == 'failed':
        print(f'✗ Execution failed!')
        print(f'  - Error: {status.get("error_message", "Unknown error")}')
        exit(1)
    
    time.sleep(2)

# Get results
print('\n4. Fetching results...')
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                    headers=headers)

if resp.status_code != 200:
    print(f'Error getting results: {resp.text}')
    exit(1)

results = resp.json()
print(f'Retrieved {results["total_rows"]} rows')

# Display sample results
if results['rows']:
    print('\n5. Sample results:')
    print('Columns:', [col['name'] for col in results['columns']])
    print('\nFirst 3 rows:')
    for i, row in enumerate(results['rows'][:3]):
        print(f'Row {i+1}:', row)

# Show execution details
if 'execution_details' in results:
    print('\n6. Execution details:')
    details = results['execution_details']
    print(f'  - Query runtime: {details.get("query_runtime_seconds", 0)}s')
    print(f'  - Data scanned: {details.get("data_scanned_gb", 0)} GB')
    print(f'  - Cost estimate: ${details.get("cost_estimate_usd", 0):.4f}')

# Convert to CSV
print('\n7. Converting to CSV...')
headers_csv = ','.join([col['name'] for col in results['columns']])
rows_csv = []
for row in results['rows']:
    row_str = []
    for cell in row:
        if isinstance(cell, str) and ',' in cell:
            row_str.append(f'"{cell}"')
        else:
            row_str.append(str(cell))
    rows_csv.append(','.join(row_str))

csv_content = headers_csv + '\n' + '\n'.join(rows_csv)

# Save to file
filename = f'results_{execution_id}.csv'
with open(filename, 'w') as f:
    f.write(csv_content)

print(f'✓ Results saved to {filename}')
print(f'\nTotal rows in CSV: {len(results["rows"])}')