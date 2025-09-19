"""
Report Backfill Executor Service
Handles sequential execution of report backfill segments with rate limiting
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.services.report_execution_service import ReportExecutionService
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, max_calls: int = 100, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []

    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.utcnow()

        # Remove calls outside the window
        self.calls = [
            call_time for call_time in self.calls
            if (now - call_time).total_seconds() < self.window_seconds
        ]

        # If at limit, wait until oldest call expires
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            wait_time = self.window_seconds - (now - oldest_call).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time + 0.1)  # Add small buffer

        # Record this call
        self.calls.append(now)


class ReportBackfillExecutorService(DatabaseService):
    """
    Background service that processes report backfill collections
    Executes segments sequentially with rate limiting and retry logic
    """

    def __init__(self):
        super().__init__()
        self.execution_service = ReportExecutionService()
        self.rate_limiter = RateLimiter(max_calls=100, window_seconds=60)
        self.check_interval = 30  # Check for work every 30 seconds
        self.max_retries = 3
        self.retry_delay = 5  # Seconds between retries

    async def run(self):
        """Main loop for the backfill executor service"""
        logger.info("Starting Report Backfill Executor Service")

        try:
            while True:
                try:
                    # Get active collections
                    active_collections = await self.get_active_collections()

                    if active_collections:
                        logger.info(f"Found {len(active_collections)} active backfill collections")

                        for collection in active_collections:
                            await self.process_collection(collection)

                except Exception as e:
                    logger.error(f"Error in backfill loop: {e}")

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Report Backfill Executor Service stopped")
            raise

    @with_connection_retry
    async def get_active_collections(self) -> List[Dict[str, Any]]:
        """
        Get collections that are actively being processed

        Returns:
            List of active collection records
        """
        try:
            response = self.client.table('report_data_collections').select(
                '*, report_definitions!inner(*)'
            ).in_(
                'status', ['pending', 'running']
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching active collections: {e}")
            return []

    async def process_collection(self, collection: Dict[str, Any]):
        """
        Process a single collection's segments sequentially

        Args:
            collection: Collection record with embedded report
        """
        try:
            logger.info(f"Processing collection {collection['collection_id']}")

            # Update collection status to running if pending
            if collection['status'] == 'pending':
                self.client.table('report_data_collections').update({
                    'status': 'running',
                    'started_at': datetime.utcnow().isoformat()
                }).eq('id', collection['id']).execute()

            # Get pending segments
            pending_segments = await self.get_pending_segments(collection['id'])

            if not pending_segments:
                # Check if all segments are complete
                await self.check_collection_completion(collection['id'])
                return

            report = collection.get('report_definitions')
            if not report:
                report = await self.get_report(collection['report_id'])

            if not report:
                logger.error(f"Report not found for collection {collection['collection_id']}")
                return

            # Get instance with entity
            instance = await self.get_instance_with_entity(report['instance_id'])
            if not instance:
                logger.error(f"Instance not found for collection {collection['collection_id']}")
                return

            # Process segments sequentially
            for segment in pending_segments:
                try:
                    # Apply rate limiting
                    await self.wait_for_rate_limit()

                    # Execute segment with retry logic
                    await self.execute_segment_with_retry(segment, report, instance)

                    # Update progress
                    await self.update_collection_progress(collection['id'])

                except Exception as e:
                    logger.error(f"Error processing segment {segment.get('week_number')}: {e}")
                    # Continue with next segment even if this one fails

        except Exception as e:
            logger.error(f"Error processing collection {collection['collection_id']}: {e}")

    @with_connection_retry
    async def get_pending_segments(self, collection_id: str) -> List[Dict[str, Any]]:
        """
        Get pending segments for a collection

        Args:
            collection_id: Collection UUID

        Returns:
            List of pending segment records
        """
        try:
            response = self.client.table('report_data_weeks').select('*').eq(
                'collection_id', collection_id
            ).eq(
                'status', 'pending'
            ).order(
                'week_number'
            ).limit(10).execute()  # Process up to 10 at a time

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching pending segments: {e}")
            return []

    async def execute_segment_with_retry(
        self,
        segment: Dict[str, Any],
        report: Dict[str, Any],
        instance: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a segment with retry logic

        Args:
            segment: Segment record
            report: Report definition
            instance: AMC instance with entity

        Returns:
            Execution result or None if failed after retries
        """
        retry_count = segment.get('retry_count', 0)

        while retry_count < self.max_retries:
            try:
                logger.info(f"Executing segment {segment['week_number']} (attempt {retry_count + 1})")

                # Update segment status to running
                self.client.table('report_data_weeks').update({
                    'status': 'running',
                    'retry_count': retry_count,
                    'started_at': datetime.utcnow().isoformat()
                }).eq('id', segment['id']).execute()

                # Process SQL with segment dates
                processed_sql = await self.process_segment_sql(
                    report['sql_query'],
                    report.get('parameters', {}),
                    segment
                )

                # Convert date strings to datetime
                start_date = datetime.fromisoformat(segment['start_date'])
                end_date = datetime.fromisoformat(segment['end_date'])

                # Execute via ad-hoc AMC query
                execution_result = await self.execution_service.execute_report_adhoc(
                    report_id=report['id'],
                    instance_id=instance['instance_id'],
                    sql_query=processed_sql,
                    parameters=report.get('parameters', {}),
                    user_id=report.get('user_id'),
                    entity_id=instance['entity_id'],
                    triggered_by='backfill',
                    collection_id=segment['collection_id'],
                    time_window_start=start_date,
                    time_window_end=end_date
                )

                if execution_result:
                    # Update segment as completed
                    self.client.table('report_data_weeks').update({
                        'status': 'completed',
                        'execution_id': execution_result['id'],
                        'completed_at': datetime.utcnow().isoformat()
                    }).eq('id', segment['id']).execute()

                    logger.info(f"Successfully executed segment {segment['week_number']}")
                    return execution_result

                # Execution returned None, treat as failure
                raise Exception("Execution returned no result")

            except Exception as e:
                logger.error(f"Segment execution failed (attempt {retry_count + 1}): {e}")
                retry_count += 1

                if retry_count < self.max_retries:
                    # Wait before retry
                    await asyncio.sleep(self.retry_delay)
                else:
                    # Max retries reached, mark as failed
                    self.client.table('report_data_weeks').update({
                        'status': 'failed',
                        'retry_count': retry_count,
                        'error_message': str(e)[:500],
                        'completed_at': datetime.utcnow().isoformat()
                    }).eq('id', segment['id']).execute()

                    logger.error(f"Segment {segment['week_number']} failed after {retry_count} attempts")
                    return None

    async def process_segment_sql(
        self,
        sql_template: str,
        parameters: Dict[str, Any],
        segment: Dict[str, Any]
    ) -> str:
        """
        Process SQL template with segment-specific date range

        Args:
            sql_template: SQL query template
            parameters: Report parameters
            segment: Segment with date range

        Returns:
            Processed SQL query
        """
        try:
            processed_sql = sql_template

            # Process date parameters from segment
            date_params = {
                'startDate': f"{segment['start_date']}T00:00:00",
                'endDate': f"{segment['end_date']}T23:59:59",
                'timeWindowStart': f"{segment['start_date']}T00:00:00",
                'timeWindowEnd': f"{segment['end_date']}T23:59:59"
            }

            for key, value in date_params.items():
                processed_sql = processed_sql.replace(f':{key}', f"'{value}'")

            # Process list parameters (campaigns, ASINs) - same for all segments
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
            logger.error(f"Error processing segment SQL: {e}")
            return sql_template

    async def wait_for_rate_limit(self):
        """Apply rate limiting before API call"""
        await self.rate_limiter.wait_if_needed()

    @with_connection_retry
    async def update_collection_progress(self, collection_id: str):
        """
        Update collection progress after segment completion

        Args:
            collection_id: Collection UUID
        """
        try:
            # Count completed segments
            completed_response = self.client.table('report_data_weeks').select(
                'id', count='exact'
            ).eq(
                'collection_id', collection_id
            ).eq(
                'status', 'completed'
            ).execute()

            completed_count = completed_response.count if hasattr(completed_response, 'count') else len(completed_response.data)

            # Get total segments
            total_response = self.client.table('report_data_collections').select(
                'total_weeks'
            ).eq('id', collection_id).execute()

            if total_response.data:
                total_weeks = total_response.data[0]['total_weeks']

                update_data = {
                    'completed_weeks': completed_count
                }

                # Mark as completed if all done
                if completed_count >= total_weeks:
                    update_data['status'] = 'completed'
                    update_data['completed_at'] = datetime.utcnow().isoformat()
                    logger.info(f"Collection {collection_id} completed: {completed_count}/{total_weeks} segments")

                self.client.table('report_data_collections').update(
                    update_data
                ).eq('id', collection_id).execute()

        except Exception as e:
            logger.error(f"Error updating collection progress: {e}")

    @with_connection_retry
    async def check_collection_completion(self, collection_id: str):
        """
        Check if collection is complete and update status

        Args:
            collection_id: Collection UUID
        """
        try:
            # Check for any pending or running segments
            pending_response = self.client.table('report_data_weeks').select(
                'id', count='exact'
            ).eq(
                'collection_id', collection_id
            ).in_(
                'status', ['pending', 'running']
            ).execute()

            pending_count = pending_response.count if hasattr(pending_response, 'count') else len(pending_response.data)

            if pending_count == 0:
                # No more segments to process
                self.client.table('report_data_collections').update({
                    'status': 'completed',
                    'completed_at': datetime.utcnow().isoformat()
                }).eq('id', collection_id).execute()

                logger.info(f"Collection {collection_id} marked as completed")

        except Exception as e:
            logger.error(f"Error checking collection completion: {e}")

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
report_backfill_executor = ReportBackfillExecutorService()