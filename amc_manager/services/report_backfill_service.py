"""
Report Backfill Service for AMC Report Builder
Handles historical data backfill orchestration
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import uuid
from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportBackfillService(DatabaseService):
    """Service for managing report backfills"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_backfill(self, report_id: str, backfill_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a backfill collection for historical data"""
        try:
            # Validate backfill config
            if not self.validate_backfill_config(backfill_config):
                return None

            # Calculate segments
            segments = self.calculate_segments(
                end_date=backfill_config.get('end_date', datetime.utcnow()),
                lookback_days=backfill_config['lookback_days'],
                segment_type=backfill_config['segment_type']
            )

            collection_id = f"col_{uuid.uuid4().hex[:8]}"

            # Get report details for instance_id
            report_response = self.client.table('report_definitions').select('instance_id').eq('id', report_id).execute()
            if not report_response.data:
                logger.error(f"Report {report_id} not found")
                return None

            # Create collection record
            collection_record = {
                'collection_id': collection_id,
                'name': f"Backfill for report {report_id}",
                'instance_id': report_response.data[0]['instance_id'],
                'report_id': report_id,
                'segment_type': backfill_config['segment_type'],
                'max_lookback_days': backfill_config['lookback_days'],
                'status': 'pending',
                'total_weeks': len(segments),  # Using weeks for compatibility
                'completed_weeks': 0,
                'workflow_id': str(uuid.uuid4())  # Dummy for legacy compatibility
            }

            response = self.client.table('report_data_collections').insert(collection_record).execute()

            if response.data:
                collection = response.data[0]
                logger.info(f"Created backfill collection {collection_id} with {len(segments)} segments")

                # Queue segment executions
                execution_ids = self.queue_segment_executions(collection['id'], segments)
                collection['execution_ids'] = execution_ids
                collection['total_segments'] = len(segments)

                return collection

            return None

        except Exception as e:
            logger.error(f"Error creating backfill: {e}")
            return None

    def validate_backfill_config(self, config: Dict[str, Any]) -> bool:
        """Validate backfill configuration"""
        try:
            lookback_days = config.get('lookback_days', 0)

            # Check 365 day limit
            if lookback_days > 365:
                raise ValueError(f"Lookback days {lookback_days} exceeds maximum of 365 days")

            # Check segment type
            valid_segments = ['daily', 'weekly', 'monthly', 'quarterly']
            if config.get('segment_type') not in valid_segments:
                raise ValueError(f"Invalid segment type: {config.get('segment_type')}")

            return True

        except Exception as e:
            logger.error(f"Backfill validation failed: {e}")
            return False

    def calculate_segments(
        self,
        end_date: datetime,
        lookback_days: int,
        segment_type: str
    ) -> List[Dict[str, datetime]]:
        """Calculate time segments for backfill"""
        segments = []

        # Account for AMC 14-day data lag
        adjusted_end = min(end_date, datetime.utcnow() - timedelta(days=14))
        start_date = adjusted_end - timedelta(days=lookback_days)

        current = adjusted_end

        while current > start_date:
            if segment_type == 'daily':
                segment_start = current - timedelta(days=1)
            elif segment_type == 'weekly':
                segment_start = current - timedelta(days=7)
            elif segment_type == 'monthly':
                segment_start = current - timedelta(days=30)
            elif segment_type == 'quarterly':
                segment_start = current - timedelta(days=90)
            else:
                segment_start = current - timedelta(days=7)

            # Ensure we don't go before start_date
            segment_start = max(segment_start, start_date)

            segments.append({
                'start': segment_start,
                'end': current
            })

            current = segment_start

            # Avoid infinite loop
            if current <= start_date:
                break

        return segments

    @with_connection_retry
    def queue_segment_executions(self, collection_id: str, segments: List[Dict[str, datetime]]) -> List[str]:
        """Queue execution for each segment"""
        execution_ids = []

        try:
            for i, segment in enumerate(segments):
                # Create a report_data_weeks record for compatibility
                week_record = {
                    'collection_id': collection_id,
                    'week_number': i + 1,
                    'start_date': segment['start'].date().isoformat(),
                    'end_date': segment['end'].date().isoformat(),
                    'status': 'pending'
                }

                response = self.client.table('report_data_weeks').insert(week_record).execute()

                if response.data:
                    execution_ids.append(response.data[0]['id'])

        except Exception as e:
            logger.error(f"Error queuing segment executions: {e}")

        return execution_ids

    @with_connection_retry
    def get_pending_segments(self, collection_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending segments for execution"""
        try:
            response = self.client.table('report_data_weeks').select('*').eq(
                'collection_id', collection_id
            ).eq(
                'status', 'pending'
            ).limit(limit).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching pending segments: {e}")
            return []

    @with_connection_retry
    def update_segment_status(self, segment_id: str, status: str, execution_id: Optional[str] = None) -> bool:
        """Update segment execution status"""
        try:
            update_data = {'status': status}
            if execution_id:
                update_data['execution_id'] = execution_id

            response = self.client.table('report_data_weeks').update(update_data).eq('id', segment_id).execute()

            if response.data and status == 'completed':
                # Update collection progress
                week = response.data[0]
                self._update_collection_progress(week['collection_id'])

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error updating segment status: {e}")
            return False

    def _update_collection_progress(self, collection_id: str):
        """Update collection progress after segment completion"""
        try:
            # Get collection and count completed segments
            weeks_response = self.client.table('report_data_weeks').select('status').eq(
                'collection_id', collection_id
            ).execute()

            if weeks_response.data:
                completed = sum(1 for w in weeks_response.data if w['status'] == 'completed')
                total = len(weeks_response.data)

                # Update collection
                collection_update = {
                    'completed_weeks': completed
                }

                if completed == total:
                    collection_update['status'] = 'completed'

                self.client.table('report_data_collections').update(
                    collection_update
                ).eq('id', collection_id).execute()

                logger.info(f"Updated collection {collection_id} progress: {completed}/{total}")

        except Exception as e:
            logger.error(f"Error updating collection progress: {e}")