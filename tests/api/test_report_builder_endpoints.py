#!/usr/bin/env python3
"""
Test suite for Report Builder API endpoints
Tests validation, preview, and submission endpoints for the enhanced Report Builder flow
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
import json

# Mock the FastAPI app import to avoid dependency issues
with patch('amc_manager.api.supabase.auth.get_current_user'):
    from main_supabase import app

client = TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    return {
        'id': 'test-user-123',
        'email': 'test@example.com',
        'name': 'Test User'
    }


@pytest.fixture
def mock_workflow():
    """Mock workflow data"""
    return {
        'id': 'workflow-123',
        'workflow_id': 'wf-test-123',
        'name': 'Test Workflow',
        'sql_query': 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
        'instance_id': 'instance-123',
        'parameters': {
            'campaigns': [],
            'asins': []
        }
    }


@pytest.fixture
def mock_instance():
    """Mock AMC instance data"""
    return {
        'id': 'instance-123',
        'instance_id': 'amc-test-instance',
        'instance_name': 'Test AMC Instance',
        'account_id': 'account-123'
    }


class TestReportBuilderValidation:
    """Test Report Builder validation endpoints"""

    def test_validate_parameters_success(self, mock_auth_user, mock_workflow):
        """Test successful parameter validation"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            },
            'parameters': {
                'campaigns': ['camp1', 'camp2'],
                'asins': ['B001', 'B002']
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/validate-parameters', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] == True
        assert 'formatted_sql' in data
        assert 'date_range' in data
        assert data['date_range']['days'] == 7

    def test_validate_parameters_invalid_lookback(self, mock_auth_user):
        """Test parameter validation with invalid lookback exceeding AMC limits"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 500,  # Exceeds 425-day limit
                'unit': 'days'
            },
            'parameters': {}
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            response = client.post('/api/report-builder/validate-parameters', json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert 'exceed' in data['detail'].lower() or 'limit' in data['detail'].lower()

    def test_validate_parameters_custom_date_range(self, mock_auth_user, mock_workflow):
        """Test parameter validation with custom date range"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'custom',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            },
            'parameters': {
                'campaigns': ['camp1']
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/validate-parameters', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['valid'] == True
        assert data['date_range']['start_date'] == '2024-01-01'
        assert data['date_range']['end_date'] == '2024-01-31'

    def test_validate_parameters_missing_workflow(self, mock_auth_user):
        """Test parameter validation with non-existent workflow"""
        request_data = {
            'workflow_id': 'non-existent',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=None):
                response = client.post('/api/report-builder/validate-parameters', json=request_data)

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_validate_parameters_unauthorized(self):
        """Test parameter validation without authentication"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', side_effect=Exception("Unauthorized")):
            response = client.post('/api/report-builder/validate-parameters', json=request_data)

        assert response.status_code in [401, 403, 500]


class TestReportBuilderSchedulePreview:
    """Test Report Builder schedule preview endpoints"""

    def test_preview_schedule_once(self, mock_auth_user, mock_workflow):
        """Test schedule preview for one-time execution"""
        request_data = {
            'workflow_id': 'workflow-123',
            'schedule_type': 'once',
            'schedule_config': None,
            'backfill_config': None
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/preview-schedule', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['schedule_type'] == 'once'
        assert data['estimated_execution_time'] is not None
        assert data['next_run'] is not None

    def test_preview_schedule_daily(self, mock_auth_user, mock_workflow):
        """Test schedule preview for daily recurring schedule"""
        request_data = {
            'workflow_id': 'workflow-123',
            'schedule_type': 'scheduled',
            'schedule_config': {
                'frequency': 'daily',
                'time': '09:00',
                'timezone': 'America/New_York'
            },
            'backfill_config': None
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/preview-schedule', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['schedule_type'] == 'scheduled'
        assert data['frequency'] == 'daily'
        assert 'cron_expression' in data
        assert 'next_5_runs' in data
        assert len(data['next_5_runs']) == 5

    def test_preview_schedule_with_backfill(self, mock_auth_user, mock_workflow):
        """Test schedule preview with 365-day backfill"""
        request_data = {
            'workflow_id': 'workflow-123',
            'schedule_type': 'backfill_with_schedule',
            'schedule_config': {
                'frequency': 'weekly',
                'time': '02:00',
                'timezone': 'UTC',
                'days_of_week': [1, 5]  # Monday and Friday
            },
            'backfill_config': {
                'enabled': True,
                'segment_type': 'weekly',
                'parallel_limit': 5,
                'include_current': True
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/preview-schedule', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['schedule_type'] == 'backfill_with_schedule'
        assert 'backfill_info' in data
        assert data['backfill_info']['total_segments'] == 52  # 52 weeks
        assert data['backfill_info']['parallel_limit'] == 5
        assert data['backfill_info']['estimated_completion_hours'] > 0

    def test_preview_schedule_invalid_config(self, mock_auth_user):
        """Test schedule preview with invalid configuration"""
        request_data = {
            'workflow_id': 'workflow-123',
            'schedule_type': 'scheduled',
            'schedule_config': {
                'frequency': 'invalid',
                'time': '25:00',  # Invalid time
                'timezone': 'Invalid/Zone'
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            response = client.post('/api/report-builder/preview-schedule', json=request_data)

        assert response.status_code == 400


class TestReportBuilderSubmit:
    """Test Report Builder submit endpoint"""

    def test_submit_once_execution(self, mock_auth_user, mock_workflow, mock_instance):
        """Test submitting a one-time execution"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            },
            'parameters': {
                'campaigns': ['camp1', 'camp2']
            },
            'schedule_type': 'once',
            'schedule_config': None,
            'backfill_config': None
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                with patch('amc_manager.services.db_service.db_service.get_instance_by_id_sync', return_value=mock_instance):
                    with patch('amc_manager.services.workflow_service.WorkflowService.execute') as mock_execute:
                        mock_execute.return_value = {'execution_id': 'exec-123', 'status': 'pending'}
                        response = client.post('/api/report-builder/submit', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert data['execution_id'] == 'exec-123'
        assert 'redirect_url' in data

    def test_submit_scheduled_execution(self, mock_auth_user, mock_workflow, mock_instance):
        """Test submitting a scheduled recurring execution"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 30,
                'unit': 'days'
            },
            'parameters': {},
            'schedule_type': 'scheduled',
            'schedule_config': {
                'frequency': 'weekly',
                'time': '09:00',
                'timezone': 'America/New_York',
                'days_of_week': [1, 3, 5]
            },
            'backfill_config': None
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                with patch('amc_manager.services.db_service.db_service.get_instance_by_id_sync', return_value=mock_instance):
                    with patch('amc_manager.services.enhanced_schedule_service.EnhancedScheduleService.create_schedule') as mock_schedule:
                        mock_schedule.return_value = {'id': 'schedule-123', 'is_active': True}
                        response = client.post('/api/report-builder/submit', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert data['schedule_id'] == 'schedule-123'
        assert 'redirect_url' in data

    def test_submit_backfill_with_schedule(self, mock_auth_user, mock_workflow, mock_instance):
        """Test submitting a backfill with ongoing schedule"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 365,
                'unit': 'days'
            },
            'parameters': {
                'campaigns': ['camp1']
            },
            'schedule_type': 'backfill_with_schedule',
            'schedule_config': {
                'frequency': 'daily',
                'time': '02:00',
                'timezone': 'UTC'
            },
            'backfill_config': {
                'enabled': True,
                'segment_type': 'weekly',
                'parallel_limit': 10,
                'include_current': True
            }
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                with patch('amc_manager.services.db_service.db_service.get_instance_by_id_sync', return_value=mock_instance):
                    with patch('amc_manager.services.historical_collection_service.historical_collection_service.start_backfill') as mock_backfill:
                        with patch('amc_manager.services.enhanced_schedule_service.EnhancedScheduleService.create_schedule') as mock_schedule:
                            mock_backfill.return_value = {'collection_id': 'collection-123', 'status': 'in_progress'}
                            mock_schedule.return_value = {'id': 'schedule-123', 'is_active': True}
                            response = client.post('/api/report-builder/submit', json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data['success'] == True
        assert data['collection_id'] == 'collection-123'
        assert data['schedule_id'] == 'schedule-123'
        assert 'redirect_url' in data

    def test_submit_audit_trail_creation(self, mock_auth_user, mock_workflow, mock_instance):
        """Test that submit creates audit trail entries"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            },
            'parameters': {},
            'schedule_type': 'once'
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                with patch('amc_manager.services.db_service.db_service.get_instance_by_id_sync', return_value=mock_instance):
                    with patch('amc_manager.services.workflow_service.WorkflowService.execute') as mock_execute:
                        with patch('amc_manager.services.db_service.db_service.create_audit_entry') as mock_audit:
                            mock_execute.return_value = {'execution_id': 'exec-123', 'status': 'pending'}
                            response = client.post('/api/report-builder/submit', json=request_data)

                            # Verify audit was called for submit step
                            assert mock_audit.called
                            audit_call_args = mock_audit.call_args[0][0]
                            assert audit_call_args['step_completed'] == 'submit'
                            assert audit_call_args['user_id'] == 'test-user-123'

        assert response.status_code == 200

    def test_submit_validation_error(self, mock_auth_user):
        """Test submit with validation errors"""
        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 500,  # Exceeds limit
                'unit': 'days'
            },
            'parameters': {},
            'schedule_type': 'once'
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            response = client.post('/api/report-builder/submit', json=request_data)

        assert response.status_code == 400

    def test_submit_insufficient_permissions(self, mock_auth_user, mock_workflow):
        """Test submit with insufficient permissions"""
        # Modify workflow to have different owner
        mock_workflow['user_id'] = 'different-user'

        request_data = {
            'workflow_id': 'workflow-123',
            'instance_id': 'instance-123',
            'lookback_config': {
                'type': 'relative',
                'value': 7,
                'unit': 'days'
            },
            'parameters': {},
            'schedule_type': 'once'
        }

        with patch('amc_manager.api.supabase.auth.get_current_user', return_value=mock_auth_user):
            with patch('amc_manager.services.db_service.db_service.get_workflow_by_id_sync', return_value=mock_workflow):
                response = client.post('/api/report-builder/submit', json=request_data)

        assert response.status_code in [403, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])