#!/usr/bin/env python3
"""
Diagnostic script for schedule execution issues
Task 1.1: Analyze schedule problems
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def diagnose_schedule_issues():
    """Comprehensive diagnostic for schedule problems"""
    
    print("=" * 60)
    print("SCHEDULE DIAGNOSTIC REPORT")
    print(f"Generated: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    db = SupabaseManager.get_client()
    
    # 1. Check Recent Schedule Runs
    print("\n1. RECENT SCHEDULE RUNS (Last 24 hours)")
    print("-" * 40)
    
    one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
    
    recent_runs = db.table('schedule_runs').select(
        'schedule_id, run_number, scheduled_at, started_at, status, error_summary'
    ).gte('created_at', one_day_ago).order('created_at', desc=True).execute()
    
    if recent_runs.data:
        # Group by schedule to find duplicates
        schedule_groups = {}
        for run in recent_runs.data:
            sid = run['schedule_id']
            if sid not in schedule_groups:
                schedule_groups[sid] = []
            schedule_groups[sid].append(run)
        
        for sid, runs in schedule_groups.items():
            if len(runs) > 1:
                print(f"\n⚠️  Schedule {sid}: {len(runs)} runs in 24h")
                for run in runs[:5]:
                    print(f"   - Run #{run['run_number']}: {run['started_at']} - {run['status']}")
                    if run['error_summary']:
                        print(f"     Error: {run['error_summary'][:100]}")
            else:
                run = runs[0]
                print(f"\n✓ Schedule {sid}: 1 run - {run['status']}")
    else:
        print("No schedule runs in last 24 hours")
    
    # 2. Check Active Schedules State
    print("\n2. ACTIVE SCHEDULES STATE")
    print("-" * 40)
    
    active_schedules = db.table('workflow_schedules').select(
        'id, schedule_id, next_run_at, last_run_at, is_active, cron_expression'
    ).eq('is_active', True).execute()
    
    if active_schedules.data:
        now = datetime.utcnow()
        for schedule in active_schedules.data:
            next_run = None
            last_run = None
            
            if schedule['next_run_at']:
                next_run = datetime.fromisoformat(schedule['next_run_at'].replace('Z', '+00:00'))
                time_until = (next_run - now).total_seconds()
                
            if schedule['last_run_at']:
                last_run = datetime.fromisoformat(schedule['last_run_at'].replace('Z', '+00:00'))
                time_since = (now - last_run).total_seconds()
            
            print(f"\nSchedule: {schedule['schedule_id']}")
            print(f"  CRON: {schedule['cron_expression']}")
            
            if next_run:
                if time_until < -300:  # More than 5 minutes overdue
                    print(f"  ⚠️  OVERDUE: Should have run {abs(time_until/60):.1f} minutes ago")
                else:
                    print(f"  Next Run: In {time_until/60:.1f} minutes")
            
            if last_run:
                print(f"  Last Run: {time_since/60:.1f} minutes ago")
    else:
        print("No active schedules found")
    
    # 3. Check Instance Configuration
    print("\n3. AMC INSTANCE VERIFICATION")
    print("-" * 40)
    
    instances = db.table('amc_instances').select(
        'id, instance_id, instance_name'
    ).execute()
    
    if instances.data:
        for instance in instances.data:
            print(f"\nInstance: {instance['instance_name']}")
            print(f"  UUID: {instance['id']}")
            print(f"  AMC ID: {instance.get('instance_id', 'NULL OR MISSING!')}")
            
            if not instance.get('instance_id'):
                print(f"  ❌ CRITICAL: Missing AMC instance_id!")
            
            # Check workflows using this instance
            workflows = db.table('workflows').select('workflow_id, name').eq(
                'instance_id', instance['id']
            ).limit(3).execute()
            
            if workflows.data:
                print(f"  Workflows using this instance:")
                for wf in workflows.data:
                    print(f"    - {wf['workflow_id']}: {wf['name']}")
    else:
        print("No AMC instances configured")
    
    # 4. Check Recent Failed Executions
    print("\n4. RECENT FAILED EXECUTIONS (Last 6 hours)")
    print("-" * 40)
    
    six_hours_ago = (datetime.utcnow() - timedelta(hours=6)).isoformat()
    
    failed_executions = db.table('workflow_executions').select(
        'workflow_id, status, error_message, triggered_by, created_at'
    ).eq('status', 'failed').gte('created_at', six_hours_ago).execute()
    
    if failed_executions.data:
        # Group by trigger type
        manual_fails = []
        scheduled_fails = []
        
        for exec in failed_executions.data:
            if exec.get('triggered_by') == 'schedule':
                scheduled_fails.append(exec)
            else:
                manual_fails.append(exec)
        
        print(f"\nFailed Executions:")
        print(f"  Scheduled: {len(scheduled_fails)} failures")
        print(f"  Manual: {len(manual_fails)} failures")
        
        if scheduled_fails:
            print(f"\n  Recent Scheduled Failures:")
            for fail in scheduled_fails[:3]:
                print(f"    - {fail['created_at']}: {fail.get('error_message', 'No error message')[:100]}")
    else:
        print("No failed executions in last 6 hours")
    
    # 5. Check for Stuck Schedules
    print("\n5. STUCK SCHEDULE DETECTION")
    print("-" * 40)
    
    stuck_found = False
    for schedule in active_schedules.data if active_schedules.data else []:
        if schedule['next_run_at']:
            next_run = datetime.fromisoformat(schedule['next_run_at'].replace('Z', '+00:00'))
            overdue_by = (now - next_run).total_seconds()
            
            if overdue_by > 300:  # More than 5 minutes overdue
                stuck_found = True
                print(f"\n❌ STUCK: {schedule['schedule_id']}")
                print(f"  Overdue by: {overdue_by/60:.1f} minutes")
                print(f"  Next Run At: {schedule['next_run_at']}")
                
                # Check if there are recent runs preventing execution
                recent = db.table('schedule_runs').select('created_at').eq(
                    'schedule_id', schedule['id']
                ).gte('created_at', (now - timedelta(minutes=10)).isoformat()).execute()
                
                if recent.data:
                    print(f"  Recent runs found: {len(recent.data)} in last 10 minutes")
                    print(f"  🔧 Likely stuck due to deduplication logic")
    
    if not stuck_found:
        print("\n✓ No stuck schedules detected")
    
    # Summary and Recommendations
    print("\n" + "=" * 60)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 60)
    
    issues_found = []
    
    # Check for missing instance_ids
    missing_instance_ids = [i for i in instances.data if not i.get('instance_id')] if instances.data else []
    if missing_instance_ids:
        issues_found.append(f"❌ {len(missing_instance_ids)} instances missing AMC instance_id")
        print(f"\n1. CRITICAL: Missing AMC instance_ids")
        print(f"   Fix: Update amc_instances table with correct instance_id values")
    
    # Check for stuck schedules
    if stuck_found:
        issues_found.append("❌ Stuck schedules detected")
        print(f"\n2. Stuck schedules need reset")
        print(f"   Fix: Run script to reset next_run_at based on CRON")
    
    # Check for high failure rate
    if failed_executions.data and scheduled_fails:
        failure_rate = len(scheduled_fails) / len(failed_executions.data) * 100
        if failure_rate > 50:
            issues_found.append(f"❌ High scheduled failure rate: {failure_rate:.0f}%")
            print(f"\n3. High scheduled execution failure rate")
            print(f"   Fix: Check instance_id passing and parameter formatting")
    
    if not issues_found:
        print("\n✅ No critical issues detected")
    else:
        print(f"\n⚠️  Found {len(issues_found)} issues requiring attention")

if __name__ == "__main__":
    try:
        diagnose_schedule_issues()
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()