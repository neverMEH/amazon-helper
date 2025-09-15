"""
Tests for Report Builder database schema changes
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

from amc_manager.services.db_service import DatabaseService


class TestReportBuilderSchema:
    """Test suite for Report Builder database schema"""

    @pytest.fixture
    def db_service(self):
        """Create database service instance"""
        return DatabaseService()

    @pytest.fixture
    def sample_template_id(self, db_service):
        """Create a sample query template for testing"""
        template_data = {
            'name': 'Test Template',
            'description': 'Test template for report builder',
            'category': 'test',
            'sql_template': 'SELECT * FROM campaigns',
            'parameter_definitions': {
                'start_date': {'type': 'date', 'required': True},
                'end_date': {'type': 'date', 'required': True}
            }
        }
        result = db_service.client.table('query_templates').insert(template_data).execute()
        return result.data[0]['id']

    @pytest.fixture
    def sample_instance_id(self, db_service):
        """Get or create a sample AMC instance for testing"""
        instances = db_service.client.table('amc_instances').select('id').limit(1).execute()
        if instances.data:
            return instances.data[0]['id']
        # Create a test instance if none exists
        instance_data = {
            'instance_id': 'test_instance',
            'instance_name': 'Test Instance',
            'region': 'us-east-1'
        }
        result = db_service.client.table('amc_instances').insert(instance_data).execute()
        return result.data[0]['id']

    @pytest.fixture
    def sample_user_id(self, db_service):
        """Get or create a sample user for testing"""
        users = db_service.client.table('users').select('id').limit(1).execute()
        if users.data:
            return users.data[0]['id']
        # Create a test user if none exists
        user_data = {
            'email': 'test@example.com',
            'full_name': 'Test User'
        }
        result = db_service.client.table('users').insert(user_data).execute()
        return result.data[0]['id']

    def test_query_templates_report_columns(self, db_service):
        """Test that query_templates table has report-specific columns"""
        # Check if columns exist by attempting to query them
        result = db_service.client.table('query_templates').select(
            'id, report_type, report_config, ui_schema'
        ).limit(1).execute()

        # Should not raise an error
        assert result is not None

        # Insert a template with report columns
        template_data = {
            'name': 'Report Template',
            'description': 'Template with report config',
            'category': 'performance',
            'sql_template': 'SELECT * FROM campaigns',
            'report_type': 'campaign_analysis',
            'report_config': {
                'widgets': [
                    {'type': 'line_chart', 'metric': 'impressions'}
                ]
            },
            'ui_schema': {
                'fields': {
                    'campaign_ids': {
                        'ui:widget': 'multiselect'
                    }
                }
            }
        }

        result = db_service.client.table('query_templates').insert(template_data).execute()
        assert result.data[0]['report_type'] == 'campaign_analysis'
        assert result.data[0]['report_config'] is not None
        assert result.data[0]['ui_schema'] is not None

    def test_report_definitions_table(self, db_service, sample_template_id, sample_instance_id, sample_user_id):
        """Test report_definitions table creation and constraints"""
        report_data = {
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'Test Report',
            'description': 'Test report description',
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'owner_id': sample_user_id,
            'parameters': {'start_date': '2025-01-01', 'end_date': '2025-01-31'},
            'frequency': 'weekly',
            'timezone': 'America/New_York',
            'is_active': True
        }

        result = db_service.client.table('report_definitions').insert(report_data).execute()
        assert result.data[0]['report_id'].startswith('rpt_')
        assert result.data[0]['frequency'] == 'weekly'
        assert result.data[0]['is_active'] is True

        # Test unique constraint on report_id
        with pytest.raises(Exception):
            db_service.client.table('report_definitions').insert({
                **report_data,
                'report_id': result.data[0]['report_id']  # Duplicate report_id
            }).execute()

        # Test frequency constraint
        with pytest.raises(Exception):
            db_service.client.table('report_definitions').insert({
                **report_data,
                'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
                'frequency': 'invalid_frequency'
            }).execute()

    def test_report_executions_table(self, db_service, sample_template_id, sample_instance_id, sample_user_id):
        """Test report_executions table creation and constraints"""
        # First create a report definition
        report_result = db_service.client.table('report_definitions').insert({
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'Test Report',
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'owner_id': sample_user_id,
            'parameters': {},
            'frequency': 'once'
        }).execute()
        report_uuid = report_result.data[0]['id']

        execution_data = {
            'execution_id': f'exec_{uuid.uuid4().hex[:8]}',
            'report_id': report_uuid,
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'user_id': sample_user_id,
            'triggered_by': 'manual',
            'status': 'pending',
            'parameters_snapshot': {'start_date': '2025-01-01'},
            'time_window_start': '2025-01-01T00:00:00Z',
            'time_window_end': '2025-01-31T23:59:59Z'
        }

        result = db_service.client.table('report_executions').insert(execution_data).execute()
        assert result.data[0]['execution_id'].startswith('exec_')
        assert result.data[0]['status'] == 'pending'
        assert result.data[0]['triggered_by'] == 'manual'

        # Test status constraint
        with pytest.raises(Exception):
            db_service.client.table('report_executions').insert({
                **execution_data,
                'execution_id': f'exec_{uuid.uuid4().hex[:8]}',
                'status': 'invalid_status'
            }).execute()

        # Test triggered_by constraint
        with pytest.raises(Exception):
            db_service.client.table('report_executions').insert({
                **execution_data,
                'execution_id': f'exec_{uuid.uuid4().hex[:8]}',
                'triggered_by': 'invalid_trigger'
            }).execute()

    def test_report_schedules_table(self, db_service, sample_template_id, sample_instance_id, sample_user_id):
        """Test report_schedules table creation and constraints"""
        # First create a report definition
        report_result = db_service.client.table('report_definitions').insert({
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'Scheduled Report',
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'owner_id': sample_user_id,
            'parameters': {},
            'frequency': 'daily'
        }).execute()
        report_uuid = report_result.data[0]['id']

        schedule_data = {
            'schedule_id': f'sch_{uuid.uuid4().hex[:8]}',
            'report_id': report_uuid,
            'schedule_type': 'daily',
            'cron_expression': '0 2 * * *',
            'timezone': 'America/New_York',
            'default_parameters': {},
            'is_active': True,
            'is_paused': False,
            'next_run_at': (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        }

        result = db_service.client.table('report_schedules').insert(schedule_data).execute()
        assert result.data[0]['schedule_id'].startswith('sch_')
        assert result.data[0]['schedule_type'] == 'daily'
        assert result.data[0]['is_active'] is True

        # Test unique constraint on active schedules per report
        with pytest.raises(Exception):
            db_service.client.table('report_schedules').insert({
                **schedule_data,
                'schedule_id': f'sch_{uuid.uuid4().hex[:8]}',
                'is_active': True  # Another active schedule for same report
            }).execute()

        # Test schedule_type constraint
        with pytest.raises(Exception):
            db_service.client.table('report_schedules').insert({
                **schedule_data,
                'schedule_id': f'sch_{uuid.uuid4().hex[:8]}',
                'is_active': False,
                'schedule_type': 'invalid_type'
            }).execute()

    def test_dashboard_favorites_table(self, db_service, sample_user_id):
        """Test dashboard_favorites table creation and constraints"""
        # First create a dashboard
        dashboard_result = db_service.client.table('dashboards').insert({
            'name': 'Test Dashboard',
            'owner_id': sample_user_id,
            'config': {}
        }).execute()
        dashboard_id = dashboard_result.data[0]['id']

        favorite_data = {
            'dashboard_id': dashboard_id,
            'user_id': sample_user_id
        }

        result = db_service.client.table('dashboard_favorites').insert(favorite_data).execute()
        assert result.data[0]['dashboard_id'] == dashboard_id
        assert result.data[0]['user_id'] == sample_user_id

        # Test unique constraint
        with pytest.raises(Exception):
            db_service.client.table('dashboard_favorites').insert(favorite_data).execute()

    def test_report_data_collections_modifications(self, db_service, sample_template_id, sample_instance_id, sample_user_id):
        """Test modifications to report_data_collections table"""
        # Create a report definition first
        report_result = db_service.client.table('report_definitions').insert({
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'Backfill Report',
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'owner_id': sample_user_id,
            'parameters': {},
            'frequency': 'once'
        }).execute()
        report_uuid = report_result.data[0]['id']

        collection_data = {
            'collection_id': f'col_{uuid.uuid4().hex[:8]}',
            'name': 'Test Backfill',
            'instance_id': sample_instance_id,
            'workflow_id': str(uuid.uuid4()),  # Legacy field
            'report_id': report_uuid,  # New field
            'segment_type': 'weekly',  # New field
            'max_lookback_days': 180,  # New field
            'status': 'pending',
            'total_weeks': 26,
            'completed_weeks': 0
        }

        result = db_service.client.table('report_data_collections').insert(collection_data).execute()
        assert result.data[0]['report_id'] == report_uuid
        assert result.data[0]['segment_type'] == 'weekly'
        assert result.data[0]['max_lookback_days'] == 180

        # Test segment_type constraint
        with pytest.raises(Exception):
            db_service.client.table('report_data_collections').insert({
                **collection_data,
                'collection_id': f'col_{uuid.uuid4().hex[:8]}',
                'segment_type': 'invalid_segment'
            }).execute()

        # Test max_lookback_days constraint (max 365)
        with pytest.raises(Exception):
            db_service.client.table('report_data_collections').insert({
                **collection_data,
                'collection_id': f'col_{uuid.uuid4().hex[:8]}',
                'max_lookback_days': 400
            }).execute()

    def test_report_runs_overview_view(self, db_service, sample_template_id, sample_instance_id, sample_user_id):
        """Test that report_runs_overview view returns expected data"""
        # Create a complete report with schedule and execution
        report_result = db_service.client.table('report_definitions').insert({
            'report_id': f'rpt_{uuid.uuid4().hex[:8]}',
            'name': 'View Test Report',
            'description': 'Testing the view',
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'owner_id': sample_user_id,
            'parameters': {},
            'frequency': 'weekly',
            'is_active': True,
            'execution_count': 5
        }).execute()
        report_uuid = report_result.data[0]['id']

        # Add a schedule
        db_service.client.table('report_schedules').insert({
            'schedule_id': f'sch_{uuid.uuid4().hex[:8]}',
            'report_id': report_uuid,
            'schedule_type': 'weekly',
            'cron_expression': '0 3 * * 1',
            'timezone': 'UTC',
            'is_active': True,
            'is_paused': False,
            'next_run_at': (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        }).execute()

        # Add an execution
        db_service.client.table('report_executions').insert({
            'execution_id': f'exec_{uuid.uuid4().hex[:8]}',
            'report_id': report_uuid,
            'template_id': sample_template_id,
            'instance_id': sample_instance_id,
            'user_id': sample_user_id,
            'triggered_by': 'schedule',
            'status': 'completed',
            'started_at': datetime.utcnow().isoformat() + 'Z',
            'completed_at': datetime.utcnow().isoformat() + 'Z'
        }).execute()

        # Query the view
        result = db_service.client.rpc('get_report_runs_overview', {
            'filter_report_id': report_uuid
        }).execute()

        assert len(result.data) > 0
        report_view = result.data[0]
        assert report_view['report_uuid'] == report_uuid
        assert report_view['name'] == 'View Test Report'
        assert report_view['frequency'] == 'weekly'
        assert report_view['state'] == 'active'
        assert report_view['latest_status'] == 'completed'
        assert report_view['execution_count'] == 5

    def test_workflow_archival(self, db_service):
        """Test that workflow tables are properly archived"""
        # Check if archived tables exist
        tables = db_service.client.rpc('get_database_tables', {
            'schema_name': 'public'
        }).execute()

        table_names = [t['table_name'] for t in tables.data]

        # Archived tables should exist
        assert 'archived_workflows' in table_names
        assert 'archived_workflow_executions' in table_names

        # Original tables should have deprecation comments
        workflow_comment = db_service.client.rpc('get_table_comment', {
            'table_name': 'workflows'
        }).execute()

        if workflow_comment.data:
            assert 'DEPRECATED' in workflow_comment.data[0].get('comment', '')

    def test_indexes_exist(self, db_service):
        """Test that all required indexes are created"""
        indexes = db_service.client.rpc('get_table_indexes', {
            'schema_name': 'public'
        }).execute()

        expected_indexes = [
            'idx_query_templates_report_type',
            'idx_report_definitions_owner',
            'idx_report_definitions_instance',
            'idx_report_definitions_template',
            'idx_report_definitions_active',
            'idx_report_executions_report',
            'idx_report_executions_status',
            'idx_report_executions_started',
            'idx_report_schedules_next_run',
            'idx_report_schedules_report',
            'idx_dashboard_favorites_user',
            'idx_collections_report'
        ]

        index_names = [idx['index_name'] for idx in indexes.data]

        for expected_idx in expected_indexes:
            assert expected_idx in index_names, f"Missing index: {expected_idx}"