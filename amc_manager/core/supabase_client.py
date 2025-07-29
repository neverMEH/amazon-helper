"""Supabase client manager for Amazon AMC Manager"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from ..config import settings
from .logger import get_logger

logger = get_logger(__name__)


class SupabaseManager:
    """Singleton manager for Supabase client connections"""
    
    _instance: Optional[Client] = None
    _service_client: Optional[Client] = None
    
    @classmethod
    def get_client(cls, use_service_role: bool = True) -> Client:
        """
        Get Supabase client instance
        
        Args:
            use_service_role: Whether to use service role key (for server-side operations)
                            or anon key (for client-side operations)
        
        Returns:
            Supabase client instance
        """
        if use_service_role:
            if cls._service_client is None:
                cls._service_client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key
                )
                logger.info("Created Supabase service role client")
            return cls._service_client
        else:
            if cls._instance is None:
                cls._instance = create_client(
                    settings.supabase_url,
                    settings.supabase_anon_key
                )
                logger.info("Created Supabase anon client")
            return cls._instance
    
    @classmethod
    def reset_clients(cls):
        """Reset client instances (useful for testing)"""
        cls._instance = None
        cls._service_client = None


class SupabaseService:
    """Base service class for Supabase operations"""
    
    def __init__(self, use_service_role: bool = True):
        """
        Initialize service with Supabase client
        
        Args:
            use_service_role: Whether to use service role for elevated permissions
        """
        self.client = SupabaseManager.get_client(use_service_role)
        self.logger = get_logger(self.__class__.__name__)
    
    async def execute_rpc(self, function_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a Supabase RPC function
        
        Args:
            function_name: Name of the database function
            params: Parameters to pass to the function
            
        Returns:
            Function result
        """
        try:
            response = self.client.rpc(function_name, params).execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error executing RPC {function_name}: {str(e)}")
            raise
    
    def handle_response(self, response) -> Any:
        """
        Handle Supabase response and check for errors
        
        Args:
            response: Supabase response object
            
        Returns:
            Response data
            
        Raises:
            Exception: If response contains an error
        """
        if hasattr(response, 'error') and response.error:
            self.logger.error(f"Supabase error: {response.error}")
            raise Exception(f"Supabase error: {response.error}")
        return response.data


class CampaignMappingService(SupabaseService):
    """Service for managing campaign mappings"""
    
    async def get_campaigns_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all campaigns for a user"""
        response = self.client.table('campaign_mappings')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        return self.handle_response(response)
    
    async def get_campaigns_by_brand(self, user_id: str, brand_tag: str) -> List[Dict[str, Any]]:
        """Get campaigns for a specific brand"""
        response = self.client.table('campaign_mappings')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('brand_tag', brand_tag)\
            .execute()
        return self.handle_response(response)
    
    async def get_campaigns_by_asins(self, user_id: str, asins: List[str]) -> List[Dict[str, Any]]:
        """Get campaigns that contain specific ASINs"""
        result = await self.execute_rpc('get_campaigns_by_asins', {
            'user_id_param': user_id,
            'asin_list': asins
        })
        return result
    
    async def create_campaign_mapping(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign mapping"""
        response = self.client.table('campaign_mappings')\
            .insert(campaign_data)\
            .execute()
        return self.handle_response(response)
    
    async def update_campaign_mapping(self, campaign_id: str, marketplace_id: str, 
                                    updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing campaign mapping"""
        response = self.client.table('campaign_mappings')\
            .update(updates)\
            .eq('campaign_id', campaign_id)\
            .eq('marketplace_id', marketplace_id)\
            .execute()
        return self.handle_response(response)
    
    async def search_campaigns(self, user_id: str, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search campaigns across multiple fields"""
        result = await self.execute_rpc('search_campaigns', {
            'search_term': search_term,
            'user_id_param': user_id,
            'limit_param': limit
        })
        return result


class BrandConfigurationService(SupabaseService):
    """Service for managing brand configurations"""
    
    async def get_user_brands(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all brands accessible to a user (owned or shared)"""
        response = self.client.table('brand_configurations')\
            .select('*')\
            .or_(f'owner_user_id.eq.{user_id},shared_with_users.cs.{{{user_id}}}')\
            .execute()
        return self.handle_response(response)
    
    async def create_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand configuration"""
        response = self.client.table('brand_configurations')\
            .insert(brand_data)\
            .execute()
        return self.handle_response(response)
    
    async def update_brand_asins(self, brand_tag: str, primary_asins: List[str], 
                               all_asins: List[str]) -> Dict[str, Any]:
        """Update ASINs for a brand"""
        response = self.client.table('brand_configurations')\
            .update({
                'primary_asins': primary_asins,
                'all_asins': all_asins
            })\
            .eq('brand_tag', brand_tag)\
            .execute()
        return self.handle_response(response)
    
    async def auto_tag_campaign(self, campaign_name: str, user_id: str) -> Optional[str]:
        """Auto-tag a campaign based on brand patterns"""
        result = await self.execute_rpc('auto_tag_campaign', {
            'campaign_name_param': campaign_name,
            'user_id_param': user_id
        })
        return result[0] if result else None


class WorkflowService(SupabaseService):
    """Service for managing workflows and executions"""
    
    async def get_user_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a user"""
        response = self.client.table('workflows')\
            .select('*, amc_instances(*)')\
            .eq('user_id', user_id)\
            .execute()
        return self.handle_response(response)
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow"""
        response = self.client.table('workflows')\
            .insert(workflow_data)\
            .execute()
        return self.handle_response(response)
    
    async def create_execution(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow execution"""
        response = self.client.table('workflow_executions')\
            .insert(execution_data)\
            .execute()
        return self.handle_response(response)
    
    async def update_execution_status(self, execution_id: str, status: str, 
                                    **kwargs) -> Dict[str, Any]:
        """Update execution status and related fields"""
        update_data = {'status': status, **kwargs}
        response = self.client.table('workflow_executions')\
            .update(update_data)\
            .eq('execution_id', execution_id)\
            .execute()
        return self.handle_response(response)
    
    async def get_execution_stats(self, workflow_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get execution statistics for a workflow"""
        result = await self.execute_rpc('get_workflow_execution_stats', {
            'workflow_id_param': workflow_id,
            'days_back': days_back
        })
        return result[0] if result else {}
    
    def subscribe_to_executions(self, workflow_id: str, callback):
        """Subscribe to real-time execution updates"""
        self.client.table('workflow_executions')\
            .on('UPDATE', callback)\
            .eq('workflow_id', workflow_id)\
            .subscribe()


class AMCInstanceService(SupabaseService):
    """Service for managing AMC instances"""
    
    async def get_user_instances(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all AMC instances accessible to a user"""
        response = self.client.table('amc_instances')\
            .select('*, amc_accounts(*)')\
            .eq('amc_accounts.user_id', user_id)\
            .execute()
        return self.handle_response(response)
    
    async def validate_instance_access(self, instance_id: str, user_id: str) -> bool:
        """Validate if user has access to an AMC instance"""
        result = await self.execute_rpc('validate_instance_access', {
            'instance_id_param': instance_id,
            'user_id_param': user_id
        })
        return result[0] if result else False
    
    async def create_instance(self, instance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AMC instance"""
        response = self.client.table('amc_instances')\
            .insert(instance_data)\
            .execute()
        return self.handle_response(response)
    
    async def update_instance_status(self, instance_id: str, status: str) -> Dict[str, Any]:
        """Update AMC instance status"""
        response = self.client.table('amc_instances')\
            .update({'status': status})\
            .eq('instance_id', instance_id)\
            .execute()
        return self.handle_response(response)