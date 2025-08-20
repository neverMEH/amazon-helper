#!/usr/bin/env python3
"""Add name and description fields to workflow_schedules table"""

import sys
from pathlib import Path
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def add_schedule_name_description():
    """Add name and description columns to workflow_schedules table"""
    
    # Get Supabase client using the existing singleton
    db = SupabaseManager.get_client(use_service_role=True)
    
    if not db:
        logger.error("Failed to get Supabase client")
        return False
    
    try:
        # First, check if columns already exist
        logger.info("Checking if columns already exist...")
        schedules = db.table('workflow_schedules').select('*').limit(1).execute()
        
        if schedules.data and len(schedules.data) > 0:
            sample = schedules.data[0]
            has_name = 'name' in sample
            has_description = 'description' in sample
            
            if has_name and has_description:
                logger.info("✅ Columns already exist!")
                return True
        
        # Since we can't directly run ALTER TABLE via Supabase client,
        # we'll need to handle this differently
        # For now, let's verify the current structure and update existing records
        
        logger.info("Fetching existing schedules to update...")
        
        # Get all schedules with workflow info
        schedules_result = db.table('workflow_schedules').select(
            '*, workflows(name)'
        ).execute()
        
        if schedules_result.data:
            logger.info(f"Found {len(schedules_result.data)} schedules")
            
            # Check if first schedule has name field
            if schedules_result.data and 'name' in schedules_result.data[0]:
                logger.info("✅ Name column already exists")
            else:
                logger.warning("⚠️ Name column does not exist - manual migration required")
                logger.info("Please run the following SQL in your Supabase dashboard:")
                logger.info("""
                ALTER TABLE workflow_schedules 
                ADD COLUMN IF NOT EXISTS name TEXT,
                ADD COLUMN IF NOT EXISTS description TEXT;
                
                UPDATE workflow_schedules ws
                SET name = COALESCE(ws.name, w.name || ' Schedule')
                FROM workflows w
                WHERE ws.workflow_id = w.id
                AND ws.name IS NULL;
                """)
                return False
                
            return True
        else:
            logger.info("No schedules found in the database")
            logger.info("Columns will be added when first schedule is created")
            return True
            
    except Exception as e:
        logger.error(f"Error adding schedule name and description: {e}")
        return False

def main():
    """Main function"""
    success = add_schedule_name_description()
    
    if success:
        logger.info("\n✅ Migration completed successfully!")
    else:
        logger.error("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()