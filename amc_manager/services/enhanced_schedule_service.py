"""Enhanced Schedule Service with flexible interval support"""

import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from croniter import croniter
from zoneinfo import ZoneInfo

from ..core.logger_simple import get_logger
from .db_service import DatabaseService

logger = get_logger(__name__)


class EnhancedScheduleService(DatabaseService):
    """Enhanced scheduling service with flexible interval support"""
    
    # Interval presets for common scheduling patterns
    INTERVAL_PRESETS = {
        'daily': {'cron': '0 2 * * *', 'description': 'Every day at 2 AM'},
        'every_3_days': {'cron': '0 2 */3 * *', 'description': 'Every 3 days at 2 AM'},
        'weekly': {'cron': '0 2 * * 1', 'description': 'Every Monday at 2 AM'},
        'bi_weekly': {'cron': '0 2 */14 * *', 'description': 'Every 14 days at 2 AM'},
        'monthly': {'cron': '0 2 1 * *', 'description': '1st of each month at 2 AM'},
        'monthly_last': {'cron': '0 2 L * *', 'description': 'Last day of month at 2 AM'},
        'quarterly': {'cron': '0 2 1 */3 *', 'description': 'Every 3 months on the 1st'},
        'business_day_first': {'cron': '0 8 1-3 * 1-5', 'description': 'First business day at 8 AM'},
        'business_day_last': {'cron': '0 8 L * 1-5', 'description': 'Last business day at 8 AM'},
    }
    
    # Supported interval days
    SUPPORTED_INTERVALS = [1, 3, 7, 14, 30, 60, 90]
    
    def __init__(self):
        """Initialize the enhanced schedule service"""
        super().__init__()
        
    def create_schedule_from_preset(
        self,
        workflow_id: str,
        preset_type: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        interval_days: Optional[int] = None,
        timezone: str = 'UTC',
        execute_time: str = '02:00',
        parameters: Optional[Dict[str, Any]] = None,
        notification_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a schedule from a user-friendly preset
        
        Args:
            workflow_id: ID of the workflow to schedule
            preset_type: Type of preset ('daily', 'interval', 'monthly', etc.)
            user_id: ID of the user creating the schedule
            interval_days: Number of days for interval type (1, 3, 7, 14, 30, 60, 90)
            timezone: Timezone for the schedule
            execute_time: Time of day to execute (HH:MM format)
            parameters: Default parameters for executions
            notification_config: Email/webhook notification settings
            
        Returns:
            Created schedule record
        """
        try:
            # Generate CRON expression based on preset
            cron_expression = self._generate_cron_expression(
                preset_type, 
                interval_days, 
                execute_time
            )
            
            # Validate CRON expression
            if not self._validate_cron_expression(cron_expression):
                raise ValueError(f"Invalid CRON expression generated: {cron_expression}")
            
            # Calculate next run time
            next_run_at = self._calculate_next_run(cron_expression, timezone)
            
            # First, get the actual UUID of the workflow from the workflows table
            workflow_result = self.client.table('workflows').select('id').eq('workflow_id', workflow_id).execute()
            if not workflow_result.data:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow_uuid = workflow_result.data[0]['id']
            
            # Create schedule record
            schedule_data = {
                'schedule_id': f"sched_{uuid.uuid4().hex[:12]}",
                'workflow_id': workflow_uuid,  # Use the UUID, not the workflow_id string
                'user_id': user_id,
                'name': name,  # Add name field
                'description': description,  # Add description field
                'schedule_type': preset_type,
                'interval_days': interval_days,
                'cron_expression': cron_expression,
                'timezone': timezone,
                'default_parameters': json.dumps(parameters or {}),
                'notification_config': json.dumps(notification_config or {}),
                'is_active': True,
                'next_run_at': next_run_at.isoformat() if next_run_at else None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('workflow_schedules').insert(schedule_data).execute()
            
            if result.data:
                logger.info(f"Created schedule {schedule_data['schedule_id']} for workflow {workflow_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create schedule")
                
        except Exception as e:
            logger.error(f"Error creating schedule from preset: {e}")
            raise
    
    def create_custom_schedule(
        self,
        workflow_id: str,
        cron_expression: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timezone: str = 'UTC',
        parameters: Optional[Dict[str, Any]] = None,
        notification_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a schedule with a custom CRON expression
        
        Args:
            workflow_id: ID of the workflow to schedule
            cron_expression: Custom CRON expression
            user_id: ID of the user creating the schedule
            timezone: Timezone for the schedule
            parameters: Default parameters for executions
            notification_config: Notification settings
            
        Returns:
            Created schedule record
        """
        try:
            # Validate CRON expression
            if not self._validate_cron_expression(cron_expression):
                raise ValueError(f"Invalid CRON expression: {cron_expression}")
            
            # Calculate next run time
            next_run_at = self._calculate_next_run(cron_expression, timezone)
            
            # First, get the actual UUID of the workflow from the workflows table
            workflow_result = self.client.table('workflows').select('id').eq('workflow_id', workflow_id).execute()
            if not workflow_result.data:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow_uuid = workflow_result.data[0]['id']
            
            # Create schedule record
            schedule_data = {
                'schedule_id': f"sched_{uuid.uuid4().hex[:12]}",
                'workflow_id': workflow_uuid,  # Use the UUID, not the workflow_id string
                'user_id': user_id,
                'name': name,  # Add name field
                'description': description,  # Add description field
                'schedule_type': 'custom',
                'cron_expression': cron_expression,
                'timezone': timezone,
                'default_parameters': json.dumps(parameters or {}),
                'notification_config': json.dumps(notification_config or {}),
                'is_active': True,
                'next_run_at': next_run_at.isoformat() if next_run_at else None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('workflow_schedules').insert(schedule_data).execute()
            
            if result.data:
                logger.info(f"Created custom schedule {schedule_data['schedule_id']} for workflow {workflow_id}")
                return result.data[0]
            else:
                raise Exception("Failed to create schedule")
                
        except Exception as e:
            logger.error(f"Error creating custom schedule: {e}")
            raise
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by ID
        
        Args:
            schedule_id: Schedule ID (can be UUID or string format like sched_xxx)
            
        Returns:
            Schedule record or None
        """
        try:
            # Check if schedule_id looks like a UUID or a string ID
            # If it starts with 'sched_' it's likely a string ID stored in schedule_id column
            # Otherwise treat it as the UUID id column
            if schedule_id.startswith('sched_'):
                # Query by schedule_id column
                result = self.client.table('workflow_schedules').select(
                    '*',
                    'workflows(*, amc_instances(id, instance_id, instance_name))'
                ).eq('schedule_id', schedule_id).single().execute()
            else:
                # Query by id column (UUID)
                result = self.client.table('workflow_schedules').select(
                    '*',
                    'workflows(*, amc_instances(id, instance_id, instance_name))'
                ).eq('id', schedule_id).single().execute()
            
            if result.data:
                # Parse JSON fields
                schedule = result.data
                if isinstance(schedule.get('default_parameters'), str):
                    schedule['default_parameters'] = json.loads(schedule['default_parameters'])
                if isinstance(schedule.get('notification_config'), str):
                    schedule['notification_config'] = json.loads(schedule['notification_config'])
                return schedule
            return None
            
        except Exception as e:
            logger.error(f"Error getting schedule {schedule_id}: {e}")
            return None
    
    def list_schedules(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List schedules with optional filters
        
        Args:
            workflow_id: Filter by workflow ID
            user_id: Filter by user ID
            is_active: Filter by active status
            limit: Maximum number of records
            offset: Pagination offset
            
        Returns:
            List of schedule records
        """
        try:
            query = self.client.table('workflow_schedules').select(
                '*',
                'workflows(id, workflow_id, name, instance_id, amc_instances(id, instance_id, instance_name))'
            )
            
            if workflow_id:
                # If workflow_id looks like a string ID (e.g., wf_xxxxx), look up the UUID
                if workflow_id.startswith('wf_'):
                    workflow_result = self.client.table('workflows').select('id').eq('workflow_id', workflow_id).execute()
                    if workflow_result.data:
                        workflow_uuid = workflow_result.data[0]['id']
                        query = query.eq('workflow_id', workflow_uuid)
                    else:
                        # No matching workflow, return empty list
                        return []
                else:
                    # Assume it's already a UUID
                    query = query.eq('workflow_id', workflow_id)
            if user_id:
                query = query.eq('user_id', user_id)
            if is_active is not None:
                query = query.eq('is_active', is_active)
            
            query = query.order('created_at', desc=True)
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            schedules = result.data or []
            
            # Parse JSON fields
            for schedule in schedules:
                if isinstance(schedule.get('default_parameters'), str):
                    schedule['default_parameters'] = json.loads(schedule['default_parameters'])
                if isinstance(schedule.get('notification_config'), str):
                    schedule['notification_config'] = json.loads(schedule['notification_config'])
            
            return schedules
            
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
            return []
    
    def update_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a schedule
        
        Args:
            schedule_id: Schedule ID
            updates: Fields to update
            
        Returns:
            Updated schedule record
        """
        try:
            # Handle JSON fields
            if 'default_parameters' in updates and not isinstance(updates['default_parameters'], str):
                updates['default_parameters'] = json.dumps(updates['default_parameters'])
            if 'notification_config' in updates and not isinstance(updates['notification_config'], str):
                updates['notification_config'] = json.dumps(updates['notification_config'])
            
            # Recalculate next run if CRON or timezone changed
            if 'cron_expression' in updates or 'timezone' in updates:
                schedule = self.get_schedule(schedule_id)
                if schedule:
                    cron = updates.get('cron_expression', schedule['cron_expression'])
                    tz = updates.get('timezone', schedule['timezone'])
                    next_run = self._calculate_next_run(cron, tz)
                    updates['next_run_at'] = next_run.isoformat() if next_run else None
            
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.client.table('workflow_schedules').update(
                updates
            ).eq('schedule_id', schedule_id).execute()
            
            if result.data:
                logger.info(f"Updated schedule {schedule_id}")
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {e}")
            return None
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = self.client.table('workflow_schedules').delete().eq(
                'schedule_id', schedule_id
            ).execute()
            
            logger.info(f"Deleted schedule {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule {schedule_id}: {e}")
            return False
    
    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule"""
        updates = {
            'is_active': True,
            'next_run_at': None  # Will be recalculated
        }
        
        # Get schedule to recalculate next run
        schedule = self.get_schedule(schedule_id)
        if schedule:
            next_run = self._calculate_next_run(
                schedule['cron_expression'],
                schedule['timezone']
            )
            updates['next_run_at'] = next_run.isoformat() if next_run else None
        
        result = self.update_schedule(schedule_id, updates)
        return result is not None
    
    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule"""
        updates = {'is_active': False}
        result = self.update_schedule(schedule_id, updates)
        return result is not None
    
    def calculate_next_runs(
        self,
        schedule_id: str,
        count: int = 10
    ) -> List[datetime]:
        """
        Preview the next N execution times for a schedule
        
        Args:
            schedule_id: Schedule ID
            count: Number of next runs to calculate
            
        Returns:
            List of datetime objects for next runs
        """
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return []
            
            cron = croniter(schedule['cron_expression'])
            tz = ZoneInfo(schedule['timezone'])
            
            # Start from now in the schedule's timezone
            now = datetime.now(tz)
            cron.set_current(now)
            
            next_runs = []
            for _ in range(count):
                next_run = cron.get_next(datetime)
                next_runs.append(next_run)
            
            return next_runs
            
        except Exception as e:
            logger.error(f"Error calculating next runs for schedule {schedule_id}: {e}")
            return []
    
    def get_due_schedules(self, buffer_minutes: int = 1) -> List[Dict[str, Any]]:
        """
        Get schedules that are due to run
        
        Args:
            buffer_minutes: Minutes of buffer for checking due schedules
            
        Returns:
            List of due schedules
        """
        try:
            now = datetime.utcnow()
            buffer_time = now + timedelta(minutes=buffer_minutes)
            
            result = self.client.table('workflow_schedules').select(
                '*',
                'workflows(*)'
            ).eq('is_active', True).lte('next_run_at', buffer_time.isoformat()).execute()
            
            schedules = result.data or []
            
            # Parse JSON fields
            for schedule in schedules:
                if isinstance(schedule.get('default_parameters'), str):
                    schedule['default_parameters'] = json.loads(schedule['default_parameters'])
                if isinstance(schedule.get('notification_config'), str):
                    schedule['notification_config'] = json.loads(schedule['notification_config'])
            
            return schedules
            
        except Exception as e:
            logger.error(f"Error getting due schedules: {e}")
            return []
    
    def update_after_run(
        self,
        schedule_id: str,
        last_run_at: datetime,
        success: bool = True
    ) -> bool:
        """
        Update schedule after execution
        
        Args:
            schedule_id: Schedule ID
            last_run_at: Time of last execution
            success: Whether the execution was successful
            
        Returns:
            True if updated successfully
        """
        try:
            schedule = self.get_schedule(schedule_id)
            if not schedule:
                return False
            
            # Calculate next run time
            next_run_at = self._calculate_next_run(
                schedule['cron_expression'],
                schedule['timezone'],
                after=last_run_at
            )
            
            updates = {
                'last_run_at': last_run_at.isoformat() if isinstance(last_run_at, datetime) else last_run_at,
                'next_run_at': next_run_at.isoformat() if next_run_at else None,
                'execution_count': schedule.get('execution_count', 0) + 1
            }
            
            # Update success/failure counts
            if success:
                updates['success_count'] = schedule.get('success_count', 0) + 1
            else:
                updates['failure_count'] = schedule.get('failure_count', 0) + 1
            
            # Handle failure threshold if configured
            if not success and schedule.get('auto_pause_on_failure'):
                failure_count = schedule.get('consecutive_failures', 0) + 1
                updates['consecutive_failures'] = failure_count
                
                if failure_count >= schedule.get('failure_threshold', 3):
                    updates['is_active'] = False
                    logger.warning(f"Auto-pausing schedule {schedule_id} after {failure_count} failures")
            elif success:
                updates['consecutive_failures'] = 0
            
            result = self.update_schedule(schedule_id, updates)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id} after run: {e}")
            return False
    
    def _generate_cron_expression(
        self,
        preset_type: str,
        interval_days: Optional[int] = None,
        execute_time: str = '02:00'
    ) -> str:
        """
        Generate CRON expression from preset type
        
        Args:
            preset_type: Type of preset
            interval_days: Days for interval type
            execute_time: Time of day (HH:MM)
            
        Returns:
            CRON expression string
        """
        # Parse execute time
        hour, minute = execute_time.split(':')
        
        if preset_type == 'interval' and interval_days:
            if interval_days == 1:
                return f"{minute} {hour} * * *"  # Daily
            else:
                return f"{minute} {hour} */{interval_days} * *"  # Every N days
        
        elif preset_type in self.INTERVAL_PRESETS:
            # Use preset but replace time
            base_cron = self.INTERVAL_PRESETS[preset_type]['cron']
            parts = base_cron.split()
            parts[0] = minute
            parts[1] = hour
            return ' '.join(parts)
        
        elif preset_type == 'weekly_custom':
            # Custom weekly (specific day)
            return f"{minute} {hour} * * 1"  # Default to Monday
        
        elif preset_type == 'monthly_specific':
            # Specific day of month
            return f"{minute} {hour} 15 * *"  # Default to 15th
        
        else:
            # Default to daily
            return f"{minute} {hour} * * *"
    
    def _validate_cron_expression(self, cron_expression: str) -> bool:
        """
        Validate a CRON expression
        
        Args:
            cron_expression: CRON expression to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            croniter(cron_expression)
            return True
        except Exception:
            return False
    
    def _calculate_next_run(
        self,
        cron_expression: str,
        timezone: str,
        after: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate next run time for a CRON expression
        
        Args:
            cron_expression: CRON expression
            timezone: Timezone string
            after: Calculate next run after this time (default: now)
            
        Returns:
            Next run time in UTC
        """
        try:
            tz = ZoneInfo(timezone)
            
            # Start from specified time or now
            if after:
                start_time = after if after.tzinfo else after.replace(tzinfo=tz)
            else:
                start_time = datetime.now(tz)
            
            # Calculate next run in local timezone
            cron = croniter(cron_expression, start_time)
            next_run_local = cron.get_next(datetime)
            
            # Convert to UTC for storage
            if next_run_local.tzinfo is None:
                next_run_local = next_run_local.replace(tzinfo=tz)
            
            next_run_utc = next_run_local.astimezone(ZoneInfo('UTC'))
            
            return next_run_utc.replace(tzinfo=None)  # Store as naive UTC
            
        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            # Default to 1 hour from now
            return datetime.utcnow() + timedelta(hours=1)
    
    def check_schedule_conflicts(
        self,
        workflow_id: str,
        cron_expression: str,
        exclude_schedule_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for scheduling conflicts with existing schedules
        
        Args:
            workflow_id: Workflow ID
            cron_expression: Proposed CRON expression
            exclude_schedule_id: Schedule ID to exclude from check (for updates)
            
        Returns:
            List of conflicting schedules
        """
        try:
            query = self.client.table('workflow_schedules').select('*').eq(
                'workflow_id', workflow_id
            ).eq('is_active', True)
            
            if exclude_schedule_id:
                query = query.neq('schedule_id', exclude_schedule_id)
            
            result = query.execute()
            
            conflicts = []
            for schedule in result.data or []:
                if schedule['cron_expression'] == cron_expression:
                    conflicts.append(schedule)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking schedule conflicts: {e}")
            return []