#!/usr/bin/env python3
"""
Make workflows available across all AMC instances
by converting them to templates
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def make_workflows_global():
    """Convert existing workflows to templates so they can be used on any instance"""
    
    print("🔄 Making workflows available across all instances...")
    
    # 1. Get all existing workflows
    response = supabase.table('workflows').select('*').execute()
    workflows = response.data
    
    print(f"Found {len(workflows)} workflows")
    
    # 2. Update existing workflows to be templates
    for workflow in workflows:
        # Skip if already a template
        if workflow.get('is_template'):
            continue
            
        print(f"\n📝 Converting workflow: {workflow['name']}")
        
        # Update to be a template
        update_response = supabase.table('workflows')\
            .update({'is_template': True})\
            .eq('id', workflow['id'])\
            .execute()
        
        if update_response.data:
            print(f"✓ Converted {workflow['name']} to template")
        else:
            print(f"❌ Failed to convert {workflow['name']}")
    
    # 3. Add a new column to track which instance a workflow was executed on
    # This is handled in workflow_executions table already
    
    print("\n✅ Workflows are now available across all instances!")
    print("\nNext steps:")
    print("1. The UI will show all template workflows on every instance")
    print("2. When executing, users can choose which instance to run on")
    print("3. Execution history will track which instance was used")


if __name__ == "__main__":
    make_workflows_global()