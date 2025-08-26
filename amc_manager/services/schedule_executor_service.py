"""Schedule Executor Service for running scheduled workflows - FIXED VERSION"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

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
        self._max_api_retries = 3  # Maximum retries for API errors
        self._needs_next_run_reset = set()  # Track schedules that need next_run reset
    
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
            # Get all due schedules with a tighter buffer (30 seconds instead of 2 minutes)
            due_schedules = self.schedule_service.get_due_schedules(buffer_minutes=0.5)
            
            if due_schedules:
                logger.info(f"Found {len(due_schedules)} potentially due schedules")
                
                for schedule in due_schedules:
                    # Skip if already executing
                    if schedule['id'] in self._execution_tasks:
                        logger.debug(f"Schedule {schedule['id']} is already executing")
                        continue
                    
                    # CRITICAL FIX: Atomic check-and-update to prevent race conditions
                    if await self._atomic_claim_schedule(schedule['id']):
                        # Create execution task only if we successfully claimed it
                        task = asyncio.create_task(self.execute_schedule(schedule))
                        self._execution_tasks[schedule['id']] = task
                        
                        # Clean up completed tasks
                        task.add_done_callback(
                            lambda t, sid=schedule['id']: self._execution_tasks.pop(sid, None)
                        )
                    else:
                        logger.debug(f"Schedule {schedule['id']} was claimed by another process or recently executed")
        
            # Reset next_run_at for stuck schedules (test runs that weren't properly reset)
            for schedule_id in self._needs_next_run_reset:
                try:
                    await self._reset_stuck_schedule(schedule_id)
                except Exception as e:
                    logger.error(f"Error resetting stuck schedule {schedule_id}: {e}")
            self._needs_next_run_reset.clear()
        
        except Exception as e:
            logger.error(f"Error checking schedules: {e}", exc_info=True)
    
    async def _atomic_claim_schedule(self, schedule_id: str) -> bool:
        """
        Atomically claim a schedule for execution to prevent duplicate runs
        
        This performs an atomic check-and-update operation to ensure only one
        process can claim a schedule for execution.
        
        Args:
            schedule_id: Schedule ID to claim
            
        Returns:
            True if successfully claimed, False if already claimed
        """
        try:
            # Get current schedule state
            current_schedule = self.db.table('workflow_schedules').select(
                'id', 'next_run_at', 'last_run_at'
            ).eq('id', schedule_id).single().execute()
            
            if not current_schedule.data:
                logger.error(f"Schedule {schedule_id} not found")
                return False
            
            schedule_data = current_schedule.data
            next_run_at = schedule_data.get('next_run_at')
            last_run_at = schedule_data.get('last_run_at')
            
            # Check if it's actually due (within 30 seconds of now)
            if next_run_at:
                next_run_time = datetime.fromisoformat(next_run_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_until_due = (next_run_time - now).total_seconds()
                
                # Skip if not actually due yet (more than 30 seconds away)
                if time_until_due > 30:
                    logger.debug(f"Schedule {schedule_id} not due yet ({time_until_due:.0f} seconds away)")
                    return False
            
            # Check for recent runs (prevent duplicate within 5 minutes)
            if last_run_at:
                last_run_time = datetime.fromisoformat(last_run_at.replace('Z', '+00:00'))
                time_since_last = (datetime.now(timezone.utc) - last_run_time).total_seconds()
                
                if time_since_last < 300:  # 5 minutes
                    logger.info(f"Schedule {schedule_id} ran {time_since_last:.0f} seconds ago, skipping")
                    return False
            
            # Check schedule_runs table for very recent executions (double-check)
            recent_runs = self.db.table('schedule_runs').select('created_at').eq(
                'schedule_id', schedule_id
            ).gte('created_at', (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            ).execute()
            
            if recent_runs.data and len(recent_runs.data) > 0:
                logger.info(f"Schedule {schedule_id} has {len(recent_runs.data)} recent runs, skipping")
                # IMPORTANT: If this was a test run that's now overdue, reset next_run_at
                if next_run_at and time_until_due < -300:  # More than 5 minutes overdue
                    logger.info(f"Schedule {schedule_id} appears stuck after test run, will reset next_run_at after skipping")
                    self._needs_next_run_reset.add(schedule_id)
                return False
            
            # ATOMIC UPDATE: Set last_run_at NOW to claim this execution
            # This prevents other processes from executing it
            claim_time = datetime.utcnow()
            
            # Build update query
            update_query = self.db.table('workflow_schedules').update({
                'last_run_at': claim_time.isoformat()
            }).eq('id', schedule_id)
            
            # Only add last_run_at condition if it's not None (optimistic locking)
            if last_run_at is not None:
                update_query = update_query.eq('last_run_at', last_run_at)
            else:
                # For schedules that have never run, use is_null check
                update_query = update_query.is_('last_run_at', 'null')
            
            update_result = update_query.execute()
            
            # If update affected a row, we successfully claimed it
            if update_result.data and len(update_result.data) > 0:
                logger.info(f"Successfully claimed schedule {schedule_id} for execution")
                return True
            else:
                logger.debug(f"Failed to claim schedule {schedule_id} - already claimed by another process")
                return False
                
        except Exception as e:
            logger.error(f"Error claiming schedule {schedule_id}: {e}")
            return False
    
    async def execute_schedule(self, schedule: Dict[str, Any]):
        """
        Execute a single scheduled workflow with retry logic for API errors
        
        Args:
            schedule: Schedule record with workflow details
        """
        schedule_id = schedule['id']
        workflow = schedule.get('workflows', {})
        
        logger.info(f"Executing schedule {schedule_id} for workflow {workflow.get('workflow_id')}")
        
        # Use semaphore to limit concurrent executions
        async with self._execution_semaphore:
            run_id = None
            execution_attempts = 0
            max_attempts = self._max_api_retries
            
            while execution_attempts < max_attempts:
                execution_attempts += 1
                
                try:
                    # Check if this is a test run
                    is_test_run = await self._is_test_run(schedule)
                    
                    # Create schedule run record (only on first attempt)
                    if execution_attempts == 1:
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
                    
                    # Debug logging for scheduled execution
                    logger.info(f"Retrieved instance for schedule: UUID={instance.get('id')}, AMC_ID={instance.get('instance_id')}, Name={instance.get('instance_name')}")
                    logger.info(f"Date parameters: startDate={params.get('startDate')}, endDate={params.get('endDate')}")
                    
                    # Execute workflow
                    execution = await self.execute_workflow(
                        workflow_id=workflow['id'],
                        workflow_amc_id=workflow.get('amc_workflow_id'),
                        instance=instance,
                        user_id=user_id,
                        parameters=params,
                        schedule_run_id=run_id,
                        attempt_number=execution_attempts
                    )
                    
                    # Success! Update next_run_at for regular runs
                    if not is_test_run:
                        await self._update_next_run(schedule_id, schedule)
                    else:
                        await self._restore_test_run_schedule(schedule_id, schedule)
                    
                    # Update run record
                    await self.update_schedule_run(run_id, 'completed', execution['id'])
                    
                    logger.info(f"Successfully executed schedule {schedule_id} on attempt {execution_attempts}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error executing schedule {schedule_id} (attempt {execution_attempts}/{max_attempts}): {error_msg}")
                    
                    # Check if this is an API error that warrants a retry
                    is_api_error = any(keyword in error_msg.lower() for keyword in [
                        'api', 'timeout', 'connection', 'network', '500', '502', '503', '504',
                        'rate limit', 'throttle', 'temporary', 'unavailable'
                    ])
                    
                    if is_api_error and execution_attempts < max_attempts:
                        # Wait before retry (exponential backoff)
                        wait_time = min(60, 10 * (2 ** (execution_attempts - 1)))  # 10s, 20s, 40s, max 60s
                        logger.info(f"API error detected, retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Final failure or non-retryable error
                        if run_id:
                            await self.update_schedule_run(
                                run_id,
                                'failed',
                                error_message=f"{error_msg} (after {execution_attempts} attempts)"
                            )
                        
                        # Update next_run_at even on failure to prevent infinite retries
                        if not await self._is_test_run(schedule):
                            await self._update_next_run(schedule_id, schedule)
                        
                        # Send failure notification
                        await self.send_failure_notification(schedule, error_msg)
                        break  # Exit retry loop
    
    async def _is_test_run(self, schedule: Dict[str, Any]) -> bool:
        """Check if this is a test run"""
        if schedule.get('next_run_at'):
            next_run_time = datetime.fromisoformat(schedule['next_run_at'].replace('Z', '+00:00'))
            time_diff = (next_run_time - datetime.now(timezone.utc)).total_seconds()
            # If scheduled within 2 minutes from now, likely a test run
            return 0 < time_diff < 120
        return False
    
    async def _update_next_run(self, schedule_id: str, schedule: Dict[str, Any]):
        """Calculate and update the next run time based on cron expression"""
        try:
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
            
            logger.info(f"Updated next_run_at for schedule {schedule_id} to {next_run.isoformat()}")
            
        except Exception as e:
            logger.error(f"Error updating next_run for schedule {schedule_id}: {e}")
    
    async def _reset_stuck_schedule(self, schedule_id: str):
        """Reset a schedule that's stuck after a test run"""
        try:
            # Get the schedule details
            schedule = self.db.table('workflow_schedules').select(
                'id', 'cron_expression', 'timezone'
            ).eq('id', schedule_id).single().execute()
            
            if not schedule.data:
                logger.error(f"Schedule {schedule_id} not found for reset")
                return
            
            await self._update_next_run(schedule_id, schedule.data)
            logger.info(f"Reset stuck schedule {schedule_id} to proper next run time")
            
        except Exception as e:
            logger.error(f"Error resetting stuck schedule {schedule_id}: {e}")
    
    async def _restore_test_run_schedule(self, schedule_id: str, schedule: Dict[str, Any]):
        """Restore original next_run_at for test runs"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error restoring test run schedule {schedule_id}: {e}")
    
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
        params['_schedule_id'] = schedule.get('id')
        params['_scheduled_execution'] = True
        
        return params
    
    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_amc_id: Optional[str],
        instance: Dict[str, Any],
        user_id: str,
        parameters: Dict[str, Any],
        schedule_run_id: str,
        attempt_number: int = 1
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
            attempt_number: Current attempt number for retries
            
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
            execution_params['_attempt_number'] = attempt_number
            
            # Use the amc_execution_service to execute the workflow
            logger.info(f"Executing workflow {workflow_id} via amc_execution_service (attempt {attempt_number})")
            
            # Make sure we have the AMC instance ID
            amc_instance_id = instance.get('instance_id')
            if not amc_instance_id:
                logger.error(f"No instance_id found in instance data. Instance UUID: {instance.get('id')}, Instance name: {instance.get('instance_name')}")
                raise ValueError(f"AMC instance ID not found for instance {instance.get('id')}")
            
            logger.info(f"Using AMC instance_id: {amc_instance_id} for scheduled execution")
            
            result = await amc_execution_service.execute_workflow(
                workflow_id=workflow_id,
                user_id=user_id,
                execution_parameters=execution_params,
                triggered_by="schedule",
                instance_id=amc_instance_id  # Pass the AMC instance ID
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