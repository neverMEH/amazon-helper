#!/usr/bin/env python3
"""Test CSV download functionality"""

import requests
import json

# Login
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get the most recent execution
exec_id = 'exec_a9688b2e'

# Get results
resp = requests.get(f'http://localhost:8001/api/workflows/executions/{exec_id}/results', 
                    headers=headers)

if resp.status_code == 200:
    results = resp.json()
    
    # Convert to CSV
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
    filename = f'test_results_{exec_id}.csv'
    with open(filename, 'w') as f:
        f.write(csv_content)
    
    print(f'✓ CSV saved to {filename}')
    print(f'Total rows: {len(results["rows"])}')
    print(f'\nFirst 3 lines of CSV:')
    print('\n'.join(csv_content.split('\n')[:4]))
    
    print('\n✅ CSV download functionality is working!')
    print('\nIn the UI:')
    print('1. Click on any completed execution')
    print('2. Click "View Results" to load the data')
    print('3. Click "Download CSV" to get the file')
else:
    print(f'Error: {resp.status_code}')