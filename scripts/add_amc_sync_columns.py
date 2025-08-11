#!/usr/bin/env python3
"""
Add AMC sync tracking columns to workflows table
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def add_amc_sync_columns():
    """Add AMC sync tracking columns to workflows table"""
    
    client = SupabaseManager.get_client(use_service_role=True)
    
    # SQL to add the columns if they don't exist
    sql_commands = [
        """
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS amc_workflow_id VARCHAR(255);
        """,
        """
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS is_synced_to_amc BOOLEAN DEFAULT FALSE;
        """,
        """
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS amc_sync_status VARCHAR(50) DEFAULT 'not_synced';
        """,
        """
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS amc_synced_at TIMESTAMP WITH TIME ZONE;
        """,
        """
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS amc_last_updated_at TIMESTAMP WITH TIME ZONE;
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_workflows_amc_workflow_id 
        ON workflows(amc_workflow_id) 
        WHERE amc_workflow_id IS NOT NULL;
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_workflows_is_synced_to_amc 
        ON workflows(is_synced_to_amc) 
        WHERE is_synced_to_amc = TRUE;
        """
    ]
    
    try:
        for i, sql in enumerate(sql_commands, 1):
            logger.info(f"Executing migration step {i}/{len(sql_commands)}...")
            # Execute raw SQL through Supabase
            result = client.rpc('exec_sql', {'query': sql.strip()}).execute()
            logger.info(f"Step {i} completed")
        
        logger.info("✓ Successfully added AMC sync columns to workflows table")
        
        # Verify the columns were added
        logger.info("Verifying column additions...")
        test_query = """
        SELECT 
            column_name, 
            data_type 
        FROM information_schema.columns 
        WHERE table_name = 'workflows' 
        AND column_name IN (
            'amc_workflow_id', 
            'is_synced_to_amc', 
            'amc_sync_status', 
            'amc_synced_at', 
            'amc_last_updated_at'
        )
        ORDER BY column_name;
        """
        
        result = client.rpc('exec_sql', {'query': test_query.strip()}).execute()
        
        if result.data:
            logger.info("Columns verified:")
            for row in result.data:
                logger.info(f"  - {row['column_name']}: {row['data_type']}")
        else:
            logger.warning("Could not verify columns, but migration may have succeeded")
            
    except Exception as e:
        logger.error(f"Error adding AMC sync columns: {e}")
        
        # Try a simpler approach using Supabase SQL editor function
        logger.info("Attempting alternative approach...")
        
        # Create a single combined migration
        combined_sql = """
        -- Add AMC sync tracking columns to workflows table
        ALTER TABLE workflows 
        ADD COLUMN IF NOT EXISTS amc_workflow_id VARCHAR(255),
        ADD COLUMN IF NOT EXISTS is_synced_to_amc BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS amc_sync_status VARCHAR(50) DEFAULT 'not_synced',
        ADD COLUMN IF NOT EXISTS amc_synced_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS amc_last_updated_at TIMESTAMP WITH TIME ZONE;
        
        -- Add indexes for performance
        CREATE INDEX IF NOT EXISTS idx_workflows_amc_workflow_id 
        ON workflows(amc_workflow_id) 
        WHERE amc_workflow_id IS NOT NULL;
        
        CREATE INDEX IF NOT EXISTS idx_workflows_is_synced_to_amc 
        ON workflows(is_synced_to_amc) 
        WHERE is_synced_to_amc = TRUE;
        """
        
        logger.info("Please run the following SQL in Supabase SQL editor:")
        print("\n" + "="*60)
        print(combined_sql)
        print("="*60 + "\n")
        
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting AMC sync columns migration...")
    
    if add_amc_sync_columns():
        logger.info("✅ Migration completed successfully!")
    else:
        logger.error("❌ Migration failed - please run the SQL manually in Supabase")
        sys.exit(1)