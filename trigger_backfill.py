#!/usr/bin/env python3
"""
Script to trigger backfill of existing workflow executions to Snowflake
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amc_manager.core.supabase_manager import SupabaseManager
from amc_manager.services.universal_snowflake_sync_service import UniversalSnowflakeSyncService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def trigger_backfill():
    """Trigger backfill of existing executions"""
    try:
        # Initialize Supabase client
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get completed executions from the last 7 days
        logger.info("Fetching completed executions from the last 7 days...")
        
        response = client.table('workflow_executions').select('*').eq('status', 'completed').gte('created_at', 'now() - interval \'7 days\'').execute()
        
        executions = response.data
        logger.info(f"Found {len(executions)} completed executions")
        
        if not executions:
            logger.info("No completed executions found in the last 7 days")
            return
        
        # Initialize the sync service
        sync_service = UniversalSnowflakeSyncService()
        
        # Process each execution
        queued_count = 0
        for execution in executions:
            execution_id = execution['execution_id']
            
            # Check if already queued
            existing = client.table('snowflake_sync_queue').select('id').eq('execution_id', execution_id).execute()
            
            if existing.data:
                logger.info(f"Execution {execution_id} already queued, skipping")
                continue
            
            # Get user_id from workflow
            workflow_response = client.table('workflows').select('user_id').eq('id', execution['workflow_id']).execute()
            
            if not workflow_response.data:
                logger.warning(f"Workflow {execution['workflow_id']} not found for execution {execution_id}")
                continue
            
            user_id = workflow_response.data[0]['user_id']
            
            # Queue the execution
            queue_response = client.table('snowflake_sync_queue').insert({
                'execution_id': execution_id,
                'user_id': user_id,
                'status': 'pending'
            }).execute()
            
            if queue_response.data:
                queued_count += 1
                logger.info(f"Queued execution {execution_id} for user {user_id}")
            else:
                logger.error(f"Failed to queue execution {execution_id}")
        
        logger.info(f"Successfully queued {queued_count} executions for Snowflake sync")
        
        # Show queue status
        queue_response = client.table('snowflake_sync_queue').select('*').eq('status', 'pending').execute()
        pending_count = len(queue_response.data)
        logger.info(f"Total pending syncs in queue: {pending_count}")
        
        if pending_count > 0:
            logger.info("The background sync service will process these executions automatically")
            logger.info("You can monitor progress via the API endpoints:")
            logger.info("  GET /api/snowflake-sync/stats")
            logger.info("  GET /api/snowflake-sync/queue")
            logger.info("  GET /api/snowflake-sync/failed")
        
    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Universal Snowflake Sync Backfill...")
    print("=" * 50)
    
    success = asyncio.run(trigger_backfill())
    
    if success:
        print("=" * 50)
        print("✅ Backfill completed successfully!")
        print("📊 Check the sync queue and monitor progress via API endpoints")
    else:
        print("=" * 50)
        print("❌ Backfill failed - check logs above")
        sys.exit(1)
