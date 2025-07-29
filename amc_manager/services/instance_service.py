"""AMC Instance Management Service"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core import AMCAPIClient, AMCAPIEndpoints, get_logger
from ..core.exceptions import APIError, ValidationError


logger = get_logger(__name__)


class AMCInstanceService:
    """Service for managing AMC instances"""
    
    def __init__(self, api_client: AMCAPIClient):
        """
        Initialize instance service
        
        Args:
            api_client: Configured AMC API client
        """
        self.api_client = api_client
        
    async def list_instances(
        self,
        user_id: str,
        user_token: Dict[str, Any],
        entity_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all available AMC instances for the user
        
        Args:
            user_id: User identifier
            user_token: User's auth token
            entity_id: Optional entity ID to filter instances
            filters: Optional filters (status, region, etc.)
            
        Returns:
            List of AMC instances
        """
        try:
            params = {"nextToken": ""}  # Include empty nextToken as per API spec
            if filters:
                params.update(filters)
                
            headers = {}
            if entity_id:
                # Pass entity_id as header - this is the key discovery!
                headers['Amazon-Advertising-API-AdvertiserId'] = entity_id
                
            response = self.api_client.get(
                AMCAPIEndpoints.INSTANCES,
                user_id,
                user_token,
                params=params,
                headers=headers
            )
            
            instances = response.get('instances', [])
            logger.info(f"Retrieved {len(instances)} AMC instances for user {user_id}")
            
            # Enrich instance data
            for instance in instances:
                instance['last_accessed'] = instance.get('last_accessed', datetime.utcnow().isoformat())
                instance['is_active'] = instance.get('status') == 'active'
                
            return instances
            
        except APIError as e:
            logger.error(f"Failed to list instances: {e}")
            raise
            
    async def get_instance(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            Instance details
        """
        try:
            endpoint = AMCAPIEndpoints.INSTANCE_DETAIL.format(instance_id=instance_id)
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            logger.info(f"Retrieved details for instance {instance_id}")
            return response
            
        except APIError as e:
            logger.error(f"Failed to get instance {instance_id}: {e}")
            raise
            
    async def get_instance_advertisers(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get advertisers associated with an AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            List of advertisers
        """
        try:
            endpoint = AMCAPIEndpoints.ADVERTISERS.format(instance_id=instance_id)
            response = self.api_client.get(
                endpoint,
                user_id,
                user_token
            )
            
            advertisers = response.get('advertisers', [])
            logger.info(f"Retrieved {len(advertisers)} advertisers for instance {instance_id}")
            
            return advertisers
            
        except APIError as e:
            logger.error(f"Failed to get advertisers for instance {instance_id}: {e}")
            raise
            
    async def get_instance_metrics(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get usage metrics and statistics for an AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            Instance metrics and statistics
        """
        # This would typically aggregate data from multiple sources
        metrics = {
            'instance_id': instance_id,
            'total_workflows': 0,
            'active_workflows': 0,
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'last_execution': None,
            'storage_used_gb': 0,
            'compute_hours': 0
        }
        
        try:
            # Get workflow statistics
            workflows_endpoint = AMCAPIEndpoints.WORKFLOWS.format(instance_id=instance_id)
            workflows_response = self.api_client.get(
                workflows_endpoint,
                user_id,
                user_token
            )
            
            workflows = workflows_response.get('workflows', [])
            metrics['total_workflows'] = len(workflows)
            metrics['active_workflows'] = sum(1 for w in workflows if w.get('status') == 'active')
            
            # Get execution statistics
            executions_endpoint = AMCAPIEndpoints.EXECUTIONS.format(instance_id=instance_id)
            executions_response = self.api_client.get(
                executions_endpoint,
                user_id,
                user_token,
                params={'limit': 1000}  # Get recent executions
            )
            
            executions = executions_response.get('executions', [])
            metrics['total_executions'] = len(executions)
            metrics['successful_executions'] = sum(1 for e in executions if e.get('status') == 'completed')
            metrics['failed_executions'] = sum(1 for e in executions if e.get('status') == 'failed')
            
            if executions:
                metrics['last_execution'] = max(e.get('created_at', '') for e in executions)
            
            logger.info(f"Retrieved metrics for instance {instance_id}")
            return metrics
            
        except APIError as e:
            logger.error(f"Failed to get metrics for instance {instance_id}: {e}")
            # Return partial metrics on error
            return metrics
            
    async def validate_instance_access(
        self,
        instance_id: str,
        user_id: str,
        user_token: Dict[str, Any]
    ) -> bool:
        """
        Validate user has access to the specified AMC instance
        
        Args:
            instance_id: AMC instance ID
            user_id: User identifier
            user_token: User's auth token
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            await self.get_instance(instance_id, user_id, user_token)
            return True
        except APIError as e:
            if e.status_code == 403 or e.status_code == 404:
                return False
            raise


class InstanceCache:
    """Simple in-memory cache for instance data"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize cache with TTL
        
        Args:
            ttl_seconds: Cache time-to-live in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.utcnow().timestamp() - entry['timestamp'] < self.ttl_seconds:
                return entry['data']
        return None
        
    def set(self, key: str, data: Dict[str, Any]):
        """Set cache value with timestamp"""
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.utcnow().timestamp()
        }
        
    def invalidate(self, key: str):
        """Remove key from cache"""
        self._cache.pop(key, None)
        
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()