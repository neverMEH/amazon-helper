#!/usr/bin/env python3
"""
Delete script for ASIN Purchase Overlap for Upselling Build Guide
This script removes the guide and all associated data from the database
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def delete_asin_overlap_guide():
    """Delete the ASIN Purchase Overlap for Upselling guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        guide_id = 'guide_asin_purchase_overlap_upselling'
        
        # Delete the guide (cascades to related tables)
        response = client.table('build_guides').delete().eq('guide_id', guide_id).execute()
        
        if response.data:
            logger.info(f"✅ Successfully deleted ASIN Purchase Overlap guide: {guide_id}")
            return True
        else:
            logger.warning(f"Guide not found: {guide_id}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete guide: {e}")
        return False

if __name__ == "__main__":
    success = delete_asin_overlap_guide()
    sys.exit(0 if success else 1)