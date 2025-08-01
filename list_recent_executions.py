#!/usr/bin/env python3
"""List recent executions to help debug UI issue"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("Recent workflow executions:\n")

# Get recent executions with workflow names
executions = supabase.table('workflow_executions')\
    .select('*, workflows!inner(name, workflow_id)')\
    .order('created_at', desc=True)\
    .limit(10)\
    .execute()

if executions.data:
    for exec in executions.data:
        print(f"Execution ID: {exec['execution_id']}")
        print(f"  Workflow: {exec['workflows']['name']} ({exec['workflows']['workflow_id']})")
        print(f"  Status: {exec['status']}")
        print(f"  Created: {exec['created_at']}")
        
        # Check if has results
        has_results = (
            exec.get('result_columns') is not None and 
            exec.get('result_rows') is not None
        )
        print(f"  Has Results: {'Yes' if has_results else 'No'}")
        
        if has_results:
            print(f"  Result Stats: {len(exec['result_columns'])} columns, {len(exec['result_rows'])} rows")
        
        print()
else:
    print("No executions found")