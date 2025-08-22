#!/usr/bin/env python3
"""
Delete and recreate the cart abandonment guide
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)

def delete_existing_guide():
    """Delete existing cart abandonment guide if it exists"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # First get the guide ID
        guide_response = client.table('build_guides').select('id').eq('guide_id', 'guide_cart_abandonment_audience').execute()
        
        if guide_response.data and len(guide_response.data) > 0:
            guide_uuid = guide_response.data[0]['id']
            logger.info(f"Found existing guide with UUID: {guide_uuid}")
            
            # Delete in order due to foreign key constraints
            # Delete user progress
            client.table('user_guide_progress').delete().eq('guide_id', guide_uuid).execute()
            logger.info("Deleted user progress")
            
            # Delete user favorites
            client.table('user_guide_favorites').delete().eq('guide_id', guide_uuid).execute()
            logger.info("Deleted user favorites")
            
            # Delete metrics
            client.table('build_guide_metrics').delete().eq('guide_id', guide_uuid).execute()
            logger.info("Deleted metrics")
            
            # Delete examples (need to get query IDs first)
            queries_response = client.table('build_guide_queries').select('id').eq('guide_id', guide_uuid).execute()
            if queries_response.data:
                for query in queries_response.data:
                    client.table('build_guide_examples').delete().eq('guide_query_id', query['id']).execute()
                logger.info("Deleted examples")
            
            # Delete queries
            client.table('build_guide_queries').delete().eq('guide_id', guide_uuid).execute()
            logger.info("Deleted queries")
            
            # Delete sections
            client.table('build_guide_sections').delete().eq('guide_id', guide_uuid).execute()
            logger.info("Deleted sections")
            
            # Finally delete the guide itself
            client.table('build_guides').delete().eq('id', guide_uuid).execute()
            logger.info("Deleted guide")
            
            return True
        else:
            logger.info("No existing guide found")
            return True
            
    except Exception as e:
        logger.error(f"Failed to delete guide: {e}")
        return False

if __name__ == "__main__":
    # First delete existing guide
    if delete_existing_guide():
        logger.info("✅ Successfully cleaned up existing guide")
        # Now run the seed script
        import seed_cart_abandonment_audience_guide
        success = seed_cart_abandonment_audience_guide.create_cart_abandonment_guide()
        sys.exit(0 if success else 1)
    else:
        logger.error("Failed to delete existing guide")
        sys.exit(1)