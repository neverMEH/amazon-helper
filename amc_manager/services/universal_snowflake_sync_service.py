"""
Universal Snowflake Sync Service
Automatically syncs ALL workflow executions to Snowflake for users with configurations
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from ..core.supabase_client import SupabaseManager
from ..core.logger_simple import get_logger
from .snowflake_service import SnowflakeService

logger = get_logger(__name__)


class UniversalSnowflakeSyncService:
    """Background service for universal Snowflake syncing"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 30  # Check every 30 seconds
        self.snowflake_service = SnowflakeService()
        self.client = SupabaseManager.get_client(use_service_role=True)
        self.max_concurrent_syncs = 5
        self._sync_semaphore = asyncio.Semaphore(self.max_concurrent_syncs)
        self._sync_tasks = {}  # Track running sync tasks
    
    async def start(self):
        """Start the universal Snowflake sync service"""
        logger.info("Starting Universal Snowflake Sync Service")
        self.running = True
        
        while self.running:
            try:
                await self.process_sync_queue()
            except Exception as e:
                logger.error(f"Universal Snowflake sync error: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the sync service"""
        logger.info("Stopping Universal Snowflake Sync Service")
        self.running = False
        
        # Wait for running sync tasks to complete
        if self._sync_tasks:
            logger.info(f"Waiting for {len(self._sync_tasks)} sync tasks to complete")
            await asyncio.gather(*self._sync_tasks.values(), return_exceptions=True)
    
    async def process_sync_queue(self):
        """Process pending sync queue items"""
        try:
            # Get pending sync items
            response = self.client.table('snowflake_sync_queue')\
                .select('*, users(id)')\
                .eq('status', 'pending')\
                .order('created_at')\
                .limit(10)\
                .execute()
            
            if not response.data:
                return
            
            logger.info(f"Processing {len(response.data)} universal Snowflake sync items")
            
            # Process each item concurrently
            tasks = []
            for item in response.data:
                # Skip if already processing
                if item['id'] in self._sync_tasks:
                    continue
                
                task = asyncio.create_task(self.sync_execution_to_snowflake(item))
                self._sync_tasks[item['id']] = task
                
                # Clean up completed tasks
                task.add_done_callback(
                    lambda t, item_id=item['id']: self._sync_tasks.pop(item_id, None)
                )
                
                tasks.append(task)
            
            # Wait for all tasks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error processing universal sync queue: {e}")
    
    async def sync_execution_to_snowflake(self, sync_item: Dict[str, Any]):
        """Sync a single execution to Snowflake"""
        async with self._sync_semaphore:
            execution_id = sync_item['execution_id']
            user_id = sync_item['user_id']
            sync_id = sync_item['id']
            
            try:
                # Update status to processing
                self._update_sync_status(sync_id, 'processing')

                # Get execution data separately
                exec_response = self.client.table('workflow_executions')\
                    .select('*')\
                    .eq('execution_id', execution_id)\
                    .single()\
                    .execute()

                execution = exec_response.data
                if not execution:
                    raise Exception("Execution not found")
                
                # Check if user has Snowflake config
                snowflake_config = self.snowflake_service.get_user_snowflake_config(user_id)
                if not snowflake_config:
                    logger.info(f"No Snowflake config for user {user_id}, marking as completed")
                    self._update_sync_status(sync_id, 'completed')
                    return
                
                # Prepare results data
                results = {
                    'columns': execution.get('result_columns', []),
                    'rows': execution.get('result_rows', []),
                    'total_rows': execution.get('result_total_rows', 0)
                }
                
                if not results['columns'] or not results['rows']:
                    logger.warning(f"No results data for execution {execution_id}")
                    self._update_sync_status(sync_id, 'failed',
                                           error_message="No results data available")
                    return
                
                # Generate table name
                table_name = self._generate_table_name(execution)
                
                logger.info(f"Syncing execution {execution_id} to Snowflake table {table_name}")
                
                # Upload to Snowflake
                upload_result = self.snowflake_service.upload_execution_results(
                    execution_id=execution_id,
                    results=results,
                    table_name=table_name,
                    user_id=user_id
                )
                
                if upload_result['success']:
                    logger.info(f"Successfully synced execution {execution_id} to Snowflake")
                    self._update_sync_status(sync_id, 'completed')
                    
                    # Update execution record with Snowflake info
                    self._update_execution_snowflake_info(execution_id, table_name, upload_result)
                else:
                    raise Exception(upload_result.get('error', 'Unknown upload error'))
                    
            except Exception as e:
                logger.error(f"Error syncing execution {execution_id}: {e}")
                retry_count = sync_item['retry_count'] + 1
                
                if retry_count <= sync_item['max_retries']:
                    # Retry later
                    logger.info(f"Retrying sync for execution {execution_id} (attempt {retry_count})")
                    self._update_sync_status(sync_id, 'pending', 
                                           retry_count=retry_count)
                else:
                    # Max retries exceeded
                    logger.error(f"Max retries exceeded for execution {execution_id}")
                    self._update_sync_status(sync_id, 'failed', 
                                           error_message=str(e))
    
    def _generate_table_name(self, execution: Dict[str, Any]) -> str:
        """Generate a meaningful table name for the execution
        Format: instance_workflowname_startdate_enddate
        """
        import re
        import json

        # Get workflow info
        workflow_response = self.client.table('workflows')\
            .select('name, instance_id, query_text')\
            .eq('id', execution.get('workflow_id'))\
            .single()\
            .execute()

        if workflow_response.data:
            workflow = workflow_response.data

            # Get instance info
            instance_response = self.client.table('amc_instances')\
                .select('instance_id')\
                .eq('id', workflow['instance_id'])\
                .single()\
                .execute()

            instance_name = "unknown"
            if instance_response.data:
                # Clean instance ID for table name (remove special chars)
                instance_name = re.sub(r'[^a-zA-Z0-9_]', '_', instance_response.data['instance_id'])

            # Clean workflow name for table name
            workflow_name = re.sub(r'[^a-zA-Z0-9_]', '_', workflow['name'][:50])  # Limit length

            # Try to extract date range from parameters
            start_date = "unknown"
            end_date = "unknown"

            if execution.get('parameters'):
                try:
                    params = json.loads(execution['parameters']) if isinstance(execution['parameters'], str) else execution['parameters']

                    # Common parameter names for dates
                    for start_key in ['startDate', 'start_date', 'from_date', 'fromDate']:
                        if start_key in params:
                            start_date = params[start_key][:10].replace('-', '_') if params[start_key] else "unknown"
                            break

                    for end_key in ['endDate', 'end_date', 'to_date', 'toDate']:
                        if end_key in params:
                            end_date = params[end_key][:10].replace('-', '_') if params[end_key] else "unknown"
                            break

                except Exception as e:
                    logger.debug(f"Could not parse parameters for date range: {e}")

            # Build table name
            table_name = f"{instance_name}_{workflow_name}_{start_date}_to_{end_date}"

            # Ensure table name is valid (alphanumeric and underscores only)
            table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)

            # Remove multiple consecutive underscores
            table_name = re.sub(r'_{2,}', '_', table_name)

            # Ensure it doesn't start with a number (Snowflake requirement)
            if table_name[0].isdigit():
                table_name = f"t_{table_name}"

            # Limit total length to 255 chars (Snowflake limit)
            if len(table_name) > 255:
                # Keep instance and dates, truncate workflow name
                table_name = f"{instance_name}_{workflow_name[:30]}_{start_date}_to_{end_date}"

            return table_name.upper()  # Snowflake prefers uppercase

        # Fallback to simple format if we can't get workflow info
        execution_date = execution.get('created_at', datetime.now().isoformat())[:10].replace('-', '_')
        execution_id_short = execution.get('execution_id', 'unknown')[-8:]
        return f"WORKFLOW_EXECUTION_{execution_date}_{execution_id_short}".upper()
    
    def _update_sync_status(self, sync_id: str, status: str, 
                          retry_count: int = None, error_message: str = None):
        """Update sync queue item status"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if status == 'completed':
                update_data['processed_at'] = datetime.now(timezone.utc).isoformat()
            elif retry_count is not None:
                update_data['retry_count'] = retry_count
            elif error_message:
                update_data['error_message'] = error_message
            
            response = self.client.table('snowflake_sync_queue')\
                .update(update_data)\
                .eq('id', sync_id)\
                .execute()
            
            if response.data:
                logger.debug(f"Updated sync status for {sync_id} to {status}")
            else:
                logger.warning(f"No sync item found with ID {sync_id}")
                
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    def _update_execution_snowflake_info(self, execution_id: str, table_name: str, 
                                       upload_result: Dict[str, Any]):
        """Update execution record with Snowflake sync information"""
        try:
            update_data = {
                'snowflake_enabled': True,  # Mark as enabled since we synced it
                'snowflake_table_name': table_name,
                'snowflake_status': 'completed',
                'snowflake_uploaded_at': datetime.now(timezone.utc).isoformat(),
                'snowflake_row_count': upload_result.get('row_count', 0)
            }
            
            response = self.client.table('workflow_executions')\
                .update(update_data)\
                .eq('execution_id', execution_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated execution {execution_id} with Snowflake info")
            else:
                logger.warning(f"No execution found with ID {execution_id}")
                
        except Exception as e:
            logger.error(f"Error updating execution Snowflake info: {e}")
    
    async def get_sync_stats(self) -> Dict[str, Any]:
        """Get sync queue statistics"""
        try:
            response = self.client.table('snowflake_sync_queue_summary')\
                .select('*')\
                .execute()
            
            stats = {}
            for row in response.data:
                stats[row['status']] = {
                    'count': row['count'],
                    'oldest_item': row['oldest_item'],
                    'newest_item': row['newest_item'],
                    'avg_retries': row['avg_retries']
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting sync stats: {e}")
            return {}
    
    async def get_failed_syncs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of failed syncs with details"""
        try:
            response = self.client.table('snowflake_sync_failures')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting failed syncs: {e}")
            return []
    
    async def retry_failed_sync(self, sync_id: str) -> bool:
        """Retry a failed sync"""
        try:
            # Reset retry count and status
            update_data = {
                'status': 'pending',
                'retry_count': 0,
                'error_message': None,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.client.table('snowflake_sync_queue')\
                .update(update_data)\
                .eq('id', sync_id)\
                .execute()
            
            if response.data:
                logger.info(f"Retrying sync {sync_id}")
                return True
            else:
                logger.warning(f"No sync item found with ID {sync_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error retrying sync {sync_id}: {e}")
            return False


# Singleton instance
universal_snowflake_sync_service = UniversalSnowflakeSyncService()
