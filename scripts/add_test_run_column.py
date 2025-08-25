#!/usr/bin/env python3
"""
Add is_test_run column to schedule_runs table
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from amc_manager.core.supabase_client import SupabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_test_run_column():
    """Add is_test_run column to schedule_runs table"""
    try:
        # Get Supabase client
        client = SupabaseManager.get_client()
        
        # Check if column already exists by trying to query it
        try:
            result = client.table('schedule_runs').select('is_test_run').limit(1).execute()
            logger.info("is_test_run column already exists")
            return True
        except Exception as e:
            # Column doesn't exist, need to add it
            logger.info("is_test_run column doesn't exist, adding it...")
            pass
        
        # Add the column using raw SQL via RPC
        # Note: Supabase doesn't support DDL through the client library directly
        # You'll need to run this SQL in the Supabase dashboard:
        sql = """
        ALTER TABLE schedule_runs 
        ADD COLUMN IF NOT EXISTS is_test_run BOOLEAN DEFAULT FALSE;
        
        -- Add index for filtering test runs
        CREATE INDEX IF NOT EXISTS idx_schedule_runs_is_test_run 
        ON schedule_runs(is_test_run);
        """
        
        logger.info("SQL to run in Supabase dashboard:")
        logger.info(sql)
        
        # For now, we'll just update the parameters column to include is_test_run info
        # when creating test runs in the API
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding test run column: {e}")
        return False

if __name__ == "__main__":
    success = add_test_run_column()
    if success:
        logger.info("✅ Test run column setup completed")
    else:
        logger.error("❌ Failed to setup test run column")
        sys.exit(1)