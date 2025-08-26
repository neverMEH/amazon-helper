#!/usr/bin/env python3
"""
Database state verification for schedule issues
Task 1.2: Verify database integrity
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager

def verify_database_state():
    """Verify database integrity for scheduling system"""
    
    print("=" * 60)
    print("DATABASE STATE VERIFICATION")
    print(f"Generated: {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    db = SupabaseManager.get_client()
    issues = []
    
    # 1. Check AMC Instances Table
    print("\n1. AMC INSTANCES TABLE CHECK")
    print("-" * 40)
    
    instances = db.table('amc_instances').select('*').execute()
    
    if instances.data:
        for instance in instances.data:
            print(f"\nInstance: {instance.get('instance_name', 'UNNAMED')}")
            print(f"  ID (UUID): {instance['id']}")
            print(f"  Instance ID (AMC): {instance.get('instance_id', 'NULL!')}")
            print(f"  Region: {instance.get('region', 'NULL')}")
            
            # Critical checks
            if not instance.get('instance_id'):
                issues.append(f"Instance {instance['id']} missing instance_id")
                print(f"  ❌ MISSING AMC INSTANCE_ID!")
            elif not instance['instance_id'].startswith('amc'):
                issues.append(f"Instance {instance['id']} has invalid instance_id format")
                print(f"  ⚠️  Unusual instance_id format (expected to start with 'amc')")
    else:
        print("❌ No instances found in database!")
        issues.append("No AMC instances configured")
    
    # 2. Check Workflows Table
    print("\n2. WORKFLOWS TABLE CHECK")
    print("-" * 40)
    
    workflows = db.table('workflows').select(
        'id, workflow_id, name, instance_id, user_id'
    ).limit(10).execute()
    
    if workflows.data:
        orphaned_workflows = []
        for workflow in workflows.data:
            # Check if instance_id references a valid instance
            if workflow.get('instance_id'):
                valid = any(i['id'] == workflow['instance_id'] for i in (instances.data or []))
                if not valid:
                    orphaned_workflows.append(workflow['workflow_id'])
                    print(f"\n⚠️  Workflow {workflow['workflow_id']} references non-existent instance")
            else:
                print(f"\n❌ Workflow {workflow['workflow_id']} has NULL instance_id")
                issues.append(f"Workflow {workflow['workflow_id']} missing instance_id")
        
        if orphaned_workflows:
            issues.append(f"{len(orphaned_workflows)} workflows reference non-existent instances")
        
        print(f"\nTotal workflows checked: {len(workflows.data)}")
        print(f"Orphaned workflows: {len(orphaned_workflows)}")
    
    # 3. Check Workflow Schedules Table
    print("\n3. WORKFLOW SCHEDULES TABLE CHECK")
    print("-" * 40)
    
    schedules = db.table('workflow_schedules').select(
        'id, schedule_id, workflow_id, next_run_at, last_run_at, is_active, user_id'
    ).execute()
    
    if schedules.data:
        active_count = sum(1 for s in schedules.data if s.get('is_active'))
        print(f"\nTotal schedules: {len(schedules.data)}")
        print(f"Active schedules: {active_count}")
        
        # Check for issues
        for schedule in schedules.data:
            if schedule.get('is_active'):
                # Check if workflow exists
                wf_exists = any(w['id'] == schedule.get('workflow_id') for w in (workflows.data or []))
                if not wf_exists:
                    print(f"\n❌ Schedule {schedule['schedule_id']} references non-existent workflow")
                    issues.append(f"Schedule {schedule['schedule_id']} has invalid workflow_id")
                
                # Check next_run_at
                if not schedule.get('next_run_at'):
                    print(f"\n❌ Active schedule {schedule['schedule_id']} has NULL next_run_at")
                    issues.append(f"Schedule {schedule['schedule_id']} missing next_run_at")
    
    # 4. Check Schedule Runs Table
    print("\n4. SCHEDULE RUNS TABLE CHECK")
    print("-" * 40)
    
    # Get recent schedule runs
    recent_runs = db.table('schedule_runs').select(
        'schedule_id, run_number, status, created_at'
    ).order('created_at', desc=True).limit(20).execute()
    
    if recent_runs.data:
        # Check for duplicate runs
        from collections import defaultdict
        run_times = defaultdict(list)
        
        for run in recent_runs.data:
            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            run_times[run['schedule_id']].append(created)
        
        for schedule_id, times in run_times.items():
            if len(times) > 1:
                # Check for runs within 1 minute of each other
                times.sort()
                for i in range(len(times) - 1):
                    diff = (times[i] - times[i+1]).total_seconds()
                    if abs(diff) < 60:
                        print(f"\n⚠️  Schedule {schedule_id} has runs within 1 minute")
                        issues.append(f"Schedule {schedule_id} possible duplicate executions")
    
    # 5. Check Workflow Executions Table
    print("\n5. WORKFLOW EXECUTIONS TABLE CHECK")
    print("-" * 40)
    
    # Check for missing relationships
    executions = db.table('workflow_executions').select(
        'id, workflow_id, instance_id, status, triggered_by'
    ).order('created_at', desc=True).limit(20).execute()
    
    if executions.data:
        triggered_by_counts = {}
        for exec in executions.data:
            trigger = exec.get('triggered_by', 'unknown')
            triggered_by_counts[trigger] = triggered_by_counts.get(trigger, 0) + 1
        
        print("\nExecution trigger types:")
        for trigger, count in triggered_by_counts.items():
            print(f"  {trigger}: {count}")
        
        # Check for missing instance_id
        missing_instance = [e for e in executions.data if not e.get('instance_id')]
        if missing_instance:
            print(f"\n⚠️  {len(missing_instance)} executions missing instance_id")
            issues.append(f"{len(missing_instance)} executions without instance_id")
    
    # Summary
    print("\n" + "=" * 60)
    print("DATABASE INTEGRITY SUMMARY")
    print("=" * 60)
    
    if issues:
        print(f"\n❌ Found {len(issues)} database integrity issues:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\nRECOMMENDED FIXES:")
        print("1. Update amc_instances table with correct instance_id values")
        print("2. Fix orphaned workflow references")
        print("3. Reset stuck schedule next_run_at values")
        print("4. Add missing foreign key constraints")
    else:
        print("\n✅ No database integrity issues found")
    
    return issues

if __name__ == "__main__":
    try:
        issues = verify_database_state()
        sys.exit(0 if not issues else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)