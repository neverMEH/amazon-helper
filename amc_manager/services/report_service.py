"""
Report Service for AMC Report Builder
Handles CRUD operations for report definitions
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from amc_manager.services.db_service import DatabaseService, with_connection_retry
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportService(DatabaseService):
    """Service for managing report definitions"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_report(self, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new report definition

        Args:
            report_data: Report configuration including:
                - name: Report name
                - template_id: Reference to query template
                - instance_id: AMC instance ID
                - owner_id: User ID
                - parameters: Report parameters
                - frequency: once|daily|weekly|monthly|quarterly
                - timezone: Timezone for scheduling
                - description: Optional description

        Returns:
            Created report record or None if failed
        """
        try:
            # Generate unique report ID
            report_id = f"rpt_{uuid.uuid4().hex[:8]}"

            # Prepare report data
            report_record = {
                'report_id': report_id,
                'name': report_data['name'],
                'description': report_data.get('description'),
                'template_id': report_data['template_id'],
                'instance_id': report_data['instance_id'],
                'owner_id': report_data['owner_id'],
                'parameters': report_data.get('parameters', {}),
                'frequency': report_data.get('frequency', 'once'),
                'timezone': report_data.get('timezone', 'UTC'),
                'is_active': True,
                'execution_count': 0
            }

            # Create report
            response = self.client.table('report_definitions').insert(report_record).execute()

            if response.data:
                logger.info(f"Created report {report_id}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error creating report: {e}")
            return None

    @with_connection_retry
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get report by ID (UUID or report_id string)

        Args:
            report_id: Report UUID or report_id string

        Returns:
            Report record or None if not found
        """
        try:
            # Check if it's a UUID or report_id string
            if report_id.startswith('rpt_'):
                response = self.client.table('report_definitions').select('*').eq('report_id', report_id).execute()
            else:
                response = self.client.table('report_definitions').select('*').eq('id', report_id).execute()

            if response.data:
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {e}")
            return None

    @with_connection_retry
    def update_report(self, report_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update report configuration

        Args:
            report_id: Report UUID
            update_data: Fields to update

        Returns:
            Updated report record or None if failed
        """
        try:
            # Remove fields that shouldn't be updated
            update_data.pop('id', None)
            update_data.pop('report_id', None)
            update_data.pop('created_at', None)

            response = self.client.table('report_definitions').update(update_data).eq('id', report_id).execute()

            if response.data:
                logger.info(f"Updated report {report_id}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error updating report {report_id}: {e}")
            return None

    @with_connection_retry
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report definition

        Args:
            report_id: Report UUID

        Returns:
            True if deleted, False otherwise
        """
        try:
            response = self.client.table('report_definitions').delete().eq('id', report_id).execute()

            if response.data:
                logger.info(f"Deleted report {report_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting report {report_id}: {e}")
            return False

    @with_connection_retry
    def list_reports(
        self,
        instance_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        frequency: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List reports with optional filters

        Args:
            instance_id: Filter by AMC instance
            owner_id: Filter by owner
            is_active: Filter by active status
            frequency: Filter by frequency
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of report records
        """
        try:
            query = self.client.table('report_definitions').select('*')

            if instance_id:
                query = query.eq('instance_id', instance_id)
            if owner_id:
                query = query.eq('owner_id', owner_id)
            if is_active is not None:
                query = query.eq('is_active', is_active)
            if frequency:
                query = query.eq('frequency', frequency)

            query = query.order('created_at', desc=True).limit(limit).offset(offset)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error listing reports: {e}")
            return []

    @with_connection_retry
    def get_report_with_details(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get report with template and instance details

        Args:
            report_id: Report UUID

        Returns:
            Report record with joined data
        """
        try:
            response = self.client.table('report_definitions').select(
                '*',
                'query_templates(*)',
                'amc_instances(*)',
                'users!owner_id(*)'
            ).eq('id', report_id).execute()

            if response.data:
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"Error fetching report details {report_id}: {e}")
            return None

    @with_connection_retry
    def get_instance_with_entity(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get AMC instance with entity_id from joined amc_accounts table

        Args:
            instance_id: AMC instance UUID

        Returns:
            Instance record with entity_id or None
        """
        try:
            response = self.client.table('amc_instances').select(
                '*',
                'amc_accounts(account_id)'
            ).eq('id', instance_id).execute()

            if response.data and response.data[0].get('amc_accounts'):
                instance = response.data[0]
                # Add entity_id from amc_accounts.account_id
                instance['entity_id'] = instance['amc_accounts']['account_id']
                return instance

            return None

        except Exception as e:
            logger.error(f"Error fetching instance with entity {instance_id}: {e}")
            return None

    @with_connection_retry
    def create_report_with_dashboard(self, report_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create report and associated dashboard from template config

        Args:
            report_data: Report configuration

        Returns:
            Created report with dashboard_id
        """
        try:
            # First get the template to check for report_config
            template_response = self.client.table('query_templates').select(
                'report_config'
            ).eq('id', report_data['template_id']).execute()

            if not template_response.data:
                logger.error(f"Template {report_data['template_id']} not found")
                return None

            template = template_response.data[0]
            dashboard_id = None

            # Create dashboard if template has report_config
            if template.get('report_config'):
                dashboard_id = self.create_dashboard_from_config(
                    name=report_data['name'],
                    config=template['report_config'],
                    owner_id=report_data['owner_id']
                )
                report_data['dashboard_id'] = dashboard_id

            # Create the report
            report = self.create_report(report_data)

            if report and dashboard_id:
                logger.info(f"Created report {report['report_id']} with dashboard {dashboard_id}")

            return report

        except Exception as e:
            logger.error(f"Error creating report with dashboard: {e}")
            return None

    @with_connection_retry
    def create_dashboard_from_config(
        self,
        name: str,
        config: Dict[str, Any],
        owner_id: str
    ) -> Optional[str]:
        """
        Create a dashboard from report config

        Args:
            name: Dashboard name
            config: Dashboard configuration from template
            owner_id: User ID

        Returns:
            Dashboard ID or None if failed
        """
        try:
            dashboard_data = {
                'name': f"{name} Dashboard",
                'owner_id': owner_id,
                'config': config,
                'is_public': False
            }

            response = self.client.table('dashboards').insert(dashboard_data).execute()

            if response.data:
                return response.data[0]['id']

            return None

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return None

    @with_connection_retry
    def activate_report(self, report_id: str) -> bool:
        """
        Activate a report

        Args:
            report_id: Report UUID

        Returns:
            True if activated
        """
        return self.update_report(report_id, {'is_active': True}) is not None

    @with_connection_retry
    def deactivate_report(self, report_id: str) -> bool:
        """
        Deactivate a report

        Args:
            report_id: Report UUID

        Returns:
            True if deactivated
        """
        return self.update_report(report_id, {'is_active': False}) is not None

    @with_connection_retry
    def increment_execution_count(self, report_id: str) -> bool:
        """
        Increment the execution count for a report

        Args:
            report_id: Report UUID

        Returns:
            True if incremented
        """
        try:
            # Get current count
            report = self.get_report(report_id)
            if not report:
                return False

            new_count = report.get('execution_count', 0) + 1

            response = self.client.table('report_definitions').update({
                'execution_count': new_count,
                'last_execution_id': None  # Will be updated by execution service
            }).eq('id', report_id).execute()

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error incrementing execution count: {e}")
            return False

    @with_connection_retry
    def get_reports_overview(
        self,
        instance_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get reports overview from the view

        Args:
            instance_id: Filter by instance
            owner_id: Filter by owner
            limit: Maximum results

        Returns:
            List of report overview records
        """
        try:
            # Use the report_runs_overview view
            query = self.client.table('report_runs_overview').select('*')

            if instance_id:
                query = query.eq('instance_id', instance_id)
            if owner_id:
                query = query.eq('owner_id', owner_id)

            query = query.limit(limit)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching reports overview: {e}")
            return []