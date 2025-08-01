#!/usr/bin/env python3
"""Test the complete workflow creation and execution flow"""

import requests
import json
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8001/api"

# Test credentials
EMAIL = "nick@nevermeh.com"
PASSWORD = "123456"

def login():
    """Login and get access token"""
    response = requests.post(f"{BASE_URL}/auth/login", params={
        "email": EMAIL,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return None
        
    data = response.json()
    return data["access_token"]

def get_instances(token):
    """Get user's AMC instances"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/instances", headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to get instances: {response.status_code}")
        print(response.json())
        return []
        
    return response.json()

def create_workflow(token, instance_id):
    """Create a test workflow"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Calculate dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    workflow_data = {
        "name": f"Test DSP Performance Report {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Test workflow to analyze DSP campaign performance",
        "instance_id": instance_id,
        "sql_query": """-- DSP Campaign Performance Analysis
SELECT 
    campaign_id,
    campaign_name,
    advertiser_id,
    COUNT(DISTINCT user_id) as unique_reach,
    COUNT(*) as total_impressions,
    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as total_clicks,
    SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as total_conversions,
    ROUND(SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as ctr_percent,
    ROUND(SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as cvr_percent
FROM dsp_impressions
WHERE impression_dt >= '{{start_date}}' 
  AND impression_dt <= '{{end_date}}'
GROUP BY campaign_id, campaign_name, advertiser_id
HAVING COUNT(DISTINCT user_id) >= 10  -- AMC privacy threshold
ORDER BY total_impressions DESC""",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date
        },
        "tags": ["dsp", "performance", "test"]
    }
    
    url = f"{BASE_URL}/workflows"  # Remove trailing slash
    print(f"  POST to: {url}")
    print(f"  Headers: {headers}")
    print(f"  Data: {json.dumps(workflow_data, indent=2)[:200]}...")
    response = requests.post(url, json=workflow_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to create workflow: {response.status_code}")
        print(response.json())
        return None
        
    return response.json()

def list_workflows(token):
    """List all workflows"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/workflows", headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to list workflows: {response.status_code}")
        print(response.json())
        return []
        
    return response.json()

def execute_workflow(token, workflow_id, instance_id=None):
    """Execute a workflow"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Calculate dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    execution_data = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    if instance_id:
        execution_data["instance_id"] = instance_id
    
    response = requests.post(
        f"{BASE_URL}/workflows/{workflow_id}/execute", 
        json=execution_data, 
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Failed to execute workflow: {response.status_code}")
        print(response.json())
        return None
        
    return response.json()

def check_execution_status(token, execution_id):
    """Check execution status"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/workflows/executions/{execution_id}/status", 
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Failed to get execution status: {response.status_code}")
        print(response.json())
        return None
        
    return response.json()

def main():
    print("Testing workflow creation and execution flow...")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1. Logging in...")
    token = login()
    if not token:
        print("Login failed!")
        return
    print(f"✓ Login successful. Token: {token[:20]}...")
    
    # Step 2: Get instances
    print("\n2. Getting AMC instances...")
    instances = get_instances(token)
    if not instances:
        print("No instances found!")
        return
    
    print(f"✓ Found {len(instances)} instances:")
    for inst in instances[:3]:  # Show first 3
        print(f"  - {inst['instanceName']} ({inst['instanceId']}) - {inst['accountName']} - Active: {inst.get('isActive', 'N/A')}")
    
    # Use the first active instance
    active_instances = [i for i in instances if i.get('isActive', False)]
    if not active_instances:
        print("No active instances found!")
        return
        
    test_instance = active_instances[0]
    instance_id = test_instance['instanceId']  # Use external instance ID for workflow creation
    
    print(f"\n✓ Using instance: {test_instance['instanceName']} (ID: {instance_id})")
    
    # Step 3: Create workflow
    print("\n3. Creating test workflow...")
    workflow = create_workflow(token, instance_id)
    if not workflow:
        print("Failed to create workflow!")
        return
        
    workflow_id = workflow['workflow_id']
    print(f"✓ Created workflow: {workflow['name']} (ID: {workflow_id})")
    
    # Step 4: List workflows
    print("\n4. Listing workflows...")
    workflows = list_workflows(token)
    print(f"✓ Found {len(workflows)} workflows")
    
    # Find our created workflow
    our_workflow = next((w for w in workflows if w['workflowId'] == workflow_id), None)
    if our_workflow:
        print(f"✓ Found our workflow in the list: {our_workflow['name']}")
    else:
        print("✗ Our workflow not found in the list!")
    
    # Step 5: Execute workflow
    print("\n5. Executing workflow...")
    execution = execute_workflow(token, workflow_id)
    if not execution:
        print("Failed to execute workflow!")
        return
        
    execution_id = execution['execution_id']
    print(f"✓ Started execution: {execution_id}")
    
    # Step 6: Check execution status
    print("\n6. Checking execution status...")
    max_retries = 30  # Check for up to 60 seconds
    retry_count = 0
    
    while retry_count < max_retries:
        status = check_execution_status(token, execution_id)
        if not status:
            print("Failed to get status!")
            break
            
        print(f"  Status: {status['status']} (Progress: {status.get('progress', 0)}%)")
        
        if status['status'] in ['completed', 'failed']:
            if status['status'] == 'completed':
                print(f"✓ Execution completed successfully!")
                if status.get('row_count'):
                    print(f"  Rows returned: {status['row_count']}")
            else:
                print(f"✗ Execution failed: {status.get('error_message', 'Unknown error')}")
            break
            
        time.sleep(2)
        retry_count += 1
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()