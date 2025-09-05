"""Background Collection Executor Service - Executes data collection operations asynchronously"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import uuid

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .historical_collection_service import historical_collection_service
from .reporting_database_service import reporting_db_service
from .db_service import db_service
from .token_service import token_service

logger = get_logger(__name__)


class CollectionExecutorService:
    """Background service for executing data collection operations"""
    
    def __init__(self):
        """Initialize the collection executor service"""
        self.running = False
        self.check_interval = 30  # Check every 30 seconds for pending collections
        self.db = SupabaseManager.get_client(use_service_role=True)
        self.reporting_db = reporting_db_service
        self.collection_service = historical_collection_service
        self.token_service = token_service
        
        # Execution management
        self._execution_tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent_collections = 5  # Limit concurrent collections
        self._max_concurrent_weeks = 10  # Limit concurrent week executions
        self._collection_semaphore = asyncio.Semaphore(self._max_concurrent_collections)
        self._week_semaphore = asyncio.Semaphore(self._max_concurrent_weeks)
        self._claimed_collections: Set[str] = set()  # Track claimed collections
        
        # Rate limiting
        self._rate_limit_delay = 2  # Seconds between AMC API calls
        self._last_api_call = datetime.now()
        
        # Retry configuration
        self._max_retries = 3
        self._retry_delay = 60  # Seconds before retry
    
    async def start(self):
        """Start the collection executor background task"""
        logger.info("Starting Collection Executor Service")
        self.running = True
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_abandoned_collections())
        
        while self.running:
            try:
                await self._check_and_execute_collections()
            except Exception as e:
                logger.error(f"Collection executor error: {e}", exc_info=True)
            
            # Wait for next check interval
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the collection executor service"""
        logger.info("Stopping Collection Executor Service")
        self.running = False
        
        # Wait for running executions to complete
        if self._execution_tasks:
            logger.info(f"Waiting for {len(self._execution_tasks)} collections to complete")
            await asyncio.gather(*self._execution_tasks.values(), return_exceptions=True)
    
    async def _check_and_execute_collections(self):
        """Check for pending collections and execute them"""
        try:
            # Find pending collections
            pending_collections = await self._get_pending_collections()
            
            if pending_collections:
                logger.info(f"Found {len(pending_collections)} pending collections")
                
                for collection in pending_collections:
                    collection_id = collection['collection_id']
                    
                    # Skip if already executing
                    if collection_id in self._execution_tasks:
                        continue
                    
                    # Atomically claim the collection
                    if await self._atomic_claim_collection(collection['id']):
                        # Create execution task
                        task = asyncio.create_task(
                            self._execute_collection_with_semaphore(collection)
                        )
                        self._execution_tasks[collection_id] = task
                        
                        # Clean up completed tasks
                        task.add_done_callback(
                            lambda t, cid=collection_id: self._cleanup_task(cid)
                        )
                    else:
                        logger.debug(f"Collection {collection_id} already claimed")
            
            # Also check for collections that need retry
            await self._check_failed_collections()
            
        except Exception as e:
            logger.error(f"Error checking collections: {e}", exc_info=True)
    
    async def _get_pending_collections(self) -> List[Dict[str, Any]]:
        """Get collections that are pending execution"""
        try:
            response = self.db.table('report_data_collections')\
                .select('*')\
                .in_('status', ['pending', 'running'])\
                .order('created_at')\
                .limit(10)\
                .execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting pending collections: {e}")
            return []
    
    async def _atomic_claim_collection(self, collection_uuid: str) -> bool:
        """
        Atomically claim a collection to prevent duplicate processing
        
        Returns:
            True if successfully claimed, False if already claimed
        """
        try:
            if collection_uuid in self._claimed_collections:
                return False
            
            # Update status to running atomically
            response = self.db.table('report_data_collections')\
                .update({'status': 'running', 'updated_at': datetime.now().isoformat()})\
                .eq('id', collection_uuid)\
                .in_('status', ['pending', 'paused'])\
                .execute()
            
            if response.data:
                self._claimed_collections.add(collection_uuid)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error claiming collection: {e}")
            return False
    
    async def _execute_collection_with_semaphore(self, collection: Dict[str, Any]):
        """Execute collection with semaphore control"""
        async with self._collection_semaphore:
            await self._execute_collection(collection)
    
    async def _execute_collection(self, collection: Dict[str, Any]):
        """Execute a data collection job"""
        collection_id = collection['collection_id']
        collection_uuid = collection['id']
        
        try:
            logger.info(f"Starting collection execution: {collection_id}")
            
            # Get pending weeks for this collection
            weeks = await self._get_pending_weeks(collection_uuid)
            
            if not weeks:
                logger.info(f"No pending weeks for collection {collection_id}")
                await self._complete_collection(collection_uuid)
                return
            
            logger.info(f"Processing {len(weeks)} weeks for collection {collection_id}")
            
            # Process weeks with rate limiting
            completed_weeks = 0
            failed_weeks = 0
            
            for week in weeks:
                # Check if collection was paused
                if await self._is_collection_paused(collection_uuid):
                    logger.info(f"Collection {collection_id} was paused")
                    break
                
                # Rate limiting
                await self._apply_rate_limit()
                
                # Execute week with semaphore control
                success = await self._execute_week_with_semaphore(
                    collection_uuid,
                    collection_id,
                    week
                )
                
                if success:
                    completed_weeks += 1
                else:
                    failed_weeks += 1
                    
                    # Stop on too many failures
                    if failed_weeks >= 3:
                        logger.error(f"Too many failures for collection {collection_id}")
                        await self._fail_collection(collection_uuid, "Too many week execution failures")
                        break
                
                # Update progress
                progress = int((completed_weeks / len(weeks)) * 100)
                await self._update_collection_progress(
                    collection_uuid,
                    collection_id,
                    progress,
                    completed_weeks
                )
            
            # Complete collection if all weeks processed
            if completed_weeks == len(weeks):
                await self._complete_collection(collection_uuid)
            elif not await self._is_collection_paused(collection_uuid):
                # Mark as failed if not paused and not all weeks completed
                await self._fail_collection(
                    collection_uuid,
                    f"Completed {completed_weeks}/{len(weeks)} weeks"
                )
            
        except Exception as e:
            logger.error(f"Error executing collection {collection_id}: {e}", exc_info=True)
            await self._fail_collection(collection_uuid, str(e))
        finally:
            # Remove from claimed set
            self._claimed_collections.discard(collection_uuid)
    
    async def _execute_week_with_semaphore(
        self,
        collection_uuid: str,
        collection_id: str,
        week: Dict[str, Any]
    ) -> bool:
        """Execute a week with semaphore control"""
        async with self._week_semaphore:
            return await self._execute_week(collection_uuid, collection_id, week)
    
    async def _execute_week(
        self,
        collection_uuid: str,
        collection_id: str,
        week: Dict[str, Any]
    ) -> bool:
        """Execute a single week of data collection"""
        try:
            logger.info(f"Executing week {week['week_start_date']} to {week['week_end_date']}")
            
            # Execute via collection service
            success = await self.collection_service.execute_collection_week(
                collection_id,
                week['id'],
                week['week_start_date'],
                week['week_end_date']
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing week: {e}")
            
            # Update week status to failed
            self.reporting_db.update_week_status(
                week['id'],
                'failed',
                error_message=str(e)
            )
            
            return False
    
    async def _get_pending_weeks(self, collection_uuid: str) -> List[Dict[str, Any]]:
        """Get pending weeks for a collection"""
        try:
            response = self.db.table('report_data_weeks')\
                .select('*')\
                .eq('collection_id', collection_uuid)\
                .in_('status', ['pending', 'failed'])\
                .order('week_start_date')\
                .execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting pending weeks: {e}")
            return []
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between AMC API calls"""
        now = datetime.now()
        time_since_last = (now - self._last_api_call).total_seconds()
        
        if time_since_last < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - time_since_last)
        
        self._last_api_call = datetime.now()
    
    async def _is_collection_paused(self, collection_uuid: str) -> bool:
        """Check if a collection has been paused"""
        try:
            response = self.db.table('report_data_collections')\
                .select('status')\
                .eq('id', collection_uuid)\
                .single()\
                .execute()
            
            return response.data and response.data['status'] == 'paused'
        except Exception as e:
            logger.error(f"Error checking collection status: {e}")
            return False
    
    async def _update_collection_progress(
        self,
        collection_uuid: str,
        collection_id: str,
        progress: int,
        weeks_completed: int
    ):
        """Update collection progress"""
        try:
            self.db.table('report_data_collections')\
                .update({
                    'progress_percentage': progress,
                    'weeks_completed': weeks_completed,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', collection_uuid)\
                .execute()
                
            logger.info(f"Collection {collection_id}: {progress}% complete ({weeks_completed} weeks)")
            
        except Exception as e:
            logger.error(f"Error updating collection progress: {e}")
    
    async def _complete_collection(self, collection_uuid: str):
        """Mark a collection as completed"""
        try:
            self.db.table('report_data_collections')\
                .update({
                    'status': 'completed',
                    'progress_percentage': 100,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', collection_uuid)\
                .execute()
                
            logger.info(f"Collection {collection_uuid} completed successfully")
            
        except Exception as e:
            logger.error(f"Error completing collection: {e}")
    
    async def _fail_collection(self, collection_uuid: str, error_message: str):
        """Mark a collection as failed"""
        try:
            self.db.table('report_data_collections')\
                .update({
                    'status': 'failed',
                    'error_message': error_message,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', collection_uuid)\
                .execute()
                
            logger.error(f"Collection {collection_uuid} failed: {error_message}")
            
        except Exception as e:
            logger.error(f"Error failing collection: {e}")
    
    def _cleanup_task(self, collection_id: str):
        """Clean up completed task"""
        self._execution_tasks.pop(collection_id, None)
        logger.debug(f"Cleaned up task for collection {collection_id}")
    
    async def _check_failed_collections(self):
        """Check for failed collections that should be retried"""
        try:
            # Find collections that failed recently and haven't exceeded retry limit
            cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
            
            response = self.db.table('report_data_collections')\
                .select('*')\
                .eq('status', 'failed')\
                .gte('updated_at', cutoff)\
                .execute()
            
            failed_collections = response.data or []
            
            for collection in failed_collections:
                # Check retry count (stored in configuration)
                config = collection.get('configuration', {})
                retry_count = config.get('retry_count', 0)
                
                if retry_count < self._max_retries:
                    # Update retry count and reset status
                    config['retry_count'] = retry_count + 1
                    
                    self.db.table('report_data_collections')\
                        .update({
                            'status': 'pending',
                            'configuration': config,
                            'error_message': None,
                            'updated_at': datetime.now().isoformat()
                        })\
                        .eq('id', collection['id'])\
                        .execute()
                    
                    logger.info(f"Retrying failed collection {collection['collection_id']} (attempt {retry_count + 1})")
            
        except Exception as e:
            logger.error(f"Error checking failed collections: {e}")
    
    async def _cleanup_abandoned_collections(self):
        """Periodic cleanup of abandoned collections"""
        while self.running:
            try:
                # Clean up collections stuck in 'running' for too long
                count = await self.collection_service.cleanup_abandoned_collections(hours_old=24)
                if count > 0:
                    logger.info(f"Cleaned up {count} abandoned collections")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)


# Singleton instance
_collection_executor_instance = None


def get_collection_executor() -> CollectionExecutorService:
    """Get or create the collection executor singleton"""
    global _collection_executor_instance
    if _collection_executor_instance is None:
        _collection_executor_instance = CollectionExecutorService()
    return _collection_executor_instance