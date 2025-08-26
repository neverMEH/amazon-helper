#!/usr/bin/env python3
"""
Compare manual vs scheduled execution paths
Task 1.3: Document execution flow differences
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def compare_execution_paths():
    """Compare manual vs scheduled execution paths"""
    
    print("=" * 60)
    print("EXECUTION PATH COMPARISON")
    print("Manual vs Scheduled Workflows")
    print("=" * 60)
    
    # Document the execution flows
    manual_flow = """
    MANUAL EXECUTION FLOW:
    1. User clicks Execute in UI
    2. Frontend calls: POST /api/workflows/{workflow_id}/execute
       - Sends: { instance_id: "amcXXXXX", ...parameters }
       - instance_id is AMC ID directly from frontend
    3. API endpoint (workflows.py):
       - Gets workflow by workflow_id
       - Verifies user ownership
       - Calls amc_execution_service.execute_workflow()
    4. AMC Execution Service:
       - Receives instance_id (AMC ID) directly
       - Creates AMC workflow if needed
       - Executes with provided parameters
    """
    
    scheduled_flow = """
    SCHEDULED EXECUTION FLOW:
    1. Schedule Executor polls every 60 seconds
    2. Finds due schedules (next_run_at < now + buffer)
    3. Attempts atomic claim on schedule
    4. Gets workflow from schedule.workflows relationship
    5. Gets instance_id from workflow (UUID, not AMC ID!)
    6. Queries amc_instances by UUID: 
       - SELECT * FROM amc_instances WHERE id = {UUID}
    7. Extracts instance['instance_id'] (should be AMC ID)
    8. Calls amc_execution_service.execute_workflow()
       - Passes instance['instance_id'] as instance_id param
    """
    
    print("\n" + "=" * 60)
    print(manual_flow)
    print("\n" + "=" * 60)
    print(scheduled_flow)
    
    print("\n" + "=" * 60)
    print("KEY DIFFERENCES IDENTIFIED")
    print("=" * 60)
    
    differences = """
    1. INSTANCE ID SOURCE:
       ✅ Manual: Frontend provides AMC ID directly (e.g., "amcibersblt")
       ❌ Scheduled: Must lookup UUID → AMC ID conversion
    
    2. PARAMETER STRUCTURE:
       ✅ Manual: Parameters come from UI form
       ❌ Scheduled: Parameters calculated with date logic
    
    3. TOKEN MANAGEMENT:
       ✅ Manual: User's current session token
       ❌ Scheduled: Must refresh token before execution
    
    4. ERROR HANDLING:
       ✅ Manual: Immediate UI feedback
       ❌ Scheduled: Must log and update schedule_runs table
    
    5. CRITICAL ISSUE:
       The scheduled execution depends on:
       - workflow.instance_id (UUID) existing
       - amc_instances.instance_id (AMC ID) being populated
       - Correct field extraction from database
    
    LIKELY ROOT CAUSE:
    If amc_instances.instance_id is NULL or missing, the scheduled
    execution will fail because it can't provide the AMC instance ID
    that the AMC API requires.
    """
    
    print(differences)
    
    print("\n" + "=" * 60)
    print("VERIFICATION STEPS")
    print("=" * 60)
    
    verification = """
    To verify the issue:
    
    1. Check database:
       SELECT id, instance_id, instance_name 
       FROM amc_instances;
       
       If instance_id (AMC ID) is NULL, that's the problem.
    
    2. Check a working manual execution:
       - Look at browser DevTools Network tab
       - Find the /execute request
       - Check what instance_id is sent
    
    3. Check the scheduled execution logs for:
       - "Retrieved instance for schedule: UUID=X, AMC_ID=Y"
       - "Using AMC instance_id: Z for scheduled execution"
       
       If AMC_ID or Z is null/empty, that confirms the issue.
    
    4. Fix:
       UPDATE amc_instances 
       SET instance_id = 'amcXXXXXXXX' 
       WHERE id = 'uuid-here';
    """
    
    print(verification)
    
    # Create a simple test
    print("\n" + "=" * 60)
    print("QUICK TEST CODE")
    print("=" * 60)
    
    test_code = """
    # Test code to verify the issue:
    
    from amc_manager.core.supabase_client import SupabaseManager
    
    db = SupabaseManager.get_client()
    
    # Get all instances
    instances = db.table('amc_instances').select('*').execute()
    
    for instance in instances.data:
        print(f"Instance: {instance['instance_name']}")
        print(f"  UUID (id): {instance['id']}")
        print(f"  AMC ID (instance_id): {instance.get('instance_id', 'MISSING!')}")
        
        if not instance.get('instance_id'):
            print("  ❌ This will cause scheduled executions to fail!")
    """
    
    print(test_code)

if __name__ == "__main__":
    try:
        compare_execution_paths()
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()