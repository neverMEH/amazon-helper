"""AMC Executions API endpoints for fetching workflow executions directly from AMC

Note: The AMC API /workflows endpoint returns workflow executions (historical runs),
not workflow definitions. Each execution represents a past run of a workflow."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import logging

from ...services.amc_execution_service import amc_execution_service
from ...services.db_service import db_service
from ...services.token_service import token_service
from ...core.supabase_client import SupabaseManager
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{instance_id}")
async def list_amc_executions(
    instance_id: str,
    limit: int = 50,
    next_token: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all AMC workflow executions for an instance directly from AMC API
    
    Args:
        instance_id: The AMC instance ID
        limit: Maximum number of executions to return
        current_user: The authenticated user
        
    Returns:
        List of AMC executions with their current status
    """
    try:
        # Get instance details
        instance = db_service.get_instance_details_sync(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Check if user has access to this instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to this instance")
        
        # Get valid token
        valid_token = await token_service.get_valid_token(current_user['id'])
        
        if not valid_token:
            raise HTTPException(status_code=401, detail="No valid authentication token")
        
        # Get AMC account details
        account = instance.get('amc_accounts')
        if not account:
            raise HTTPException(status_code=404, detail="AMC account not found")
        
        entity_id = account['account_id']
        marketplace_id = account['marketplace_id']
        
        # Use AMC API client to list executions
        from ...services.amc_api_client import AMCAPIClient
        api_client = AMCAPIClient()
        
        response = api_client.list_executions(
            instance_id=instance_id,
            access_token=valid_token,
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            limit=limit,
            next_token=next_token
        )
        
        if not response.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch AMC executions: {response.get('error')}"
            )
        
        executions = response.get('executions', [])
        
        # Log the first execution to see its structure
        if executions:
            logger.info(f"Sample execution data: {executions[0]}")
        
        # For now, return the AMC executions directly
        # The AMC API returns workflow executions (past runs), not workflow definitions
        enhanced_executions = []
        for amc_exec in executions:
            # Ensure we have essential fields for frontend display
            enhanced_exec = {
                **amc_exec,
                'instanceId': instance_id,
                # Ensure workflowExecutionId exists (some APIs might use different field names)
                'workflowExecutionId': amc_exec.get('workflowExecutionId') or amc_exec.get('executionId') or amc_exec.get('id'),
                # Default workflowName for ad-hoc queries
                'workflowName': amc_exec.get('workflowName') or 'Ad-hoc Query'
            }
            enhanced_executions.append(enhanced_exec)
        
        return {
            "success": True,
            "executions": enhanced_executions,
            "total": len(enhanced_executions),
            "nextToken": response.get('nextToken')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing AMC executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{instance_id}/{execution_id}")
async def get_amc_execution_details(
    instance_id: str,
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get details for a specific AMC execution
    
    Args:
        instance_id: The AMC instance ID
        execution_id: The AMC execution ID
        current_user: The authenticated user
        
    Returns:
        Execution details including status and results
    """
    try:
        # Get instance details
        instance = db_service.get_instance_details_sync(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Check if user has access to this instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to this instance")
        
        # Get valid token
        valid_token = await token_service.get_valid_token(current_user['id'])
        
        if not valid_token:
            raise HTTPException(status_code=401, detail="No valid authentication token")
        
        # Get AMC account details
        account = instance.get('amc_accounts')
        if not account:
            raise HTTPException(status_code=404, detail="AMC account not found")
        
        entity_id = account['account_id']
        marketplace_id = account['marketplace_id']
        
        # Use AMC API client to get execution status
        from ...services.amc_api_client import AMCAPIClient
        api_client = AMCAPIClient()
        
        status_response = api_client.get_execution_status(
            execution_id=execution_id,
            access_token=valid_token,
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            instance_id=instance_id
        )
        
        if not status_response.get('success'):
            raise HTTPException(
                status_code=404,
                detail=f"Execution not found: {status_response.get('error')}"
            )
        
        # If execution is completed, try to get download URLs
        result_data = None
        if status_response.get('status') == 'completed':
            download_response = api_client.get_download_urls(
                execution_id=execution_id,
                access_token=valid_token,
                entity_id=entity_id,
                marketplace_id=marketplace_id,
                instance_id=instance_id
            )
            
            if download_response.get('success'):
                urls = download_response.get('downloadUrls', [])
                if urls:
                    # Download and parse the first CSV file
                    csv_response = api_client.download_and_parse_csv(urls[0])
                    if csv_response.get('success'):
                        result_data = csv_response.get('data')
        
        return {
            "success": True,
            "execution": {
                **status_response,
                "resultData": result_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AMC execution details: {e}")
        raise HTTPException(status_code=500, detail=str(e))