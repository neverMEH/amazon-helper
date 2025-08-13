#!/usr/bin/env python3
"""
Apply AMC sync columns migration using direct database update
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from amc_manager.config import settings
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def apply_migration():
    """Apply the AMC sync columns migration"""
    
    # Create a Supabase client with service role key
    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )
    
    # For now, we'll add the columns by updating the workflow creation logic
    # to handle missing columns gracefully
    
    logger.info("Checking if columns need to be added...")
    
    # Try to create a test workflow with the new columns
    # If it fails, we know the columns don't exist
    test_data = {
        "workflow_id": "test_migration_check",
        "name": "Migration Test",
        "sql_query": "SELECT 1",
        "user_id": "00000000-0000-0000-0000-000000000000",
        "instance_id": "00000000-0000-0000-0000-000000000000",
        "amc_workflow_id": None,
        "is_synced_to_amc": False,
        "amc_sync_status": "not_synced"
    }
    
    try:
        # Try to insert with new columns
        result = supabase.table('workflows').insert(test_data).execute()
        
        # If successful, delete the test record
        supabase.table('workflows').delete().eq('workflow_id', 'test_migration_check').execute()
        
        logger.info("✓ AMC sync columns already exist in the database")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "amc_synced_at" in error_msg or "amc_workflow_id" in error_msg:
            logger.error("AMC sync columns are missing from the database")
            logger.info("\n" + "="*60)
            logger.info("MANUAL ACTION REQUIRED:")
            logger.info("Please run the following SQL in your Supabase SQL editor:")
            logger.info("https://supabase.com/dashboard/project/loqaorroihxfkjvcrkdv/sql/new")
            logger.info("="*60 + "\n")
            
            with open(Path(__file__).parent / 'apply_amc_sync_migration.sql', 'r') as f:
                print(f.read())
            
            logger.info("\n" + "="*60)
            logger.info("After running the SQL, restart the backend server.")
            logger.info("="*60)
            return False
        else:
            # Some other error
            logger.error(f"Unexpected error: {e}")
            return False

if __name__ == "__main__":
    if apply_migration():
        logger.info("✅ Database is ready for AMC sync features!")
    else:
        logger.error("❌ Database migration required - see instructions above")
        sys.exit(1)