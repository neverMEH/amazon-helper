"""Service for managing batch execution of workflows across multiple AMC instances."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID
import uuid
import secrets

from ..core.supabase_client import SupabaseManager
from .amc_execution_service import AMCExecutionService
from .db_service import db_service

logger = logging.getLogger(__name__)

# Configuration constants
MAX_CONCURRENT_EXECUTIONS = 5  # Rate limit for parallel executions
MAX_BATCH_SIZE = 100  # Maximum instances per batch
MAX_RETRY_ATTEMPTS = 3  # Retry attempts for transient failures
RETRY_DELAY_BASE = 2  # Base delay in seconds for exponential backoff


class BatchExecutionService:
    """Service for orchestrating batch execution of workflows across multiple instances."""

    def __init__(self):
        """Initialize the batch execution service."""
        self.supabase = SupabaseManager.get_client(use_service_role=True)
        self.amc_execution_service = AMCExecutionService()
        # Semaphore for rate limiting concurrent executions
        self.execution_semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)

    def generate_batch_id(self) -> str:
        """Generate a unique batch ID.
        
        Returns:
            str: A unique batch ID in format 'batch_XXXXXXXX'
        """
        # Use cryptographically secure random generation
        random_str = secrets.token_urlsafe(6)[:8].lower()
        return f"batch_{random_str}"
    
    def _get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow details from database.
        
        Args:
            workflow_id: The workflow ID (can be UUID or string ID with 'wf_' prefix)
            
        Returns:
            Workflow dict or None if not found
        """
        try:
            # Use db_service method which handles both UUID and string workflow IDs
            return db_service.get_workflow_by_id_sync(workflow_id)
        except Exception as e:
            logger.error(f"Error fetching workflow {workflow_id}: {e}")
            return None

    async def create_batch_execution(
        self,
        workflow_id: str,
        instance_ids: List[str],
        parameters: Dict[str, Any],
        instance_parameters: Optional[Dict[str, Dict[str, Any]]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Create a new batch execution record.
        
        Args:
            workflow_id: The workflow UUID to execute
            instance_ids: List of instance UUIDs to execute on
            parameters: Base parameters for all instances
            instance_parameters: Optional per-instance parameter overrides
            name: Optional name for the batch execution
            description: Optional description
            user_id: User ID creating the batch
            
        Returns:
            Dict containing the batch execution record
        """
        try:
            # Generate batch ID
            batch_id = self.generate_batch_id()
            
            # Get workflow details for default name directly from database
            loop = asyncio.get_event_loop()
            workflow = await loop.run_in_executor(
                None,
                self._get_workflow,
                workflow_id
            )
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Generate default name if not provided
            if not name:
                name = f"{workflow['name']} - Batch {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create batch execution record
            batch_data = {
                'batch_id': batch_id,
                'workflow_id': workflow_id,
                'name': name,
                'description': description,
                'instance_ids': instance_ids,
                'base_parameters': parameters,
                'instance_parameters': instance_parameters or {},
                'status': 'pending',
                'total_instances': len(instance_ids),
                'completed_instances': 0,
                'failed_instances': 0,
                'user_id': user_id
            }
            
            result = self.supabase.table('batch_executions').insert(batch_data).execute()
            
            if result.data:
                logger.info(f"Created batch execution {batch_id} for {len(instance_ids)} instances")
                return result.data[0]
            else:
                raise Exception("Failed to create batch execution record")
                
        except Exception as e:
            logger.error(f"Error creating batch execution: {str(e)}")
            raise

    async def execute_batch(
        self,
        workflow_id: str,
        instance_ids: List[str],
        parameters: Dict[str, Any],
        instance_parameters: Optional[Dict[str, Dict[str, Any]]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Execute a workflow across multiple instances as a batch.
        
        Args:
            workflow_id: The workflow UUID to execute
            instance_ids: List of instance UUIDs to execute on
            parameters: Base parameters for all instances
            instance_parameters: Optional per-instance parameter overrides
            name: Optional name for the batch execution
            description: Optional description
            user_id: User ID executing the batch
            
        Returns:
            Dict containing batch execution details and individual execution IDs
        """
        # Validate input
        if not instance_ids:
            raise ValueError("At least one instance ID must be provided")
        
        if len(instance_ids) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds maximum of {MAX_BATCH_SIZE} instances")
        
        try:
            # Create batch execution record
            batch = await self.create_batch_execution(
                workflow_id=workflow_id,
                instance_ids=instance_ids,
                parameters=parameters,
                instance_parameters=instance_parameters,
                name=name,
                description=description,
                user_id=user_id
            )
            
            batch_id = batch['id']
            batch_execution_id = batch['batch_id']
            
            # Update batch status to running
            self.supabase.table('batch_executions').update({
                'status': 'running',
                'started_at': datetime.utcnow().isoformat()
            }).eq('id', batch_id).execute()
            
            # Execute on each instance
            executions = []
            tasks = []
            
            for instance_id in instance_ids:
                # Merge base parameters with instance-specific overrides
                exec_params = parameters.copy()
                if instance_parameters and instance_id in instance_parameters:
                    exec_params.update(instance_parameters[instance_id])
                
                # Create execution task with retry logic
                task = self._execute_single_instance_with_retry(
                    workflow_id=workflow_id,
                    instance_id=instance_id,
                    parameters=exec_params,
                    batch_execution_id=batch_id,
                    user_id=user_id
                )
                tasks.append(task)
            
            # Execute all instances in parallel
            execution_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(execution_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to execute on instance {instance_ids[i]}: {str(result)}")
                    executions.append({
                        'instance_id': instance_ids[i],
                        'status': 'failed',
                        'error': str(result)
                    })
                else:
                    executions.append({
                        'instance_id': instance_ids[i],
                        'execution_id': result.get('execution_id'),
                        'status': result.get('status', 'pending')
                    })
            
            # Return batch details with execution list
            return {
                'batch_id': batch_execution_id,
                'batch_execution_id': batch_id,
                'workflow_id': workflow_id,
                'total_instances': len(instance_ids),
                'status': 'running',
                'executions': executions
            }
            
        except Exception as e:
            logger.error(f"Error executing batch: {str(e)}")
            raise

    def _is_valid_uuid(self, val: str) -> bool:
        """Check if a string is a valid UUID.
        
        Args:
            val: String to check
            
        Returns:
            bool: True if valid UUID, False otherwise
        """
        try:
            uuid.UUID(str(val))
            return True
        except (ValueError, AttributeError):
            return False
    
    async def _execute_single_instance_with_retry(
        self,
        workflow_id: str,
        instance_id: str,
        parameters: Dict[str, Any],
        batch_execution_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Execute workflow on a single instance with retry logic.
        
        Args:
            workflow_id: The workflow UUID
            instance_id: The instance UUID to execute on
            parameters: Execution parameters
            batch_execution_id: Parent batch execution UUID
            user_id: User ID
            
        Returns:
            Dict containing execution details
        """
        last_error = None
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                # Use semaphore for rate limiting
                async with self.execution_semaphore:
                    result = await self._execute_single_instance(
                        workflow_id=workflow_id,
                        instance_id=instance_id,
                        parameters=parameters,
                        batch_execution_id=batch_execution_id,
                        user_id=user_id
                    )
                    return result
                    
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Don't retry for non-transient errors
                if any(msg in error_str.lower() for msg in ['not found', 'access denied', 'invalid']):
                    logger.error(f"Non-transient error on instance {instance_id}: {e}")
                    raise
                
                # Log retry attempt
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    delay = RETRY_DELAY_BASE ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed for instance {instance_id}, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for instance {instance_id}: {e}")
        
        # All retries failed
        raise last_error or Exception(f"Failed to execute on instance {instance_id} after {MAX_RETRY_ATTEMPTS} attempts")
    
    async def _execute_single_instance(
        self,
        workflow_id: str,
        instance_id: str,
        parameters: Dict[str, Any],
        batch_execution_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Execute workflow on a single instance as part of a batch.
        
        Args:
            workflow_id: The workflow UUID
            instance_id: The instance UUID to execute on
            parameters: Execution parameters
            batch_execution_id: Parent batch execution UUID
            user_id: User ID
            
        Returns:
            Dict containing execution details
        """
        try:
            # Convert instance UUID to AMC instance ID if needed
            amc_instance_id = instance_id
            
            # Use proper UUID validation instead of string length check
            if self._is_valid_uuid(instance_id):
                # This is a UUID, need to get the AMC instance ID
                instance_data = self.supabase.table('amc_instances')\
                    .select('instance_id')\
                    .eq('id', instance_id)\
                    .single()\
                    .execute()
                
                if instance_data.data:
                    amc_instance_id = instance_data.data['instance_id']
                    logger.info(f"Converted UUID {instance_id} to AMC ID {amc_instance_id}")
                else:
                    raise ValueError(f"Instance with UUID {instance_id} not found")
            
            # Execute the workflow (AMCExecutionService.execute_workflow is synchronous)
            # Run it in a thread executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.amc_execution_service.execute_workflow,
                workflow_id,
                user_id,
                parameters,
                'batch',  # triggered_by
                amc_instance_id  # Pass AMC instance_id for batch execution
            )
            
            # Update the execution record to link it to the batch
            if result and 'execution_id' in result:
                self.supabase.table('workflow_executions').update({
                    'batch_execution_id': batch_execution_id,
                    'target_instance_id': instance_id,
                    'is_batch_member': True
                }).eq('id', result['execution_id']).execute()
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing on instance {instance_id}: {str(e)}")
            raise

    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get the status of a batch execution.
        
        Args:
            batch_id: The batch execution ID (format: batch_XXXXXXXX)
            
        Returns:
            Dict containing batch status and execution details
        """
        try:
            # Get batch execution record
            batch_result = self.supabase.table('batch_executions')\
                .select('*')\
                .eq('batch_id', batch_id)\
                .single()\
                .execute()
            
            if not batch_result.data:
                raise ValueError(f"Batch execution {batch_id} not found")
            
            batch = batch_result.data
            
            # Get all executions for this batch
            executions_result = self.supabase.table('workflow_executions')\
                .select('*, amc_instances!target_instance_id(name, instance_id)')\
                .eq('batch_execution_id', batch['id'])\
                .execute()
            
            executions = executions_result.data if executions_result.data else []
            
            # Calculate summary statistics
            status_counts = {
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }
            
            for exec in executions:
                status = exec.get('status', 'pending')
                if status in status_counts:
                    status_counts[status] += 1
            
            # Determine overall batch status
            if status_counts['running'] > 0:
                batch_status = 'running'
            elif status_counts['pending'] > 0:
                batch_status = 'running'
            elif status_counts['failed'] > 0 and status_counts['completed'] > 0:
                batch_status = 'partial'
            elif status_counts['failed'] > 0 and status_counts['completed'] == 0:
                batch_status = 'failed'
            elif status_counts['completed'] == batch['total_instances']:
                batch_status = 'completed'
            else:
                batch_status = batch['status']
            
            return {
                'batch_id': batch_id,
                'workflow_id': batch['workflow_id'],
                'name': batch['name'],
                'description': batch['description'],
                'status': batch_status,
                'total_instances': batch['total_instances'],
                'completed_instances': status_counts['completed'],
                'failed_instances': status_counts['failed'],
                'running_instances': status_counts['running'],
                'pending_instances': status_counts['pending'],
                'started_at': batch['started_at'],
                'completed_at': batch['completed_at'],
                'executions': executions,
                'status_counts': status_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting batch status: {str(e)}")
            raise

    async def get_batch_results(self, batch_id: str) -> Dict[str, Any]:
        """Get aggregated results from a batch execution.
        
        Args:
            batch_id: The batch execution ID (format: batch_XXXXXXXX)
            
        Returns:
            Dict containing aggregated results and per-instance results
        """
        try:
            # Get batch status first
            batch_status = await self.get_batch_status(batch_id)
            
            # Get all completed executions with results
            batch_result = self.supabase.table('batch_executions')\
                .select('id')\
                .eq('batch_id', batch_id)\
                .single()\
                .execute()
            
            if not batch_result.data:
                raise ValueError(f"Batch execution {batch_id} not found")
            
            batch_uuid = batch_result.data['id']
            
            # Get execution results
            results_query = self.supabase.table('workflow_executions')\
                .select('*, amc_instances!target_instance_id(name, instance_id, region)')\
                .eq('batch_execution_id', batch_uuid)\
                .eq('status', 'completed')
            
            results = results_query.execute()
            
            if not results.data:
                return {
                    'batch_id': batch_id,
                    'status': batch_status['status'],
                    'total_instances': batch_status['total_instances'],
                    'completed_instances': 0,
                    'results': [],
                    'aggregated_data': None
                }
            
            # Aggregate results
            all_rows = []
            instance_results = []
            
            for exec in results.data:
                instance_info = exec.get('amc_instances', {})
                
                # Extract result data
                result_rows = exec.get('result_rows', [])
                row_count = exec.get('row_count', 0)
                
                # Add instance identifier to each row
                for row in result_rows:
                    row_with_instance = row.copy() if isinstance(row, dict) else {'data': row}
                    row_with_instance['_instance_name'] = instance_info.get('name', 'Unknown')
                    row_with_instance['_instance_id'] = instance_info.get('instance_id', exec.get('target_instance_id'))
                    all_rows.append(row_with_instance)
                
                instance_results.append({
                    'instance_id': exec.get('target_instance_id'),
                    'instance_name': instance_info.get('name'),
                    'instance_region': instance_info.get('region'),
                    'execution_id': exec.get('execution_id'),
                    'row_count': row_count,
                    'duration_seconds': exec.get('duration_seconds'),
                    'completed_at': exec.get('completed_at')
                })
            
            # Get column definitions from first successful execution
            columns = []
            if results.data and results.data[0].get('result_columns'):
                columns = results.data[0]['result_columns']
                # Add instance columns
                columns.insert(0, {'name': '_instance_name', 'type': 'string'})
                columns.insert(1, {'name': '_instance_id', 'type': 'string'})
            
            return {
                'batch_id': batch_id,
                'status': batch_status['status'],
                'total_instances': batch_status['total_instances'],
                'completed_instances': batch_status['completed_instances'],
                'failed_instances': batch_status['failed_instances'],
                'instance_results': instance_results,
                'aggregated_data': {
                    'columns': columns,
                    'rows': all_rows,
                    'total_rows': len(all_rows)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting batch results: {str(e)}")
            raise

    async def cancel_batch_execution(self, batch_id: str) -> bool:
        """Cancel a batch execution and all its child executions.
        
        Args:
            batch_id: The batch execution ID to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            # Get batch execution
            batch_result = self.supabase.table('batch_executions')\
                .select('id')\
                .eq('batch_id', batch_id)\
                .single()\
                .execute()
            
            if not batch_result.data:
                raise ValueError(f"Batch execution {batch_id} not found")
            
            batch_uuid = batch_result.data['id']
            
            # Update batch status
            self.supabase.table('batch_executions').update({
                'status': 'cancelled',
                'completed_at': datetime.utcnow().isoformat()
            }).eq('id', batch_uuid).execute()
            
            # Cancel all pending/running child executions
            self.supabase.table('workflow_executions').update({
                'status': 'cancelled',
                'completed_at': datetime.utcnow().isoformat()
            }).eq('batch_execution_id', batch_uuid)\
              .in_('status', ['pending', 'running'])\
              .execute()
            
            logger.info(f"Cancelled batch execution {batch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling batch execution: {str(e)}")
            raise

    async def list_batch_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List batch executions with optional filters.
        
        Args:
            workflow_id: Optional workflow UUID to filter by
            user_id: Optional user ID to filter by
            status: Optional status to filter by
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of batch execution records
        """
        try:
            query = self.supabase.table('batch_executions')\
                .select('*, workflows(name, description)')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .offset(offset)
            
            if workflow_id:
                query = query.eq('workflow_id', workflow_id)
            if user_id:
                query = query.eq('user_id', user_id)
            if status:
                query = query.eq('status', status)
            
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error listing batch executions: {str(e)}")
            raise
    
    async def recover_stale_batch_executions(
        self,
        stale_threshold_minutes: int = 30
    ) -> Dict[str, Any]:
        """Recover batch executions stuck in running state.
        
        This method identifies batch executions that have been running longer than
        the threshold and attempts to recover them by checking their actual status
        or marking them as failed.
        
        Args:
            stale_threshold_minutes: Minutes after which a running batch is considered stale
            
        Returns:
            Dict with recovery statistics
        """
        try:
            stale_time = datetime.utcnow() - timedelta(minutes=stale_threshold_minutes)
            
            # Find stale batch executions
            stale_batches = self.supabase.table('batch_executions')\
                .select('*')\
                .eq('status', 'running')\
                .lt('started_at', stale_time.isoformat())\
                .execute()
            
            recovered = 0
            failed = 0
            
            for batch in (stale_batches.data or []):
                try:
                    # Check actual status of child executions
                    executions = self.supabase.table('workflow_executions')\
                        .select('status')\
                        .eq('batch_execution_id', batch['id'])\
                        .execute()
                    
                    if executions.data:
                        # Calculate actual status based on child executions
                        statuses = [e['status'] for e in executions.data]
                        
                        if all(s in ['completed', 'failed'] for s in statuses):
                            # All executions finished
                            if all(s == 'completed' for s in statuses):
                                new_status = 'completed'
                            elif all(s == 'failed' for s in statuses):
                                new_status = 'failed'
                            else:
                                new_status = 'partial'
                            
                            # Update batch status
                            self.supabase.table('batch_executions').update({
                                'status': new_status,
                                'completed_at': datetime.utcnow().isoformat(),
                                'completed_instances': len([s for s in statuses if s == 'completed']),
                                'failed_instances': len([s for s in statuses if s == 'failed'])
                            }).eq('id', batch['id']).execute()
                            
                            logger.info(f"Recovered stale batch {batch['batch_id']} with status {new_status}")
                            recovered += 1
                        else:
                            # Still has running/pending executions - check if they're actually stale
                            running_count = len([s for s in statuses if s in ['running', 'pending']])
                            if running_count > 0:
                                logger.warning(f"Batch {batch['batch_id']} has {running_count} executions still running after {stale_threshold_minutes} minutes")
                                # Could implement force-fail logic here if needed
                    else:
                        # No child executions found - mark as failed
                        self.supabase.table('batch_executions').update({
                            'status': 'failed',
                            'completed_at': datetime.utcnow().isoformat(),
                            'failed_instances': batch.get('total_instances', 0)
                        }).eq('id', batch['id']).execute()
                        
                        logger.error(f"Batch {batch['batch_id']} marked as failed - no child executions found")
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error recovering batch {batch.get('batch_id', 'unknown')}: {e}")
                    failed += 1
            
            return {
                'stale_batches_found': len(stale_batches.data or []),
                'recovered': recovered,
                'failed': failed,
                'threshold_minutes': stale_threshold_minutes
            }
            
        except Exception as e:
            logger.error(f"Error in batch recovery process: {e}")
            raise
    
    async def get_batch_health_metrics(self) -> Dict[str, Any]:
        """Get health metrics for batch execution system.
        
        Returns:
            Dict with system health metrics
        """
        try:
            # Get counts by status
            status_counts = {}
            for status in ['pending', 'running', 'completed', 'partial', 'failed', 'cancelled']:
                result = self.supabase.table('batch_executions')\
                    .select('*', count='exact')\
                    .eq('status', status)\
                    .execute()
                status_counts[status] = result.count or 0
            
            # Get recent execution stats (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent = self.supabase.table('batch_executions')\
                .select('*')\
                .gte('created_at', yesterday.isoformat())\
                .execute()
            
            recent_batches = recent.data or []
            
            # Calculate metrics
            total_instances = sum(b.get('total_instances', 0) for b in recent_batches)
            completed_instances = sum(b.get('completed_instances', 0) for b in recent_batches)
            failed_instances = sum(b.get('failed_instances', 0) for b in recent_batches)
            
            return {
                'status_counts': status_counts,
                'last_24_hours': {
                    'batches_created': len(recent_batches),
                    'total_instances': total_instances,
                    'completed_instances': completed_instances,
                    'failed_instances': failed_instances,
                    'success_rate': (completed_instances / total_instances * 100) if total_instances > 0 else 0
                },
                'current_running': status_counts.get('running', 0),
                'semaphore_available': self.execution_semaphore._value if hasattr(self.execution_semaphore, '_value') else MAX_CONCURRENT_EXECUTIONS
            }
            
        except Exception as e:
            logger.error(f"Error getting batch health metrics: {e}")
            return {
                'error': str(e),
                'status': 'unhealthy'
            }