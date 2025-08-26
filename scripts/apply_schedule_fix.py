#!/usr/bin/env python
"""
Apply the schedule execution fix to prevent multiple runs

This script:
1. Backs up the current schedule executor service
2. Replaces it with the fixed version
3. Restarts the services
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

def main():
    """Apply the schedule execution fix"""
    
    print("=" * 60)
    print("SCHEDULE EXECUTION FIX - Preventing Multiple Runs")
    print("=" * 60)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "amc_manager" / "services"
    original_file = services_dir / "schedule_executor_service.py"
    fixed_file = services_dir / "schedule_executor_service_fixed.py"
    backup_file = services_dir / f"schedule_executor_service_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    print(f"\n📁 Project root: {project_root}")
    print(f"📁 Services directory: {services_dir}")
    
    # Check if fixed file exists
    if not fixed_file.exists():
        print(f"\n❌ Fixed file not found: {fixed_file}")
        print("Please ensure schedule_executor_service_fixed.py exists")
        return 1
    
    # Step 1: Backup current file
    print(f"\n1. Backing up current file...")
    print(f"   From: {original_file}")
    print(f"   To: {backup_file}")
    
    try:
        shutil.copy2(original_file, backup_file)
        print(f"   ✅ Backup created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create backup: {e}")
        return 1
    
    # Step 2: Replace with fixed version
    print(f"\n2. Applying fixed version...")
    print(f"   From: {fixed_file}")
    print(f"   To: {original_file}")
    
    try:
        shutil.copy2(fixed_file, original_file)
        print(f"   ✅ Fixed version applied successfully")
    except Exception as e:
        print(f"   ❌ Failed to apply fix: {e}")
        print(f"   Restoring from backup...")
        shutil.copy2(backup_file, original_file)
        return 1
    
    # Step 3: Provide restart instructions
    print(f"\n3. Next steps:")
    print(f"   ⚠️  You need to restart the backend services for changes to take effect")
    print(f"   ")
    print(f"   Option A - Full restart (recommended):")
    print(f"   1. Stop services: Ctrl+C in the terminal running start_services.sh")
    print(f"   2. Restart: ./start_services.sh")
    print(f"   ")
    print(f"   Option B - Backend only:")
    print(f"   1. Stop backend: Ctrl+C in the terminal running main_supabase.py")
    print(f"   2. Restart: python main_supabase.py")
    
    # Step 4: Summary of changes
    print(f"\n📝 Summary of Changes Applied:")
    print(f"   ✅ Atomic schedule claiming with optimistic locking")
    print(f"   ✅ Reduced buffer window from 2 minutes to 30 seconds")
    print(f"   ✅ Double-check on last_run_at and schedule_runs table")
    print(f"   ✅ API error retry logic (max 3 attempts)")
    print(f"   ✅ Proper distributed locking for concurrent processes")
    
    print(f"\n🔍 Testing the Fix:")
    print(f"   1. Schedule a test workflow to run in 1-2 minutes")
    print(f"   2. Monitor the logs: tail -f server.log | grep schedule")
    print(f"   3. Check schedule_runs table for single execution")
    print(f"   4. Verify only one workflow_execution is created")
    
    print(f"\n✅ Fix applied successfully!")
    print(f"💾 Backup saved as: {backup_file.name}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())