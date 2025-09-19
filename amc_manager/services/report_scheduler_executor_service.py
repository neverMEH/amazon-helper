"""
Report Scheduler Executor Service
Handles automatic execution of scheduled reports using ad-hoc AMC queries
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from croniter import croniter
import pytz

from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.services.report_execution_service import ReportExecutionService
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportSchedulerExecutorService(DatabaseService):
    """
    Background service that checks for due report schedules and executes them
    using ad-hoc AMC queries (not workflows)
    """

    def __init__(self):
        super().__init__()
        self.execution_service = ReportExecutionService()
        self.check_interval = 60  # Check every 60 seconds
        self.deduplication_window = 5  # Minutes to check for recent runs

    async def run(self):
        """Main loop for the scheduler executor service"""
        logger.info("Starting Report Scheduler Executor Service")

        try:
            while True:
                try:
                    # Check for due schedules
                    due_schedules = await self.check_due_schedules()

                    if due_schedules:
                        logger.info(f"Found {len(due_schedules)} due report schedules")

                        for schedule in due_schedules:
                            try:
                                # Check deduplication
                                if await self.should_execute_schedule(schedule):
                                    await self.execute_schedule(schedule)
                                else:
                                    logger.info(f"Skipping schedule {schedule['schedule_id']} - recent run exists")
                            except Exception as e:
                                logger.error(f"Error executing schedule {schedule['schedule_id']}: {e}")
                                await self.handle_schedule_failure(schedule['id'], str(e))

                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Report Scheduler Executor Service stopped")
            raise

    @with_connection_retry
    async def check_due_schedules(self) -> List[Dict[str, Any]]:
        """
        Check for schedules that are due to run

        Returns:
            List of due schedule records
        """
        try:
            cutoff_time = datetime.utcnow() + timedelta(minutes=5)

            response = self.client.table('report_schedules').select(
                '*, report_definitions!inner(*)'
            ).eq(
                'is_active', True
            ).eq(
                'is_paused', False
            ).lte(
                'next_run_at', cutoff_time.isoformat()
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error checking due schedules: {e}")
            return []

    async def should_execute_schedule(self, schedule: Dict[str, Any]) -> bool:
        """
        Check if schedule should execute (deduplication logic)

        Args:
            schedule: Schedule record

        Returns:
            True if should execute, False if duplicate detected
        """
        try:
            # Check for recent runs within deduplication window
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.deduplication_window)

            response = self.client.table('report_schedule_runs').select('id').eq(
                'schedule_id', schedule['id']
            ).gte(
                'started_at', cutoff_time.isoformat()
            ).limit(1).execute()

            # If recent run exists, skip
            return len(response.data) == 0

        except Exception as e:
            logger.error(f"Error checking deduplication: {e}")
            # On error, proceed with execution
            return True

    async def execute_schedule(self, schedule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a scheduled report using ad-hoc AMC query

        Args:
            schedule: Schedule record with embedded report definition

        Returns:
            Execution result or None if failed
        """
        try:
            report = schedule.get('report_definitions')
            if not report:
                # Fetch report if not included
                report = await self.get_report(schedule['report_id'])
                if not report:
                    logger.error(f"Report not found for schedule {schedule['schedule_id']}")
                    return None

            # Get instance with entity ID
            instance = await self.get_instance_with_entity(report['instance_id'])
            if not instance:
                logger.error(f"Instance not found: {report['instance_id']}")
                return None

            # Create schedule run record
            run_record = {
                'schedule_id': schedule['id'],
                'started_at': datetime.utcnow().isoformat(),
                'status': 'running'
            }
            run_response = self.client.table('report_schedule_runs').insert(run_record).execute()
            run_id = run_response.data[0]['id'] if run_response.data else None

            # Calculate date range for this execution
            start_date, end_date = await self.calculate_date_range(schedule)

            # Merge parameters from schedule defaults and report defaults
            parameters = {
                **(report.get('parameters', {})),
                **(schedule.get('default_parameters', {}))
            }

            # Process SQL with parameters
            processed_sql = await self.process_sql_parameters(
                report['sql_query'],
                parameters,
                start_date,
                end_date
            )

            # Execute report ad-hoc (no workflow)
            execution_result = await self.execution_service.execute_report_adhoc(
                report_id=report['id'],
                instance_id=instance['instance_id'],  # AMC instance ID string
                sql_query=processed_sql,
                parameters=parameters,
                user_id=schedule.get('user_id', report.get('user_id')),
                entity_id=instance['entity_id'],
                triggered_by='schedule',
                schedule_id=schedule['id'],
                time_window_start=start_date,
                time_window_end=end_date
            )

            if execution_result:
                # Update schedule run with execution ID
                if run_id:
                    self.client.table('report_schedule_runs').update({
                        'execution_id': execution_result['id'],
                        'status': 'completed',
                        'completed_at': datetime.utcnow().isoformat()
                    }).eq('id', run_id).execute()

                # Update schedule after successful run
                await self.update_schedule_after_run(schedule['id'], 'completed')

                logger.info(f"Successfully executed schedule {schedule['schedule_id']}")
                return execution_result
            else:
                # Execution failed
                if run_id:
                    self.client.table('report_schedule_runs').update({
                        'status': 'failed',
                        'completed_at': datetime.utcnow().isoformat(),
                        'error_message': 'Failed to create execution'
                    }).eq('id', run_id).execute()

                await self.handle_schedule_failure(schedule['id'], 'Execution failed')
                return None

        except Exception as e:
            logger.error(f"Error executing schedule {schedule['schedule_id']}: {e}")
            await self.handle_schedule_failure(schedule['id'], str(e))
            return None

    async def calculate_date_range(self, schedule: Dict[str, Any]) -> tuple[datetime, datetime]:
        """
        Calculate date range for scheduled execution

        Args:
            schedule: Schedule record

        Returns:
            Tuple of (start_date, end_date)
        """
        try:
            # Account for AMC 14-day data lag
            max_end_date = datetime.utcnow() - timedelta(days=14)

            schedule_type = schedule.get('schedule_type', 'daily')

            if schedule_type == 'daily':
                # Previous day's data
                end_date = max_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=1)
            elif schedule_type == 'weekly':
                # Previous week's data
                end_date = max_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=7)
            elif schedule_type == 'monthly':
                # Previous month's data
                end_date = max_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=30)
            else:
                # Default to daily
                end_date = max_end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=1)

            return start_date, end_date

        except Exception as e:
            logger.error(f"Error calculating date range: {e}")
            # Default to yesterday
            end_date = datetime.utcnow() - timedelta(days=14)
            start_date = end_date - timedelta(days=1)
            return start_date, end_date

    async def process_sql_parameters(
        self,
        sql_template: str,
        parameters: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """
        Process SQL template with parameters and date range

        Args:
            sql_template: SQL query template
            parameters: Parameters to inject
            start_date: Time window start
            end_date: Time window end

        Returns:
            Processed SQL query
        """
        try:
            processed_sql = sql_template

            # Process date parameters
            date_params = {
                'startDate': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'endDate': end_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeWindowStart': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeWindowEnd': end_date.strftime('%Y-%m-%dT%H:%M:%S')
            }

            for key, value in date_params.items():
                processed_sql = processed_sql.replace(f':{key}', f"'{value}'")

            # Process list parameters (campaigns, ASINs)
            if 'campaigns' in parameters and parameters['campaigns']:
                campaigns_str = ','.join([f"'{c}'" for c in parameters['campaigns']])
                processed_sql = processed_sql.replace(':campaigns', f"({campaigns_str})")

            if 'asins' in parameters and parameters['asins']:
                asins_str = ','.join([f"'{a}'" for a in parameters['asins']])
                processed_sql = processed_sql.replace(':asins', f"({asins_str})")

            # Process other parameters
            for key, value in parameters.items():
                if key not in ['campaigns', 'asins']:
                    if isinstance(value, list):
                        value_str = ','.join([f"'{v}'" for v in value])
                        processed_sql = processed_sql.replace(f':{key}', f"({value_str})")
                    else:
                        processed_sql = processed_sql.replace(f':{key}', f"'{value}'")

            return processed_sql

        except Exception as e:
            logger.error(f"Error processing SQL parameters: {e}")
            return sql_template

    async def update_schedule_after_run(self, schedule_id: str, status: str):
        """
        Update schedule after execution

        Args:
            schedule_id: Schedule UUID
            status: Execution status (completed/failed)
        """
        try:
            # Get schedule to recalculate next run
            schedule_response = self.client.table('report_schedules').select('*').eq('id', schedule_id).execute()

            if not schedule_response.data:
                return

            schedule = schedule_response.data[0]

            # Calculate next run time
            tz = pytz.timezone(schedule.get('timezone', 'UTC'))
            now = datetime.now(tz)
            cron = croniter(schedule['cron_expression'], now)
            next_run = cron.get_next(datetime)
            next_run_utc = next_run.astimezone(pytz.UTC).replace(tzinfo=None)

            update_data = {
                'last_run_at': datetime.utcnow().isoformat(),
                'next_run_at': next_run_utc.isoformat(),
                'run_count': schedule.get('run_count', 0) + 1
            }

            if status == 'failed':
                update_data['failure_count'] = schedule.get('failure_count', 0) + 1

            self.client.table('report_schedules').update(update_data).eq('id', schedule_id).execute()

        except Exception as e:
            logger.error(f"Error updating schedule after run: {e}")

    async def handle_schedule_failure(self, schedule_id: str, error_message: str):
        """
        Handle schedule execution failure

        Args:
            schedule_id: Schedule UUID
            error_message: Error details
        """
        try:
            # Update failure count
            schedule_response = self.client.table('report_schedules').select('*').eq('id', schedule_id).execute()

            if schedule_response.data:
                schedule = schedule_response.data[0]
                failure_count = schedule.get('failure_count', 0) + 1

                update_data = {
                    'failure_count': failure_count,
                    'last_error': error_message[:500]  # Limit error message length
                }

                # Disable schedule after multiple failures
                if failure_count >= 5:
                    update_data['is_active'] = False
                    logger.warning(f"Disabling schedule {schedule['schedule_id']} after {failure_count} failures")

                self.client.table('report_schedules').update(update_data).eq('id', schedule_id).execute()

        except Exception as e:
            logger.error(f"Error handling schedule failure: {e}")

    @with_connection_retry
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report definition"""
        try:
            response = self.client.table('report_definitions').select('*').eq('id', report_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching report: {e}")
            return None

    @with_connection_retry
    async def get_instance_with_entity(self, instance_uuid: str) -> Optional[Dict[str, Any]]:
        """Get instance with entity ID"""
        try:
            response = self.client.table('amc_instances').select(
                '*, amc_accounts!inner(account_id)'
            ).eq('id', instance_uuid).execute()

            if response.data:
                instance = response.data[0]
                instance['entity_id'] = instance['amc_accounts']['account_id']
                return instance

            return None
        except Exception as e:
            logger.error(f"Error fetching instance: {e}")
            return None


# Create singleton instance
report_scheduler_executor = ReportSchedulerExecutorService()