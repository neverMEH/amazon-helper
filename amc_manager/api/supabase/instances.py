"""AMC Instances API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List

from ...services.db_service import db_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_instances(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all AMC instances accessible to the current user"""
    try:
        instances = await db_service.get_user_instances(current_user['id'])
        
        # Format response with camelCase for frontend
        return [{
            "id": inst['id'],
            "instanceId": inst['instance_id'],
            "instanceName": inst['instance_name'],
            "type": inst.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": inst['region'],
            "status": inst['status'],
            "isActive": inst['status'] == 'active',
            "accountId": inst['amc_accounts']['account_id'] if 'amc_accounts' in inst else None,
            "accountName": inst['amc_accounts']['account_name'] if 'amc_accounts' in inst else None,
            "endpointUrl": inst.get('endpoint_url'),
            "dataUploadAccountId": inst.get('data_upload_account_id'),
            "createdAt": inst.get('created_at', '')
        } for inst in instances]
    except Exception as e:
        logger.error(f"Error listing instances: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instances")


@router.get("/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get details for a specific AMC instance"""
    try:
        instance = await db_service.get_instance_by_id(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Verify user has access
        user_instances = await db_service.get_user_instances(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "instance_id": instance['instance_id'],
            "instance_name": instance['instance_name'],
            "instance_type": instance.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": instance['region'],
            "status": instance['status'],
            "account": {
                "id": instance['amc_accounts']['account_id'],
                "name": instance['amc_accounts']['account_name']
            } if 'amc_accounts' in instance else None,
            "endpoint_url": instance.get('endpoint_url'),
            "data_upload_account_id": instance.get('data_upload_account_id'),
            "capabilities": instance.get('capabilities', {}),
            "created_at": instance.get('created_at'),
            "updated_at": instance.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance")


@router.get("/{instance_id}/metrics")
async def get_instance_metrics(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get metrics for an AMC instance"""
    # Verify access
    instance = await db_service.get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    user_instances = await db_service.get_user_instances(current_user['id'])
    if not any(inst['instance_id'] == instance_id for inst in user_instances):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual metrics fetching from AMC API
    # For now, return mock data
    return {
        "instance_id": instance_id,
        "metrics": {
            "total_workflows": 0,
            "active_workflows": 0,
            "executions_today": 0,
            "executions_this_week": 0,
            "storage_used_gb": 0,
            "last_execution": None
        }
    }