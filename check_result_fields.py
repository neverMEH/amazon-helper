#!/usr/bin/env python3
"""Check if result fields exist in workflow_executions table"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("Checking for result fields in workflow_executions table...")

# Get a recent execution
executions = supabase.table('workflow_executions').select('*').order('created_at', desc=True).limit(1).execute()

if executions.data:
    execution = executions.data[0]
    print(f"\nFound execution: {execution.get('execution_id', 'unknown')}")
    print(f"Status: {execution.get('status', 'unknown')}")
    
    # Check for result fields
    result_fields = [
        'result_columns',
        'result_rows', 
        'result_total_rows',
        'result_sample_size',
        'query_runtime_seconds',
        'data_scanned_gb',
        'cost_estimate_usd'
    ]
    
    print("\nChecking for result fields:")
    for field in result_fields:
        if field in execution:
            value = execution[field]
            if value is not None:
                print(f"✓ {field}: {type(value).__name__} - has data")
            else:
                print(f"✓ {field}: exists but is None")
        else:
            print(f"✗ {field}: NOT FOUND")
    
    # Show all fields in the execution
    print("\nAll fields in execution record:")
    for key in sorted(execution.keys()):
        print(f"  - {key}")
else:
    print("No executions found")