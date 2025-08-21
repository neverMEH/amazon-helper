#!/usr/bin/env python3
"""Restore the original schedule name after testing"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def restore_schedule_name():
    """Restore the original schedule name"""
    
    # Get Supabase client
    db = SupabaseManager.get_client(use_service_role=True)
    
    try:
        # Find the schedule we modified
        schedules = db.table('workflow_schedules').select('*').eq('schedule_id', 'sched_d0d8b2c5f533').execute()
        
        if schedules.data and len(schedules.data) > 0:
            schedule = schedules.data[0]
            
            # Restore original name and clear test description
            update_result = db.table('workflow_schedules').update({
                'name': 'Intraday Brand Search Return Analysis Schedule',
                'description': None
            }).eq('id', schedule['id']).execute()
            
            if update_result.data:
                logger.info("✅ Successfully restored original schedule name")
            else:
                logger.warning("Failed to restore schedule")
        else:
            logger.info("Schedule not found")
            
    except Exception as e:
        logger.error(f"Error restoring schedule: {e}")

if __name__ == "__main__":
    restore_schedule_name()