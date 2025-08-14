"""
Enhanced AMC API Client with automatic token refresh on authentication failures
"""
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
import asyncio

from .amc_api_client import AMCAPIClient
from .token_service import token_service
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class AMCAPIClientWithRetry:
    """
    Wrapper around AMCAPIClient that automatically refreshes tokens and retries on 401 errors
    """
    
    def __init__(self):
        self.api_client = AMCAPIClient()
        self.max_retries = 2  # Maximum number of retry attempts for token refresh
    
    async def _execute_with_retry(
        self,
        api_method: Callable,
        user_id: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an API method with automatic token refresh on 401 errors
        
        Args:
            api_method: The API method to call
            user_id: User ID for token refresh
            *args: Positional arguments for the API method
            **kwargs: Keyword arguments for the API method
            
        Returns:
            API response
        """
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                # Get fresh token
                if retry_count > 0:
                    logger.info(f"Retry attempt {retry_count}: Refreshing token for user {user_id}")
                    # Force token refresh by clearing the cached token
                    await token_service.refresh_access_token(
                        token_service.decrypt_token(
                            (await token_service.get_user_by_id(user_id))['auth_tokens']['refresh_token']
                        )
                    )
                
                # Get valid token (will refresh if needed)
                valid_token = await token_service.get_valid_token(user_id)
                if not valid_token:
                    logger.error(f"No valid token available for user {user_id}")
                    return {
                        "success": False,
                        "error": "No valid Amazon OAuth token. Please re-authenticate with Amazon."
                    }
                
                # Update the access_token in kwargs
                kwargs['access_token'] = valid_token
                
                # Execute the API method
                response = api_method(*args, **kwargs)
                
                # Check for authentication errors in response
                if isinstance(response, dict):
                    # Check for 401 or authentication errors
                    if response.get('status_code') == 401 or \
                       'unauthorized' in str(response.get('error', '')).lower() or \
                       'authentication' in str(response.get('error', '')).lower():
                        logger.warning(f"Authentication error detected: {response.get('error')}")
                        retry_count += 1
                        last_error = response.get('error')
                        continue
                    
                    # Success or non-auth error
                    return response
                
                # If response is not a dict, return as-is
                return response
                
            except Exception as e:
                logger.error(f"Error executing API method: {e}")
                last_error = str(e)
                retry_count += 1
        
        # Max retries exceeded
        logger.error(f"Max retries ({self.max_retries}) exceeded. Last error: {last_error}")
        return {
            "success": False,
            "error": f"Authentication failed after {self.max_retries} attempts. Last error: {last_error}"
        }
    
    async def create_workflow_execution(
        self,
        instance_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        sql_query: Optional[str] = None,
        workflow_id: Optional[str] = None,
        parameter_values: Optional[Dict[str, Any]] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Create a workflow execution with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.create_workflow_execution,
            user_id,
            instance_id=instance_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            sql_query=sql_query,
            workflow_id=workflow_id,
            parameter_values=parameter_values,
            output_format=output_format
        )
    
    async def get_execution_status(
        self,
        execution_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get execution status with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.get_execution_status,
            user_id,
            execution_id=execution_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            instance_id=instance_id
        )
    
    async def get_execution_results(
        self,
        execution_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get execution results with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.get_execution_results,
            user_id,
            execution_id=execution_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            instance_id=instance_id
        )
    
    async def list_executions(
        self,
        instance_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        limit: int = 50,
        next_token: Optional[str] = None,
        workflow_id: Optional[str] = None,
        min_creation_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List executions with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.list_executions,
            user_id,
            instance_id=instance_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            limit=limit,
            next_token=next_token,
            workflow_id=workflow_id,
            min_creation_time=min_creation_time
        )
    
    async def create_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        distinct_user_count_column: Optional[str] = None,
        filtered_metrics_discriminator_column: Optional[str] = None,
        filtered_reason_column: Optional[str] = None,
        input_parameters: Optional[list] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Create a workflow with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.create_workflow,
            user_id,
            instance_id=instance_id,
            workflow_id=workflow_id,
            sql_query=sql_query,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            distinct_user_count_column=distinct_user_count_column,
            filtered_metrics_discriminator_column=filtered_metrics_discriminator_column,
            filtered_reason_column=filtered_reason_column,
            input_parameters=input_parameters,
            output_format=output_format
        )
    
    async def update_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        sql_query: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        distinct_user_count_column: Optional[str] = None,
        filtered_metrics_discriminator_column: Optional[str] = None,
        filtered_reason_column: Optional[str] = None,
        input_parameters: Optional[list] = None,
        output_format: str = "CSV"
    ) -> Dict[str, Any]:
        """
        Update a workflow with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.update_workflow,
            user_id,
            instance_id=instance_id,
            workflow_id=workflow_id,
            sql_query=sql_query,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            distinct_user_count_column=distinct_user_count_column,
            filtered_metrics_discriminator_column=filtered_metrics_discriminator_column,
            filtered_reason_column=filtered_reason_column,
            input_parameters=input_parameters,
            output_format=output_format
        )
    
    async def delete_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Delete a workflow with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.delete_workflow,
            user_id,
            instance_id=instance_id,
            workflow_id=workflow_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id
        )
    
    async def get_workflow(
        self,
        instance_id: str,
        workflow_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER"
    ) -> Dict[str, Any]:
        """
        Get workflow details with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.get_workflow,
            user_id,
            instance_id=instance_id,
            workflow_id=workflow_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id
        )
    
    async def list_workflows(
        self,
        instance_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        limit: int = 50,
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workflows with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.list_workflows,
            user_id,
            instance_id=instance_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            limit=limit,
            next_token=next_token
        )
    
    async def get_download_urls(
        self,
        execution_id: str,
        user_id: str,
        entity_id: str,
        marketplace_id: str = "ATVPDKIKX0DER",
        instance_id: str = None
    ) -> Dict[str, Any]:
        """
        Get download URLs with automatic token refresh
        """
        return await self._execute_with_retry(
            self.api_client.get_download_urls,
            user_id,
            execution_id=execution_id,
            access_token=None,  # Will be set by _execute_with_retry
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            instance_id=instance_id
        )


# Singleton instance
amc_api_client_with_retry = AMCAPIClientWithRetry()