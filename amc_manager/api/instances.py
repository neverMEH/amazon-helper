"""AMC Instances API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..core import AMCAPIClient, get_logger
from ..models import get_db, User
from ..services import AMCInstanceService
from .dependencies import get_current_user, get_api_client


logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_instances(
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    status: Optional[str] = Query(None, description="Filter by instance status"),
    region: Optional[str] = Query(None, description="Filter by AWS region")
) -> List[Dict[str, Any]]:
    """
    List all AMC instances accessible to the user
    """
    try:
        service = AMCInstanceService(api_client)
        
        filters = {}
        if status:
            filters['status'] = status
        if region:
            filters['region'] = region
            
        instances = await service.list_instances(
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            filters=filters
        )
        
        return instances
        
    except Exception as e:
        logger.error(f"Failed to list instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific AMC instance
    """
    try:
        service = AMCInstanceService(api_client)
        
        instance = await service.get_instance(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return instance
        
    except Exception as e:
        logger.error(f"Failed to get instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/advertisers")
async def get_instance_advertisers(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> List[Dict[str, Any]]:
    """
    Get advertisers associated with an AMC instance
    """
    try:
        service = AMCInstanceService(api_client)
        
        advertisers = await service.get_instance_advertisers(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return advertisers
        
    except Exception as e:
        logger.error(f"Failed to get advertisers for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/metrics")
async def get_instance_metrics(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get usage metrics and statistics for an AMC instance
    """
    try:
        service = AMCInstanceService(api_client)
        
        metrics = await service.get_instance_metrics(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get metrics for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/validate-access")
async def validate_instance_access(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, bool]:
    """
    Validate user has access to the specified AMC instance
    """
    try:
        service = AMCInstanceService(api_client)
        
        has_access = await service.validate_instance_access(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return {"has_access": has_access}
        
    except Exception as e:
        logger.error(f"Failed to validate access for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))