#!/usr/bin/env python3
"""
Delete script for 'Audience that clicked sponsored ads but did not purchase' Build Guide
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

def delete_audience_clicked_not_purchased_guide():
    """Delete the Audience that clicked sponsored ads but did not purchase guide"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        guide_id = 'guide_audience_clicked_not_purchased'
        
        # Get the guide first to confirm it exists
        guide_response = client.table('build_guides').select('*').eq('guide_id', guide_id).execute()
        
        if not guide_response.data:
            logger.warning(f"Guide with ID '{guide_id}' not found")
            return False
        
        actual_id = guide_response.data[0]['id']
        logger.info(f"Found guide with UUID: {actual_id}")
        
        # Delete in order due to foreign key constraints
        # 1. Delete user progress
        progress_response = client.table('user_guide_progress').delete().eq('guide_id', actual_id).execute()
        logger.info(f"Deleted user progress records")
        
        # 2. Delete user favorites
        favorites_response = client.table('user_guide_favorites').delete().eq('guide_id', actual_id).execute()
        logger.info(f"Deleted user favorite records")
        
        # 3. Delete examples
        examples_response = client.table('build_guide_examples').delete().match({
            'guide_query_id': client.table('build_guide_queries').select('id').eq('guide_id', actual_id)
        }).execute()
        logger.info(f"Deleted example data")
        
        # 4. Delete metrics
        metrics_response = client.table('build_guide_metrics').delete().eq('guide_id', actual_id).execute()
        logger.info(f"Deleted metrics")
        
        # 5. Delete queries
        queries_response = client.table('build_guide_queries').delete().eq('guide_id', actual_id).execute()
        logger.info(f"Deleted queries")
        
        # 6. Delete sections
        sections_response = client.table('build_guide_sections').delete().eq('guide_id', actual_id).execute()
        logger.info(f"Deleted sections")
        
        # 7. Finally delete the guide itself
        guide_delete_response = client.table('build_guides').delete().eq('id', actual_id).execute()
        logger.info(f"Deleted main guide record")
        
        logger.info("✅ Successfully deleted 'Audience that clicked sponsored ads but did not purchase' guide!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete guide: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete the 'Audience that clicked sponsored ads but did not purchase' guide? (yes/no): ")
    if confirm.lower() == 'yes':
        success = delete_audience_clicked_not_purchased_guide()
        sys.exit(0 if success else 1)
    else:
        logger.info("Deletion cancelled")
        sys.exit(0)