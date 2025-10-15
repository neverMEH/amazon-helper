"""Instance Template Management Service

Manages SQL templates scoped to specific AMC instances
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..core.logger_simple import get_logger
from .db_service import DatabaseService, with_connection_retry

logger = get_logger(__name__)


class InstanceTemplateService(DatabaseService):
    """Service for managing instance-scoped SQL templates"""

    def __init__(self):
        """Initialize the instance template service"""
        super().__init__()
        self._template_cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._cache_timestamps = {}

    @with_connection_retry
    def create_template(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new instance template

        Args:
            template_data: Dictionary containing template fields:
                - name: Template name (required)
                - description: Template description (optional)
                - sql_query: SQL query text (required)
                - instance_id: UUID of AMC instance (required)
                - user_id: UUID of owner (required)
                - tags: List of tags (optional)

        Returns:
            Created template dict or None on error
        """
        try:
            logger.info(f"Creating instance template: {template_data.get('name')}")

            # Generate unique template_id
            template_data['template_id'] = f"tpl_inst_{uuid.uuid4().hex[:12]}"

            # Ensure usage_count is initialized
            if 'usage_count' not in template_data:
                template_data['usage_count'] = 0

            # Ensure tags is an array
            if 'tags' not in template_data:
                template_data['tags'] = []

            response = self.client.table('instance_templates').insert(template_data).execute()

            if response.data:
                logger.info(f"Created instance template: {response.data[0]['template_id']}")
                return response.data[0]
            else:
                logger.error("No data returned from insert operation")
                return None
        except Exception as e:
            logger.error(f"Error creating instance template: {e}")
            return None

    @with_connection_retry
    def get_template(self, template_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific instance template

        Args:
            template_id: Template identifier (tpl_inst_xxx)
            user_id: User requesting access (for access control)

        Returns:
            Template dict or None if not found/access denied
        """
        try:
            # Check cache first
            cache_key = f"{template_id}:{user_id}"
            if self._is_cache_valid(cache_key):
                return self._template_cache[cache_key]

            response = self.client.table('instance_templates')\
                .select('*')\
                .eq('template_id', template_id)\
                .execute()

            if response.data:
                template = response.data[0]

                # Check access: only owner can view
                if template['user_id'] == user_id:
                    # Update cache
                    self._update_cache(cache_key, template)
                    return template
                else:
                    logger.warning(f"User {user_id} denied access to template {template_id}")
                    return None

            return None
        except Exception as e:
            logger.error(f"Error getting instance template {template_id}: {e}")
            return None

    @with_connection_retry
    def list_templates(self, instance_id: str, user_id: str) -> List[Dict[str, Any]]:
        """List all templates for a specific instance and user

        Args:
            instance_id: UUID of AMC instance
            user_id: UUID of template owner

        Returns:
            List of template dicts
        """
        try:
            query = self.client.table('instance_templates')\
                .select('*')\
                .eq('instance_id', instance_id)\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)

            response = query.execute()

            templates = response.data or []
            logger.info(f"Retrieved {len(templates)} templates for instance {instance_id}, user {user_id}")
            return templates
        except Exception as e:
            logger.error(f"Error listing instance templates: {e}")
            return []

    @with_connection_retry
    def update_template(self, template_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing instance template

        Args:
            template_id: Template identifier
            user_id: User requesting update (must be owner)
            updates: Dictionary of fields to update

        Returns:
            Updated template dict or None on error/access denied
        """
        try:
            # Invalidate cache
            self._invalidate_cache(f"{template_id}:{user_id}")

            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot update template {template_id}")
                return None

            response = self.client.table('instance_templates')\
                .update(updates)\
                .eq('template_id', template_id)\
                .execute()

            if response.data:
                logger.info(f"Updated instance template: {template_id}")
                return response.data[0]

            return None
        except Exception as e:
            logger.error(f"Error updating instance template {template_id}: {e}")
            return None

    @with_connection_retry
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete an instance template

        Args:
            template_id: Template identifier
            user_id: User requesting deletion (must be owner)

        Returns:
            True if deleted, False on error/access denied
        """
        try:
            # Invalidate cache
            self._invalidate_cache(f"{template_id}:{user_id}")

            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot delete template {template_id}")
                return False

            response = self.client.table('instance_templates')\
                .delete()\
                .eq('template_id', template_id)\
                .execute()

            logger.info(f"Deleted instance template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting instance template {template_id}: {e}")
            return False

    @with_connection_retry
    def increment_usage(self, template_id: str) -> None:
        """Increment usage count for a template

        Args:
            template_id: Template identifier
        """
        try:
            # Get current usage count
            response = self.client.table('instance_templates')\
                .select('usage_count')\
                .eq('template_id', template_id)\
                .execute()

            if response.data:
                current_count = response.data[0].get('usage_count', 0)

                # Increment usage count
                self.client.table('instance_templates')\
                    .update({'usage_count': current_count + 1})\
                    .eq('template_id', template_id)\
                    .execute()

                logger.info(f"Incremented usage count for template {template_id}")
        except Exception as e:
            logger.error(f"Error incrementing usage count for template {template_id}: {e}")

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
        logger.info("Instance template cache cleared")


# Create singleton instance
instance_template_service = InstanceTemplateService()
