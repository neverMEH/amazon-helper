"""Query Template Management Service with enhanced versioning and forking"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from functools import wraps

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .db_service import DatabaseService, with_connection_retry

logger = get_logger(__name__)


class QueryTemplateService(DatabaseService):
    """Enhanced service for managing query templates with versioning and forking"""
    
    def __init__(self):
        """Initialize the query template service"""
        super().__init__()
        self._template_cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._cache_timestamps = {}
    
    @with_connection_retry
    def create_template(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new query template"""
        try:
            logger.info(f"Creating template with name: {template_data.get('name')}")
            logger.info(f"Template user_id: {template_data.get('user_id')}")
            logger.info(f"Template is_public: {template_data.get('is_public')}")

            # Generate unique template_id
            template_data['template_id'] = f"tpl_{uuid.uuid4().hex[:12]}"

            # Add default values for new fields
            if 'version' not in template_data:
                template_data['version'] = 1
            if 'execution_count' not in template_data:
                template_data['execution_count'] = 0

            logger.info(f"Inserting template with ID: {template_data['template_id']}")
            response = self.client.table('query_templates').insert(template_data).execute()

            if response.data:
                logger.info(f"Created query template successfully: {response.data[0]['template_id']}")
                return response.data[0]
            else:
                logger.error(f"No data returned from insert operation")
                return None
        except Exception as e:
            logger.error(f"Error creating query template: {e}")
            logger.error(f"Full error details: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Error response: {e.response}")
            return None
    
    @with_connection_retry
    def get_template(self, template_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific query template"""
        try:
            # Check cache first
            cache_key = f"{template_id}:{user_id}"
            if self._is_cache_valid(cache_key):
                return self._template_cache[cache_key]
            
            response = self.client.table('query_templates')\
                .select('*')\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                template = response.data[0]
                # Check access: owner or public template
                if template['user_id'] == user_id or template.get('is_public', False):
                    # Update cache
                    self._update_cache(cache_key, template)
                    return template
                else:
                    logger.warning(f"User {user_id} denied access to private template {template_id}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error getting query template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def list_templates(self, user_id: str, include_public: bool = True, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List query templates accessible to user"""
        try:
            # Build query for user's templates and optionally public templates
            query = self.client.table('query_templates').select('*')
            
            if include_public:
                # Get user's templates OR public templates
                query = query.or_(f'user_id.eq.{user_id},is_public.eq.true')
            else:
                # Only user's templates
                query = query.eq('user_id', user_id)
            
            if category:
                query = query.eq('category', category)
            
            # Order by execution_count desc, then created_at desc
            query = query.order('execution_count', desc=True).order('created_at', desc=True)
            
            response = query.execute()
            
            templates = response.data or []
            logger.info(f"Retrieved {len(templates)} templates for user {user_id}")
            return templates
        except Exception as e:
            logger.error(f"Error listing query templates: {e}")
            return []
    
    @with_connection_retry
    def update_template(self, template_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a query template"""
        try:
            # Invalidate cache
            self._invalidate_cache(f"{template_id}:{user_id}")
            
            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot update template {template_id}")
                return None
            
            response = self.client.table('query_templates')\
                .update(updates)\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated query template: {template_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating query template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a query template"""
        try:
            # Invalidate cache
            self._invalidate_cache(f"{template_id}:{user_id}")
            
            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot delete template {template_id}")
                return False
            
            response = self.client.table('query_templates')\
                .delete()\
                .eq('template_id', template_id)\
                .execute()
            
            logger.info(f"Deleted query template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting query template {template_id}: {e}")
            return False
    
    @with_connection_retry
    def increment_usage(self, template_id: str) -> None:
        """Increment usage count for a template (deprecated - use increment_execution_count)"""
        try:
            # Get current usage count
            response = self.client.table('query_templates')\
                .select('usage_count')\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                current_count = response.data[0].get('usage_count', 0)
                
                # Increment usage count
                self.client.table('query_templates')\
                    .update({'usage_count': current_count + 1})\
                    .eq('template_id', template_id)\
                    .execute()
                
                logger.info(f"Incremented usage count for template {template_id}")
        except Exception as e:
            logger.error(f"Error incrementing usage count for template {template_id}: {e}")
    
    @with_connection_retry
    def get_categories(self, user_id: str) -> List[str]:
        """Get all unique categories accessible to user"""
        try:
            # Get distinct categories from user's templates and public templates
            response = self.client.table('query_templates')\
                .select('category')\
                .or_(f'user_id.eq.{user_id},is_public.eq.true')\
                .execute()
            
            if response.data:
                # Extract unique categories
                categories = list(set(item['category'] for item in response.data if item.get('category')))
                categories.sort()
                return categories
            return []
        except Exception as e:
            logger.error(f"Error getting template categories: {e}")
            return []
    
    @with_connection_retry
    def create_from_workflow(self, workflow_id: str, user_id: str, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a template from an existing workflow"""
        try:
            # Get workflow details
            workflow_response = self.client.table('workflows')\
                .select('*')\
                .eq('workflow_id', workflow_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not workflow_response.data:
                logger.warning(f"Workflow {workflow_id} not found for user {user_id}")
                return None
            
            workflow = workflow_response.data[0]
            
            # Create template from workflow
            template = {
                'name': template_data.get('name', f"{workflow['name']} Template"),
                'description': template_data.get('description', workflow.get('description', '')),
                'category': template_data.get('category', 'Custom'),
                'sql_template': workflow['sql_query'],
                'parameters_schema': template_data.get('parameters_schema', {}),
                'default_parameters': workflow.get('parameters', {}),
                'user_id': user_id,
                'is_public': template_data.get('is_public', False),
                'tags': template_data.get('tags', workflow.get('tags', [])),
                'version': 1,
                'execution_count': 0
            }
            
            return self.create_template(template)
        except Exception as e:
            logger.error(f"Error creating template from workflow {workflow_id}: {e}")
            return None
    
    # Enhanced methods for versioning and forking
    
    @with_connection_retry
    def fork_template(self, template_id: str, user_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        """Fork a template to create a new version owned by the user"""
        try:
            # Use the database function to fork template with all relationships
            response = self.client.rpc(
                'fork_query_template',
                {
                    'source_template_id': template_id,
                    'new_user_id': user_id,
                    'new_name': new_name
                }
            ).execute()
            
            if response.data:
                logger.info(f"Forked template {template_id} to new template for user {user_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error forking template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def increment_version(self, template_id: str, user_id: str) -> Optional[int]:
        """Increment the version number of a template"""
        try:
            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot increment version of template {template_id}")
                return None
            
            current_version = template.get('version', 1)
            new_version = current_version + 1
            
            response = self.client.table('query_templates')\
                .update({'version': new_version})\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                self._invalidate_cache(f"{template_id}:{user_id}")
                logger.info(f"Incremented template {template_id} to version {new_version}")
                return new_version
            return None
        except Exception as e:
            logger.error(f"Error incrementing version for template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def get_template_versions(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a template (parent and children)"""
        try:
            # First get the template to find parent
            template_response = self.client.table('query_templates')\
                .select('id, parent_template_id')\
                .eq('template_id', template_id)\
                .execute()
            
            if not template_response.data:
                return []
            
            template = template_response.data[0]
            template_uuid = template['id']
            parent_id = template.get('parent_template_id')
            
            # Find the root parent if this is a child
            root_id = parent_id if parent_id else template_uuid
            
            # Get all versions (parent and all children)
            response = self.client.table('query_templates')\
                .select('*')\
                .or_(f'id.eq.{root_id},parent_template_id.eq.{root_id}')\
                .order('version', desc=False)\
                .execute()
            
            versions = response.data or []
            logger.info(f"Found {len(versions)} versions for template {template_id}")
            return versions
        except Exception as e:
            logger.error(f"Error getting versions for template {template_id}: {e}")
            return []
    
    @with_connection_retry
    def get_template_full(self, template_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get template with all related data (parameters, reports, instances)"""
        try:
            response = self.client.table('query_templates')\
                .select('''
                    *,
                    query_template_parameters(*),
                    query_template_reports(*),
                    query_template_instances!inner(*)
                ''')\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                template = response.data[0]
                # Check access
                if template['user_id'] == user_id or template.get('is_public', False):
                    # Filter instances to only user's instances
                    if 'query_template_instances' in template:
                        template['query_template_instances'] = [
                            inst for inst in template['query_template_instances']
                            if inst['user_id'] == user_id
                        ]
                    return template
                else:
                    logger.warning(f"User {user_id} denied access to private template {template_id}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error getting full template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def increment_execution_count(self, template_id: str) -> Optional[int]:
        """Increment the execution count for a template"""
        try:
            # Use database function for atomic increment
            response = self.client.rpc(
                'increment_template_execution_count',
                {'template_uuid': template_id}
            ).execute()
            
            if response.data:
                count = response.data[0].get('execution_count')
                logger.info(f"Incremented execution count for template {template_id} to {count}")
                return count
            return None
        except Exception as e:
            logger.error(f"Error incrementing execution count for template {template_id}: {e}")
            return None
    
    # Cache management methods
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._template_cache:
            return False
        
        timestamp = self._cache_timestamps.get(cache_key, 0)
        current_time = datetime.now().timestamp()
        
        return (current_time - timestamp) < self._cache_ttl
    
    def _update_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Update cache with new data"""
        self._template_cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now().timestamp()
    
    def _invalidate_cache(self, cache_key: str) -> None:
        """Invalidate a cache entry"""
        if cache_key in self._template_cache:
            del self._template_cache[cache_key]
        if cache_key in self._cache_timestamps:
            del self._cache_timestamps[cache_key]
    
    def clear_cache(self) -> None:
        """Clear entire template cache"""
        self._template_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Template cache cleared")


# Create singleton instance
query_template_service = QueryTemplateService()