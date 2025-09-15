"""
Tests for Report Builder Service Layer
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
import json
from typing import Dict, Any, Optional

from amc_manager.services.report_service import ReportService
from amc_manager.services.report_execution_service import ReportExecutionService
from amc_manager.services.report_schedule_service import ReportScheduleService


class TestReportService:
    """Test suite for ReportService CRUD operations"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database client"""
        mock = MagicMock()
        mock.table = MagicMock(return_value=mock)
        mock.select = MagicMock(return_value=mock)
        mock.insert = MagicMock(return_value=mock)
        mock.update = MagicMock(return_value=mock)
        mock.delete = MagicMock(return_value=mock)
        mock.eq = MagicMock(return_value=mock)
        mock.execute = MagicMock()
        return mock

    @pytest.fixture
    def report_service(self, mock_db):
        """Create ReportService instance with mocked database"""
        service = ReportService()
        service._client = mock_db  # Access private _client attribute
        return service

    @pytest.fixture
    def sample_report_data(self):
        """Sample report data for testing"""
        return {
            'name': 'Test Report',
            'description': 'Test report description',
            'template_id': str(uuid.uuid4()),
            'instance_id': str(uuid.uuid4()),
            'owner_id': str(uuid.uuid4()),
            'parameters': {
                'start_date': '2025-01-01',
                'end_date': '2025-01-31',
                'campaign_ids': ['123', '456']
            },
            'frequency': 'weekly',
            'timezone': 'America/New_York'
        }

    def test_create_report_definition(self, report_service, mock_db, sample_report_data):
        """Test creating a new report definition"""
        # Arrange
        expected_report_id = f"rpt_{uuid.uuid4().hex[:8]}"
        mock_db.execute.return_value.data = [{
            'id': str(uuid.uuid4()),
            'report_id': expected_report_id,
            **sample_report_data
        }]

        # Act
        result = report_service.create_report(sample_report_data)

        # Assert
        assert result is not None
        assert result['report_id'].startswith('rpt_')
        assert result['name'] == sample_report_data['name']
        mock_db.table.assert_called_with('report_definitions')
        mock_db.insert.assert_called_once()

    def test_get_report_by_id(self, report_service, mock_db):
        """Test retrieving a report by ID"""
        # Arrange
        report_id = str(uuid.uuid4())
        mock_db.execute.return_value.data = [{
            'id': report_id,
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'Test Report'
        }]

        # Act
        result = report_service.get_report(report_id)

        # Assert
        assert result is not None
        assert result['id'] == report_id
        mock_db.eq.assert_called_with('id', report_id)

    def test_update_report(self, report_service, mock_db):
        """Test updating report configuration"""
        # Arrange
        report_id = str(uuid.uuid4())
        update_data = {
            'name': 'Updated Report Name',
            'parameters': {'new_param': 'value'}
        }
        mock_db.execute.return_value.data = [{
            'id': report_id,
            **update_data
        }]

        # Act
        result = report_service.update_report(report_id, update_data)

        # Assert
        assert result is not None
        assert result['name'] == update_data['name']
        mock_db.update.assert_called_with(update_data)
        mock_db.eq.assert_called_with('id', report_id)

    def test_delete_report(self, report_service, mock_db):
        """Test deleting a report"""
        # Arrange
        report_id = str(uuid.uuid4())
        mock_db.execute.return_value.data = [{'id': report_id}]

        # Act
        result = report_service.delete_report(report_id)

        # Assert
        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.eq.assert_called_with('id', report_id)

    def test_list_reports_with_filters(self, report_service, mock_db):
        """Test listing reports with various filters"""
        # Arrange
        mock_db.execute.return_value.data = [
            {'id': str(uuid.uuid4()), 'name': 'Report 1'},
            {'id': str(uuid.uuid4()), 'name': 'Report 2'}
        ]

        # Act
        result = report_service.list_reports(
            instance_id=str(uuid.uuid4()),
            is_active=True
        )

        # Assert
        assert len(result) == 2
        assert mock_db.eq.call_count >= 2  # Called for instance_id and is_active

    def test_create_report_with_dashboard(self, report_service, mock_db):
        """Test creating report with automatic dashboard creation"""
        # Arrange
        template_data = {
            'report_config': {
                'widgets': [
                    {'type': 'line_chart', 'config': {}}
                ]
            }
        }
        mock_db.execute.return_value.data = [template_data]

        report_data = {
            'template_id': str(uuid.uuid4()),
            'name': 'Report with Dashboard'
        }

        # Act
        with patch.object(report_service, 'create_dashboard_from_config') as mock_create_dashboard:
            mock_create_dashboard.return_value = str(uuid.uuid4())
            result = report_service.create_report_with_dashboard(report_data)

        # Assert
        mock_create_dashboard.assert_called_once()


class TestReportExecutionService:
    """Test suite for Report Execution Service"""

    @pytest.fixture
    def mock_amc_client(self):
        """Create mock AMC API client"""
        mock = AsyncMock()
        mock.create_workflow_execution = AsyncMock()
        mock.get_execution_status = AsyncMock()
        return mock

    @pytest.fixture
    def execution_service(self, mock_db, mock_amc_client):
        """Create ExecutionService instance"""
        service = ReportExecutionService()
        service._client = mock_db  # Access private _client attribute
        service.amc_client = mock_amc_client
        return service

    @pytest.mark.asyncio
    async def test_execute_report_adhoc(self, execution_service, mock_amc_client):
        """Test ad-hoc report execution"""
        # Arrange
        report_id = str(uuid.uuid4())
        instance_id = 'test_instance'
        sql_query = 'SELECT * FROM campaigns'

        mock_amc_client.create_workflow_execution.return_value = {
            'executionId': 'amc_exec_123',
            'status': 'PENDING'
        }

        # Act
        result = await execution_service.execute_report_adhoc(
            report_id=report_id,
            instance_id=instance_id,
            sql_query=sql_query,
            parameters={}
        )

        # Assert
        assert result is not None
        assert result['amc_execution_id'] == 'amc_exec_123'
        assert result['status'] == 'pending'
        mock_amc_client.create_workflow_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_time_window(self, execution_service):
        """Test execution with time window calculation"""
        # Arrange
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)

        # Act
        result = await execution_service.execute_with_time_window(
            report_id=str(uuid.uuid4()),
            sql_query='SELECT * FROM campaigns',
            start_date=start_date,
            end_date=end_date
        )

        # Assert
        assert result['time_window_start'] == start_date
        assert result['time_window_end'] == end_date

    @pytest.mark.asyncio
    async def test_cancel_execution(self, execution_service, mock_amc_client):
        """Test cancelling an execution"""
        # Arrange
        execution_id = str(uuid.uuid4())
        mock_amc_client.cancel_execution = AsyncMock(return_value=True)

        # Act
        result = await execution_service.cancel_execution(execution_id)

        # Assert
        assert result is True
        mock_amc_client.cancel_execution.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_update_execution_status(self, execution_service, mock_db):
        """Test updating execution status"""
        # Arrange
        execution_id = str(uuid.uuid4())
        mock_db.execute.return_value.data = [{'id': execution_id}]

        # Act
        result = await execution_service.update_status(
            execution_id=execution_id,
            status='completed',
            row_count=1000
        )

        # Assert
        assert result is not None
        mock_db.update.assert_called_once()


class TestReportScheduleService:
    """Test suite for Report Schedule Service"""

    @pytest.fixture
    def schedule_service(self, mock_db):
        """Create ScheduleService instance"""
        service = ReportScheduleService()
        service._client = mock_db  # Access private _client attribute
        return service

    def test_create_schedule(self, schedule_service, mock_db):
        """Test creating a schedule for a report"""
        # Arrange
        report_id = str(uuid.uuid4())
        schedule_data = {
            'schedule_type': 'weekly',
            'cron_expression': '0 3 * * 1',
            'timezone': 'America/New_York'
        }
        mock_db.execute.return_value.data = [{
            'id': str(uuid.uuid4()),
            'schedule_id': f'sch_{uuid.uuid4().hex[:8]}',
            **schedule_data
        }]

        # Act
        result = schedule_service.create_schedule(report_id, schedule_data)

        # Assert
        assert result is not None
        assert result['schedule_id'].startswith('sch_')
        assert result['schedule_type'] == 'weekly'

    def test_pause_resume_schedule(self, schedule_service, mock_db):
        """Test pausing and resuming a schedule"""
        # Arrange
        schedule_id = str(uuid.uuid4())
        mock_db.execute.return_value.data = [{'id': schedule_id, 'is_paused': False}]

        # Act - Pause
        result_pause = schedule_service.pause_schedule(schedule_id)

        # Assert
        assert result_pause is not None
        mock_db.update.assert_called_with({'is_paused': True})

        # Act - Resume
        mock_db.execute.return_value.data = [{'id': schedule_id, 'is_paused': True}]
        result_resume = schedule_service.resume_schedule(schedule_id)

        # Assert
        assert result_resume is not None

    def test_calculate_next_run(self, schedule_service):
        """Test next run time calculation"""
        # Arrange
        cron_expression = '0 2 * * *'  # Daily at 2 AM
        timezone = 'UTC'

        # Act
        next_run = schedule_service.calculate_next_run(cron_expression, timezone)

        # Assert
        assert next_run is not None
        assert isinstance(next_run, datetime)
        assert next_run > datetime.utcnow()

    def test_get_due_schedules(self, schedule_service, mock_db):
        """Test retrieving schedules due for execution"""
        # Arrange
        current_time = datetime.utcnow()
        mock_db.execute.return_value.data = [
            {
                'id': str(uuid.uuid4()),
                'schedule_id': 'sch_123',
                'next_run_at': (current_time - timedelta(minutes=5)).isoformat()
            }
        ]

        # Act
        result = schedule_service.get_due_schedules()

        # Assert
        assert len(result) == 1
        assert result[0]['schedule_id'] == 'sch_123'

    def test_update_schedule_after_run(self, schedule_service, mock_db):
        """Test updating schedule after execution"""
        # Arrange
        schedule_id = str(uuid.uuid4())
        mock_db.execute.return_value.data = [{
            'id': schedule_id,
            'run_count': 5,
            'cron_expression': '0 2 * * *'
        }]

        # Act
        result = schedule_service.update_after_run(
            schedule_id=schedule_id,
            status='completed'
        )

        # Assert
        assert result is not None
        update_call = mock_db.update.call_args[0][0]
        assert 'last_run_at' in update_call
        assert 'last_run_status' in update_call
        assert 'next_run_at' in update_call
        assert update_call['run_count'] == 6


class TestBackfillOrchestration:
    """Test suite for Backfill Orchestration"""

    @pytest.fixture
    def backfill_service(self, mock_db):
        """Create BackfillService instance"""
        from amc_manager.services.report_backfill_service import ReportBackfillService
        service = ReportBackfillService()
        service._client = mock_db  # Access private _client attribute
        return service

    def test_create_backfill_collection(self, backfill_service, mock_db):
        """Test creating a backfill collection"""
        # Arrange
        report_id = str(uuid.uuid4())
        backfill_config = {
            'segment_type': 'weekly',
            'lookback_days': 180,
            'end_date': datetime(2025, 9, 15)
        }

        mock_db.execute.return_value.data = [{
            'id': str(uuid.uuid4()),
            'collection_id': f'col_{uuid.uuid4().hex[:8]}',
            'total_segments': 26
        }]

        # Act
        result = backfill_service.create_backfill(report_id, backfill_config)

        # Assert
        assert result is not None
        assert result['collection_id'].startswith('col_')
        assert result['total_segments'] == 26

    def test_segment_time_periods(self, backfill_service):
        """Test segmenting time periods for backfill"""
        # Arrange
        end_date = datetime(2025, 9, 15)
        lookback_days = 90
        segment_type = 'weekly'

        # Act
        segments = backfill_service.calculate_segments(
            end_date=end_date,
            lookback_days=lookback_days,
            segment_type=segment_type
        )

        # Assert
        assert len(segments) == 13  # ~13 weeks in 90 days
        assert segments[0]['end'] <= end_date
        assert segments[-1]['start'] >= end_date - timedelta(days=lookback_days)

    def test_validate_backfill_limits(self, backfill_service):
        """Test backfill validation limits"""
        # Test exceeding 365 day limit
        with pytest.raises(ValueError) as exc_info:
            backfill_service.validate_backfill_config({
                'lookback_days': 400,
                'segment_type': 'daily'
            })
        assert '365 days' in str(exc_info.value)

        # Test valid config
        result = backfill_service.validate_backfill_config({
            'lookback_days': 180,
            'segment_type': 'weekly'
        })
        assert result is True

    def test_queue_segment_executions(self, backfill_service, mock_db):
        """Test queuing executions for each segment"""
        # Arrange
        collection_id = str(uuid.uuid4())
        segments = [
            {'start': datetime(2025, 1, 1), 'end': datetime(2025, 1, 7)},
            {'start': datetime(2025, 1, 8), 'end': datetime(2025, 1, 14)}
        ]

        # Act
        result = backfill_service.queue_segment_executions(collection_id, segments)

        # Assert
        assert len(result) == 2
        assert all('execution_id' in r for r in result)