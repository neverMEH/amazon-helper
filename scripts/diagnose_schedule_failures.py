#!/usr/bin/env python
"""Diagnose schedule execution failures"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta, timezone
from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.token_service import TokenService
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_failures():
    """Diagnose why schedule executions are failing"""
    db = SupabaseManager().get_client()
    token_service = TokenService()
    
    # Get the schedule
    schedule_result = db.table('workflow_schedules').select(
        '*',
        'workflows(*, amc_instances(*))'
    ).eq('schedule_id', 'sched_11c9ad39fe5f').single().execute()
    
    if not schedule_result.data:
        print("Schedule not found")
        return
    
    schedule = schedule_result.data
    workflow = schedule['workflows']
    instance = workflow.get('amc_instances', {}) if workflow else {}
    
    print("\n=== Schedule Details ===")
    print(f"Schedule ID: {schedule['schedule_id']}")
    print(f"Schedule Name: {schedule.get('name', 'N/A')}")
    print(f"Active: {schedule['is_active']}")
    print(f"User ID: {schedule['user_id']}")
    
    print("\n=== Workflow Details ===")
    print(f"Workflow ID: {workflow['id']}")
    print(f"Workflow Name: {workflow['workflow_id']}")
    print(f"AMC Workflow ID: {workflow.get('amc_workflow_id', 'Not synced')}")
    
    print("\n=== Instance Details ===")
    print(f"Instance UUID: {instance['id']}")
    print(f"Instance Name: {instance['instance_name']}")
    print(f"Instance ID (AMC): {instance.get('instance_id', 'MISSING!')}")
    print(f"Entity ID: {instance.get('entity_id', 'MISSING!')}")
    
    # Check user tokens
    user_id = schedule['user_id']
    print(f"\n=== Token Check for User {user_id} ===")
    
    user_result = db.table('users').select('*').eq('id', user_id).single().execute()
    if not user_result.data:
        print("ERROR: User not found!")
        return
    
    user = user_result.data
    
    # Check token validity
    try:
        access_token = await token_service.get_valid_access_token(user_id)
        if access_token:
            print("✓ Valid access token available")
        else:
            print("✗ No valid access token!")
    except Exception as e:
        print(f"✗ Token error: {e}")
    
    # Get recent failed runs
    print("\n=== Recent Failed Runs ===")
    failed_runs = db.table('schedule_runs').select(
        '*'
    ).eq('schedule_id', schedule['id']).eq('status', 'failed').order('started_at', desc=True).limit(5).execute()
    
    for run in failed_runs.data:
        print(f"\nRun #{run['run_number']} at {run['started_at']}")
        print(f"  Status: {run['status']}")
        print(f"  Error: {run.get('error_message', 'No error message')}")
        print(f"  Execution ID: {run.get('workflow_execution_id', 'None')}")
        
        # Check if there's a workflow execution record
        if run.get('workflow_execution_id'):
            exec_result = db.table('workflow_executions').select(
                'id,amc_execution_id,status,error_message,created_at'
            ).eq('id', run['workflow_execution_id']).single().execute()
            
            if exec_result.data:
                exec_data = exec_result.data
                print(f"  Execution Status: {exec_data['status']}")
                print(f"  AMC Execution ID: {exec_data.get('amc_execution_id', 'None')}")
                print(f"  Execution Error: {exec_data.get('error_message', 'None')}")
    
    # Test actual API call
    print("\n=== Testing AMC API Connection ===")
    try:
        # Get valid token
        access_token = await token_service.get_valid_access_token(user_id)
        if not access_token:
            print("✗ Cannot test API - no valid token")
            return
        
        # Test API call
        amc_instance_id = instance.get('instance_id')
        entity_id = instance.get('entity_id')
        
        if not amc_instance_id or not entity_id:
            print(f"✗ Missing required IDs: instance_id={amc_instance_id}, entity_id={entity_id}")
            return
        
        print(f"Testing API with instance_id={amc_instance_id}, entity_id={entity_id}")
        
        # Try to list workflows
        result = await amc_api_client_with_retry.list_workflows(
            instance_id=amc_instance_id,
            user_id=user_id,
            entity_id=entity_id
        )
        
        if result:
            print(f"✓ API connection successful - Found {len(result.get('workflows', []))} workflows")
        else:
            print("✗ API returned empty result")
            
    except Exception as e:
        print(f"✗ API test failed: {e}")
    
    # Check if AMC workflow exists
    if workflow.get('amc_workflow_id'):
        print(f"\n=== Checking AMC Workflow {workflow['amc_workflow_id']} ===")
        try:
            result = await amc_api_client_with_retry.get_workflow_details(
                instance_id=amc_instance_id,
                workflow_id=workflow['amc_workflow_id'],
                user_id=user_id,
                entity_id=entity_id
            )
            if result:
                print(f"✓ AMC workflow exists: {result.get('workflowId')}")
            else:
                print("✗ AMC workflow not found")
        except Exception as e:
            print(f"✗ Error checking workflow: {e}")
    else:
        print("\n⚠ Workflow not synced to AMC yet")

if __name__ == "__main__":
    asyncio.run(diagnose_failures())