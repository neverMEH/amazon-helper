#!/usr/bin/env python3
"""
Add instance_id to workflow_executions table
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

def add_instance_id_column():
    """Add instance_id column to workflow_executions table"""
    
    print("🔄 Adding instance_id to workflow_executions table...")
    
    # SQL to add column
    sql = """
    -- Add instance_id column to workflow_executions
    ALTER TABLE workflow_executions 
    ADD COLUMN IF NOT EXISTS instance_id TEXT;
    
    -- Add index for faster queries
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_instance_id 
    ON workflow_executions(instance_id);
    
    -- Add composite index for workflow + instance queries
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_instance 
    ON workflow_executions(workflow_id, instance_id);
    """
    
    try:
        # Execute SQL via Supabase RPC or direct SQL if available
        print("⚠️  Please run the following SQL in your Supabase SQL Editor:")
        print(sql)
        print("\n✅ After running the SQL, the instance_id column will be available")
        print("\nNext steps:")
        print("1. New executions will track which instance they ran on")
        print("2. Execution history can be filtered by instance")
        print("3. Instance selector will be available in execution modal")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_instance_id_column()