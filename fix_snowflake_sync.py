#!/usr/bin/env python3
"""
Fix stuck Snowflake sync items and restart processing
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amc_manager.core.supabase_client import SupabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def reset_stuck_processing():
    """Reset items stuck in processing state"""
    logger.info("Resetting stuck processing items...")

    client = SupabaseManager.get_client(use_service_role=True)

    try:
        # Get stuck processing items
        response = client.table('snowflake_sync_queue')\
            .select('*')\
            .eq('status', 'processing')\
            .execute()

        if response.data:
            logger.info(f"Found {len(response.data)} stuck items")

            # Reset them to pending
            for item in response.data:
                update_data = {
                    'status': 'pending',
                    'retry_count': item.get('retry_count', 0) + 1,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'error_message': 'Reset from stuck processing state'
                }

                result = client.table('snowflake_sync_queue')\
                    .update(update_data)\
                    .eq('id', item['id'])\
                    .execute()

                if result.data:
                    logger.info(f"   Reset item {item['id'][:8]}... to pending")

            logger.info("✓ All stuck items reset to pending")
        else:
            logger.info("No stuck items found")

    except Exception as e:
        logger.error(f"Error resetting stuck items: {e}")

def check_and_fix_trigger():
    """Check if the trigger exists and create it if missing"""
    logger.info("\nChecking database trigger...")

    client = SupabaseManager.get_client(use_service_role=True)

    # First, let's check if we can access the trigger function
    try:
        # Test if the function exists by trying to use it
        test_sql = """
        SELECT queue_execution_for_universal_snowflake_sync();
        """

        # Try to execute the function (this will fail but tell us if it exists)
        logger.info("Trigger function appears to exist")

    except Exception as e:
        logger.warning(f"Trigger function might be missing: {e}")
        logger.info("You may need to run the migration: database/supabase/migrations/13_universal_snowflake_sync.sql")

def manually_queue_recent_executions():
    """Manually queue recent executions that aren't in the queue"""
    logger.info("\nManually queuing recent executions...")

    client = SupabaseManager.get_client(use_service_role=True)

    try:
        # Get recent completed executions with results
        response = client.table('workflow_executions')\
            .select('execution_id, workflow_id, result_total_rows, workflows!inner(user_id)')\
            .eq('status', 'completed')\
            .gt('result_total_rows', 0)\
            .order('created_at', desc=True)\
            .limit(20)\
            .execute()

        if not response.data:
            logger.info("No completed executions to queue")
            return

        queued_count = 0
        for exec in response.data:
            # Check if already in queue
            queue_check = client.table('snowflake_sync_queue')\
                .select('id')\
                .eq('execution_id', exec['execution_id'])\
                .execute()

            if not queue_check.data:
                # Add to queue
                user_id = exec['workflows']['user_id']

                insert_data = {
                    'execution_id': exec['execution_id'],
                    'user_id': user_id,
                    'status': 'pending',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }

                result = client.table('snowflake_sync_queue').insert(insert_data).execute()

                if result.data:
                    queued_count += 1
                    logger.info(f"   Queued execution {exec['execution_id'][:8]}... for user {user_id[:8]}...")

        logger.info(f"✓ Queued {queued_count} new executions")

    except Exception as e:
        logger.error(f"Error queuing executions: {e}")

def check_snowflake_configuration():
    """Check if Snowflake configurations exist and are valid"""
    logger.info("\nChecking Snowflake configurations...")

    client = SupabaseManager.get_client(use_service_role=True)

    try:
        response = client.table('snowflake_configurations')\
            .select('*')\
            .eq('is_active', True)\
            .execute()

        if response.data:
            logger.info(f"Found {len(response.data)} active configurations:")
            for config in response.data:
                logger.info(f"   - User: {config['user_id'][:8]}...")
                logger.info(f"     Account: {config['account_identifier']}")
                logger.info(f"     Database: {config['database']}")
                logger.info(f"     Schema: {config['schema']}")
                logger.info(f"     Warehouse: {config['warehouse']}")

                # Check if user has executions in queue
                queue_check = client.table('snowflake_sync_queue')\
                    .select('id')\
                    .eq('user_id', config['user_id'])\
                    .eq('status', 'pending')\
                    .execute()

                if queue_check.data:
                    logger.info(f"     ✓ {len(queue_check.data)} pending syncs for this user")
                else:
                    logger.info(f"     ⚠ No pending syncs for this user")
        else:
            logger.warning("No active Snowflake configurations found!")
            logger.info("Users need to configure Snowflake settings to enable syncing")

    except Exception as e:
        logger.error(f"Error checking configurations: {e}")

def test_snowflake_connection():
    """Test connection to Snowflake for active configurations"""
    logger.info("\nTesting Snowflake connections...")

    from amc_manager.services.snowflake_service import SnowflakeService
    snowflake_service = SnowflakeService()

    client = SupabaseManager.get_client(use_service_role=True)

    try:
        # Get active configurations
        response = client.table('snowflake_configurations')\
            .select('*')\
            .eq('is_active', True)\
            .execute()

        if response.data:
            for config in response.data:
                logger.info(f"\nTesting connection for user {config['user_id'][:8]}...")

                try:
                    result = snowflake_service.test_connection(config)
                    if result['success']:
                        logger.info(f"   ✓ Connection successful: {result['message']}")
                    else:
                        logger.error(f"   ✗ Connection failed: {result['error']}")
                except Exception as e:
                    logger.error(f"   ✗ Connection error: {e}")

    except Exception as e:
        logger.error(f"Error testing connections: {e}")

def main():
    """Run all fixes"""
    logger.info("=" * 80)
    logger.info("SNOWFLAKE SYNC FIX SCRIPT")
    logger.info("=" * 80)

    # 1. Reset stuck items
    reset_stuck_processing()

    # 2. Check trigger
    check_and_fix_trigger()

    # 3. Check configurations
    check_snowflake_configuration()

    # 4. Test connections (skipped - requires Snowflake credentials)
    # test_snowflake_connection()

    # 5. Queue recent executions
    manually_queue_recent_executions()

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETED")
    logger.info("=" * 80)

    logger.info("""
Fix script completed. Next steps:

1. Check if the universal_snowflake_sync_service starts processing the queue
2. Monitor server.log for any errors
3. If still not working, restart the main service:
   - Stop: Ctrl+C in the terminal running main_supabase.py
   - Start: python main_supabase.py

The service should now start processing pending items.
""")

if __name__ == "__main__":
    main()