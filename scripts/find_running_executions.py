#!/usr/bin/env python3
"""
Script to find running executions across both internal database and AMC console.

This helps identify executions that are:
1. Running in your app but not visible in AMC console yet
2. Running in AMC console but not tracked in your database
3. Stuck in pending status
4. Missing AMC execution IDs

Usage:
    python scripts/find_running_executions.py [--instance-id INSTANCE_ID] [--user-email EMAIL]
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add the project root to the path
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.services.amc_api_client import AMCAPIClient
from amc_manager.services.token_service import token_service
from amc_manager.services.db_service import db_service


class ExecutionFinder:
    """Utility to find and cross-reference executions between systems"""
    
    def __init__(self):
        self.api_client = AMCAPIClient()
        self.db_client = SupabaseManager.get_client(use_service_role=True)
    
    async def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email address"""
        try:
            response = self.db_client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    def get_database_executions(self, user_id: str = None, instance_id: str = None) -> List[Dict[str, Any]]:
        """Get executions from internal database"""
        try:
            query = self.db_client.table('workflow_executions')\
                .select('*, workflows!inner(user_id, instance_id, name, amc_instances!inner(instance_id, instance_name))')
            
            if user_id:
                query = query.eq('workflows.user_id', user_id)
            
            if instance_id:
                query = query.eq('workflows.amc_instances.instance_id', instance_id)
            
            # Only get recent executions (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            query = query.gte('started_at', yesterday.isoformat())
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error getting database executions: {e}")
            return []
    
    async def get_amc_executions(self, instance_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get executions from AMC API"""
        try:
            # Get instance details
            instance = db_service.get_instance_details_sync(instance_id)
            if not instance:
                print(f"Instance {instance_id} not found")
                return []
            
            # Get valid token
            valid_token = await token_service.get_valid_token(user_id)
            if not valid_token:
                print(f"No valid token for user {user_id}")
                return []
            
            # Get AMC account details
            account = instance.get('amc_accounts')
            if not account:
                print(f"No AMC account found for instance {instance_id}")
                return []
            
            entity_id = account['account_id']
            marketplace_id = account['marketplace_id']
            
            # List recent executions from AMC
            response = self.api_client.list_executions(
                instance_id=instance_id,
                access_token=valid_token,
                entity_id=entity_id,
                marketplace_id=marketplace_id,
                limit=50
            )
            
            if response.get('success'):
                return response.get('executions', [])
            else:
                print(f"Failed to get AMC executions: {response.get('error')}")
                return []
                
        except Exception as e:
            print(f"Error getting AMC executions: {e}")
            return []
    
    def cross_reference_executions(self, db_executions: List[Dict], amc_executions: List[Dict]) -> Dict[str, Any]:
        """Cross-reference executions between systems"""
        
        # Create lookup maps
        db_by_amc_id = {}
        amc_by_id = {}
        
        for db_exec in db_executions:
            amc_exec_id = db_exec.get('amc_execution_id')
            if amc_exec_id:
                db_by_amc_id[amc_exec_id] = db_exec
        
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id:
                amc_by_id[exec_id] = amc_exec
        
        # Find discrepancies
        results = {
            'matched_executions': [],
            'db_only_executions': [],
            'amc_only_executions': [],
            'running_in_db': [],
            'running_in_amc': [],
            'missing_amc_ids': []
        }
        
        # Check database executions
        for db_exec in db_executions:
            amc_exec_id = db_exec.get('amc_execution_id')
            
            if not amc_exec_id:
                # Execution missing AMC ID
                results['missing_amc_ids'].append({
                    'internal_id': db_exec.get('execution_id'),
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'status': db_exec.get('status'),
                    'started_at': db_exec.get('started_at'),
                    'instance_id': db_exec.get('workflows', {}).get('amc_instances', {}).get('instance_id')
                })
            elif amc_exec_id in amc_by_id:
                # Matched execution
                amc_exec = amc_by_id[amc_exec_id]
                results['matched_executions'].append({
                    'internal_id': db_exec.get('execution_id'),
                    'amc_id': amc_exec_id,
                    'db_status': db_exec.get('status'),
                    'amc_status': amc_exec.get('status'),
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'started_at': db_exec.get('started_at')
                })
            else:
                # In database but not found in AMC
                results['db_only_executions'].append({
                    'internal_id': db_exec.get('execution_id'),
                    'amc_id': amc_exec_id,
                    'status': db_exec.get('status'),
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'started_at': db_exec.get('started_at')
                })
            
            # Check for running status in database
            if db_exec.get('status') in ['pending', 'running']:
                results['running_in_db'].append({
                    'internal_id': db_exec.get('execution_id'),
                    'amc_id': amc_exec_id,
                    'status': db_exec.get('status'),
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'started_at': db_exec.get('started_at'),
                    'progress': db_exec.get('progress', 0)
                })
        
        # Check AMC executions not in database
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id and exec_id not in db_by_amc_id:
                results['amc_only_executions'].append({
                    'amc_id': exec_id,
                    'status': amc_exec.get('status'),
                    'workflow_id': amc_exec.get('workflowId'),
                    'created_time': amc_exec.get('createdTime'),
                    'started_time': amc_exec.get('startTime')
                })
            
            # Check for running status in AMC
            if amc_exec.get('status') in ['PENDING', 'RUNNING']:
                results['running_in_amc'].append({
                    'amc_id': exec_id,
                    'status': amc_exec.get('status'),
                    'workflow_id': amc_exec.get('workflowId'),
                    'created_time': amc_exec.get('createdTime'),
                    'started_time': amc_exec.get('startTime')
                })
        
        return results
    
    def print_results(self, results: Dict[str, Any], instance_id: str = None):
        """Print formatted results"""
        print(f"\n{'='*60}")
        print(f"EXECUTION FINDER RESULTS")
        if instance_id:
            print(f"Instance: {instance_id}")
        print(f"{'='*60}")
        
        # Running executions in database
        if results['running_in_db']:
            print(f"\n🔄 RUNNING IN YOUR DATABASE ({len(results['running_in_db'])} found):")
            for exec in results['running_in_db']:
                print(f"  • Internal ID: {exec['internal_id']}")
                print(f"    AMC ID: {exec['amc_id'] or 'MISSING'}")
                print(f"    Workflow: {exec['workflow_name']}")
                print(f"    Status: {exec['status']} ({exec['progress']}%)")
                print(f"    Started: {exec['started_at']}")
                print()
        
        # Running executions in AMC
        if results['running_in_amc']:
            print(f"\n🔄 RUNNING IN AMC CONSOLE ({len(results['running_in_amc'])} found):")
            for exec in results['running_in_amc']:
                print(f"  • AMC ID: {exec['amc_id']}")
                print(f"    Status: {exec['status']}")
                print(f"    Workflow ID: {exec['workflow_id']}")
                print(f"    Started: {exec['started_time']}")
                print()
        
        # Missing AMC IDs
        if results['missing_amc_ids']:
            print(f"\n⚠️  EXECUTIONS MISSING AMC IDs ({len(results['missing_amc_ids'])} found):")
            for exec in results['missing_amc_ids']:
                print(f"  • Internal ID: {exec['internal_id']}")
                print(f"    Workflow: {exec['workflow_name']}")
                print(f"    Status: {exec['status']}")
                print(f"    Started: {exec['started_at']}")
                print()
        
        # Database only executions
        if results['db_only_executions']:
            print(f"\n🔍 IN DATABASE BUT NOT IN AMC ({len(results['db_only_executions'])} found):")
            for exec in results['db_only_executions']:
                print(f"  • Internal ID: {exec['internal_id']}")
                print(f"    AMC ID: {exec['amc_id']}")
                print(f"    Workflow: {exec['workflow_name']}")
                print(f"    Status: {exec['status']}")
                print()
        
        # AMC only executions
        if results['amc_only_executions']:
            print(f"\n🔍 IN AMC BUT NOT IN DATABASE ({len(results['amc_only_executions'])} found):")
            for exec in results['amc_only_executions']:
                print(f"  • AMC ID: {exec['amc_id']}")
                print(f"    Status: {exec['status']}")
                print(f"    Workflow ID: {exec['workflow_id']}")
                print()
        
        # Matched executions
        if results['matched_executions']:
            print(f"\n✅ PROPERLY MATCHED EXECUTIONS ({len(results['matched_executions'])} found):")
            for exec in results['matched_executions']:
                print(f"  • {exec['workflow_name']} - DB: {exec['db_status']}, AMC: {exec['amc_status']}")
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print(f"  Running in Database: {len(results['running_in_db'])}")
        print(f"  Running in AMC: {len(results['running_in_amc'])}")
        print(f"  Missing AMC IDs: {len(results['missing_amc_ids'])}")
        print(f"  Database Only: {len(results['db_only_executions'])}")
        print(f"  AMC Only: {len(results['amc_only_executions'])}")
        print(f"  Properly Matched: {len(results['matched_executions'])}")
        print(f"{'='*60}")
        
        # Recommendations
        if results['running_in_db'] and not results['running_in_amc']:
            print("\n💡 RECOMMENDATION:")
            print("  Your executions are running in the database but may not be visible")
            print("  in AMC console yet. Wait 1-2 minutes and check AMC console again.")
        
        if results['missing_amc_ids']:
            print("\n⚠️  WARNING:")
            print("  Some executions are missing AMC execution IDs. This usually means")
            print("  the AMC API call failed or there was an error during execution creation.")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Find running executions across systems')
    parser.add_argument('--instance-id', help='Specific AMC instance ID to check')
    parser.add_argument('--user-email', help='User email to check executions for')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    finder = ExecutionFinder()
    
    # Get user if email provided
    user = None
    if args.user_email:
        user = await finder.find_user_by_email(args.user_email)
        if not user:
            print(f"User with email {args.user_email} not found")
            sys.exit(1)
    
    user_id = user['id'] if user else None
    
    # Get database executions
    print("🔍 Fetching executions from database...")
    db_executions = finder.get_database_executions(user_id, args.instance_id)
    
    if args.instance_id:
        # Get AMC executions for specific instance
        print(f"🔍 Fetching executions from AMC for instance {args.instance_id}...")
        if not user_id:
            print("Error: --user-email is required when checking AMC executions")
            sys.exit(1)
        
        amc_executions = await finder.get_amc_executions(args.instance_id, user_id)
        
        # Cross-reference
        results = finder.cross_reference_executions(db_executions, amc_executions)
        
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            finder.print_results(results, args.instance_id)
    else:
        # Just show database results
        if args.json:
            print(json.dumps(db_executions, indent=2, default=str))
        else:
            running_executions = [
                exec for exec in db_executions 
                if exec.get('status') in ['pending', 'running']
            ]
            
            print(f"\n🔄 RUNNING EXECUTIONS IN DATABASE ({len(running_executions)} found):")
            for exec in running_executions:
                workflow = exec.get('workflows', {})
                instance_info = workflow.get('amc_instances', {})
                
                print(f"  • Internal ID: {exec.get('execution_id')}")
                print(f"    AMC ID: {exec.get('amc_execution_id') or 'MISSING'}")
                print(f"    Workflow: {workflow.get('name', 'Unknown')}")
                print(f"    Instance: {instance_info.get('instance_name', 'Unknown')} ({instance_info.get('instance_id', 'Unknown')})")
                print(f"    Status: {exec.get('status')} ({exec.get('progress', 0)}%)")
                print(f"    Started: {exec.get('started_at')}")
                print()
            
            if not running_executions:
                print("  No running executions found in database.")


if __name__ == "__main__":
    asyncio.run(main())