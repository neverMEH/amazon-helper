"""Database service layer for Supabase operations"""

from typing import Optional, Dict, Any, List, TypeVar, Callable
from datetime import datetime
import uuid
from functools import wraps
from supabase import Client
from ..core.supabase_client import SupabaseManager
from ..core.logger_simple import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

def with_connection_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to retry database operations on connection errors"""
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> T:
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "Server disconnected" in error_msg or "connection" in error_msg.lower():
                logger.info(f"Connection error in {func.__name__}, forcing reconnection...")
                self._client = None  # Force reconnection
                try:
                    # Retry the operation
                    return func(self, *args, **kwargs)
                except Exception as retry_error:
                    logger.error(f"Retry failed for {func.__name__}: {retry_error}")
                    raise retry_error
            raise e
    return wrapper


class DatabaseService:
    """Unified database service for all Supabase operations"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._last_connection_time: Optional[datetime] = None
        self._connection_timeout_minutes = 30  # Refresh connection after 30 minutes
    
    @property
    def client(self) -> Client:
        """Get Supabase client with automatic refresh"""
        current_time = datetime.now()
        
        # Check if we need to refresh the connection
        if (self._client is None or 
            self._last_connection_time is None or
            (current_time - self._last_connection_time).total_seconds() > self._connection_timeout_minutes * 60):
            
            logger.info("Refreshing Supabase connection...")
            SupabaseManager.reset_clients()  # Reset the singleton
            self._client = SupabaseManager.get_client(use_service_role=True)
            self._last_connection_time = current_time
            logger.info("Supabase connection refreshed")
        
        return self._client
    
    # User operations - Sync versions for FastAPI
    @with_connection_retry
    def get_user_by_email_sync(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email - sync version"""
        try:
            response = self.client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None
    
    @with_connection_retry
    def get_user_instances_sync(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all AMC instances accessible to a user - sync version"""
        try:
            # First get user's accounts
            accounts_response = self.client.table('amc_accounts').select('id').eq('user_id', user_id).execute()
            if not accounts_response.data:
                return []
            
            account_ids = [acc['id'] for acc in accounts_response.data]
            
            # Then get instances for those accounts with joined account data
            instances_response = self.client.table('amc_instances')\
                .select('*, amc_accounts!inner(*)')\
                .in_('account_id', account_ids)\
                .eq('status', 'active')\
                .execute()
            
            return instances_response.data or []
        except Exception as e:
            logger.error(f"Error fetching user instances: {e}")
            return []
    
    @with_connection_retry
    def get_user_campaigns_sync(self, user_id: str, brand_tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get campaigns for user - sync version"""
        try:
            query = self.client.table('campaign_mappings').select('*').eq('user_id', user_id)
            if brand_tag:
                query = query.eq('brand_tag', brand_tag)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching campaigns: {e}")
            return []
    
    @with_connection_retry
    def get_user_workflows_sync(self, user_id: str) -> List[Dict[str, Any]]:
        """Get workflows for user - sync version"""
        try:
            response = self.client.table('workflows')\
                .select('*, amc_instances!inner(*)')\
                .eq('user_id', user_id)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching workflows: {e}")
            return []
    
    def create_user_sync(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user - sync version"""
        try:
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            response = self.client.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def get_workflow_by_id_sync(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID - sync version"""
        try:
            response = self.client.table('workflows')\
                .select('*, amc_instances(*)')\
                .eq('workflow_id', workflow_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching workflow: {e}")
            return None
    
    def create_workflow_sync(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new workflow - sync version"""
        try:
            if 'id' not in workflow_data:
                workflow_data['id'] = str(uuid.uuid4())
            if 'workflow_id' not in workflow_data:
                workflow_data['workflow_id'] = f"wf_{uuid.uuid4().hex[:8]}"
            
            response = self.client.table('workflows').insert(workflow_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None
    
    def update_workflow_sync(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update workflow - sync version"""
        try:
            response = self.client.table('workflows').update(updates).eq('workflow_id', workflow_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return None
    
    def create_execution_sync(self, execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create workflow execution record - sync version"""
        try:
            if 'id' not in execution_data:
                execution_data['id'] = str(uuid.uuid4())
            if 'execution_id' not in execution_data:
                execution_data['execution_id'] = f"exec_{uuid.uuid4().hex[:8]}"
            
            response = self.client.table('workflow_executions').insert(execution_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating execution: {e}")
            return None
    
    def get_workflow_executions_sync(self, workflow_id: str, limit: int = 50, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get executions for a workflow - sync version, optionally filtered by instance"""
        try:
            query = self.client.table('workflow_executions').select('*').eq(
                'workflow_id', workflow_id
            )
            
            if instance_id:
                query = query.eq('instance_id', instance_id)
                
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching executions: {e}")
            return []
    
    def get_query_templates_sync(self, user_id: Optional[str] = None, is_public: bool = True) -> List[Dict[str, Any]]:
        """Get query templates - sync version"""
        try:
            query = self.client.table('query_templates').select('*')
            
            if user_id:
                # Get user's templates or public ones
                query = query.or_(f'user_id.eq.{user_id},is_public.eq.true')
            elif is_public:
                query = query.eq('is_public', True)
            
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching query templates: {e}")
            return []
    
    def get_template_by_id_sync(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get query template by ID - sync version"""
        try:
            response = self.client.table('query_templates').select('*').eq('template_id', template_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching template: {e}")
            return None
    
    @with_connection_retry
    def get_instance_brands_sync(self, user_id: str) -> Dict[str, List[str]]:
        """Get brands associated with each instance based on campaigns"""
        try:
            # Get all campaigns for the user
            campaigns = self.get_user_campaigns_sync(user_id)
            
            # Group brands by profile_id (which maps to instances)
            brands_by_profile = {}
            for campaign in campaigns:
                profile_id = campaign.get('profile_id')
                brand_tag = campaign.get('brand_tag')
                if profile_id and brand_tag:
                    if profile_id not in brands_by_profile:
                        brands_by_profile[profile_id] = set()
                    brands_by_profile[profile_id].add(brand_tag)
            
            # Convert sets to lists
            return {k: list(v) for k, v in brands_by_profile.items()}
        except Exception as e:
            logger.error(f"Error fetching instance brands: {e}")
            return {}
    
    @with_connection_retry
    def get_instance_stats_sync(self, instance_id: str) -> Dict[str, int]:
        """Get statistics for an instance"""
        try:
            stats = {
                "totalCampaigns": 0,
                "totalWorkflows": 0,
                "activeWorkflows": 0
            }
            
            # Get instance internal ID
            try:
                instance_response = self.client.table('amc_instances').select('id').eq('instance_id', instance_id).execute()
                if not instance_response.data:
                    return stats
                
                internal_id = instance_response.data[0]['id']
            except Exception as e:
                logger.warning(f"Could not get instance ID for stats: {e}")
                return stats
            
            # Count workflows - with error handling for each query
            try:
                workflows_response = self.client.table('workflows').select('count', count='exact').eq('instance_id', internal_id).execute()
                stats["totalWorkflows"] = workflows_response.count or 0
            except Exception as e:
                logger.warning(f"Could not count workflows: {e}")
            
            # Count active workflows
            try:
                active_response = self.client.table('workflows').select('count', count='exact').eq('instance_id', internal_id).eq('status', 'active').execute()
                stats["activeWorkflows"] = active_response.count or 0
            except Exception as e:
                logger.warning(f"Could not count active workflows: {e}")
            
            return stats
        except Exception as e:
            logger.error(f"Error fetching instance stats: {e}")
            return {"totalCampaigns": 0, "totalWorkflows": 0, "activeWorkflows": 0}
    
    def get_instance_details_sync(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an instance"""
        try:
            response = self.client.table('amc_instances')\
                .select('*, amc_accounts(*)')\
                .eq('instance_id', instance_id)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching instance details: {e}")
            return None
    
    @with_connection_retry
    def get_instance_brands_direct_sync(self, instance_id: str) -> List[str]:
        """Get brands directly associated with an instance"""
        try:
            # First get the internal instance ID
            instance_response = self.client.table('amc_instances').select('id').eq('instance_id', instance_id).execute()
            if not instance_response.data:
                return []
            
            internal_id = instance_response.data[0]['id']
            
            # Get brands from instance_brands table
            response = self.client.table('instance_brands')\
                .select('brand_tag')\
                .eq('instance_id', internal_id)\
                .execute()
            
            return [item['brand_tag'] for item in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error fetching instance brands: {e}")
            return []
    
    @with_connection_retry
    def update_instance_brands_sync(self, instance_id: str, brand_tags: List[str], user_id: str) -> bool:
        """Update brands associated with an instance"""
        try:
            # Get internal instance ID
            instance_response = self.client.table('amc_instances').select('id').eq('instance_id', instance_id).execute()
            if not instance_response.data:
                logger.error(f"Instance not found: {instance_id}")
                return False
            
            internal_id = instance_response.data[0]['id']
            
            # Delete existing brands
            delete_response = self.client.table('instance_brands')\
                .delete()\
                .eq('instance_id', internal_id)\
                .execute()
            
            # Insert new brands
            if brand_tags:
                new_brands = [
                    {
                        'instance_id': internal_id,
                        'brand_tag': brand_tag,
                        'user_id': user_id
                    }
                    for brand_tag in brand_tags
                ]
                
                insert_response = self.client.table('instance_brands')\
                    .insert(new_brands)\
                    .execute()
                
                return bool(insert_response.data)
            
            return True  # Success even if no brands to insert
            
        except Exception as e:
            logger.error(f"Error updating instance brands: {e}")
            return False
    
    @with_connection_retry
    def get_available_brands_sync(self, user_id: str) -> List[Dict[str, str]]:
        """Get all available brands for a user"""
        try:
            # Call the database function
            response = self.client.rpc('get_available_brands', {'p_user_id': user_id}).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching available brands: {e}")
            return []
    
    @with_connection_retry
    def get_user_instances_with_data_sync(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all AMC instances with stats and brands in a single optimized query"""
        try:
            # First get user's accounts
            accounts_response = self.client.table('amc_accounts').select('id').eq('user_id', user_id).execute()
            if not accounts_response.data:
                return []
            
            account_ids = [acc['id'] for acc in accounts_response.data]
            
            # Get instances with account data
            instances_response = self.client.table('amc_instances')\
                .select('''
                    *,
                    amc_accounts!inner(*),
                    instance_brands(brand_tag),
                    workflows(id, status)
                ''')\
                .in_('account_id', account_ids)\
                .eq('status', 'active')\
                .execute()
            
            if not instances_response.data:
                return []
            
            # Process the data to calculate stats
            result = []
            for inst in instances_response.data:
                # Calculate stats from the included workflows data
                workflows = inst.get('workflows', [])
                stats = {
                    "totalCampaigns": 0,  # Will be populated if needed
                    "totalWorkflows": len(workflows),
                    "activeWorkflows": len([w for w in workflows if w.get('status') == 'active'])
                }
                
                # Extract brands
                brands = [b['brand_tag'] for b in inst.get('instance_brands', [])]
                
                # Clean up the instance data
                inst_copy = inst.copy()
                inst_copy.pop('workflows', None)
                inst_copy.pop('instance_brands', None)
                inst_copy['stats'] = stats
                inst_copy['brands'] = brands[:5]  # Limit to 5 for display
                
                result.append(inst_copy)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching user instances with data: {e}")
            return []
    
    @with_connection_retry
    def get_instance_campaigns_filtered_sync(self, instance_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get campaigns filtered by instance brands"""
        try:
            # Get internal instance ID
            instance_response = self.client.table('amc_instances').select('id').eq('instance_id', instance_id).execute()
            if not instance_response.data:
                return []
            
            internal_id = instance_response.data[0]['id']
            
            # Call the database function
            response = self.client.rpc('get_instance_campaigns', {
                'p_instance_id': internal_id,
                'p_user_id': user_id
            }).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching filtered campaigns: {e}")
            return []
    
    # User operations
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            response = self.client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            if 'id' not in user_data:
                user_data['id'] = str(uuid.uuid4())
            response = self.client.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        try:
            response = self.client.table('users').update(updates).eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None
    
    # AMC Instance operations
    async def get_user_instances(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all AMC instances accessible to a user"""
        try:
            # First get user's accounts
            accounts_response = self.client.table('amc_accounts').select('id').eq('user_id', user_id).execute()
            if not accounts_response.data:
                return []
            
            account_ids = [acc['id'] for acc in accounts_response.data]
            
            # Then get instances for those accounts
            response = self.client.table('amc_instances').select(
                '*, amc_accounts(*)'
            ).in_('account_id', account_ids).execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching user instances: {e}")
            return []
    
    async def get_instance_by_id(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get AMC instance by ID"""
        try:
            response = self.client.table('amc_instances').select(
                '*, amc_accounts(*)'
            ).eq('instance_id', instance_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching instance: {e}")
            return None
    
    # Workflow operations
    async def get_user_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a user"""
        try:
            response = self.client.table('workflows').select(
                '*, amc_instances(instance_id, instance_name)'
            ).eq('user_id', user_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching workflows: {e}")
            return []
    
    async def get_workflow_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        try:
            response = self.client.table('workflows').select(
                '*, amc_instances(*)'
            ).eq('workflow_id', workflow_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching workflow: {e}")
            return None
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new workflow"""
        try:
            if 'id' not in workflow_data:
                workflow_data['id'] = str(uuid.uuid4())
            if 'workflow_id' not in workflow_data:
                workflow_data['workflow_id'] = f"wf_{uuid.uuid4().hex[:8]}"
            
            response = self.client.table('workflows').insert(workflow_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return None
    
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update workflow"""
        try:
            response = self.client.table('workflows').update(updates).eq('workflow_id', workflow_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return None
    
    # Execution operations
    async def create_execution(self, execution_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create workflow execution record"""
        try:
            if 'id' not in execution_data:
                execution_data['id'] = str(uuid.uuid4())
            if 'execution_id' not in execution_data:
                execution_data['execution_id'] = f"exec_{uuid.uuid4().hex[:8]}"
            
            response = self.client.table('workflow_executions').insert(execution_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating execution: {e}")
            return None
    
    async def update_execution(self, execution_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update execution status"""
        try:
            response = self.client.table('workflow_executions').update(updates).eq('execution_id', execution_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating execution: {e}")
            return None
    
    async def get_workflow_executions(self, workflow_id: str, limit: int = 50, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get executions for a workflow, optionally filtered by instance"""
        try:
            query = self.client.table('workflow_executions').select('*').eq(
                'workflow_id', workflow_id
            )
            
            if instance_id:
                query = query.eq('instance_id', instance_id)
                
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching executions: {e}")
            return []
    
    # Campaign operations
    async def get_user_campaigns(self, user_id: str, brand_tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get campaigns for a user, optionally filtered by brand"""
        try:
            query = self.client.table('campaign_mappings').select('*').eq('user_id', user_id)
            
            if brand_tag:
                query = query.eq('brand_tag', brand_tag)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching campaigns: {e}")
            return []
    
    async def create_campaign_mapping(self, campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update campaign mapping"""
        try:
            if 'id' not in campaign_data:
                campaign_data['id'] = str(uuid.uuid4())
            
            response = self.client.table('campaign_mappings').upsert(
                campaign_data,
                on_conflict='campaign_id,marketplace_id'
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating campaign mapping: {e}")
            return None
    
    # Query template operations
    async def get_query_templates(self, user_id: Optional[str] = None, is_public: bool = True) -> List[Dict[str, Any]]:
        """Get query templates"""
        try:
            query = self.client.table('query_templates').select('*')
            
            if user_id:
                # Get user's templates or public ones
                query = query.or_(f'user_id.eq.{user_id},is_public.eq.true')
            elif is_public:
                query = query.eq('is_public', True)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching query templates: {e}")
            return []
    
    async def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get query template by ID"""
        try:
            response = self.client.table('query_templates').select('*').eq('template_id', template_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching template: {e}")
            return None

# Global instance
db_service = DatabaseService()