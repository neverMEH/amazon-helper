#!/usr/bin/env python
"""Add missing parameters column to schedule_runs table."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

def main():
    """Add parameters column to schedule_runs table."""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # SQL to add the parameters column
    sql = """
    -- Add parameters column to schedule_runs table if it doesn't exist
    ALTER TABLE schedule_runs 
    ADD COLUMN IF NOT EXISTS parameters jsonb;
    
    -- Add comment for documentation
    COMMENT ON COLUMN schedule_runs.parameters IS 'Execution parameters used for this run (date ranges, filters, etc.)';
    """
    
    try:
        # Execute the migration
        result = client.rpc('exec_sql', {'query': sql}).execute()
        print("✅ Successfully added parameters column to schedule_runs table")
        return True
    except Exception as e:
        # Check if it's just a "column already exists" error
        error_msg = str(e)
        if "already exists" in error_msg.lower():
            print("ℹ️  Parameters column already exists in schedule_runs table")
            return True
        else:
            print(f"❌ Error adding parameters column: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)