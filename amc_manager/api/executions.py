"""Execution tracking API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..core import AMCAPIClient, get_logger
from ..models import get_db, User
from ..services import ExecutionTrackingService
from .dependencies import get_current_user, get_api_client


logger = get_logger(__name__)
router = APIRouter()


@router.get("/{instance_id}")
async def list_executions(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    start_date: Optional[str] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO format)"),
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return")
) -> List[Dict[str, Any]]:
    """
    List executions for an AMC instance
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        filters = {
            'offset': skip,
            'limit': limit
        }
        
        if workflow_id:
            filters['workflowId'] = workflow_id
        if status:
            filters['status'] = status
        if start_date:
            filters['startDate'] = start_date
        if end_date:
            filters['endDate'] = end_date
            
        executions = await service.list_executions(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            filters=filters
        )
        
        return executions
        
    except Exception as e:
        logger.error(f"Failed to list executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/{execution_id}")
async def get_execution_status(
    instance_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, Any]:
    """
    Get current status of an execution
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        status = await service.get_execution_status(
            instance_id=instance_id,
            execution_id=execution_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/workflow/{workflow_id}/history")
async def get_workflow_execution_history(
    instance_id: str,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    limit: int = Query(50, description="Maximum number of executions to retrieve")
) -> Dict[str, Any]:
    """
    Get execution history for a specific workflow
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        history = await service.get_execution_history(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            limit=limit
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/{execution_id}/monitor")
async def monitor_execution(
    instance_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    polling_interval: int = Query(10, description="Seconds between status checks"),
    timeout: int = Query(3600, description="Maximum seconds to wait")
) -> Dict[str, Any]:
    """
    Monitor an execution until completion
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        final_status = await service.monitor_execution(
            instance_id=instance_id,
            execution_id=execution_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            polling_interval=polling_interval,
            timeout=timeout
        )
        
        return final_status
        
    except Exception as e:
        logger.error(f"Failed to monitor execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/{execution_id}/cancel")
async def cancel_execution(
    instance_id: str,
    execution_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, bool]:
    """
    Cancel a running execution
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        success = await service.cancel_execution(
            instance_id=instance_id,
            execution_id=execution_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/metrics")
async def get_execution_metrics(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get execution metrics for an instance
    """
    try:
        service = ExecutionTrackingService(api_client)
        
        metrics = await service.get_execution_metrics(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            time_range_days=days
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get execution metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))