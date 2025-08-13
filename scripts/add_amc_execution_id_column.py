#!/usr/bin/env python3
"""Add amc_execution_id column to workflow_executions table"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def apply_migration():
    """Apply the amc_execution_id migration"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Read migration file
        migration_path = Path(__file__).parent.parent / "database/supabase/migrations/08_add_amc_execution_id.sql"
        with open(migration_path, 'r') as f:
            sql = f.read()
        
        logger.info("Applying migration: Add amc_execution_id column")
        
        # Execute SQL
        client.postgrest.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Migration applied successfully!")
        
        # Verify column exists
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_executions' 
        AND column_name = 'amc_execution_id';
        """
        
        result = client.postgrest.rpc('exec_sql', {'query': check_sql}).execute()
        
        if result.data:
            logger.info("✓ Verified: amc_execution_id column exists")
        else:
            logger.error("✗ Column not found after migration")
            
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if apply_migration():
        print("\n✓ Migration completed successfully!")
    else:
        print("\n✗ Migration failed!")
        sys.exit(1)