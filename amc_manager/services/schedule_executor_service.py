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
            run_id = None
            try:
                # Check for recent executions to prevent duplicates
                recent_runs = self.db.table('schedule_runs').select('*').eq(
                    'schedule_id', schedule_id
                ).gte('created_at', (datetime.utcnow() - timedelta(minutes=5)).isoformat()
                ).execute()
                
                if recent_runs.data:
                    logger.info(f"Schedule {schedule_id} has a recent run within 5 minutes, skipping")
                    return
                
                # Check if this is a test run (scheduled for very near future, not matching cron pattern)
                is_test_run = False
                if schedule.get('next_run_at'):
                    next_run_time = datetime.fromisoformat(schedule['next_run_at'].replace('Z', '+00:00'))
                    time_diff = (next_run_time - datetime.utcnow()).total_seconds()
                    # If scheduled within 2 minutes from now, likely a test run
                    if 0 < time_diff < 120:
                        is_test_run = True
                        logger.info(f"Detected test run for schedule {schedule_id}")
                
                # Only update next_run for regular runs, not test runs
                if not is_test_run:
                    # Always update next_run first to prevent duplicate executions
                    self.schedule_service.update_after_run(
                        schedule_id,
                        datetime.utcnow(),
                        success=False  # Assume failure, will update to success if it completes
                    )
                
                # Create schedule run record (with test run flag)
                run_id = await self.create_schedule_run(schedule, is_test_run=is_test_run)
                
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
                
                # Update schedule record with success (only for regular runs)
                if not is_test_run:
                    self.schedule_service.update_after_run(
                        schedule_id,
                        datetime.utcnow(),
                        success=True
                    )
                else:
                    # For test runs, restore the original next_run_at based on cron expression
                    from croniter import croniter
                    from zoneinfo import ZoneInfo
                    
                    cron = croniter(schedule.get('cron_expression', '0 2 * * *'))
                    tz = ZoneInfo(schedule.get('timezone', 'America/New_York'))
                    now = datetime.now(tz)
                    cron.set_current(now)
                    next_run = cron.get_next(datetime)
                    
                    self.db.table('workflow_schedules').update({
                        'next_run_at': next_run.isoformat()
                    }).eq('id', schedule_id).execute()
                    
                    logger.info(f"Test run completed, restored next_run_at to {next_run.isoformat()}")
                
                # Update run record
                await self.update_schedule_run(run_id, 'completed', execution['id'])
                
                logger.info(f"Successfully executed schedule {schedule_id}")
                
            except Exception as e:
                logger.error(f"Error executing schedule {schedule_id}: {e}", exc_info=True)
                
                # Note: next_run was already updated at the beginning to prevent duplicate executions
                
                # Update run record if it exists
                if run_id:
                    await self.update_schedule_run(
                        run_id,
                        'failed',
                        error_message=str(e)
                    )
                
                # Handle notification if configured
                await self.send_failure_notification(schedule, str(e))
    
    async def create_schedule_run(self, schedule: Dict[str, Any], is_test_run: bool = False) -> str:
        """
        Create a schedule run record
        
        Args:
            schedule: Schedule record
            is_test_run: Whether this is a test run
            
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
                # 'is_test_run': is_test_run  # Uncomment when column is added
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
                    new_tokens = await self.token_service.refresh_access_token(
                        auth_tokens.get('refresh_token')
                    )
                    
                    if not new_tokens:
                        raise ValueError("Failed to refresh token")
                    
                    # Store the refreshed tokens
                    await self.token_service.store_tokens(user_id, new_tokens)
                        
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
        
        # Use lookback_days if specified, otherwise calculate based on schedule type
        lookback_days = schedule.get('lookback_days')
        
        if lookback_days:
            # Use the configured lookback period
            start_date = end_date - timedelta(days=lookback_days)
        else:
            # Fall back to old logic if lookback_days not set
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
        Execute a workflow via AMC API using the existing amc_execution_service
        
        Args:
            workflow_id: Internal workflow ID
            workflow_amc_id: AMC workflow ID (not used anymore, kept for compatibility)
            instance: Instance record  
            user_id: User ID
            parameters: Execution parameters
            schedule_run_id: Schedule run ID
            
        Returns:
            Execution record
        """
        try:
            # Import the amc_execution_service
            from .amc_execution_service import amc_execution_service
            
            # Add schedule metadata to parameters
            execution_params = parameters.copy()
            execution_params['_schedule_run_id'] = schedule_run_id
            execution_params['_triggered_by'] = 'schedule'
            
            # Use the amc_execution_service to execute the workflow
            # This handles all the complexity of workflow creation, token refresh, etc.
            logger.info(f"Executing workflow {workflow_id} via amc_execution_service for schedule")
            
            result = await amc_execution_service.execute_workflow(
                workflow_id=workflow_id,
                user_id=user_id,
                execution_parameters=execution_params,
                triggered_by="schedule",
                instance_id=instance['instance_id']  # Pass the AMC instance ID
            )
            
            # Check if execution was successful
            if result.get('status') == 'failed':
                error_msg = result.get('error', 'Unknown error')
                raise Exception(f"Failed to execute workflow: {error_msg}")
            
            # Get the execution ID from the result
            execution_id = result.get('execution_id')
            if not execution_id:
                raise Exception("No execution ID returned from amc_execution_service")
            
            # Get the full execution record to return
            execution_result = self.db.table('workflow_executions').select('*').eq(
                'execution_id', execution_id
            ).single().execute()
            
            if not execution_result.data:
                raise Exception(f"Execution record {execution_id} not found after creation")
            
            execution = execution_result.data
            
            # Update the execution with the schedule_run_id if not already set
            if not execution.get('schedule_run_id'):
                self.db.table('workflow_executions').update({
                    'schedule_run_id': schedule_run_id
                }).eq('execution_id', execution_id).execute()
                execution['schedule_run_id'] = schedule_run_id
            
            logger.info(f"Successfully created execution {execution_id} for scheduled workflow")
            return execution
                
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