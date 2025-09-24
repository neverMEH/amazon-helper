"""Service for managing report configurations"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportConfigurationService(DatabaseService):
    """Service for managing report configurations and dashboard settings"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_report_config(self, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a new report configuration

        Args:
            config_data: Report configuration data including:
                - workflow_id OR query_template_id (one required)
                - dashboard_type: Type of dashboard (funnel, performance, etc.)
                - visualization_settings: Chart and visualization configs
                - data_aggregation_settings: Data aggregation rules
                - export_settings: Export preferences
                - is_enabled: Whether report is enabled
            user_id: User ID creating the configuration

        Returns:
            Created report configuration
        """
        try:
            # Validate that either workflow_id or query_template_id is provided, but not both
            has_workflow = 'workflow_id' in config_data and config_data['workflow_id']
            has_template = 'query_template_id' in config_data and config_data['query_template_id']

            if has_workflow and has_template:
                raise ValueError("Provide either workflow_id or query_template_id, not both")
            if not has_workflow and not has_template:
                raise ValueError("Either workflow_id or query_template_id is required")

            # Validate dashboard type
            if 'dashboard_type' in config_data:
                if not self.validate_dashboard_type(config_data['dashboard_type']):
                    raise ValueError(f"Invalid dashboard type: {config_data['dashboard_type']}")

            # Prepare data for insertion
            insert_data = {
                'workflow_id': config_data.get('workflow_id'),
                'query_template_id': config_data.get('query_template_id'),
                'dashboard_type': config_data.get('dashboard_type', 'custom'),
                'visualization_settings': config_data.get('visualization_settings', {}),
                'data_aggregation_settings': config_data.get('data_aggregation_settings', {}),
                'export_settings': config_data.get('export_settings', {}),
                'is_enabled': config_data.get('is_enabled', False),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('report_configurations').insert(insert_data).execute()

            if response.data:
                logger.info(f"Created report configuration: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("Failed to create report configuration")

        except Exception as e:
            logger.error(f"Error creating report configuration: {e}")
            raise

    @with_connection_retry
    def get_report_config(self, config_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a report configuration by ID

        Args:
            config_id: Report configuration ID
            user_id: User ID for authorization

        Returns:
            Report configuration or None if not found
        """
        try:
            response = self.client.table('report_configurations')\
                .select('*')\
                .eq('id', config_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching report configuration {config_id}: {e}")
            return None

    @with_connection_retry
    def list_report_configs(self, user_id: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all report configurations for a user

        Args:
            user_id: User ID
            enabled_only: If True, only return enabled configurations

        Returns:
            List of report configurations
        """
        try:
            # First get user's workflows
            workflows_response = self.client.table('workflows')\
                .select('id')\
                .eq('user_id', user_id)\
                .execute()

            workflow_ids = [w['id'] for w in workflows_response.data] if workflows_response.data else []

            # Build query for report configurations
            query = self.client.table('report_configurations').select('*')

            # Filter by workflows or templates
            if workflow_ids:
                query = query.in_('workflow_id', workflow_ids)

            # Filter by enabled status if requested
            if enabled_only:
                query = query.eq('is_enabled', True)

            response = query.order('created_at', desc=True).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error listing report configurations: {e}")
            return []

    @with_connection_retry
    def update_report_config(self, config_id: str, update_data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """
        Update a report configuration

        Args:
            config_id: Report configuration ID
            update_data: Fields to update
            user_id: User ID for authorization

        Returns:
            Updated report configuration or None if not found
        """
        try:
            # Validate dashboard type if provided
            if 'dashboard_type' in update_data:
                if not self.validate_dashboard_type(update_data['dashboard_type']):
                    raise ValueError(f"Invalid dashboard type: {update_data['dashboard_type']}")

            # Add updated_at timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()

            response = self.client.table('report_configurations')\
                .update(update_data)\
                .eq('id', config_id)\
                .execute()

            if response.data:
                logger.info(f"Updated report configuration: {config_id}")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating report configuration {config_id}: {e}")
            raise

    @with_connection_retry
    def delete_report_config(self, config_id: str, user_id: str) -> bool:
        """
        Delete a report configuration

        Args:
            config_id: Report configuration ID
            user_id: User ID for authorization

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.client.table('report_configurations')\
                .delete()\
                .eq('id', config_id)\
                .execute()

            if response.data:
                logger.info(f"Deleted report configuration: {config_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting report configuration {config_id}: {e}")
            return False

    @with_connection_retry
    def toggle_enabled(self, config_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Toggle the enabled status of a report configuration

        Args:
            config_id: Report configuration ID
            user_id: User ID for authorization

        Returns:
            Updated report configuration or None if not found
        """
        try:
            # Get current status
            current = self.get_report_config(config_id, user_id)
            if not current:
                return None

            # Toggle the status
            new_status = not current.get('is_enabled', False)

            return self.update_report_config(config_id, {'is_enabled': new_status}, user_id)

        except Exception as e:
            logger.error(f"Error toggling report configuration {config_id}: {e}")
            return None

    @with_connection_retry
    def bulk_update_enabled(self, config_ids: List[str], enabled: bool, user_id: str) -> List[Dict[str, Any]]:
        """
        Bulk update enabled status for multiple report configurations

        Args:
            config_ids: List of report configuration IDs
            enabled: New enabled status
            user_id: User ID for authorization

        Returns:
            List of updated report configurations
        """
        try:
            update_data = {
                'is_enabled': enabled,
                'updated_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('report_configurations')\
                .update(update_data)\
                .in_('id', config_ids)\
                .execute()

            if response.data:
                logger.info(f"Bulk updated {len(response.data)} report configurations")
                return response.data
            return []

        except Exception as e:
            logger.error(f"Error bulk updating report configurations: {e}")
            return []

    @with_connection_retry
    def get_config_by_workflow(self, workflow_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get report configuration by workflow ID

        Args:
            workflow_id: Workflow ID
            user_id: User ID for authorization

        Returns:
            Report configuration or None if not found
        """
        try:
            response = self.client.table('report_configurations')\
                .select('*')\
                .eq('workflow_id', workflow_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching report configuration for workflow {workflow_id}: {e}")
            return None

    @with_connection_retry
    def get_config_by_template(self, template_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get report configuration by query template ID

        Args:
            template_id: Query template ID
            user_id: User ID for authorization

        Returns:
            Report configuration or None if not found
        """
        try:
            response = self.client.table('report_configurations')\
                .select('*')\
                .eq('query_template_id', template_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching report configuration for template {template_id}: {e}")
            return None

    @with_connection_retry
    def create_or_update_workflow_config(self, workflow_id: str, config_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create or update report configuration for a workflow

        Args:
            workflow_id: Workflow ID
            config_data: Report configuration data
            user_id: User ID

        Returns:
            Created or updated report configuration
        """
        try:
            # Check if config already exists
            existing = self.get_config_by_workflow(workflow_id, user_id)

            if existing:
                # Update existing config
                return self.update_report_config(existing['id'], config_data, user_id)
            else:
                # Create new config
                config_data['workflow_id'] = workflow_id
                return self.create_report_config(config_data, user_id)

        except Exception as e:
            logger.error(f"Error creating/updating report configuration for workflow {workflow_id}: {e}")
            raise

    def validate_dashboard_type(self, dashboard_type: str) -> bool:
        """
        Validate dashboard type against allowed values

        Args:
            dashboard_type: Dashboard type to validate

        Returns:
            True if valid, False otherwise
        """
        valid_types = ['funnel', 'performance', 'attribution', 'audience', 'custom']
        return dashboard_type in valid_types

    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Validate settings JSON structure

        Args:
            settings: Settings dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # For now, just check that it's a dictionary
        # Can add more specific validation logic here
        return isinstance(settings, dict)