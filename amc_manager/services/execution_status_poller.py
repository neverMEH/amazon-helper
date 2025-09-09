"""
Background service to poll AMC execution statuses
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set

from ..core.supabase_client import SupabaseManager
from .amc_execution_service import amc_execution_service

logger = logging.getLogger(__name__)


class ExecutionStatusPoller:
    """Service to poll pending/running executions and update their status"""
    
    def __init__(self, poll_interval: int = 15):
        """
        Initialize the poller
        
        Args:
            poll_interval: Seconds between polling cycles (default 15)
        """
        self.poll_interval = poll_interval
        self.is_running = False
        self._task = None
        self._processed_executions: Set[str] = set()
        
    async def start(self):
        """Start the polling service"""
        if self.is_running:
            logger.info("Execution status poller already running")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._polling_loop())
        logger.info(f"Started execution status poller (interval: {self.poll_interval}s)")
        
    async def stop(self):
        """Stop the polling service"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped execution status poller")
        
    async def _polling_loop(self):
        """Main polling loop"""
        while self.is_running:
            try:
                await self._poll_executions()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.poll_interval)
            
    async def _poll_executions(self):
        """Poll all pending/running executions"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get executions that need status updates
            # Only get executions from the last 2 hours to avoid polling old ones
            cutoff_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
            
            response = client.table('workflow_executions')\
                .select('id, execution_id, amc_execution_id, workflow_id, progress')\
                .in_('status', ['pending', 'running'])\
                .gte('started_at', cutoff_time)\
                .execute()
            
            if not response.data:
                return
            
            logger.info(f"Found {len(response.data)} executions to poll")
            
            for execution in response.data:
                execution_uuid = execution['id']  # Internal UUID for database relations
                execution_id = execution['execution_id']  # Human-readable ID
                amc_execution_id = execution.get('amc_execution_id')
                
                if not amc_execution_id:
                    logger.debug(f"Skipping {execution_id} - no AMC execution ID yet")
                    continue
                
                # Get workflow info to find instance and user
                workflow_response = client.table('workflows')\
                    .select('instance_id, user_id')\
                    .eq('id', execution['workflow_id'])\
                    .single()\
                    .execute()
                
                if not workflow_response.data:
                    logger.warning(f"Workflow not found for execution {execution_id}")
                    continue
                
                # Get instance info
                instance_response = client.table('amc_instances')\
                    .select('instance_id')\
                    .eq('id', workflow_response.data['instance_id'])\
                    .single()\
                    .execute()
                
                if not instance_response.data:
                    logger.warning(f"Instance not found for execution {execution_id}")
                    continue
                
                # Poll AMC for status update
                try:
                    logger.info(f"Polling status for execution {execution_id} (AMC: {amc_execution_id})")
                    
                    # Use the amc_execution_service to poll and update
                    user_id = workflow_response.data.get('user_id')
                    status = await amc_execution_service.poll_and_update_execution(
                        execution_id=execution_id,
                        user_id=user_id
                    )
                    
                    if status:
                        current_status = status.get('status', 'unknown')
                        progress = status.get('progress', 0)
                        logger.info(f"Execution {execution_id}: status={current_status}, progress={progress}%")
                        
                        # Update report_data_weeks if this execution is part of a collection
                        if current_status in ['completed', 'failed', 'cancelled']:
                            self._processed_executions.add(execution_id)
                            
                            # Check if this execution is linked to a report_data_weeks record
                            # Pass both the UUID and the execution_id
                            await self._update_report_week_status(execution_uuid, execution_id, current_status, status)
                    
                except Exception as e:
                    logger.error(f"Error polling execution {execution_id}: {e}")
                    
                # Small delay between individual polls to avoid rate limiting
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in poll_executions: {e}")
    
    async def _update_report_week_status(self, execution_uuid: str, execution_id: str, status: str, execution_data: dict):
        """Update report_data_weeks record if this execution is part of a collection
        
        Args:
            execution_uuid: Internal UUID of the workflow_execution record
            execution_id: Human-readable execution ID (exec_xxx)
            status: Execution status (completed, failed, cancelled)
            execution_data: Additional execution data including row_count
        """
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # We already have the UUID, no need to look it up
            workflow_execution_uuid = execution_uuid
            
            # Check if there's a report_data_weeks record linked to this execution
            # Try both possible column names for backward compatibility
            week_response = None
            try:
                # First try with 'execution_id' (newer schema)
                week_response = client.table('report_data_weeks')\
                    .select('id, status')\
                    .eq('execution_id', workflow_execution_uuid)\
                    .execute()
            except Exception as e:
                if 'PGRST204' in str(e) or 'column' in str(e).lower():
                    # Try with 'workflow_execution_id' (older schema)
                    try:
                        week_response = client.table('report_data_weeks')\
                            .select('id, status')\
                            .eq('workflow_execution_id', workflow_execution_uuid)\
                            .execute()
                    except:
                        # Column doesn't exist in either form
                        logger.debug(f"No execution tracking column found in report_data_weeks")
                        return
            
            if not week_response.data:
                # No report_data_weeks record linked to this execution
                return
            
            for week_record in week_response.data:
                # Only update if the week is still in 'running' status
                if week_record['status'] != 'running':
                    continue
                
                # Prepare update based on execution status
                update_data = {
                    'status': status,  # Always update the status
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if status == 'completed':
                    # Try to add completed_at if column exists
                    update_data['completed_at'] = datetime.utcnow().isoformat()
                    
                    # Add row count if available - the column is 'record_count' in the database
                    if 'row_count' in execution_data:
                        update_data['record_count'] = execution_data['row_count']
                    elif 'total_rows' in execution_data:
                        update_data['record_count'] = execution_data['total_rows']
                    
                    logger.info(f"Updating report_data_weeks {week_record['id']} to completed with {update_data.get('record_count', 0)} rows")
                    
                elif status == 'failed':
                    # Try to add completed_at if column exists
                    update_data['completed_at'] = datetime.utcnow().isoformat()
                    
                    # Add error message if available
                    if 'error_message' in execution_data:
                        update_data['error_message'] = execution_data['error_message']
                    
                    logger.info(f"Updating report_data_weeks {week_record['id']} to failed")
                    
                elif status == 'cancelled':
                    update_data['status'] = 'failed'  # Map cancelled to failed
                    update_data['completed_at'] = datetime.utcnow().isoformat()
                    update_data['error_message'] = 'Execution was cancelled'
                    
                    logger.info(f"Updating report_data_weeks {week_record['id']} to failed (cancelled)")
                
                # Update the week record
                client.table('report_data_weeks')\
                    .update(update_data)\
                    .eq('id', week_record['id'])\
                    .execute()
                    
                logger.info(f"Successfully updated report_data_weeks {week_record['id']} status to {update_data.get('status', status)}")
                
        except Exception as e:
            logger.error(f"Error updating report_data_weeks for execution {execution_id}: {e}")


# Global instance
execution_status_poller = ExecutionStatusPoller(poll_interval=15)