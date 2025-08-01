#!/usr/bin/env python3
"""Test script to simulate workflow execution and verify toLocaleString fixes"""

import requests
import json
import time

def test_workflow_execution():
    base_url = "http://localhost:8001/api"
    
    # Login first
    resp = requests.post(f"{base_url}/auth/login?email=nick@nevermeh.com")
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get workflows
    resp = requests.get(f"{base_url}/workflows", headers=headers)
    workflows_data = resp.json()
    workflows = workflows_data.get('workflows', workflows_data if isinstance(workflows_data, list) else [])
    if not workflows:
        print("No workflows found")
        return
    
    workflow = workflows[0]
    print(f"Testing with workflow: {workflow['name']} ({workflow['workflowId']})")
    
    # Get instances
    resp = requests.get(f"{base_url}/instances", headers=headers)
    instances = resp.json()
    if not instances:
        print("No instances found")
        return
    
    # Find a production instance
    prod_instance = next((i for i in instances if 'SANDBOX' not in i['instance_name']), instances[0])
    print(f"Using instance: {prod_instance['instance_name']} ({prod_instance['instance_id']})")
    
    # Execute workflow with parameters that might have null values
    execution_data = {
        "workflow_id": workflow["workflowId"],
        "instance_id": prod_instance["instance_id"],
        "execution_parameters": {
            "startDate": "2024-01-01",
            "endDate": "2024-01-07",
            "granularity": "DAILY"
        }
    }
    
    print("\nExecuting workflow...")
    resp = requests.post(
        f"{base_url}/workflows/{workflow['workflowId']}/execute",
        headers=headers,
        json=execution_data
    )
    
    if resp.status_code != 200:
        print(f"Execution failed: {resp.text}")
        return
    
    execution = resp.json()
    execution_id = execution["execution_id"]
    print(f"Execution started: {execution_id}")
    
    # Poll for status (this is where toLocaleString errors might occur)
    print("\nPolling for status...")
    for i in range(10):
        time.sleep(2)
        
        resp = requests.get(
            f"{base_url}/workflows/executions/{execution_id}/status",
            headers=headers
        )
        status = resp.json()
        print(f"Status: {status['status']} (progress: {status.get('progress', 0)}%)")
        
        # Check if row_count is null - this was causing toLocaleString errors
        if 'row_count' in status and status['row_count'] is None:
            print("  - row_count is null (this previously caused toLocaleString error)")
        
        if status['status'] in ['completed', 'failed']:
            print(f"\nExecution finished with status: {status['status']}")
            
            if status['status'] == 'completed':
                # Try to get results
                resp = requests.get(
                    f"{base_url}/workflows/executions/{execution_id}/results",
                    headers=headers
                )
                if resp.status_code == 200:
                    results = resp.json()
                    print(f"Results retrieved: {results.get('total_rows', 0)} rows")
                    
                    # Check for null values that might cause toLocaleString errors
                    if results.get('total_rows') is None:
                        print("  - total_rows is null (this previously caused toLocaleString error)")
                    
                    details = results.get('execution_details', {})
                    for key in ['query_runtime_seconds', 'data_scanned_gb', 'cost_estimate_usd']:
                        if key in details and details[key] is None:
                            print(f"  - {key} is null (this previously caused toLocaleString error)")
            
            if status.get('error_message'):
                print(f"Error: {status['error_message']}")
            
            break
    
    # Get execution detail
    print("\nGetting execution details...")
    resp = requests.get(
        f"{base_url}/workflows/executions/{execution_id}/detail",
        headers=headers
    )
    if resp.status_code == 200:
        detail = resp.json()
        print("Execution detail retrieved successfully")
        
        # Check for null values
        for key in ['row_count', 'duration_seconds', 'size_bytes']:
            if key in detail and detail[key] is None:
                print(f"  - {key} is null (this previously caused toLocaleString error)")
    
    print("\nTest completed - no JavaScript errors should appear in the browser console")
    print("\nIMPORTANT: Please check the browser console at http://localhost:5173")
    print("Navigate to an instance detail view and click on the Executions tab")
    print("Then execute a workflow and watch for any toLocaleString errors")

if __name__ == "__main__":
    test_workflow_execution()