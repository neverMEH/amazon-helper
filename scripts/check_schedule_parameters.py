"""Script to check schedule parameters in the database"""
import json
from amc_manager.core.supabase_client import SupabaseManager

def check_schedule_parameters():
    """Check what parameters are stored in schedules"""
    db = SupabaseManager.get_client(use_service_role=True)

    # Get all schedules with their parameters
    result = db.table('workflow_schedules').select(
        'schedule_id, name, default_parameters, workflows(workflow_id, name, parameters)'
    ).order('created_at', desc=True).limit(10).execute()

    if not result.data:
        print("No schedules found")
        return

    print(f"\n{'='*100}")
    print(f"Found {len(result.data)} recent schedules:\n")

    for schedule in result.data:
        print(f"Schedule: {schedule.get('name', 'Unnamed')} ({schedule['schedule_id']})")
        print(f"  Workflow: {schedule['workflows']['name']} ({schedule['workflows']['workflow_id']})")

        # Parse default_parameters
        default_params = schedule.get('default_parameters')
        if isinstance(default_params, str):
            try:
                default_params = json.loads(default_params)
            except:
                default_params = {}

        print(f"  Schedule default_parameters: {default_params}")

        # Parse workflow parameters
        workflow_params = schedule['workflows'].get('parameters')
        if isinstance(workflow_params, str):
            try:
                workflow_params = json.loads(workflow_params)
            except:
                workflow_params = {}

        print(f"  Workflow parameters: {workflow_params}")

        # Check for non-date parameters
        non_date_params = {k: v for k, v in (default_params or {}).items()
                          if k not in ['startDate', 'endDate', 'start_date', 'end_date',
                                      '_schedule_id', '_scheduled_execution']}

        if non_date_params:
            print(f"  ✓ Non-date parameters found: {list(non_date_params.keys())}")
        else:
            print(f"  ✗ NO non-date parameters (ASIN, campaign, etc.)")

        print(f"{'-'*100}\n")

if __name__ == '__main__':
    check_schedule_parameters()
