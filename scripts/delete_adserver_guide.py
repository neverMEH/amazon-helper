#!/usr/bin/env python3
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def delete_guide():
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Delete the guide (cascade will handle related tables)
        response = client.table('build_guides').delete().eq('guide_id', 'guide_adserver_dsp_cost').execute()
        
        if response.data:
            logger.info(f"Deleted guide: {response.data}")
            return True
        else:
            logger.info("No guide found to delete")
            return True
            
    except Exception as e:
        logger.error(f"Error deleting guide: {str(e)}")
        return False

if __name__ == "__main__":
    success = delete_guide()
    if success:
        print("✅ Successfully deleted guide")
    else:
        print("❌ Failed to delete guide")
        sys.exit(1)