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
                .select('execution_id, amc_execution_id, workflow_id, progress')\
                .in_('status', ['pending', 'running'])\
                .gte('started_at', cutoff_time)\
                .execute()
            
            if not response.data:
                return
            
            logger.info(f"Found {len(response.data)} executions to poll")
            
            for execution in response.data:
                execution_id = execution['execution_id']
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
                        
                        # Mark as processed if completed
                        if current_status in ['completed', 'failed', 'cancelled']:
                            self._processed_executions.add(execution_id)
                    
                except Exception as e:
                    logger.error(f"Error polling execution {execution_id}: {e}")
                    
                # Small delay between individual polls to avoid rate limiting
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in poll_executions: {e}")


# Global instance
execution_status_poller = ExecutionStatusPoller(poll_interval=15)