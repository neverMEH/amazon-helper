#!/usr/bin/env python3
"""Check workflow_executions table structure"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

# Try to get a sample execution or insert a minimal one
print("Checking workflow_executions table...")

# First, get a workflow ID to use
workflows = supabase.table('workflows').select('id').limit(1).execute()
if workflows.data:
    workflow_id = workflows.data[0]['id']
    print(f"Using workflow ID: {workflow_id}")
    
    # Try to create a minimal execution record
    minimal_data = {
        "workflow_id": workflow_id,
        "status": "test"
    }
    
    try:
        result = supabase.table('workflow_executions').insert(minimal_data).execute()
        print("Successfully created execution with minimal data:")
        print(result.data[0])
        
        # Clean up
        if result.data:
            supabase.table('workflow_executions').delete().eq('id', result.data[0]['id']).execute()
            print("Cleaned up test record")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No workflows found")