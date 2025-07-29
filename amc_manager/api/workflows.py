"""Workflows API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core import AMCAPIClient, get_logger
from ..models import get_db, User, Workflow
from ..services import WorkflowService
from .dependencies import get_current_user, get_api_client


logger = get_logger(__name__)
router = APIRouter()


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instance_id: str
    sql_query: str
    parameters: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sql_query: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class WorkflowExecute(BaseModel):
    parameters: Optional[Dict[str, Any]] = {}


class ScheduleCreate(BaseModel):
    cron_expression: str
    timezone: str = "UTC"
    default_parameters: Optional[Dict[str, Any]] = {}


@router.post("/")
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new AMC workflow
    """
    try:
        service = WorkflowService(api_client)
        
        # Create via API
        api_workflow = await service.create_workflow(
            instance_id=workflow_data.instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            workflow_data=workflow_data.dict()
        )
        
        # Store in database
        db_workflow = Workflow(
            workflow_id=api_workflow['workflowId'],
            name=workflow_data.name,
            description=workflow_data.description,
            instance_id=workflow_data.instance_id,
            sql_query=workflow_data.sql_query,
            parameters=workflow_data.parameters,
            user_id=current_user.id,
            tags=workflow_data.tags
        )
        db.add(db_workflow)
        db.commit()
        
        return api_workflow
        
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}")
async def list_workflows(
    instance_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Number of items to return")
) -> List[Dict[str, Any]]:
    """
    List workflows in an AMC instance
    """
    try:
        service = WorkflowService(api_client)
        
        filters = {}
        if status:
            filters['status'] = status
        filters['offset'] = skip
        filters['limit'] = limit
        
        workflows = await service.list_workflows(
            instance_id=instance_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            filters=filters
        )
        
        return workflows
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/{workflow_id}")
async def get_workflow(
    instance_id: str,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, Any]:
    """
    Get detailed workflow information
    """
    try:
        service = WorkflowService(api_client)
        
        workflow = await service.get_workflow(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return workflow
        
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{instance_id}/{workflow_id}")
async def update_workflow(
    instance_id: str,
    workflow_id: str,
    updates: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update an existing workflow
    """
    try:
        service = WorkflowService(api_client)
        
        # Update via API
        updated_workflow = await service.update_workflow(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            updates=updates.dict(exclude_unset=True)
        )
        
        # Update in database
        db_workflow = db.query(Workflow).filter_by(
            workflow_id=workflow_id,
            user_id=current_user.id
        ).first()
        
        if db_workflow:
            db_workflow.update(**updates.dict(exclude_unset=True))
            db.commit()
        
        return updated_workflow
        
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{instance_id}/{workflow_id}")
async def delete_workflow(
    instance_id: str,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    Delete a workflow
    """
    try:
        service = WorkflowService(api_client)
        
        # Delete via API
        success = await service.delete_workflow(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        # Delete from database
        if success:
            db_workflow = db.query(Workflow).filter_by(
                workflow_id=workflow_id,
                user_id=current_user.id
            ).first()
            
            if db_workflow:
                db.delete(db_workflow)
                db.commit()
        
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/{workflow_id}/execute")
async def execute_workflow(
    instance_id: str,
    workflow_id: str,
    execution_params: WorkflowExecute,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, Any]:
    """
    Execute a workflow
    """
    try:
        service = WorkflowService(api_client)
        
        execution = await service.execute_workflow(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            parameters=execution_params.parameters
        )
        
        return execution
        
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/{workflow_id}/schedules")
async def create_schedule(
    instance_id: str,
    workflow_id: str,
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> Dict[str, Any]:
    """
    Create a schedule for workflow execution
    """
    try:
        service = WorkflowService(api_client)
        
        schedule = await service.create_schedule(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            schedule_data=schedule_data.dict()
        )
        
        return schedule
        
    except Exception as e:
        logger.error(f"Failed to create schedule for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/{workflow_id}/schedules")
async def list_schedules(
    instance_id: str,
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client)
) -> List[Dict[str, Any]]:
    """
    List schedules for a workflow
    """
    try:
        service = WorkflowService(api_client)
        
        schedules = await service.list_schedules(
            instance_id=instance_id,
            workflow_id=workflow_id,
            user_id=current_user.id,
            user_token=current_user.auth_tokens
        )
        
        return schedules
        
    except Exception as e:
        logger.error(f"Failed to list schedules for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))