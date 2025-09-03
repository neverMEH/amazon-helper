"""Service for managing Query Flow Templates with CRUD operations"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import uuid
import json
from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class QueryFlowTemplateService(DatabaseService):
    """Service for managing query flow templates"""
    
    def __init__(self):
        super().__init__()
        
    @with_connection_retry
    def list_templates(
        self,
        user_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        include_stats: bool = True
    ) -> Dict[str, Any]:
        """
        List query flow templates with filtering and search
        
        Args:
            user_id: Current user ID for favorites check
            category: Filter by category
            search: Search in name and description
            tags: Filter by tags
            limit: Maximum number of results
            offset: Pagination offset
            include_stats: Include execution statistics
            
        Returns:
            Dict containing templates and metadata
        """
        try:
            # Build base query
            query = self.client.table('query_flow_templates').select(
                '*',
                count='exact'
            )
            
            # Apply filters
            query = query.eq('is_active', True)
            
            if category:
                query = query.eq('category', category)
            
            if search:
                # Search in name and description
                query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
            
            if tags:
                # Filter by tags (contains all specified tags)
                for tag in tags:
                    query = query.contains('tags', [tag])
            
            # Add pagination
            query = query.order('execution_count', desc=True)
            query = query.range(offset, offset + limit - 1)
            
            # Execute query
            result = query.execute()
            
            templates = result.data
            total_count = result.count
            
            # Enrich with additional data if requested
            if include_stats and templates:
                template_ids = [t['id'] for t in templates]
                
                # Get favorites for current user
                favorites_result = self.client.table('user_template_favorites')\
                    .select('template_id')\
                    .eq('user_id', user_id)\
                    .in_('template_id', template_ids)\
                    .execute()
                
                favorite_ids = {f['template_id'] for f in favorites_result.data}
                
                # Get average ratings
                ratings_result = self.client.table('template_ratings')\
                    .select('template_id, rating')\
                    .in_('template_id', template_ids)\
                    .execute()
                
                # Calculate average ratings per template
                ratings_by_template = {}
                rating_counts = {}
                for rating in ratings_result.data:
                    tid = rating['template_id']
                    if tid not in ratings_by_template:
                        ratings_by_template[tid] = []
                    ratings_by_template[tid].append(rating['rating'])
                
                for tid, ratings in ratings_by_template.items():
                    rating_counts[tid] = {
                        'avg_rating': sum(ratings) / len(ratings) if ratings else 0,
                        'rating_count': len(ratings)
                    }
                
                # Add stats to templates
                for template in templates:
                    template['is_favorite'] = template['id'] in favorite_ids
                    template['rating_info'] = rating_counts.get(template['id'], {
                        'avg_rating': 0,
                        'rating_count': 0
                    })
            
            return {
                'templates': templates,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            raise
    
    @with_connection_retry
    def get_template(
        self,
        template_id: str,
        user_id: Optional[str] = None,
        include_parameters: bool = True,
        include_charts: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single template with all details
        
        Args:
            template_id: Template ID (can be UUID or template_id string)
            user_id: Current user ID for personalization
            include_parameters: Include parameter definitions
            include_charts: Include chart configurations
            
        Returns:
            Template with full details or None if not found
        """
        try:
            # Check if template_id is UUID or string identifier
            if self._is_valid_uuid(template_id):
                query = self.client.table('query_flow_templates')\
                    .select('*')\
                    .eq('id', template_id)\
                    .eq('is_active', True)\
                    .single()
            else:
                query = self.client.table('query_flow_templates')\
                    .select('*')\
                    .eq('template_id', template_id)\
                    .eq('is_active', True)\
                    .single()
            
            result = query.execute()
            
            if not result.data:
                return None
            
            template = result.data
            
            # Get parameters
            if include_parameters:
                params_result = self.client.table('template_parameters')\
                    .select('*')\
                    .eq('template_id', template['id'])\
                    .order('order_index')\
                    .execute()
                
                template['parameters'] = params_result.data
            
            # Get chart configurations
            if include_charts:
                charts_result = self.client.table('template_chart_configs')\
                    .select('*')\
                    .eq('template_id', template['id'])\
                    .order('order_index')\
                    .execute()
                
                template['chart_configs'] = charts_result.data
            
            # Get user-specific data
            if user_id:
                # Check if favorited
                fav_result = self.client.table('user_template_favorites')\
                    .select('id')\
                    .eq('user_id', user_id)\
                    .eq('template_id', template['id'])\
                    .execute()
                
                template['is_favorite'] = len(fav_result.data) > 0
                
                # Get user's rating
                rating_result = self.client.table('template_ratings')\
                    .select('rating, review')\
                    .eq('user_id', user_id)\
                    .eq('template_id', template['id'])\
                    .execute()
                
                if rating_result.data:
                    template['user_rating'] = rating_result.data[0]
            
            # Update view count (execution_count for now)
            self.client.table('query_flow_templates')\
                .update({'execution_count': template.get('execution_count', 0) + 1})\
                .eq('id', template['id'])\
                .execute()
            
            return template
            
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {e}")
            return None
    
    @with_connection_retry
    def create_template(
        self,
        template_data: Dict[str, Any],
        parameters: List[Dict[str, Any]],
        chart_configs: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new query flow template
        
        Args:
            template_data: Template metadata and SQL
            parameters: List of parameter definitions
            chart_configs: List of chart configurations
            user_id: Creating user ID
            
        Returns:
            Created template with ID
        """
        try:
            # Add creator and timestamps
            template_data['created_by'] = user_id
            template_data['created_at'] = datetime.utcnow().isoformat()
            template_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Ensure template_id is set and valid
            if 'template_id' not in template_data:
                template_data['template_id'] = self._generate_template_id(template_data['name'])
            
            # Create template
            template_result = self.client.table('query_flow_templates')\
                .insert(template_data)\
                .execute()
            
            if not template_result.data:
                raise Exception("Failed to create template")
            
            template = template_result.data[0]
            
            # Add parameters
            if parameters:
                for i, param in enumerate(parameters):
                    param['template_id'] = template['id']
                    param['order_index'] = param.get('order_index', i)
                
                self.client.table('template_parameters')\
                    .insert(parameters)\
                    .execute()
            
            # Add chart configs
            if chart_configs:
                for i, chart in enumerate(chart_configs):
                    chart['template_id'] = template['id']
                    chart['order_index'] = chart.get('order_index', i)
                
                self.client.table('template_chart_configs')\
                    .insert(chart_configs)\
                    .execute()
            
            # Return complete template
            return self.get_template(template['id'], user_id)
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    @with_connection_retry
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update an existing template (only by creator)
        
        Args:
            template_id: Template ID to update
            updates: Fields to update
            user_id: User attempting update
            
        Returns:
            Updated template
        """
        try:
            # Check ownership
            template = self.get_template(template_id)
            if not template or template['created_by'] != user_id:
                raise Exception("Template not found or unauthorized")
            
            # Update timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Don't allow changing certain fields
            protected_fields = ['id', 'template_id', 'created_by', 'created_at']
            for field in protected_fields:
                updates.pop(field, None)
            
            # Update template
            result = self.client.table('query_flow_templates')\
                .update(updates)\
                .eq('id', template['id'])\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            raise
    
    @with_connection_retry
    def delete_template(
        self,
        template_id: str,
        user_id: str
    ) -> bool:
        """
        Soft delete a template (only by creator)
        
        Args:
            template_id: Template ID to delete
            user_id: User attempting deletion
            
        Returns:
            True if deleted successfully
        """
        try:
            # Check ownership
            template = self.get_template(template_id)
            if not template or template['created_by'] != user_id:
                raise Exception("Template not found or unauthorized")
            
            # Soft delete by setting is_active to false
            result = self.client.table('query_flow_templates')\
                .update({'is_active': False, 'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', template['id'])\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    @with_connection_retry
    def toggle_favorite(
        self,
        template_id: str,
        user_id: str
    ) -> bool:
        """
        Toggle template favorite status for a user
        
        Args:
            template_id: Template ID
            user_id: User ID
            
        Returns:
            True if now favorited, False if unfavorited
        """
        try:
            # Check if already favorited
            existing = self.client.table('user_template_favorites')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('template_id', template_id)\
                .execute()
            
            if existing.data:
                # Remove favorite
                self.client.table('user_template_favorites')\
                    .delete()\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
                return False
            else:
                # Add favorite
                self.client.table('user_template_favorites')\
                    .insert({
                        'user_id': user_id,
                        'template_id': template_id,
                        'created_at': datetime.utcnow().isoformat()
                    })\
                    .execute()
                return True
                
        except Exception as e:
            logger.error(f"Error toggling favorite for template {template_id}: {e}")
            raise
    
    @with_connection_retry
    def rate_template(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        review: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rate a template
        
        Args:
            template_id: Template ID
            user_id: User ID
            rating: Rating (1-5)
            review: Optional review text
            
        Returns:
            Rating record
        """
        try:
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
            
            # Check if already rated
            existing = self.client.table('template_ratings')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('template_id', template_id)\
                .execute()
            
            rating_data = {
                'template_id': template_id,
                'user_id': user_id,
                'rating': rating,
                'review': review,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if existing.data:
                # Update existing rating
                result = self.client.table('template_ratings')\
                    .update(rating_data)\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Create new rating
                rating_data['created_at'] = datetime.utcnow().isoformat()
                result = self.client.table('template_ratings')\
                    .insert(rating_data)\
                    .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error rating template {template_id}: {e}")
            raise
    
    @with_connection_retry
    def get_categories(self) -> List[str]:
        """Get all available template categories"""
        try:
            result = self.client.table('query_flow_templates')\
                .select('category')\
                .eq('is_active', True)\
                .execute()
            
            categories = list(set(row['category'] for row in result.data if row['category']))
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    @with_connection_retry
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular tags with counts"""
        try:
            result = self.client.table('query_flow_templates')\
                .select('tags')\
                .eq('is_active', True)\
                .execute()
            
            # Count tag occurrences
            tag_counts = {}
            for row in result.data:
                if row.get('tags'):
                    for tag in row['tags']:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count and return top tags
            sorted_tags = sorted(
                [{'tag': tag, 'count': count} for tag, count in tag_counts.items()],
                key=lambda x: x['count'],
                reverse=True
            )
            
            return sorted_tags[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular tags: {e}")
            return []
    
    # Helper methods
    def _is_valid_uuid(self, value: str) -> bool:
        """Check if a string is a valid UUID"""
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False
    
    def _generate_template_id(self, name: str) -> str:
        """Generate a template_id from template name"""
        import re
        # Convert to lowercase, replace spaces with underscores, remove special chars
        template_id = name.lower()
        template_id = re.sub(r'[^a-z0-9\s_-]', '', template_id)
        template_id = re.sub(r'\s+', '_', template_id)
        template_id = re.sub(r'[_-]+', '_', template_id)
        template_id = template_id.strip('_')
        
        # Add timestamp suffix to ensure uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        return f"{template_id}_{timestamp}"