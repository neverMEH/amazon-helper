#!/usr/bin/env python3
"""Add execution results fields to workflow_executions table"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply migration to add execution results fields"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("Adding execution results fields to workflow_executions table...")
    
    # SQL to add new columns
    sql = """
    -- Add result storage columns to workflow_executions
    ALTER TABLE workflow_executions
    ADD COLUMN IF NOT EXISTS result_columns JSONB,
    ADD COLUMN IF NOT EXISTS result_rows JSONB,
    ADD COLUMN IF NOT EXISTS result_total_rows INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS result_sample_size INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS query_runtime_seconds NUMERIC,
    ADD COLUMN IF NOT EXISTS data_scanned_gb NUMERIC,
    ADD COLUMN IF NOT EXISTS cost_estimate_usd NUMERIC;
    
    -- Add index on execution_id for faster lookups
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_id 
    ON workflow_executions(execution_id);
    
    -- Add index on workflow_id and created_at for listing executions
    CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_created 
    ON workflow_executions(workflow_id, created_at DESC);
    
    -- Update RLS policies to allow users to read their execution results
    DROP POLICY IF EXISTS "Users can view their workflow execution results" ON workflow_executions;
    
    CREATE POLICY "Users can view their workflow execution results" ON workflow_executions
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_executions.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );
    """
    
    try:
        # Execute the SQL
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print("✓ Successfully added execution results fields")
        
        # Verify the changes
        verify_sql = """
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name IN (
            'result_columns', 'result_rows', 'result_total_rows', 
            'result_sample_size', 'query_runtime_seconds', 
            'data_scanned_gb', 'cost_estimate_usd'
        )
        ORDER BY column_name;
        """
        
        verify_result = supabase.rpc('exec_sql', {'query': verify_sql}).execute()
        
        if verify_result.data:
            print("\nAdded columns:")
            for col in verify_result.data:
                print(f"  - {col['column_name']} ({col['data_type']})")
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"Error applying migration: {e}")
        
        # If the exec_sql RPC doesn't exist, provide instructions
        if "exec_sql" in str(e):
            print("\nThe exec_sql RPC function doesn't exist.")
            print("Please run the following SQL in the Supabase SQL Editor:")
            print("\n" + "="*60)
            print(sql)
            print("="*60)
            print("\nAfter running the SQL, the execution results storage will be ready.")
        
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()