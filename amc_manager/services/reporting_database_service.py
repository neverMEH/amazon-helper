"""Database service for Reports & Analytics Platform operations"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timezone
import uuid
import hashlib
import json
from .db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportingDatabaseService(DatabaseService):
    """Service layer for reporting platform database operations"""
    
    def __init__(self):
        super().__init__()
    
    # ========== Dashboard Operations ==========
    
    @with_connection_retry
    def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new dashboard"""
        try:
            # Generate IDs if not provided
            if 'id' not in dashboard_data:
                dashboard_data['id'] = str(uuid.uuid4())
            if 'dashboard_id' not in dashboard_data:
                dashboard_data['dashboard_id'] = f"dash_{uuid.uuid4().hex[:8]}"
            
            # Set defaults
            dashboard_data.setdefault('layout_config', {})
            dashboard_data.setdefault('filter_config', {})
            dashboard_data.setdefault('is_public', False)
            dashboard_data.setdefault('is_template', False)
            
            response = self.client.table('dashboards').insert(dashboard_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return None
    
    @with_connection_retry
    def get_dashboard_with_widgets(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get dashboard with all its widgets"""
        try:
            # Get dashboard with widgets in a single query
            response = self.client.table('dashboards')\
                .select('*, dashboard_widgets(*)')\
                .eq('dashboard_id', dashboard_id)\
                .single()\
                .execute()
            
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching dashboard with widgets: {e}")
            return None
    
    @with_connection_retry
    def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update dashboard configuration"""
        try:
            # Remove fields that shouldn't be updated
            updates.pop('id', None)
            updates.pop('dashboard_id', None)
            updates.pop('created_at', None)
            
            response = self.client.table('dashboards')\
                .update(updates)\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
            return None
    
    @with_connection_retry
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard and all associated widgets (cascade)"""
        try:
            response = self.client.table('dashboards')\
                .delete()\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error deleting dashboard: {e}")
            return False
    
    @with_connection_retry
    def get_user_dashboards(self, user_id: str, include_shared: bool = True) -> List[Dict[str, Any]]:
        """Get all dashboards for a user (owned and optionally shared)"""
        try:
            # Get owned dashboards
            owned_response = self.client.table('dashboards')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()
            
            dashboards = owned_response.data or []
            
            if include_shared:
                # Get shared dashboards
                shared_response = self.client.table('dashboard_shares')\
                    .select('*, dashboards(*)')\
                    .eq('shared_with_user_id', user_id)\
                    .execute()
                
                if shared_response.data:
                    for share in shared_response.data:
                        if share.get('dashboards'):
                            dashboard = share['dashboards']
                            dashboard['permission_level'] = share.get('permission_level', 'view')
                            dashboard['is_shared'] = True
                            dashboards.append(dashboard)
            
            return dashboards
        except Exception as e:
            logger.error(f"Error fetching user dashboards: {e}")
            return []
    
    # ========== Widget Operations ==========
    
    @with_connection_retry
    def create_widget(self, widget_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new dashboard widget"""
        try:
            # Generate IDs if not provided
            if 'id' not in widget_data:
                widget_data['id'] = str(uuid.uuid4())
            if 'widget_id' not in widget_data:
                widget_data['widget_id'] = f"widget_{uuid.uuid4().hex[:8]}"
            
            # Set defaults
            widget_data.setdefault('display_config', {})
            
            response = self.client.table('dashboard_widgets').insert(widget_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating widget: {e}")
            return None
    
    @with_connection_retry
    def update_widget(self, widget_id: str, dashboard_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update widget configuration"""
        try:
            # Remove fields that shouldn't be updated
            updates.pop('id', None)
            updates.pop('widget_id', None)
            updates.pop('dashboard_id', None)
            updates.pop('created_at', None)
            
            response = self.client.table('dashboard_widgets')\
                .update(updates)\
                .eq('widget_id', widget_id)\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating widget: {e}")
            return None
    
    @with_connection_retry
    def delete_widget(self, widget_id: str, dashboard_id: str) -> bool:
        """Delete a widget from a dashboard"""
        try:
            response = self.client.table('dashboard_widgets')\
                .delete()\
                .eq('widget_id', widget_id)\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error deleting widget: {e}")
            return False
    
    @with_connection_retry
    def reorder_widgets(self, dashboard_id: str, widget_positions: List[Dict[str, Any]]) -> bool:
        """Update positions for multiple widgets"""
        try:
            # Update each widget's position
            for position_data in widget_positions:
                widget_id = position_data.get('widget_id')
                position_config = position_data.get('position_config')
                
                if widget_id and position_config:
                    self.client.table('dashboard_widgets')\
                        .update({'position_config': position_config})\
                        .eq('widget_id', widget_id)\
                        .eq('dashboard_id', dashboard_id)\
                        .execute()
            
            return True
        except Exception as e:
            logger.error(f"Error reordering widgets: {e}")
            return False
    
    # ========== Data Collection Operations ==========
    
    @with_connection_retry
    def create_collection(self, collection_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new data collection job"""
        try:
            # Generate IDs if not provided
            if 'id' not in collection_data:
                collection_data['id'] = str(uuid.uuid4())
            if 'collection_id' not in collection_data:
                collection_data['collection_id'] = f"coll_{uuid.uuid4().hex[:8]}"
            
            # Set defaults
            collection_data.setdefault('status', 'pending')
            collection_data.setdefault('progress_percentage', 0)
            collection_data.setdefault('weeks_completed', 0)
            collection_data.setdefault('configuration', {})
            
            response = self.client.table('report_data_collections').insert(collection_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return None
    
    @with_connection_retry
    def update_collection_progress(self, collection_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update collection progress and status"""
        try:
            # Calculate progress percentage if not provided
            if 'weeks_completed' in updates and 'target_weeks' not in updates:
                # Get the target weeks from the collection
                collection = self.get_collection_status(collection_id)
                if collection:
                    target_weeks = collection.get('target_weeks', 1)
                    updates['progress_percentage'] = int(
                        (updates['weeks_completed'] / target_weeks) * 100
                    )
            
            response = self.client.table('report_data_collections')\
                .update(updates)\
                .eq('collection_id', collection_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating collection progress: {e}")
            return None
    
    @with_connection_retry
    def get_collection_status(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a collection job"""
        try:
            response = self.client.table('report_data_collections')\
                .select('*, report_data_weeks(count), amc_instances!instance_id(instance_id)')\
                .eq('id', collection_id)\
                .single()\
                .execute()
            
            # If we have the response, extract the actual AMC instance_id
            if response.data:
                data = response.data
                # Get the actual AMC instance_id from the joined table
                if 'amc_instances' in data and data['amc_instances']:
                    data['amc_instance_id'] = data['amc_instances']['instance_id']
                return data
            return None
        except Exception as e:
            logger.error(f"Error fetching collection status: {e}")
            return None
    
    @with_connection_retry
    def get_user_collections(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all data collections for a user"""
        try:
            query = self.client.table('report_data_collections')\
                .select('*, workflows(name, workflow_id), amc_instances(instance_name, instance_id)')\
                .eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            response = query.order('created_at', desc=True).execute()
            collections = response.data or []
            
            # Add the AMC instance_id to each collection
            for collection in collections:
                if 'amc_instances' in collection and collection['amc_instances']:
                    collection['amc_instance_id'] = collection['amc_instances']['instance_id']
                    collection['instance_name'] = collection['amc_instances']['instance_name']
            
            return collections
        except Exception as e:
            logger.error(f"Error fetching user collections: {e}")
            return []
    
    @with_connection_retry
    def create_week_record(self, week_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a record for a single week's collection"""
        try:
            if 'id' not in week_data:
                week_data['id'] = str(uuid.uuid4())
            
            week_data.setdefault('status', 'pending')
            
            response = self.client.table('report_data_weeks').insert(week_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating week record: {e}")
            return None
    
    @with_connection_retry
    def update_week_status(self, week_id: str, status: str, **kwargs) -> bool:
        """Update the status of a week's collection
        
        Args:
            week_id: UUID of the week record
            status: New status for the week
            **kwargs: Optional fields including:
                - execution_date: When the execution started
                - execution_id: UUID of the workflow_execution record
                - amc_execution_id: AMC's execution ID
                - row_count: Number of rows returned
                - data_checksum: Checksum of the data
                - error_message: Error message if failed
        """
        try:
            updates = {'status': status}
            
            # Add optional fields
            if 'execution_date' in kwargs:
                # Convert datetime to ISO string if necessary
                exec_date = kwargs['execution_date']
                if hasattr(exec_date, 'isoformat'):
                    updates['execution_date'] = exec_date.isoformat()
                else:
                    updates['execution_date'] = exec_date
            
            # Handle execution tracking fields - with fallback for missing columns
            # Try to use new columns, but handle if they don't exist
            
            # Core fields that should always exist
            if 'row_count' in kwargs:
                # First try 'record_count', fallback to 'row_count' if it exists
                updates['row_count'] = kwargs['row_count']  # Use the older column name for now
                
            if 'data_checksum' in kwargs:
                updates['data_checksum'] = kwargs['data_checksum']
                
            if 'error_message' in kwargs:
                updates['error_message'] = kwargs['error_message']
            
            # Try to add execution tracking if columns exist
            # These might fail if columns don't exist, so we'll handle gracefully
            execution_tracking_updates = {}
            
            if 'execution_id' in kwargs:
                execution_tracking_updates['execution_id'] = kwargs['execution_id']
                # Also set workflow_execution_id for backward compatibility
                execution_tracking_updates['workflow_execution_id'] = kwargs['execution_id']
                logger.debug(f"Will try to store execution_id {kwargs['execution_id']} for week {week_id}")
            
            if 'amc_execution_id' in kwargs:
                # Check if this column exists by trying a minimal update first
                # For now, skip if it causes issues
                logger.debug(f"AMC execution_id {kwargs['amc_execution_id']} available for week {week_id}")
            
            # For execution_date, use the existing column if available
            if 'execution_date' in kwargs:
                updates['execution_date'] = kwargs['execution_date']
            elif status == 'running':
                # Use execution_date instead of started_at if that column exists
                updates['execution_date'] = datetime.now(timezone.utc).isoformat()
            
            # First try with all fields, then retry without problematic ones if needed
            all_updates = {**updates, **execution_tracking_updates}
            
            try:
                # Try with all updates including execution tracking
                response = self.client.table('report_data_weeks')\
                    .update(all_updates)\
                    .eq('id', week_id)\
                    .execute()
                
                if response.data:
                    logger.info(f"Updated week {week_id} status to {status} with execution tracking")
                
                return bool(response.data)
                
            except Exception as e:
                # If it fails, try without the execution tracking fields
                if 'PGRST204' in str(e) or 'column' in str(e).lower():
                    logger.warning(f"Some columns not available, retrying with basic fields: {e}")
                    
                    # Retry with only basic fields that we know exist
                    basic_updates = {'status': status}
                    
                    # Only add fields we're sure exist in the original schema
                    if 'execution_date' in updates:
                        basic_updates['execution_date'] = updates['execution_date']
                    if 'row_count' in updates:
                        basic_updates['row_count'] = updates['row_count']
                    if 'data_checksum' in updates:
                        basic_updates['data_checksum'] = updates['data_checksum']
                    if 'error_message' in updates:
                        basic_updates['error_message'] = updates['error_message']
                    
                    # Also try to store execution_id - try both column names
                    if 'execution_id' in execution_tracking_updates:
                        # Set both columns for compatibility
                        basic_updates['execution_id'] = execution_tracking_updates['execution_id']
                        basic_updates['workflow_execution_id'] = execution_tracking_updates['execution_id']
                    
                    response = self.client.table('report_data_weeks')\
                        .update(basic_updates)\
                        .eq('id', week_id)\
                        .execute()
                    
                    if response.data:
                        logger.info(f"Updated week {week_id} status to {status} (basic fields only)")
                    
                    return bool(response.data)
                else:
                    # Re-raise if it's a different error
                    raise
        except Exception as e:
            logger.error(f"Error updating week status: {e}")
            return False
    
    @with_connection_retry
    def check_duplicate_week(self, collection_id: str, week_start: date, checksum: str) -> bool:
        """Check if a week's data already exists with the same checksum"""
        try:
            response = self.client.table('report_data_weeks')\
                .select('id')\
                .eq('collection_id', collection_id)\
                .eq('week_start_date', week_start.isoformat())\
                .eq('data_checksum', checksum)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error checking duplicate week: {e}")
            return False
    
    # ========== Data Aggregation Operations ==========
    
    @with_connection_retry
    def create_or_update_aggregate(self, aggregate_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update aggregated data"""
        try:
            # Generate checksum for unique constraint
            unique_key = f"{aggregate_data['workflow_id']}_{aggregate_data['instance_id']}_{aggregate_data['aggregation_type']}_{aggregate_data['aggregation_key']}_{aggregate_data['data_date']}"
            
            if 'id' not in aggregate_data:
                aggregate_data['id'] = str(uuid.uuid4())
            
            # Use upsert to handle conflicts
            response = self.client.table('report_data_aggregates')\
                .upsert(
                    aggregate_data,
                    on_conflict='workflow_id,instance_id,aggregation_type,aggregation_key,data_date'
                )\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating/updating aggregate: {e}")
            return None
    
    @with_connection_retry
    def get_aggregates_for_dashboard(
        self, 
        workflow_id: str, 
        instance_id: str,
        aggregation_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated data for dashboard visualization"""
        try:
            query = self.client.table('report_data_aggregates')\
                .select('*')\
                .eq('workflow_id', workflow_id)\
                .eq('instance_id', instance_id)\
                .eq('aggregation_type', aggregation_type)
            
            if start_date:
                query = query.gte('data_date', start_date.isoformat())
            if end_date:
                query = query.lte('data_date', end_date.isoformat())
            
            response = query.order('data_date', desc=False).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching aggregates: {e}")
            return []
    
    @with_connection_retry
    def cleanup_old_aggregates(self, days_to_keep: int = 365) -> int:
        """Clean up aggregates older than specified days"""
        try:
            cutoff_date = (datetime.now().date() - timedelta(days=days_to_keep)).isoformat()
            
            response = self.client.table('report_data_aggregates')\
                .delete()\
                .lt('data_date', cutoff_date)\
                .execute()
            
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Error cleaning up old aggregates: {e}")
            return 0
    
    @with_connection_retry
    def compute_data_checksum(self, data: Any) -> str:
        """Compute checksum for data to detect duplicates"""
        try:
            # Convert data to JSON string for consistent hashing
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing checksum: {e}")
            return ""
    
    # ========== AI Insights Operations ==========
    
    @with_connection_retry
    def create_insight(self, insight_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Store an AI-generated insight"""
        try:
            if 'id' not in insight_data:
                insight_data['id'] = str(uuid.uuid4())
            if 'insight_id' not in insight_data:
                insight_data['insight_id'] = f"insight_{uuid.uuid4().hex[:8]}"
            
            insight_data.setdefault('data_context', {})
            insight_data.setdefault('related_metrics', {})
            
            response = self.client.table('ai_insights').insert(insight_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating insight: {e}")
            return None
    
    @with_connection_retry
    def get_user_insights(
        self, 
        user_id: str,
        dashboard_id: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get AI insights for a user"""
        try:
            query = self.client.table('ai_insights')\
                .select('*')\
                .eq('user_id', user_id)
            
            if dashboard_id:
                query = query.eq('dashboard_id', dashboard_id)
            if insight_type:
                query = query.eq('insight_type', insight_type)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching user insights: {e}")
            return []
    
    # ========== Dashboard Sharing Operations ==========
    
    @with_connection_retry
    def share_dashboard(
        self, 
        dashboard_id: str, 
        shared_by_user_id: str,
        shared_with_user_id: str,
        permission_level: str = 'view'
    ) -> Optional[Dict[str, Any]]:
        """Share a dashboard with another user"""
        try:
            share_data = {
                'id': str(uuid.uuid4()),
                'dashboard_id': dashboard_id,
                'shared_by_user_id': shared_by_user_id,
                'shared_with_user_id': shared_with_user_id,
                'permission_level': permission_level
            }
            
            response = self.client.table('dashboard_shares')\
                .upsert(
                    share_data,
                    on_conflict='dashboard_id,shared_with_user_id'
                )\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error sharing dashboard: {e}")
            return None
    
    @with_connection_retry
    def revoke_dashboard_share(self, dashboard_id: str, shared_with_user_id: str) -> bool:
        """Revoke dashboard sharing for a user"""
        try:
            response = self.client.table('dashboard_shares')\
                .delete()\
                .eq('dashboard_id', dashboard_id)\
                .eq('shared_with_user_id', shared_with_user_id)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error revoking dashboard share: {e}")
            return False
    
    @with_connection_retry
    def get_dashboard_shares(self, dashboard_id: str) -> List[Dict[str, Any]]:
        """Get all users a dashboard is shared with"""
        try:
            response = self.client.table('dashboard_shares')\
                .select('*, users!shared_with_user_id(id, email, name)')\
                .eq('dashboard_id', dashboard_id)\
                .execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching dashboard shares: {e}")
            return []
    
    @with_connection_retry
    def user_can_access_dashboard(self, user_id: str, dashboard_id: str) -> tuple[bool, str]:
        """Check if user can access a dashboard and return permission level"""
        try:
            # Check if user owns the dashboard
            dashboard_response = self.client.table('dashboards')\
                .select('user_id, is_public')\
                .eq('dashboard_id', dashboard_id)\
                .single()\
                .execute()
            
            if not dashboard_response.data:
                return False, 'none'
            
            dashboard = dashboard_response.data
            
            # Owner has full access
            if dashboard['user_id'] == user_id:
                return True, 'owner'
            
            # Check if dashboard is public
            if dashboard.get('is_public'):
                return True, 'view'
            
            # Check if dashboard is shared with user
            share_response = self.client.table('dashboard_shares')\
                .select('permission_level')\
                .eq('dashboard_id', dashboard_id)\
                .eq('shared_with_user_id', user_id)\
                .single()\
                .execute()
            
            if share_response.data:
                return True, share_response.data['permission_level']
            
            return False, 'none'
        except Exception as e:
            logger.error(f"Error checking dashboard access: {e}")
            return False, 'none'
    
    # ========== Dashboard Templates Operations ==========
    
    @with_connection_retry
    def get_dashboard_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available dashboard templates"""
        try:
            query = self.client.table('dashboards')\
                .select('*')\
                .eq('is_template', True)
            
            if template_type:
                query = query.eq('template_type', template_type)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching dashboard templates: {e}")
            return []
    
    @with_connection_retry
    def create_dashboard_from_template(
        self, 
        template_id: str, 
        user_id: str,
        name: str,
        instance_id: str
    ) -> Optional[Dict[str, Any]]:
        """Create a new dashboard from a template"""
        try:
            # Get the template with widgets
            template = self.get_dashboard_with_widgets(template_id)
            if not template:
                logger.error(f"Template {template_id} not found")
                return None
            
            # Create new dashboard
            new_dashboard = {
                'name': name,
                'description': template.get('description'),
                'user_id': user_id,
                'template_type': template.get('template_type'),
                'layout_config': template.get('layout_config'),
                'filter_config': template.get('filter_config'),
                'is_template': False
            }
            
            created_dashboard = self.create_dashboard(new_dashboard)
            if not created_dashboard:
                return None
            
            # Copy widgets with updated instance references
            for widget in template.get('dashboard_widgets', []):
                widget_copy = {
                    'dashboard_id': created_dashboard['id'],
                    'widget_type': widget['widget_type'],
                    'chart_type': widget.get('chart_type'),
                    'title': widget['title'],
                    'data_source': widget['data_source'],
                    'display_config': widget.get('display_config', {}),
                    'position_config': widget['position_config']
                }
                
                # Update instance_id in data_source if present
                if 'instance_id' in widget_copy['data_source']:
                    widget_copy['data_source']['instance_id'] = instance_id
                
                self.create_widget(widget_copy)
            
            return self.get_dashboard_with_widgets(created_dashboard['dashboard_id'])
        except Exception as e:
            logger.error(f"Error creating dashboard from template: {e}")
            return None


# Import timedelta for cleanup function
from datetime import timedelta


# Create global instance for easy import
reporting_db_service = ReportingDatabaseService()