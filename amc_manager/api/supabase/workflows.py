"""Workflows API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from ...services.db_service import db_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

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
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@router.get("/")
def list_workflows(
    instance_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all workflows for the current user"""
    try:
        workflows = db_service.get_user_workflows_sync(current_user['id'])
        
        # Filter by instance if provided
        if instance_id:
            # For now, filter by instance_id directly
            # TODO: Add proper instance lookup
            workflows = [w for w in workflows if 'amc_instances' in w and w['amc_instances'].get('instance_id') == instance_id]
        
        return [{
            "id": w['workflow_id'],
            "workflowId": w['workflow_id'],
            "name": w['name'],
            "description": w.get('description'),
            "sqlQuery": w.get('sql_query', ''),
            "parameters": w.get('parameters', {}),
            "instance": {
                "id": w['amc_instances']['instance_id'],
                "name": w['amc_instances']['instance_name']
            } if 'amc_instances' in w else None,
            "status": w.get('status', 'active'),
            "isTemplate": w.get('is_template', False),
            "tags": w.get('tags', []),
            "createdAt": w.get('created_at', ''),
            "updatedAt": w.get('updated_at', ''),
            "lastExecuted": w.get('last_executed_at')
        } for w in workflows]
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workflows")


@router.post("/")
def create_workflow(
    workflow: WorkflowCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new workflow"""
    try:
        # Verify user has access to the instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == workflow.instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get the internal instance ID
        instance = next((inst for inst in user_instances if inst['instance_id'] == workflow.instance_id), None)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Create workflow
        workflow_data = {
            "name": workflow.name,
            "description": workflow.description,
            "instance_id": instance['id'],  # Use internal UUID
            "sql_query": workflow.sql_query,
            "parameters": workflow.parameters,
            "tags": workflow.tags,
            "user_id": current_user['id'],
            "status": "active"
        }
        
        # Use sync version
        created = db_service.create_workflow_sync(workflow_data)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create workflow")
        
        return {
            "workflow_id": created['workflow_id'],
            "name": created['name'],
            "description": created.get('description'),
            "status": created['status'],
            "created_at": created['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get workflow details"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "workflow_id": workflow['workflow_id'],
            "name": workflow['name'],
            "description": workflow.get('description'),
            "instance": {
                "id": workflow['amc_instances']['instance_id'],
                "name": workflow['amc_instances']['instance_name']
            } if 'amc_instances' in workflow else None,
            "sql_query": workflow['sql_query'],
            "parameters": workflow.get('parameters', {}),
            "status": workflow.get('status', 'active'),
            "is_template": workflow.get('is_template', False),
            "tags": workflow.get('tags', []),
            "created_at": workflow.get('created_at'),
            "updated_at": workflow.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workflow")


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: str,
    updates: WorkflowUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a workflow"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare updates
        update_data = updates.dict(exclude_none=True)
        
        updated = db_service.update_workflow_sync(workflow_id, update_data)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update workflow")
        
        return {
            "workflow_id": updated['workflow_id'],
            "name": updated['name'],
            "status": updated['status'],
            "updated_at": updated['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow")


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: str,
    parameters: Optional[Dict[str, Any]] = Body(default={}),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a workflow"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create execution record
        execution_data = {
            "workflow_id": workflow['id'],  # Use internal UUID
            "status": "pending",
            "execution_parameters": parameters,
            "triggered_by": "manual",
            "started_at": datetime.utcnow().isoformat()
        }
        
        execution = db_service.create_execution_sync(execution_data)
        if not execution:
            raise HTTPException(status_code=500, detail="Failed to create execution")
        
        # TODO: Implement actual AMC query execution
        # For now, just return the execution record
        
        return {
            "execution_id": execution['execution_id'],
            "workflow_id": workflow_id,
            "status": execution['status'],
            "started_at": execution['started_at'],
            "message": "Workflow execution started. Check status endpoint for updates."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")


@router.get("/{workflow_id}/executions")
def list_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List executions for a workflow"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        executions = db_service.get_workflow_executions_sync(workflow['id'], limit)
        
        return [{
            "execution_id": e['execution_id'],
            "status": e['status'],
            "progress": e.get('progress', 0),
            "started_at": e.get('started_at'),
            "completed_at": e.get('completed_at'),
            "duration_seconds": e.get('duration_seconds'),
            "error_message": e.get('error_message'),
            "row_count": e.get('row_count'),
            "triggered_by": e.get('triggered_by', 'manual')
        } for e in executions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch executions")