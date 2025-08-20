"""Schedule Executor Service for running scheduled workflows"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .enhanced_schedule_service import EnhancedScheduleService
from .token_service import TokenService
from .amc_api_client_with_retry import amc_api_client_with_retry

logger = get_logger(__name__)


class ScheduleExecutorService:
    """Background service for executing scheduled workflows"""
    
    def __init__(self):
        """Initialize the schedule executor service"""
        self.running = False
        self.check_interval = 60  # Check every minute
        self.schedule_service = EnhancedScheduleService()
        self.token_service = TokenService()
        self.db = SupabaseManager.get_client()
        self._execution_tasks = {}  # Track running executions
        self._max_concurrent_executions = 10
        self._execution_semaphore = asyncio.Semaphore(self._max_concurrent_executions)
    
    async def start(self):
        """Start the schedule executor background task"""
        logger.info("Starting Schedule Executor Service")
        self.running = True
        
        while self.running:
            try:
                await self.check_and_execute_schedules()
            except Exception as e:
                logger.error(f"Schedule executor error: {e}", exc_info=True)
            
            # Wait for next check interval
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the schedule executor service"""
        logger.info("Stopping Schedule Executor Service")
        self.running = False
        
        # Wait for running executions to complete
        if self._execution_tasks:
            logger.info(f"Waiting for {len(self._execution_tasks)} executions to complete")
            await asyncio.gather(*self._execution_tasks.values(), return_exceptions=True)
    
    async def check_and_execute_schedules(self):
        """Check for due schedules and execute them"""
        try:
            # Get all due schedules
            due_schedules = self.schedule_service.get_due_schedules(buffer_minutes=2)
            
            if due_schedules:
                logger.info(f"Found {len(due_schedules)} due schedules")
                
                for schedule in due_schedules:
                    # Skip if already executing
                    if schedule['id'] in self._execution_tasks:
                        logger.debug(f"Schedule {schedule['id']} is already executing")
                        continue
                    
                    # Create execution task
                    task = asyncio.create_task(self.execute_schedule(schedule))
                    self._execution_tasks[schedule['id']] = task
                    
                    # Clean up completed tasks
                    task.add_done_callback(
                        lambda t, sid=schedule['id']: self._execution_tasks.pop(sid, None)
                    )
        
        except Exception as e:
            logger.error(f"Error checking schedules: {e}", exc_info=True)
    
    async def execute_schedule(self, schedule: Dict[str, Any]):
        """
        Execute a single scheduled workflow
        
        Args:
            schedule: Schedule record with workflow details
        """
        schedule_id = schedule['id']  # Use 'id' not 'schedule_id'
        workflow = schedule.get('workflows', {})
        
        logger.info(f"Executing schedule {schedule_id} for workflow {workflow.get('workflow_id')}")
        
        # Use semaphore to limit concurrent executions
        async with self._execution_semaphore:
            try:
                # Create schedule run record
                run_id = await self.create_schedule_run(schedule)
                
                # Ensure fresh token
                user_id = schedule.get('user_id') or workflow.get('user_id')
                if not user_id:
                    raise ValueError("No user_id found for schedule")
                
                await self.ensure_fresh_token(user_id)
                
                # Calculate dynamic parameters
                params = await self.calculate_parameters(schedule)
                
                # Get instance information
                instance_id = workflow.get('instance_id')
                if not instance_id:
                    raise ValueError("No instance_id found for workflow")
                
                # Get instance details
                instance_result = self.db.table('amc_instances').select('*').eq(
                    'id', instance_id
                ).single().execute()
                
                if not instance_result.data:
                    raise ValueError(f"Instance {instance_id} not found")
                
                instance = instance_result.data
                
                # Execute workflow
                execution = await self.execute_workflow(
                    workflow_id=workflow['id'],
                    workflow_amc_id=workflow.get('amc_workflow_id'),
                    instance=instance,
                    user_id=user_id,
                    parameters=params,
                    schedule_run_id=run_id
                )
                
                # Update schedule record
                self.schedule_service.update_after_run(
                    schedule_id,
                    datetime.utcnow(),
                    success=True
                )
                
                # Update run record
                await self.update_schedule_run(run_id, 'completed', execution['id'])
                
                logger.info(f"Successfully executed schedule {schedule_id}")
                
            except Exception as e:
                logger.error(f"Error executing schedule {schedule_id}: {e}", exc_info=True)
                
                # Update schedule with failure
                self.schedule_service.update_after_run(
                    schedule_id,
                    datetime.utcnow(),
                    success=False
                )
                
                # Update run record if it exists
                if 'run_id' in locals():
                    await self.update_schedule_run(
                        run_id,
                        'failed',
                        error_message=str(e)
                    )
                
                # Handle notification if configured
                await self.send_failure_notification(schedule, str(e))
    
    async def create_schedule_run(self, schedule: Dict[str, Any]) -> str:
        """
        Create a schedule run record
        
        Args:
            schedule: Schedule record
            
        Returns:
            Run ID
        """
        try:
            # Get the last run number
            last_run = self.db.table('schedule_runs').select('run_number').eq(
                'schedule_id', schedule['id']
            ).order('run_number', desc=True).limit(1).execute()
            
            run_number = 1
            if last_run.data:
                run_number = last_run.data[0]['run_number'] + 1
            
            # Create run record
            run_data = {
                'id': str(uuid.uuid4()),
                'schedule_id': schedule['id'],
                'run_number': run_number,
                'scheduled_at': schedule.get('next_run_at', datetime.utcnow().isoformat()),
                'started_at': datetime.utcnow().isoformat(),
                'status': 'running',
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.db.table('schedule_runs').insert(run_data).execute()
            
            if result.data:
                return run_data['id']
            else:
                raise Exception("Failed to create schedule run record")
                
        except Exception as e:
            logger.error(f"Error creating schedule run: {e}")
            # Return a dummy ID to continue execution
            return str(uuid.uuid4())
    
    async def update_schedule_run(
        self,
        run_id: str,
        status: str,
        execution_id: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Update a schedule run record
        
        Args:
            run_id: Run ID
            status: New status
            execution_id: Execution ID if successful
            error_message: Error message if failed
        """
        try:
            updates = {
                'status': status,
                'completed_at': datetime.utcnow().isoformat() if status in ['completed', 'failed'] else None
            }
            
            if execution_id:
                updates['execution_count'] = 1
                updates['successful_count'] = 1 if status == 'completed' else 0
                updates['failed_count'] = 1 if status == 'failed' else 0
            
            if error_message:
                updates['error_summary'] = error_message
            
            self.db.table('schedule_runs').update(updates).eq('id', run_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating schedule run {run_id}: {e}")
    
    async def ensure_fresh_token(self, user_id: str):
        """
        Ensure user has a fresh access token
        
        Args:
            user_id: User ID
        """
        try:
            # Get user's current token
            user_result = self.db.table('users').select('auth_tokens').eq(
                'id', user_id
            ).single().execute()
            
            if not user_result.data:
                raise ValueError(f"User {user_id} not found")
            
            auth_tokens = user_result.data.get('auth_tokens')
            if not auth_tokens:
                raise ValueError(f"User {user_id} has no auth tokens")
            
            # Parse tokens if they're a string
            if isinstance(auth_tokens, str):
                auth_tokens = json.loads(auth_tokens)
            
            # Check if token needs refresh (15 minute buffer)
            expires_at = auth_tokens.get('expires_at')
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                buffer_time = datetime.utcnow() + timedelta(minutes=15)
                
                if expiry_time <= buffer_time:
                    logger.info(f"Refreshing token for user {user_id} before scheduled execution")
                    
                    # Refresh the token
                    new_tokens = await self.token_service.refresh_token(
                        auth_tokens.get('refresh_token'),
                        user_id
                    )
                    
                    if not new_tokens:
                        raise ValueError("Failed to refresh token")
                        
        except Exception as e:
            logger.error(f"Error ensuring fresh token for user {user_id}: {e}")
            raise
    
    async def calculate_parameters(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate dynamic parameters based on schedule frequency
        
        Args:
            schedule: Schedule record
            
        Returns:
            Parameters dictionary
        """
        # Start with default parameters
        params = schedule.get('default_parameters', {})
        
        # Account for AMC's 14-day data lag
        end_date = datetime.utcnow() - timedelta(days=14)
        
        # Calculate lookback based on schedule type and interval
        interval_days = schedule.get('interval_days')
        schedule_type = schedule.get('schedule_type', 'daily')
        
        if interval_days:
            # Use specified interval
            start_date = end_date - timedelta(days=interval_days)
        elif schedule_type == 'daily':
            # Daily schedule - look back 1 day
            start_date = end_date - timedelta(days=1)
        elif schedule_type == 'weekly':
            # Weekly schedule - look back 7 days
            start_date = end_date - timedelta(days=7)
        elif schedule_type == 'monthly':
            # Monthly schedule - look back 30 days
            start_date = end_date - timedelta(days=30)
        else:
            # Default to 7 days
            start_date = end_date - timedelta(days=7)
        
        # Format dates for AMC (no Z suffix)
        params['startDate'] = start_date.strftime('%Y-%m-%dT00:00:00')
        params['endDate'] = end_date.strftime('%Y-%m-%dT23:59:59')
        
        # Add schedule metadata
        params['_schedule_id'] = schedule.get('id')  # Use 'id' not 'schedule_id'
        params['_scheduled_execution'] = True
        
        return params
    
    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_amc_id: Optional[str],
        instance: Dict[str, Any],
        user_id: str,
        parameters: Dict[str, Any],
        schedule_run_id: str
    ) -> Dict[str, Any]:
        """
        Execute a workflow via AMC API
        
        Args:
            workflow_id: Internal workflow ID
            workflow_amc_id: AMC workflow ID
            instance: Instance record
            user_id: User ID
            parameters: Execution parameters
            schedule_run_id: Schedule run ID
            
        Returns:
            Execution record
        """
        try:
            # Get workflow details
            workflow_result = self.db.table('workflows').select('*').eq(
                'id', workflow_id
            ).single().execute()
            
            if not workflow_result.data:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = workflow_result.data
            
            # Create or get AMC workflow if needed
            if not workflow_amc_id:
                logger.info(f"Creating AMC workflow for {workflow_id}")
                
                # Generate a unique workflow ID for AMC
                import string
                import random
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                new_workflow_id = f"wf_{random_suffix}"
                
                # Convert parameters to input_parameters format for AMC
                input_parameters = []
                if parameters:
                    for key, value in parameters.items():
                        input_parameters.append({
                            'name': key,
                            'dataType': 'STRING',
                            'defaultValue': str(value) if value else None
                        })
                
                amc_workflow = await amc_api_client_with_retry.create_workflow(
                    instance_id=instance['instance_id'],
                    workflow_id=new_workflow_id,
                    sql_query=workflow['sql_query'],
                    user_id=user_id,
                    entity_id=instance.get('entity_id'),
                    input_parameters=input_parameters if input_parameters else None
                )
                workflow_amc_id = amc_workflow.get('workflowId') or new_workflow_id
                
                # Update workflow with AMC ID
                self.db.table('workflows').update({
                    'amc_workflow_id': workflow_amc_id,
                    'is_synced_to_amc': True
                }).eq('id', workflow_id).execute()
            
            # Execute the workflow
            logger.info(f"Executing AMC workflow {workflow_amc_id} on instance {instance['instance_id']}")
            
            amc_execution = await amc_api_client_with_retry.create_workflow_execution(
                instance_id=instance['instance_id'],
                user_id=user_id,
                entity_id=instance.get('entity_id'),
                workflow_id=workflow_amc_id,
                parameter_values=parameters
            )
            
            # Create execution record
            execution_data = {
                'id': str(uuid.uuid4()),
                'execution_id': f"exec_{uuid.uuid4().hex[:8]}",  # Required field
                'workflow_id': workflow_id,
                'instance_id': instance['instance_id'],
                'amc_execution_id': amc_execution.get('executionId'),
                'amc_workflow_id': workflow_amc_id,
                'status': 'PENDING',
                'execution_parameters': json.dumps(parameters),  # Use correct column name
                'schedule_run_id': schedule_run_id,
                'started_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.db.table('workflow_executions').insert(execution_data).execute()
            
            if result.data:
                logger.info(f"Created execution {execution_data['id']} for scheduled workflow")
                
                # Update schedule run with workflow execution ID
                self.db.table('schedule_runs').update({
                    'workflow_execution_id': execution_data['id']
                }).eq('id', schedule_run_id).execute()
                
                return result.data[0]
            else:
                raise Exception("Failed to create execution record")
                
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            raise
    
    async def send_failure_notification(self, schedule: Dict[str, Any], error_message: str):
        """
        Send failure notification if configured
        
        Args:
            schedule: Schedule record
            error_message: Error message
        """
        try:
            notification_config = schedule.get('notification_config', {})
            
            if notification_config.get('on_failure'):
                # TODO: Implement email/webhook notification
                logger.info(f"Would send failure notification for schedule {schedule['id']}: {error_message}")
                
        except Exception as e:
            logger.error(f"Error sending failure notification: {e}")


# Singleton instance
_executor_instance = None


def get_schedule_executor() -> ScheduleExecutorService:
    """Get the singleton schedule executor instance"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ScheduleExecutorService()
    return _executor_instance


async def start_schedule_executor():
    """Start the schedule executor service"""
    executor = get_schedule_executor()
    await executor.start()


async def stop_schedule_executor():
    """Stop the schedule executor service"""
    executor = get_schedule_executor()
    await executor.stop()