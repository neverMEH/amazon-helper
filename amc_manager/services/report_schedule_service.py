"""
Report Schedule Service for AMC Report Builder
Handles schedule management for recurring reports
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from croniter import croniter
import pytz
from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportScheduleService(DatabaseService):
    """Service for managing report schedules"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_schedule(self, report_id: str, schedule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a schedule for a report"""
        try:
            schedule_id = f"sch_{uuid.uuid4().hex[:8]}"

            # Calculate next run time
            next_run = self.calculate_next_run(
                schedule_data['cron_expression'],
                schedule_data.get('timezone', 'UTC')
            )

            schedule_record = {
                'schedule_id': schedule_id,
                'report_id': report_id,
                'schedule_type': schedule_data['schedule_type'],
                'cron_expression': schedule_data['cron_expression'],
                'timezone': schedule_data.get('timezone', 'UTC'),
                'default_parameters': schedule_data.get('default_parameters', {}),
                'is_active': True,
                'is_paused': False,
                'next_run_at': next_run.isoformat() if next_run else None,
                'run_count': 0,
                'failure_count': 0
            }

            response = self.client.table('report_schedules').insert(schedule_record).execute()

            if response.data:
                logger.info(f"Created schedule {schedule_id} for report {report_id}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return None

    @with_connection_retry
    def pause_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Pause a schedule"""
        try:
            response = self.client.table('report_schedules').update({
                'is_paused': True
            }).eq('id', schedule_id).execute()

            if response.data:
                logger.info(f"Paused schedule {schedule_id}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error pausing schedule: {e}")
            return None

    @with_connection_retry
    def resume_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Resume a paused schedule"""
        try:
            # Get schedule to recalculate next run
            schedule_response = self.client.table('report_schedules').select('*').eq('id', schedule_id).execute()

            if not schedule_response.data:
                return None

            schedule = schedule_response.data[0]

            # Calculate next run time from now
            next_run = self.calculate_next_run(
                schedule['cron_expression'],
                schedule['timezone']
            )

            response = self.client.table('report_schedules').update({
                'is_paused': False,
                'next_run_at': next_run.isoformat() if next_run else None
            }).eq('id', schedule_id).execute()

            if response.data:
                logger.info(f"Resumed schedule {schedule_id}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error resuming schedule: {e}")
            return None

    def calculate_next_run(self, cron_expression: str, timezone: str = 'UTC') -> Optional[datetime]:
        """Calculate next run time based on cron expression"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            cron = croniter(cron_expression, now)
            next_run = cron.get_next(datetime)

            # Convert to UTC for storage
            return next_run.astimezone(pytz.UTC).replace(tzinfo=None)

        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            return None

    @with_connection_retry
    def get_due_schedules(self, buffer_minutes: int = 5) -> List[Dict[str, Any]]:
        """Get schedules due for execution"""
        try:
            cutoff_time = datetime.utcnow() + timedelta(minutes=buffer_minutes)

            response = self.client.table('report_schedules').select('*').eq(
                'is_active', True
            ).eq(
                'is_paused', False
            ).lte(
                'next_run_at', cutoff_time.isoformat()
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching due schedules: {e}")
            return []

    @with_connection_retry
    def update_after_run(self, schedule_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update schedule after execution"""
        try:
            # Get current schedule
            schedule_response = self.client.table('report_schedules').select('*').eq('id', schedule_id).execute()

            if not schedule_response.data:
                return None

            schedule = schedule_response.data[0]

            # Calculate next run
            next_run = self.calculate_next_run(
                schedule['cron_expression'],
                schedule['timezone']
            )

            # Update counts
            update_data = {
                'last_run_at': datetime.utcnow().isoformat(),
                'last_run_status': status,
                'next_run_at': next_run.isoformat() if next_run else None,
                'run_count': schedule['run_count'] + 1
            }

            if status == 'failed':
                update_data['failure_count'] = schedule.get('failure_count', 0) + 1

            response = self.client.table('report_schedules').update(update_data).eq('id', schedule_id).execute()

            if response.data:
                logger.info(f"Updated schedule {schedule_id} after run with status {status}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error updating schedule after run: {e}")
            return None

    def get_cron_from_frequency(self, frequency: str) -> str:
        """Get cron expression from frequency string"""
        cron_map = {
            'daily': '0 2 * * *',      # 2 AM daily
            'weekly': '0 3 * * 1',      # 3 AM Monday
            'monthly': '0 4 1 * *',     # 4 AM first of month
            'quarterly': '0 5 1 1,4,7,10 *'  # 5 AM quarterly
        }
        return cron_map.get(frequency, '0 2 * * *')