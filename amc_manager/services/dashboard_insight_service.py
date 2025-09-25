"""Service for managing dashboard insights"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class DashboardInsightService(DatabaseService):
    """Service for managing AI-generated dashboard insights"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_insight(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new dashboard insight

        Args:
            insight_data: Insight data including:
                - dashboard_view_id: Parent dashboard view
                - insight_type: Type of insight (trend, anomaly, recommendation, summary, comparison)
                - insight_text: The insight text
                - confidence_score: Confidence score (0-1)
                - source_data: Data used to generate insight
                - ai_model: AI model used
                - prompt_version: Version of prompt used

        Returns:
            Created dashboard insight
        """
        try:
            # Validate insight type
            if not self.validate_insight_type(insight_data.get('insight_type')):
                raise ValueError(f"Invalid insight type: {insight_data.get('insight_type')}")

            # Validate confidence score
            confidence_score = insight_data.get('confidence_score', 0.5)
            if not 0 <= confidence_score <= 1:
                raise ValueError(f"Confidence score must be between 0 and 1: {confidence_score}")

            # Prepare data for insertion
            insert_data = {
                'dashboard_view_id': insight_data['dashboard_view_id'],
                'insight_type': insight_data['insight_type'],
                'insight_text': insight_data['insight_text'],
                'confidence_score': float(confidence_score),  # Ensure it's a float
                'source_data': insight_data.get('source_data', {}),
                'ai_model': insight_data.get('ai_model'),
                'prompt_version': insight_data.get('prompt_version'),
                'generated_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('dashboard_insights').insert(insert_data).execute()

            if response.data:
                logger.info(f"Created dashboard insight: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("Failed to create dashboard insight")

        except Exception as e:
            logger.error(f"Error creating dashboard insight: {e}")
            raise

    @with_connection_retry
    def get_insight(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a dashboard insight by ID

        Args:
            insight_id: Dashboard insight ID

        Returns:
            Dashboard insight or None if not found
        """
        try:
            response = self.client.table('dashboard_insights')\
                .select('*')\
                .eq('id', insight_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching dashboard insight {insight_id}: {e}")
            return None

    @with_connection_retry
    def get_insights_for_view(self, view_id: str, insight_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all insights for a dashboard view

        Args:
            view_id: Dashboard view ID
            insight_type: Optional filter by insight type

        Returns:
            List of dashboard insights
        """
        try:
            query = self.client.table('dashboard_insights')\
                .select('*')\
                .eq('dashboard_view_id', view_id)

            if insight_type:
                query = query.eq('insight_type', insight_type)

            response = query.order('generated_at', desc=True).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching insights for view {view_id}: {e}")
            return []

    @with_connection_retry
    def get_recent_insights(self, view_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent insights within a time period

        Args:
            view_id: Dashboard view ID
            hours: Number of hours to look back (default 24)

        Returns:
            List of recent dashboard insights
        """
        try:
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            response = self.client.table('dashboard_insights')\
                .select('*')\
                .eq('dashboard_view_id', view_id)\
                .gte('generated_at', cutoff_time)\
                .order('generated_at', desc=True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching recent insights for view {view_id}: {e}")
            return []

    @with_connection_retry
    def get_high_confidence_insights(self, view_id: str, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
        """
        Get only high confidence insights

        Args:
            view_id: Dashboard view ID
            min_confidence: Minimum confidence score (default 0.8)

        Returns:
            List of high confidence insights
        """
        try:
            response = self.client.table('dashboard_insights')\
                .select('*')\
                .eq('dashboard_view_id', view_id)\
                .gte('confidence_score', min_confidence)\
                .order('confidence_score', desc=True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching high confidence insights for view {view_id}: {e}")
            return []

    @with_connection_retry
    def update_insight(self, insight_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a dashboard insight

        Args:
            insight_id: Dashboard insight ID
            update_data: Fields to update

        Returns:
            Updated dashboard insight or None if not found
        """
        try:
            # Validate insight type if provided
            if 'insight_type' in update_data:
                if not self.validate_insight_type(update_data['insight_type']):
                    raise ValueError(f"Invalid insight type: {update_data['insight_type']}")

            # Validate confidence score if provided
            if 'confidence_score' in update_data:
                confidence_score = update_data['confidence_score']
                if not 0 <= confidence_score <= 1:
                    raise ValueError(f"Confidence score must be between 0 and 1: {confidence_score}")
                update_data['confidence_score'] = float(confidence_score)

            response = self.client.table('dashboard_insights')\
                .update(update_data)\
                .eq('id', insight_id)\
                .execute()

            if response.data:
                logger.info(f"Updated dashboard insight: {insight_id}")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating dashboard insight {insight_id}: {e}")
            raise

    @with_connection_retry
    def delete_insight(self, insight_id: str) -> bool:
        """
        Delete a dashboard insight

        Args:
            insight_id: Dashboard insight ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.client.table('dashboard_insights')\
                .delete()\
                .eq('id', insight_id)\
                .execute()

            if response.data:
                logger.info(f"Deleted dashboard insight: {insight_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting dashboard insight {insight_id}: {e}")
            return False

    @with_connection_retry
    def delete_old_insights(self, view_id: str, days_to_keep: int = 30) -> int:
        """
        Delete insights older than specified days

        Args:
            view_id: Dashboard view ID
            days_to_keep: Number of days to keep insights (default 30)

        Returns:
            Number of insights deleted
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

            response = self.client.table('dashboard_insights')\
                .delete()\
                .eq('dashboard_view_id', view_id)\
                .lt('generated_at', cutoff_date)\
                .execute()

            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} old insights for view {view_id}")
            return count

        except Exception as e:
            logger.error(f"Error deleting old insights for view {view_id}: {e}")
            return 0

    @with_connection_retry
    def bulk_create_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple insights at once

        Args:
            insights: List of insight data dictionaries

        Returns:
            List of created insights
        """
        try:
            # Validate and prepare all insights
            prepared_insights = []
            for insight_data in insights:
                # Validate insight type
                if not self.validate_insight_type(insight_data.get('insight_type')):
                    logger.warning(f"Skipping invalid insight type: {insight_data.get('insight_type')}")
                    continue

                # Validate confidence score
                confidence_score = insight_data.get('confidence_score', 0.5)
                if not 0 <= confidence_score <= 1:
                    logger.warning(f"Skipping invalid confidence score: {confidence_score}")
                    continue

                prepared_insights.append({
                    'dashboard_view_id': insight_data['dashboard_view_id'],
                    'insight_type': insight_data['insight_type'],
                    'insight_text': insight_data['insight_text'],
                    'confidence_score': float(confidence_score),
                    'source_data': insight_data.get('source_data', {}),
                    'ai_model': insight_data.get('ai_model'),
                    'prompt_version': insight_data.get('prompt_version'),
                    'generated_at': datetime.utcnow().isoformat()
                })

            if not prepared_insights:
                logger.warning("No valid insights to create")
                return []

            response = self.client.table('dashboard_insights').insert(prepared_insights).execute()

            if response.data:
                logger.info(f"Created {len(response.data)} dashboard insights")
                return response.data
            return []

        except Exception as e:
            logger.error(f"Error bulk creating insights: {e}")
            return []

    @with_connection_retry
    def get_insights_by_type_and_confidence(
        self,
        view_id: str,
        insight_types: List[str],
        min_confidence: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get insights grouped by type with minimum confidence

        Args:
            view_id: Dashboard view ID
            insight_types: List of insight types to retrieve
            min_confidence: Minimum confidence score

        Returns:
            Dictionary with insight types as keys and lists of insights as values
        """
        try:
            result = {}

            for insight_type in insight_types:
                if not self.validate_insight_type(insight_type):
                    continue

                response = self.client.table('dashboard_insights')\
                    .select('*')\
                    .eq('dashboard_view_id', view_id)\
                    .eq('insight_type', insight_type)\
                    .gte('confidence_score', min_confidence)\
                    .order('confidence_score', desc=True)\
                    .execute()

                result[insight_type] = response.data if response.data else []

            return result

        except Exception as e:
            logger.error(f"Error fetching insights by type for view {view_id}: {e}")
            return {}

    @with_connection_retry
    def get_latest_insights_per_type(self, view_id: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get the most recent insight of each type for a view

        Args:
            view_id: Dashboard view ID

        Returns:
            Dictionary with insight types as keys and latest insight as value
        """
        try:
            insight_types = ['trend', 'anomaly', 'recommendation', 'summary', 'comparison']
            result = {}

            for insight_type in insight_types:
                response = self.client.table('dashboard_insights')\
                    .select('*')\
                    .eq('dashboard_view_id', view_id)\
                    .eq('insight_type', insight_type)\
                    .order('generated_at', desc=True)\
                    .limit(1)\
                    .execute()

                result[insight_type] = response.data[0] if response.data else None

            return result

        except Exception as e:
            logger.error(f"Error fetching latest insights for view {view_id}: {e}")
            return {}

    def validate_insight_type(self, insight_type: str) -> bool:
        """
        Validate insight type against allowed values

        Args:
            insight_type: Insight type to validate

        Returns:
            True if valid, False otherwise
        """
        valid_types = ['trend', 'anomaly', 'recommendation', 'summary', 'comparison']
        return insight_type in valid_types

    @with_connection_retry
    def get_insights_for_configuration(self, config_id: str, insight_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get insights for a report configuration

        Args:
            config_id: Report configuration ID
            insight_type: Filter by insight type (optional)
            limit: Maximum number of insights to return

        Returns:
            List of insights
        """
        try:
            # First, get all views for this configuration
            views_response = self.client.table('dashboard_views')\
                .select('id')\
                .eq('report_configuration_id', config_id)\
                .execute()

            if not views_response.data:
                return []

            view_ids = [view['id'] for view in views_response.data]

            # Get insights for all views
            query = self.client.table('dashboard_insights')\
                .select('*')\
                .in_('dashboard_view_id', view_ids)\
                .order('confidence_score', desc=True)\
                .limit(limit)

            if insight_type:
                query = query.eq('insight_type', insight_type)

            response = query.execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching insights for configuration {config_id}: {e}")
            return []

    async def generate_insights_async(self, config_id: str, task_id: str, force_refresh: bool = False, insight_types: Optional[List[str]] = None):
        """
        Asynchronously generate insights for a report configuration

        Args:
            config_id: Report configuration ID
            task_id: Task ID for tracking progress
            force_refresh: Force regeneration even if recent insights exist
            insight_types: Specific insight types to generate

        Note: This is a placeholder for async insight generation.
        Actual implementation would connect to AI service.
        """
        try:
            logger.info(f"Starting async insight generation for config {config_id}, task {task_id}")

            # In a real implementation, this would:
            # 1. Fetch data for the configuration
            # 2. Send to AI service for analysis
            # 3. Store generated insights
            # 4. Update task status

            # For now, just log the operation
            logger.info(f"Insight generation would process config {config_id} with types {insight_types}")

            if force_refresh:
                logger.info("Force refresh enabled - clearing existing insights")

            # Simulate async processing
            import asyncio
            await asyncio.sleep(2)

            logger.info(f"Completed async insight generation for task {task_id}")

        except Exception as e:
            logger.error(f"Error in async insight generation: {e}")
            raise

    def format_insight_for_display(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an insight for display in the UI

        Args:
            insight: Raw insight data

        Returns:
            Formatted insight data
        """
        try:
            # Convert confidence score to percentage
            confidence_percent = int(insight.get('confidence_score', 0) * 100)

            # Get appropriate icon for insight type
            type_icons = {
                'trend': '📈',
                'anomaly': '⚠️',
                'recommendation': '💡',
                'summary': '📊',
                'comparison': '⚖️'
            }

            # Get appropriate color for confidence level
            if confidence_percent >= 80:
                confidence_color = 'green'
            elif confidence_percent >= 60:
                confidence_color = 'yellow'
            else:
                confidence_color = 'red'

            return {
                'id': insight['id'],
                'type': insight['insight_type'],
                'text': insight['insight_text'],
                'confidence': confidence_percent,
                'confidence_color': confidence_color,
                'icon': type_icons.get(insight['insight_type'], '📝'),
                'generated_at': insight['generated_at'],
                'ai_model': insight.get('ai_model', 'Unknown'),
                'source_data': insight.get('source_data', {})
            }

        except Exception as e:
            logger.error(f"Error formatting insight: {e}")
            return insight