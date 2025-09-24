"""Service for managing dashboard views"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class DashboardViewService(DatabaseService):
    """Service for managing dashboard views and their configurations"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_view(self, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new dashboard view

        Args:
            view_data: Dashboard view data including:
                - report_configuration_id: Parent report configuration
                - view_name: Name of the view
                - view_type: Type of view (chart, table, metric_card, insight)
                - chart_configurations: Chart-specific settings
                - filter_settings: Filters for this view
                - layout_settings: Layout and positioning
                - processed_data: Optional pre-processed data

        Returns:
            Created dashboard view
        """
        try:
            # Validate view type
            if not self.validate_view_type(view_data.get('view_type')):
                raise ValueError(f"Invalid view type: {view_data.get('view_type')}")

            # Prepare data for insertion
            insert_data = {
                'report_configuration_id': view_data['report_configuration_id'],
                'view_name': view_data['view_name'],
                'view_type': view_data['view_type'],
                'chart_configurations': view_data.get('chart_configurations', {}),
                'filter_settings': view_data.get('filter_settings', {}),
                'layout_settings': view_data.get('layout_settings', {}),
                'processed_data': view_data.get('processed_data'),
                'last_updated': datetime.utcnow().isoformat() if view_data.get('processed_data') else None,
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('dashboard_views').insert(insert_data).execute()

            if response.data:
                logger.info(f"Created dashboard view: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("Failed to create dashboard view")

        except Exception as e:
            logger.error(f"Error creating dashboard view: {e}")
            raise

    @with_connection_retry
    def get_view(self, view_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a dashboard view by ID

        Args:
            view_id: Dashboard view ID

        Returns:
            Dashboard view or None if not found
        """
        try:
            response = self.client.table('dashboard_views')\
                .select('*')\
                .eq('id', view_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching dashboard view {view_id}: {e}")
            return None

    @with_connection_retry
    def get_views_for_report(self, report_config_id: str) -> List[Dict[str, Any]]:
        """
        Get all views for a report configuration

        Args:
            report_config_id: Report configuration ID

        Returns:
            List of dashboard views
        """
        try:
            response = self.client.table('dashboard_views')\
                .select('*')\
                .eq('report_configuration_id', report_config_id)\
                .order('created_at')\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching views for report {report_config_id}: {e}")
            return []

    @with_connection_retry
    def update_view(self, view_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a dashboard view

        Args:
            view_id: Dashboard view ID
            update_data: Fields to update

        Returns:
            Updated dashboard view or None if not found
        """
        try:
            # Validate view type if provided
            if 'view_type' in update_data:
                if not self.validate_view_type(update_data['view_type']):
                    raise ValueError(f"Invalid view type: {update_data['view_type']}")

            response = self.client.table('dashboard_views')\
                .update(update_data)\
                .eq('id', view_id)\
                .execute()

            if response.data:
                logger.info(f"Updated dashboard view: {view_id}")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating dashboard view {view_id}: {e}")
            raise

    @with_connection_retry
    def update_processed_data(self, view_id: str, processed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update processed data for a dashboard view

        Args:
            view_id: Dashboard view ID
            processed_data: New processed data

        Returns:
            Updated dashboard view or None if not found
        """
        try:
            update_data = {
                'processed_data': processed_data,
                'last_updated': datetime.utcnow().isoformat()
            }

            return self.update_view(view_id, update_data)

        except Exception as e:
            logger.error(f"Error updating processed data for view {view_id}: {e}")
            raise

    @with_connection_retry
    def delete_view(self, view_id: str) -> bool:
        """
        Delete a dashboard view

        Args:
            view_id: Dashboard view ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.client.table('dashboard_views')\
                .delete()\
                .eq('id', view_id)\
                .execute()

            if response.data:
                logger.info(f"Deleted dashboard view: {view_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting dashboard view {view_id}: {e}")
            return False

    @with_connection_retry
    def bulk_delete_views(self, report_config_id: str) -> int:
        """
        Delete all views for a report configuration

        Args:
            report_config_id: Report configuration ID

        Returns:
            Number of views deleted
        """
        try:
            response = self.client.table('dashboard_views')\
                .delete()\
                .eq('report_configuration_id', report_config_id)\
                .execute()

            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} dashboard views for report {report_config_id}")
            return count

        except Exception as e:
            logger.error(f"Error bulk deleting views for report {report_config_id}: {e}")
            return 0

    @with_connection_retry
    def create_default_views(self, report_config_id: str, dashboard_type: str) -> List[Dict[str, Any]]:
        """
        Create default views based on dashboard type

        Args:
            report_config_id: Report configuration ID
            dashboard_type: Type of dashboard (funnel, performance, etc.)

        Returns:
            List of created dashboard views
        """
        try:
            # Define default views for each dashboard type
            default_views = self.get_default_views_config(dashboard_type)
            created_views = []

            for view_config in default_views:
                view_config['report_configuration_id'] = report_config_id
                view = self.create_view(view_config)
                created_views.append(view)

            logger.info(f"Created {len(created_views)} default views for dashboard type {dashboard_type}")
            return created_views

        except Exception as e:
            logger.error(f"Error creating default views: {e}")
            return []

    def get_default_views_config(self, dashboard_type: str) -> List[Dict[str, Any]]:
        """
        Get default view configurations for a dashboard type

        Args:
            dashboard_type: Type of dashboard

        Returns:
            List of view configurations
        """
        configs = {
            'funnel': [
                {
                    'view_name': 'Conversion Funnel',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'funnel',
                        'stages': ['Impressions', 'Clicks', 'Add to Cart', 'Purchases'],
                        'colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 0, 'w': 12, 'h': 6}}
                },
                {
                    'view_name': 'Stage Metrics',
                    'view_type': 'table',
                    'chart_configurations': {
                        'columns': ['Stage', 'Count', 'Conversion Rate', 'Drop-off']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 6, 'w': 6, 'h': 4}}
                },
                {
                    'view_name': 'Drop-off Analysis',
                    'view_type': 'insight',
                    'layout_settings': {'grid': {'x': 6, 'y': 6, 'w': 6, 'h': 4}}
                }
            ],
            'performance': [
                {
                    'view_name': 'KPI Cards',
                    'view_type': 'metric_card',
                    'chart_configurations': {
                        'metrics': ['Total Spend', 'Total Revenue', 'ROAS', 'CTR']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 0, 'w': 12, 'h': 2}}
                },
                {
                    'view_name': 'Performance Trend',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'line',
                        'xAxis': 'date',
                        'yAxis': ['impressions', 'clicks', 'conversions']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 2, 'w': 8, 'h': 4}}
                },
                {
                    'view_name': 'Campaign Comparison',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'bar',
                        'xAxis': 'campaign_name',
                        'yAxis': 'spend'
                    },
                    'layout_settings': {'grid': {'x': 8, 'y': 2, 'w': 4, 'h': 4}}
                },
                {
                    'view_name': 'Performance Table',
                    'view_type': 'table',
                    'chart_configurations': {
                        'columns': ['Campaign', 'Impressions', 'Clicks', 'CTR', 'Spend', 'ROAS']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 6, 'w': 12, 'h': 4}}
                }
            ],
            'attribution': [
                {
                    'view_name': 'Attribution Model Comparison',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'grouped-bar',
                        'models': ['Last Touch', 'First Touch', 'Linear', 'Time Decay']
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 0, 'w': 12, 'h': 5}}
                },
                {
                    'view_name': 'Path Analysis',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'sankey',
                        'showPaths': True
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 5, 'w': 8, 'h': 5}}
                },
                {
                    'view_name': 'Attribution Insights',
                    'view_type': 'insight',
                    'layout_settings': {'grid': {'x': 8, 'y': 5, 'w': 4, 'h': 5}}
                }
            ],
            'audience': [
                {
                    'view_name': 'Audience Demographics',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'pie',
                        'dimension': 'age_group'
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 0, 'w': 6, 'h': 4}}
                },
                {
                    'view_name': 'Geographic Distribution',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'map',
                        'dimension': 'region'
                    },
                    'layout_settings': {'grid': {'x': 6, 'y': 0, 'w': 6, 'h': 4}}
                },
                {
                    'view_name': 'Device Breakdown',
                    'view_type': 'chart',
                    'chart_configurations': {
                        'type': 'donut',
                        'dimension': 'device_type'
                    },
                    'layout_settings': {'grid': {'x': 0, 'y': 4, 'w': 4, 'h': 3}}
                },
                {
                    'view_name': 'Audience Segments',
                    'view_type': 'table',
                    'chart_configurations': {
                        'columns': ['Segment', 'Size', 'Conversion Rate', 'Avg Order Value']
                    },
                    'layout_settings': {'grid': {'x': 4, 'y': 4, 'w': 8, 'h': 3}}
                },
                {
                    'view_name': 'Audience Insights',
                    'view_type': 'insight',
                    'layout_settings': {'grid': {'x': 0, 'y': 7, 'w': 12, 'h': 3}}
                }
            ],
            'custom': [
                {
                    'view_name': 'Main Chart',
                    'view_type': 'chart',
                    'chart_configurations': {'type': 'line'},
                    'layout_settings': {'grid': {'x': 0, 'y': 0, 'w': 12, 'h': 6}}
                },
                {
                    'view_name': 'Data Table',
                    'view_type': 'table',
                    'layout_settings': {'grid': {'x': 0, 'y': 6, 'w': 12, 'h': 4}}
                }
            ]
        }

        return configs.get(dashboard_type, configs['custom'])

    @with_connection_retry
    def reorder_views(self, view_orders: List[Dict[str, Any]]) -> bool:
        """
        Reorder dashboard views by updating their layout settings

        Args:
            view_orders: List of dicts with view_id and new layout_settings

        Returns:
            True if successful, False otherwise
        """
        try:
            for order in view_orders:
                self.update_view(order['view_id'], {'layout_settings': order['layout_settings']})

            logger.info(f"Reordered {len(view_orders)} dashboard views")
            return True

        except Exception as e:
            logger.error(f"Error reordering views: {e}")
            return False

    def validate_view_type(self, view_type: str) -> bool:
        """
        Validate view type against allowed values

        Args:
            view_type: View type to validate

        Returns:
            True if valid, False otherwise
        """
        valid_types = ['chart', 'table', 'metric_card', 'insight']
        return view_type in valid_types

    def validate_chart_type(self, chart_type: str) -> bool:
        """
        Validate chart type against allowed values

        Args:
            chart_type: Chart type to validate

        Returns:
            True if valid, False otherwise
        """
        valid_types = [
            'line', 'bar', 'pie', 'donut', 'area', 'scatter',
            'funnel', 'heatmap', 'radar', 'sankey', 'grouped-bar',
            'stacked-bar', 'map', 'bubble', 'waterfall'
        ]
        return chart_type in valid_types