"""Query Template Management Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager

logger = get_logger(__name__)


class QueryTemplateService:
    """Service for managing query templates"""
    
    def create_template(self, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new query template"""
        try:
            # Generate unique template_id
            template_data['template_id'] = f"tpl_{uuid.uuid4().hex[:12]}"
            
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('query_templates').insert(template_data).execute()
            
            if response.data:
                logger.info(f"Created query template: {response.data[0]['template_id']}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating query template: {e}")
            return None
    
    def get_template(self, template_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific query template"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('query_templates')\
                .select('*')\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                template = response.data[0]
                # Check access: owner or public template
                if template['user_id'] == user_id or template.get('is_public', False):
                    return template
                else:
                    logger.warning(f"User {user_id} denied access to private template {template_id}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error getting query template {template_id}: {e}")
            return None
    
    def list_templates(self, user_id: str, include_public: bool = True, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List query templates accessible to user"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Build query for user's templates and optionally public templates
            query = client.table('query_templates').select('*')
            
            if include_public:
                # Get user's templates OR public templates
                query = query.or_(f'user_id.eq.{user_id},is_public.eq.true')
            else:
                # Only user's templates
                query = query.eq('user_id', user_id)
            
            if category:
                query = query.eq('category', category)
            
            # Order by usage_count desc, then created_at desc
            query = query.order('usage_count', desc=True).order('created_at', desc=True)
            
            response = query.execute()
            
            templates = response.data or []
            logger.info(f"Retrieved {len(templates)} templates for user {user_id}")
            return templates
        except Exception as e:
            logger.error(f"Error listing query templates: {e}")
            return []
    
    def update_template(self, template_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a query template"""
        try:
            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot update template {template_id}")
                return None
            
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('query_templates')\
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
    
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """Delete a query template"""
        try:
            # First check ownership
            template = self.get_template(template_id, user_id)
            if not template or template['user_id'] != user_id:
                logger.warning(f"User {user_id} cannot delete template {template_id}")
                return False
            
            client = SupabaseManager.get_client(use_service_role=True)
            response = client.table('query_templates')\
                .delete()\
                .eq('template_id', template_id)\
                .execute()
            
            logger.info(f"Deleted query template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting query template {template_id}: {e}")
            return False
    
    def increment_usage(self, template_id: str) -> None:
        """Increment usage count for a template"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get current usage count
            response = client.table('query_templates')\
                .select('usage_count')\
                .eq('template_id', template_id)\
                .execute()
            
            if response.data:
                current_count = response.data[0].get('usage_count', 0)
                
                # Increment usage count
                client.table('query_templates')\
                    .update({'usage_count': current_count + 1})\
                    .eq('template_id', template_id)\
                    .execute()
                
                logger.info(f"Incremented usage count for template {template_id}")
        except Exception as e:
            logger.error(f"Error incrementing usage count for template {template_id}: {e}")
    
    def get_categories(self, user_id: str) -> List[str]:
        """Get all unique categories accessible to user"""
        try:
            client = SupabaseManager.get_client(use_service_role=True)
            
            # Get distinct categories from user's templates and public templates
            response = client.table('query_templates')\
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
    
    def create_from_workflow(self, workflow_id: str, user_id: str, template_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a template from an existing workflow"""
        try:
            # Get workflow details
            client = SupabaseManager.get_client(use_service_role=True)
            workflow_response = client.table('workflows')\
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
                'tags': template_data.get('tags', workflow.get('tags', []))
            }
            
            return self.create_template(template)
        except Exception as e:
            logger.error(f"Error creating template from workflow {workflow_id}: {e}")
            return None


# Create singleton instance
query_template_service = QueryTemplateService()