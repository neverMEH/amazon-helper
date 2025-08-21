"""Build Guide Management Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from ..core.logger_simple import get_logger
from ..core.supabase_client import SupabaseManager
from .db_service import DatabaseService, with_connection_retry

logger = get_logger(__name__)


class BuildGuideService(DatabaseService):
    """Service for managing build guides and user progress"""
    
    def __init__(self):
        super().__init__()
    
    @with_connection_retry
    async def list_guides(
        self, 
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_published: bool = True
    ) -> List[Dict[str, Any]]:
        """List all available build guides with optional filtering"""
        try:
            query = self.client.table('build_guides').select(
                '*, user_guide_progress!left(status, progress_percentage), user_guide_favorites!left(id)'
            )
            
            if is_published:
                query = query.eq('is_published', True)
            
            if category:
                query = query.eq('category', category)
            
            query = query.order('display_order').order('created_at', desc=False)
            
            response = query.execute()
            guides = response.data or []
            
            # Process guides to add user-specific data
            for guide in guides:
                # Check if user has progress
                progress = guide.pop('user_guide_progress', [])
                if user_id and progress:
                    user_progress = next((p for p in progress if p.get('user_id') == user_id), None)
                    if user_progress:
                        guide['user_progress'] = {
                            'status': user_progress.get('status', 'not_started'),
                            'progress_percentage': user_progress.get('progress_percentage', 0)
                        }
                else:
                    guide['user_progress'] = {
                        'status': 'not_started',
                        'progress_percentage': 0
                    }
                
                # Check if user has favorited
                favorites = guide.pop('user_guide_favorites', [])
                guide['is_favorite'] = bool(user_id and any(f.get('user_id') == user_id for f in favorites))
            
            logger.info(f"Retrieved {len(guides)} build guides")
            return guides
            
        except Exception as e:
            logger.error(f"Error listing build guides: {e}")
            return []
    
    @with_connection_retry
    async def get_guide(self, guide_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a specific build guide with all its sections and queries"""
        try:
            # Get guide with sections, queries, and metrics
            response = self.client.table('build_guides').select(
                '''
                *,
                build_guide_sections(*),
                build_guide_queries(*, build_guide_examples(*)),
                build_guide_metrics(*),
                user_guide_progress!left(*),
                user_guide_favorites!left(id)
                '''
            ).eq('guide_id', guide_id).single().execute()
            
            if not response.data:
                logger.warning(f"Guide not found: {guide_id}")
                return None
            
            guide = response.data
            
            # Sort sections and queries by display_order
            if 'build_guide_sections' in guide:
                guide['sections'] = sorted(
                    guide.pop('build_guide_sections', []), 
                    key=lambda x: x.get('display_order', 0)
                )
            
            if 'build_guide_queries' in guide:
                queries = guide.pop('build_guide_queries', [])
                for query in queries:
                    if 'build_guide_examples' in query:
                        query['examples'] = sorted(
                            query.pop('build_guide_examples', []),
                            key=lambda x: x.get('display_order', 0)
                        )
                guide['queries'] = sorted(queries, key=lambda x: x.get('display_order', 0))
            
            if 'build_guide_metrics' in guide:
                guide['metrics'] = sorted(
                    guide.pop('build_guide_metrics', []),
                    key=lambda x: x.get('display_order', 0)
                )
            
            # Add user progress if available
            progress = guide.pop('user_guide_progress', [])
            if user_id and progress:
                user_progress = next((p for p in progress if p.get('user_id') == user_id), None)
                if user_progress:
                    guide['user_progress'] = user_progress
            
            # Check if favorited
            favorites = guide.pop('user_guide_favorites', [])
            guide['is_favorite'] = bool(user_id and any(f.get('user_id') == user_id for f in favorites))
            
            logger.info(f"Retrieved guide: {guide_id}")
            return guide
            
        except Exception as e:
            logger.error(f"Error getting guide {guide_id}: {e}")
            return None
    
    @with_connection_retry
    async def start_guide(self, guide_id: str, user_id: str) -> Dict[str, Any]:
        """Start or resume a guide for a user"""
        try:
            # Check if progress already exists
            existing = self.client.table('user_guide_progress').select('*').eq(
                'user_id', user_id
            ).eq('guide_id', guide_id).execute()
            
            if existing.data:
                # Update last accessed
                response = self.client.table('user_guide_progress').update({
                    'last_accessed_at': datetime.utcnow().isoformat(),
                    'status': 'in_progress' if existing.data[0]['status'] == 'not_started' else existing.data[0]['status']
                }).eq('id', existing.data[0]['id']).execute()
                
                logger.info(f"Resumed guide {guide_id} for user {user_id}")
                return response.data[0] if response.data else existing.data[0]
            else:
                # Create new progress entry
                # First get the guide to find its ID
                guide_response = self.client.table('build_guides').select('id').eq('guide_id', guide_id).single().execute()
                
                if not guide_response.data:
                    raise ValueError(f"Guide not found: {guide_id}")
                
                progress_data = {
                    'user_id': user_id,
                    'guide_id': guide_response.data['id'],
                    'status': 'in_progress',
                    'started_at': datetime.utcnow().isoformat(),
                    'last_accessed_at': datetime.utcnow().isoformat(),
                    'completed_sections': [],
                    'executed_queries': [],
                    'progress_percentage': 0
                }
                
                response = self.client.table('user_guide_progress').insert(progress_data).execute()
                
                logger.info(f"Started guide {guide_id} for user {user_id}")
                return response.data[0] if response.data else progress_data
                
        except Exception as e:
            logger.error(f"Error starting guide {guide_id}: {e}")
            raise
    
    @with_connection_retry
    async def update_progress(
        self,
        guide_id: str,
        user_id: str,
        section_id: Optional[str] = None,
        query_id: Optional[str] = None,
        mark_complete: bool = False
    ) -> Dict[str, Any]:
        """Update user progress on a guide"""
        try:
            # Get current progress
            progress_response = self.client.table('user_guide_progress').select('*').eq(
                'user_id', user_id
            ).match({'guide_id': guide_id}).execute()
            
            if not progress_response.data:
                # Start the guide first
                await self.start_guide(guide_id, user_id)
                progress_response = self.client.table('user_guide_progress').select('*').eq(
                    'user_id', user_id
                ).match({'guide_id': guide_id}).execute()
            
            progress = progress_response.data[0]
            completed_sections = progress.get('completed_sections', [])
            executed_queries = progress.get('executed_queries', [])
            
            # Update completed sections
            if section_id and section_id not in completed_sections:
                completed_sections.append(section_id)
            
            # Update executed queries
            if query_id and query_id not in executed_queries:
                executed_queries.append(query_id)
            
            # Calculate progress percentage
            # Get total sections and queries for the guide
            guide_response = self.client.table('build_guides').select(
                'build_guide_sections(id), build_guide_queries(id)'
            ).eq('id', guide_id).single().execute()
            
            if guide_response.data:
                total_sections = len(guide_response.data.get('build_guide_sections', []))
                total_queries = len(guide_response.data.get('build_guide_queries', []))
                total_items = total_sections + total_queries
                
                if total_items > 0:
                    completed_items = len(completed_sections) + len(executed_queries)
                    progress_percentage = int((completed_items / total_items) * 100)
                else:
                    progress_percentage = 0
            else:
                progress_percentage = progress.get('progress_percentage', 0)
            
            # Determine status
            status = progress['status']
            if mark_complete or progress_percentage >= 100:
                status = 'completed'
                completed_at = datetime.utcnow().isoformat()
            else:
                status = 'in_progress'
                completed_at = None
            
            # Update progress
            update_data = {
                'completed_sections': completed_sections,
                'executed_queries': executed_queries,
                'progress_percentage': progress_percentage,
                'status': status,
                'last_accessed_at': datetime.utcnow().isoformat(),
                'current_section': section_id if section_id else progress.get('current_section')
            }
            
            if completed_at:
                update_data['completed_at'] = completed_at
            
            response = self.client.table('user_guide_progress').update(
                update_data
            ).eq('id', progress['id']).execute()
            
            logger.info(f"Updated progress for guide {guide_id}, user {user_id}: {progress_percentage}%")
            return response.data[0] if response.data else update_data
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            raise
    
    @with_connection_retry
    async def toggle_favorite(self, guide_id: str, user_id: str) -> bool:
        """Toggle favorite status for a guide"""
        try:
            # Get guide UUID from guide_id
            guide_response = self.client.table('build_guides').select('id').eq('guide_id', guide_id).single().execute()
            
            if not guide_response.data:
                raise ValueError(f"Guide not found: {guide_id}")
            
            guide_uuid = guide_response.data['id']
            
            # Check if already favorited
            existing = self.client.table('user_guide_favorites').select('id').eq(
                'user_id', user_id
            ).eq('guide_id', guide_uuid).execute()
            
            if existing.data:
                # Remove favorite
                self.client.table('user_guide_favorites').delete().eq('id', existing.data[0]['id']).execute()
                logger.info(f"Removed favorite for guide {guide_id}, user {user_id}")
                return False
            else:
                # Add favorite
                self.client.table('user_guide_favorites').insert({
                    'user_id': user_id,
                    'guide_id': guide_uuid
                }).execute()
                logger.info(f"Added favorite for guide {guide_id}, user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            raise
    
    @with_connection_retry
    async def get_user_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all guide progress for a user"""
        try:
            response = self.client.table('user_guide_progress').select(
                '*, build_guides(guide_id, name, category, estimated_time_minutes)'
            ).eq('user_id', user_id).order('last_accessed_at', desc=True).execute()
            
            progress_list = response.data or []
            
            # Flatten the guide data
            for progress in progress_list:
                if 'build_guides' in progress:
                    guide = progress.pop('build_guides')
                    progress['guide'] = guide
            
            logger.info(f"Retrieved {len(progress_list)} progress records for user {user_id}")
            return progress_list
            
        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return []
    
    @with_connection_retry
    async def create_guide_query_template(
        self,
        guide_id: str,
        query_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Create a query template from a guide query"""
        try:
            # Get the guide query
            query_response = self.client.table('build_guide_queries').select('*').eq('id', query_id).single().execute()
            
            if not query_response.data:
                raise ValueError(f"Query not found: {query_id}")
            
            guide_query = query_response.data
            
            # Create template
            template_data = {
                'template_id': f"tpl_{uuid.uuid4().hex[:12]}",
                'name': guide_query['title'],
                'description': guide_query.get('description', ''),
                'category': 'build-guide-templates',
                'sql_template': guide_query['sql_query'],
                'parameters_schema': guide_query.get('parameters_schema', {}),
                'default_parameters': guide_query.get('default_parameters', {}),
                'user_id': user_id,
                'is_public': False,
                'tags': [f'guide:{guide_id}', f'query:{query_id}'],
                'usage_count': 0
            }
            
            response = self.client.table('query_templates').insert(template_data).execute()
            
            if response.data:
                logger.info(f"Created template from guide query {query_id}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating template from guide query: {e}")
            return None
    
    @with_connection_retry
    async def get_guide_categories(self) -> List[str]:
        """Get all unique guide categories"""
        try:
            response = self.client.table('build_guides').select('category').eq('is_published', True).execute()
            
            categories = list(set(row['category'] for row in (response.data or []) if row.get('category')))
            categories.sort()
            
            logger.info(f"Retrieved {len(categories)} guide categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting guide categories: {e}")
            return []