#!/usr/bin/env python3
"""Demo: Workflow execution with success and failure scenarios"""

import requests
import json
import time

def execute_and_monitor(workflow_id, params, headers):
    """Execute a workflow and monitor its progress"""
    print(f'\nExecuting workflow {workflow_id} with params: {params}')
    
    # Execute
    resp = requests.post(f'http://localhost:8001/api/workflows/{workflow_id}/execute', 
                         json=params, headers=headers)
    
    if resp.status_code != 200:
        print(f'Failed to start execution: {resp.text}')
        return None
        
    execution = resp.json()
    execution_id = execution['execution_id']
    print(f'Started execution: {execution_id}')
    
    # Poll for completion
    for i in range(10):  # Max 10 attempts
        resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/status', 
                            headers=headers)
        
        if resp.status_code != 200:
            print(f'Error getting status: {resp.text}')
            return None
            
        status = resp.json()
        print(f'  Status: {status["status"]} (Progress: {status.get("progress", 0)}%)')
        
        if status['status'] == 'completed':
            print(f'  ✓ Success! Rows: {status.get("row_count", 0)}')
            return execution_id
        elif status['status'] == 'failed':
            print(f'  ✗ Failed: {status.get("error_message", "Unknown error")}')
            return None
            
        time.sleep(2)
    
    print('  Timeout waiting for completion')
    return None

# Login
print("Logging in...")
resp = requests.post('http://localhost:8001/api/auth/login', 
                     params={'email': 'nick@nevermeh.com', 'password': ''})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Scenario 1: Successful execution
print("\n=== Scenario 1: Successful Execution ===")
execution_id = execute_and_monitor(
    'wf_path_to_conversion_7cd2651c',
    {'lookback_days': 30},
    headers
)

if execution_id:
    # Get and display results
    resp = requests.get(f'http://localhost:8001/api/workflows/executions/{execution_id}/results', 
                        headers=headers)
    if resp.status_code == 200:
        results = resp.json()
        print(f'\nResults preview:')
        if results['rows']:
            print(f'  Columns: {[col["name"] for col in results["columns"]]}')
            print(f'  First row: {results["rows"][0]}')
            print(f'  Total rows: {results["total_rows"]}')
            
            # Save as CSV
            headers_csv = ','.join([col['name'] for col in results['columns']])
            filename = f'demo_results_{execution_id}.csv'
            with open(filename, 'w') as f:
                f.write(headers_csv + '\n')
                for row in results['rows'][:5]:  # Just first 5 rows for demo
                    f.write(','.join(str(cell) for cell in row) + '\n')
            print(f'  Sample saved to: {filename}')

# Note: To demonstrate failure scenario, you would need to:
# 1. Create a workflow with invalid SQL
# 2. Or pass parameters that cause the query to fail
# 3. The error message would appear in the status response

print("\n=== How to handle failures ===")
print("1. Check the error_message in the status response")
print("2. Common errors:")
print("   - Missing required parameters")
print("   - Invalid SQL syntax")
print("   - Instance access denied")
print("3. Fix the issue in the workflow SQL or parameters")
print("4. Re-execute the workflow")

print("\n=== Execution Complete ===")