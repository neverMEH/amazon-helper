#!/usr/bin/env python
"""
Fix for test run schedules getting stuck in a loop

The issue: Test runs set next_run_at to 1 minute from now, 
but after execution the schedule remains "due" and gets stuck.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from croniter import croniter
from zoneinfo import ZoneInfo

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def fix_stuck_schedules():
    """Find and fix schedules stuck after test runs"""
    
    db = SupabaseManager.get_client()
    
    print("Checking for stuck schedules...")
    
    # Get all active schedules
    schedules = db.table('workflow_schedules').select(
        'id', 'schedule_id', 'next_run_at', 'cron_expression', 'timezone', 'is_active'
    ).eq('is_active', True).execute()
    
    if not schedules.data:
        print("No active schedules found")
        return
    
    fixed_count = 0
    now = datetime.utcnow()
    
    for schedule in schedules.data:
        next_run_at = schedule.get('next_run_at')
        if not next_run_at:
            continue
            
        # Parse the next_run_at
        try:
            next_run_time = datetime.fromisoformat(next_run_at.replace('Z', '+00:00'))
        except:
            continue
        
        # Check if next_run_at is in the past (more than 5 minutes ago)
        time_since_due = (now - next_run_time).total_seconds()
        
        if time_since_due > 300:  # More than 5 minutes overdue
            print(f"\nFound stuck schedule: {schedule['schedule_id']}")
            print(f"  Was due: {next_run_at} ({time_since_due/60:.1f} minutes ago)")
            
            # Calculate proper next run based on cron expression
            cron_expr = schedule.get('cron_expression', '0 2 * * *')
            tz_name = schedule.get('timezone', 'America/New_York')
            
            try:
                cron = croniter(cron_expr)
                tz = ZoneInfo(tz_name)
                tz_now = datetime.now(tz)
                cron.set_current(tz_now)
                next_run = cron.get_next(datetime)
                
                # Update the schedule
                result = db.table('workflow_schedules').update({
                    'next_run_at': next_run.isoformat()
                }).eq('id', schedule['id']).execute()
                
                if result.data:
                    print(f"  ✅ Fixed! Next run: {next_run.isoformat()}")
                    fixed_count += 1
                else:
                    print(f"  ❌ Failed to update")
                    
            except Exception as e:
                print(f"  ❌ Error calculating next run: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: Fixed {fixed_count} stuck schedules")
    
    if fixed_count > 0:
        print("\n⚠️  The schedule executor service needs to be updated to handle test runs properly.")
        print("The atomic claiming fix is working, but test runs need special handling.")

def check_recent_test_runs():
    """Check for recent test runs that might be causing issues"""
    
    db = SupabaseManager.get_client()
    
    print("\nChecking recent test runs...")
    
    # Get test runs from the last hour
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    
    recent_runs = db.table('schedule_runs').select(
        'id', 'schedule_id', 'scheduled_at', 'status', 'created_at'
    ).gte('created_at', one_hour_ago).order('created_at', desc=True).execute()
    
    if recent_runs.data:
        print(f"Found {len(recent_runs.data)} runs in the last hour")
        
        # Group by schedule_id to find duplicates
        schedule_runs = {}
        for run in recent_runs.data:
            sid = run['schedule_id']
            if sid not in schedule_runs:
                schedule_runs[sid] = []
            schedule_runs[sid].append(run)
        
        for sid, runs in schedule_runs.items():
            if len(runs) > 1:
                print(f"\nSchedule {sid}: {len(runs)} runs")
                for run in runs[:5]:  # Show first 5
                    print(f"  - {run['created_at']}: {run['status']}")

if __name__ == "__main__":
    fix_stuck_schedules()
    check_recent_test_runs()