#!/usr/bin/env python3
"""
Execution Reconciliation Tool - Comprehensive utility to sync and fix execution discrepancies

This tool helps resolve common issues with execution tracking:
1. Updates missing AMC execution IDs
2. Syncs status between systems
3. Identifies and reports orphaned executions
4. Provides repair actions for common problems

Usage:
    python scripts/reconcile_executions.py --instance-id INSTANCE_ID --user-email EMAIL [--fix] [--dry-run]
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


class ExecutionReconciler:
    """Utility to reconcile and fix execution discrepancies"""
    
    def __init__(self, dry_run: bool = True):
        self.api_client = AMCAPIClient()
        self.db_client = SupabaseManager.get_client(use_service_role=True)
        self.dry_run = dry_run
        self.fixes_applied = []
        self.issues_found = []
    
    async def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email address"""
        try:
            response = self.db_client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    async def get_instance_executions(self, instance_id: str, user_id: str) -> Dict[str, Any]:
        """Get executions from both database and AMC for an instance"""
        
        # Get database executions
        db_executions = []
        try:
            # Get workflows for this instance
            workflows_response = self.db_client.table('workflows')\
                .select('id, workflow_id, name')\
                .eq('instance_id', instance_id)\
                .eq('user_id', user_id)\
                .execute()
            
            workflow_ids = [w['id'] for w in workflows_response.data]
            
            if workflow_ids:
                # Get recent executions (last 3 days)
                three_days_ago = datetime.utcnow() - timedelta(days=3)
                
                db_response = self.db_client.table('workflow_executions')\
                    .select('*, workflows!inner(workflow_id, name)')\
                    .in_('workflow_id', workflow_ids)\
                    .gte('started_at', three_days_ago.isoformat())\
                    .order('started_at', desc=True)\
                    .execute()
                
                db_executions = db_response.data
                
        except Exception as e:
            print(f"Error getting database executions: {e}")
        
        # Get AMC executions
        amc_executions = []
        try:
            # Get instance details
            instance = db_service.get_instance_details_sync(instance_id)
            if instance and instance.get('amc_accounts'):
                account = instance['amc_accounts']
                
                # Get valid token
                valid_token = await token_service.get_valid_token(user_id)
                if valid_token:
                    response = self.api_client.list_executions(
                        instance_id=instance_id,
                        access_token=valid_token,
                        entity_id=account['account_id'],
                        marketplace_id=account['marketplace_id'],
                        limit=100
                    )
                    
                    if response.get('success'):
                        amc_executions = response.get('executions', [])
                    
        except Exception as e:
            print(f"Error getting AMC executions: {e}")
        
        return {
            'database': db_executions,
            'amc': amc_executions,
            'instance_id': instance_id
        }
    
    def analyze_discrepancies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze discrepancies between database and AMC executions"""
        
        db_executions = data['database']
        amc_executions = data['amc']
        
        analysis = {
            'missing_amc_ids': [],
            'status_mismatches': [],
            'orphaned_amc': [],
            'orphaned_db': [],
            'repair_actions': []
        }
        
        # Create lookup maps
        amc_by_id = {}
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id:
                amc_by_id[exec_id] = amc_exec
        
        # Check database executions
        for db_exec in db_executions:
            internal_id = db_exec.get('execution_id')
            amc_exec_id = db_exec.get('amc_execution_id')
            db_status = db_exec.get('status', '').lower()
            
            if not amc_exec_id:
                # Missing AMC execution ID
                issue = {
                    'type': 'missing_amc_id',
                    'internal_id': internal_id,
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'status': db_status,
                    'started_at': db_exec.get('started_at'),
                    'severity': 'high' if db_status in ['pending', 'running'] else 'medium'
                }
                analysis['missing_amc_ids'].append(issue)
                
                if db_status in ['pending', 'running']:
                    analysis['repair_actions'].append({
                        'action': 'check_execution_logs',
                        'description': f'Check backend logs for execution {internal_id} to determine why AMC execution ID is missing',
                        'internal_id': internal_id
                    })
                elif db_status in ['completed', 'failed']:
                    analysis['repair_actions'].append({
                        'action': 'mark_as_legacy',
                        'description': f'Mark execution {internal_id} as legacy (completed without AMC tracking)',
                        'internal_id': internal_id
                    })
            
            elif amc_exec_id in amc_by_id:
                # Found matching AMC execution - check for status differences
                amc_exec = amc_by_id[amc_exec_id]
                amc_status = amc_exec.get('status', '').lower()
                
                # Map AMC status to our status
                status_map = {
                    'pending': 'pending',
                    'running': 'running', 
                    'succeeded': 'completed',
                    'failed': 'failed',
                    'cancelled': 'failed'
                }
                
                expected_db_status = status_map.get(amc_status, 'unknown')
                
                if db_status != expected_db_status and amc_status != 'unknown':
                    mismatch = {
                        'internal_id': internal_id,
                        'amc_id': amc_exec_id,
                        'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                        'db_status': db_status,
                        'amc_status': amc_status,
                        'expected_db_status': expected_db_status
                    }
                    analysis['status_mismatches'].append(mismatch)
                    
                    analysis['repair_actions'].append({
                        'action': 'sync_status',
                        'description': f'Update execution {internal_id} status from {db_status} to {expected_db_status}',
                        'internal_id': internal_id,
                        'new_status': expected_db_status
                    })
            
            else:
                # Database execution has AMC ID but AMC execution not found
                orphan = {
                    'internal_id': internal_id,
                    'amc_id': amc_exec_id,
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'status': db_status,
                    'started_at': db_exec.get('started_at')
                }
                analysis['orphaned_db'].append(orphan)
                
                analysis['repair_actions'].append({
                    'action': 'verify_amc_execution',
                    'description': f'Manually verify if AMC execution {amc_exec_id} exists but was not returned by API',
                    'amc_id': amc_exec_id
                })
        
        # Find AMC executions not in database
        db_amc_ids = {db_exec.get('amc_execution_id') for db_exec in db_executions if db_exec.get('amc_execution_id')}
        
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id and exec_id not in db_amc_ids:
                orphan = {
                    'amc_id': exec_id,
                    'workflow_id': amc_exec.get('workflowId'),
                    'status': amc_exec.get('status'),
                    'created_time': amc_exec.get('createdTime')
                }
                analysis['orphaned_amc'].append(orphan)
                
                analysis['repair_actions'].append({
                    'action': 'investigate_orphan',
                    'description': f'Investigate why AMC execution {exec_id} has no database record',
                    'amc_id': exec_id
                })
        
        return analysis
    
    async def apply_fixes(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply automatic fixes for common issues"""
        
        fixes_applied = []
        
        for action in analysis['repair_actions']:
            action_type = action['action']
            
            try:
                if action_type == 'sync_status':
                    # Update status in database
                    internal_id = action['internal_id']
                    new_status = action['new_status']
                    
                    if not self.dry_run:
                        # Get execution record
                        exec_response = self.db_client.table('workflow_executions')\
                            .select('id')\
                            .eq('execution_id', internal_id)\
                            .single()\
                            .execute()
                        
                        if exec_response.data:
                            exec_record_id = exec_response.data['id']
                            
                            # Update status
                            update_data = {'status': new_status}
                            if new_status in ['completed', 'failed']:
                                update_data['completed_at'] = datetime.utcnow().isoformat()
                                update_data['progress'] = 100
                            
                            self.db_client.table('workflow_executions')\
                                .update(update_data)\
                                .eq('id', exec_record_id)\
                                .execute()
                            
                            fixes_applied.append({
                                'action': action_type,
                                'internal_id': internal_id,
                                'old_status': 'unknown',
                                'new_status': new_status,
                                'applied': True
                            })
                    else:
                        fixes_applied.append({
                            'action': action_type,
                            'internal_id': internal_id,
                            'new_status': new_status,
                            'applied': False,
                            'dry_run': True
                        })
                
                elif action_type == 'mark_as_legacy':
                    # Mark completed executions without AMC IDs as legacy
                    internal_id = action['internal_id']
                    
                    if not self.dry_run:
                        exec_response = self.db_client.table('workflow_executions')\
                            .select('id')\
                            .eq('execution_id', internal_id)\
                            .single()\
                            .execute()
                        
                        if exec_response.data:
                            exec_record_id = exec_response.data['id']
                            
                            # Add legacy flag or comment
                            self.db_client.table('workflow_executions')\
                                .update({'error_message': 'Legacy execution - completed without AMC tracking'})\
                                .eq('id', exec_record_id)\
                                .execute()
                            
                            fixes_applied.append({
                                'action': action_type,
                                'internal_id': internal_id,
                                'applied': True
                            })
                    else:
                        fixes_applied.append({
                            'action': action_type,
                            'internal_id': internal_id,
                            'applied': False,
                            'dry_run': True
                        })
                        
            except Exception as e:
                fixes_applied.append({
                    'action': action_type,
                    'error': str(e),
                    'applied': False
                })
        
        return fixes_applied
    
    def print_analysis(self, analysis: Dict[str, Any], instance_id: str):
        """Print detailed analysis results"""
        
        print(f"\n{'='*80}")
        print(f"EXECUTION RECONCILIATION ANALYSIS")
        print(f"Instance: {instance_id}")
        print(f"{'='*80}")
        
        # Missing AMC IDs
        if analysis['missing_amc_ids']:
            print(f"\n🔴 MISSING AMC EXECUTION IDs ({len(analysis['missing_amc_ids'])} found):")
            for issue in analysis['missing_amc_ids']:
                severity_icon = "🔥" if issue['severity'] == 'high' else "⚠️"
                print(f"  {severity_icon} {issue['workflow_name']} ({issue['internal_id'][:8]}...)")
                print(f"     Status: {issue['status']} | Started: {issue['started_at']}")
        
        # Status Mismatches
        if analysis['status_mismatches']:
            print(f"\n🟡 STATUS MISMATCHES ({len(analysis['status_mismatches'])} found):")
            for mismatch in analysis['status_mismatches']:
                print(f"  • {mismatch['workflow_name']} ({mismatch['internal_id'][:8]}...)")
                print(f"    DB Status: {mismatch['db_status']} | AMC Status: {mismatch['amc_status']}")
                print(f"    Should be: {mismatch['expected_db_status']}")
        
        # Orphaned Database Executions
        if analysis['orphaned_db']:
            print(f"\n🟠 ORPHANED DATABASE EXECUTIONS ({len(analysis['orphaned_db'])} found):")
            for orphan in analysis['orphaned_db']:
                print(f"  • {orphan['workflow_name']} ({orphan['internal_id'][:8]}...)")
                print(f"    AMC ID: {orphan['amc_id']} | Status: {orphan['status']}")
        
        # Orphaned AMC Executions
        if analysis['orphaned_amc']:
            print(f"\n🔵 ORPHANED AMC EXECUTIONS ({len(analysis['orphaned_amc'])} found):")
            for orphan in analysis['orphaned_amc']:
                print(f"  • AMC ID: {orphan['amc_id']}")
                print(f"    Workflow: {orphan['workflow_id']} | Status: {orphan['status']}")
        
        # Repair Actions
        if analysis['repair_actions']:
            print(f"\n🔧 RECOMMENDED REPAIR ACTIONS ({len(analysis['repair_actions'])} actions):")
            for action in analysis['repair_actions']:
                print(f"  • {action['action'].replace('_', ' ').title()}")
                print(f"    {action['description']}")
        
        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY:")
        print(f"  Missing AMC IDs: {len(analysis['missing_amc_ids'])}")
        print(f"  Status Mismatches: {len(analysis['status_mismatches'])}")
        print(f"  Orphaned DB Executions: {len(analysis['orphaned_db'])}")
        print(f"  Orphaned AMC Executions: {len(analysis['orphaned_amc'])}")
        print(f"  Repair Actions Available: {len(analysis['repair_actions'])}")
        print(f"{'='*80}")
        
        if analysis['repair_actions']:
            print(f"\n💡 TIP: Run with --fix to automatically apply available repairs")
            print(f"        Run with --dry-run to preview changes before applying")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Reconcile execution discrepancies between systems')
    parser.add_argument('--instance-id', required=True, help='AMC instance ID to reconcile')
    parser.add_argument('--user-email', required=True, help='User email for authentication')
    parser.add_argument('--fix', action='store_true', help='Apply automatic fixes')
    parser.add_argument('--dry-run', action='store_true', help='Preview fixes without applying them')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Default to dry-run if --fix is not specified
    dry_run = not args.fix or args.dry_run
    
    reconciler = ExecutionReconciler(dry_run=dry_run)
    
    # Find user
    user = await reconciler.find_user_by_email(args.user_email)
    if not user:
        print(f"User with email {args.user_email} not found")
        sys.exit(1)
    
    print(f"🔍 Analyzing executions for instance {args.instance_id}...")
    
    # Get execution data from both systems
    data = await reconciler.get_instance_executions(args.instance_id, user['id'])
    
    print(f"Found {len(data['database'])} database executions and {len(data['amc'])} AMC executions")
    
    # Analyze discrepancies
    analysis = reconciler.analyze_discrepancies(data)
    
    # Apply fixes if requested
    fixes_applied = []
    if args.fix or args.dry_run:
        print(f"\n{'🔧 Applying fixes...' if not dry_run else '🔍 Previewing fixes...'}")
        fixes_applied = await reconciler.apply_fixes(analysis)
    
    # Output results
    if args.json:
        result = {
            'instance_id': args.instance_id,
            'analysis': analysis,
            'fixes_applied': fixes_applied,
            'summary': {
                'database_executions': len(data['database']),
                'amc_executions': len(data['amc']),
                'issues_found': (len(analysis['missing_amc_ids']) + 
                               len(analysis['status_mismatches']) + 
                               len(analysis['orphaned_db']) + 
                               len(analysis['orphaned_amc'])),
                'repairs_available': len(analysis['repair_actions']),
                'fixes_applied': len([f for f in fixes_applied if f.get('applied', False)])
            }
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        reconciler.print_analysis(analysis, args.instance_id)
        
        if fixes_applied:
            print(f"\n🔧 FIXES {'APPLIED' if not dry_run else 'PREVIEWED'}:")
            for fix in fixes_applied:
                status = "✅ Applied" if fix.get('applied') else "🔍 Dry Run" if fix.get('dry_run') else f"❌ Error: {fix.get('error', 'Unknown')}"
                print(f"  {fix['action']}: {status}")


if __name__ == "__main__":
    asyncio.run(main())