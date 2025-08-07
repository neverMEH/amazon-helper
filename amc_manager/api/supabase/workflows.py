"""Workflows API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from ...services.db_service import db_service
from ...services.token_service import token_service
from ...core.logger_simple import get_logger
from ...core.supabase_client import SupabaseManager
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
    template_id: Optional[str] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sql_query: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class ScheduleCreate(BaseModel):
    cron_expression: str
    timezone: Optional[str] = "UTC"
    default_parameters: Optional[Dict[str, Any]] = {}


class ScheduleUpdate(BaseModel):
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@router.get("")
def list_workflows(
    instance_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all workflows for the current user"""
    try:
        logger.info(f"Listing workflows for user {current_user['id']}, instance_id filter: {instance_id}")
        workflows = db_service.get_user_workflows_sync(current_user['id'])
        logger.info(f"Found {len(workflows)} total workflows for user")
        
        # Filter by instance if provided
        if instance_id:
            logger.info(f"Filtering workflows by instance_id: {instance_id}")
            # Check if any workflows have instance data
            for w in workflows[:3]:  # Log first 3 for debugging
                if 'amc_instances' in w:
                    logger.info(f"  Workflow {w['workflow_id']} has instance: {w['amc_instances'].get('instance_id')}")
                else:
                    logger.info(f"  Workflow {w['workflow_id']} has NO instance data")
            
            workflows = [w for w in workflows if 'amc_instances' in w and w['amc_instances'].get('instance_id') == instance_id]
            logger.info(f"After filtering: {len(workflows)} workflows for instance {instance_id}")
        
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
        logger.error(f"Error listing workflows: {e}", exc_info=True)
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
        
        # If template_id is provided, increment its usage count
        if workflow.template_id:
            from ...services.query_template_service import query_template_service
            query_template_service.increment_usage(workflow.template_id)
        
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
            "id": workflow['workflow_id'],
            "workflowId": workflow['workflow_id'],
            "name": workflow['name'],
            "description": workflow.get('description'),
            "instance": {
                "id": workflow['amc_instances']['instance_id'],
                "name": workflow['amc_instances']['instance_name']
            } if 'amc_instances' in workflow else None,
            "sqlQuery": workflow['sql_query'],
            "parameters": workflow.get('parameters', {}),
            "status": workflow.get('status', 'active'),
            "isTemplate": workflow.get('is_template', False),
            "tags": workflow.get('tags', []),
            "createdAt": workflow.get('created_at'),
            "updatedAt": workflow.get('updated_at'),
            "lastExecuted": workflow.get('last_executed_at')
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


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Delete a workflow"""
    try:
        # Get workflow to verify it exists and check ownership
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the workflow from database
        client = SupabaseManager.get_client(use_service_role=True)
        response = client.table('workflows').delete().eq('workflow_id', workflow_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to delete workflow")
        
        logger.info(f"Workflow {workflow_id} deleted by user {current_user['id']}")
        
        return {
            "success": True,
            "message": f"Workflow {workflow_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")


@router.post("/{workflow_id}/execute")
def execute_workflow(
    workflow_id: str,
    body: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a workflow on AMC instance"""
    try:
        # Extract instance_id and parameters from body
        instance_id = body.get('instance_id')
        parameters = {k: v for k, v in body.items() if k != 'instance_id'}
        
        logger.info(f"Executing workflow {workflow_id} with instance_id: {instance_id}, parameters: {parameters}")
        
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"Found workflow: id={workflow['id']}, name={workflow['name']}, is_template={workflow.get('is_template', False)}")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            logger.error(f"Access denied: workflow user_id={workflow['user_id']}, current user_id={current_user['id']}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Import here to avoid circular import
        from ...services.amc_execution_service import amc_execution_service
        
        # Execute workflow using AMC execution service
        logger.info(f"Calling execution service with workflow UUID: {workflow['id']}")
        result = amc_execution_service.execute_workflow(
            workflow_id=workflow['id'],  # Use internal UUID
            user_id=current_user['id'],
            execution_parameters=parameters,
            triggered_by="manual",
            instance_id=instance_id  # Pass instance_id if provided
        )
        
        return result
    except ValueError as e:
        logger.error(f"ValueError in workflow execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/{workflow_id}/executions")
def list_workflow_executions(
    workflow_id: str,
    limit: int = 50,
    instance_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List executions for a workflow, optionally filtered by instance"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        executions = db_service.get_workflow_executions_sync(workflow['id'], limit, instance_id)
        
        return [{
            "execution_id": e['execution_id'],
            "status": e['status'],
            "progress": e.get('progress', 0),
            "started_at": e.get('started_at'),
            "completed_at": e.get('completed_at'),
            "duration_seconds": e.get('duration_seconds'),
            "error_message": e.get('error_message'),
            "row_count": e.get('row_count'),
            "triggered_by": e.get('triggered_by', 'manual'),
            "amc_execution_id": e.get('amc_execution_id')
            # Note: instance_id not stored in executions - use workflow relationship if needed
        } for e in executions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch executions")


@router.get("/executions/{execution_id}/status")
def get_execution_status(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get execution status"""
    try:
        from ...services.amc_execution_service import amc_execution_service
        
        # Poll AMC for latest status and update database
        status = amc_execution_service.poll_and_update_execution(execution_id, current_user['id'])
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch execution status")


@router.get("/executions/{execution_id}/detail")
def get_execution_detail(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed execution information"""
    try:
        # Get execution record from database
        client = SupabaseManager.get_client(use_service_role=True)
        response = client.table('workflow_executions')\
            .select('*, workflows!inner(user_id, name)')\
            .eq('execution_id', execution_id)\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        execution = response.data[0]
        
        # Verify user has access
        if execution['workflows']['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Return detailed execution data
        return {
            "execution_id": execution['execution_id'],
            "workflow_id": execution['workflow_id'],
            "workflow_name": execution['workflows']['name'],
            "status": execution['status'],
            "progress": execution.get('progress', 0),
            "execution_parameters": execution.get('execution_parameters'),
            "started_at": execution.get('started_at'),
            "completed_at": execution.get('completed_at'),
            "duration_seconds": execution.get('duration_seconds'),
            "error_message": execution.get('error_message'),
            "row_count": execution.get('row_count'),
            "triggered_by": execution.get('triggered_by', 'manual'),
            "output_location": execution.get('output_location'),
            "size_bytes": execution.get('size_bytes')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch execution detail")


@router.get("/executions/{execution_id}/results")
def get_execution_results(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get execution results"""
    try:
        from ...services.amc_execution_service import amc_execution_service
        
        results = amc_execution_service.get_execution_results(execution_id, current_user['id'])
        if not results:
            raise HTTPException(status_code=404, detail="Results not found or execution not completed")
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch execution results")


# Schedule endpoints
@router.post("/{workflow_id}/schedules")
def create_workflow_schedule(
    workflow_id: str,
    schedule: ScheduleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a schedule for a workflow"""
    try:
        from ...services.schedule_service import schedule_service
        
        result = schedule_service.create_schedule(
            workflow_id=workflow_id,
            cron_expression=schedule.cron_expression,
            user_id=current_user['id'],
            timezone=schedule.timezone,
            default_parameters=schedule.default_parameters
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/{workflow_id}/schedules")
def list_workflow_schedules(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List schedules for a workflow"""
    try:
        from ...services.schedule_service import schedule_service
        
        schedules = schedule_service.list_schedules(workflow_id, current_user['id'])
        return schedules
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list schedules")


@router.get("/schedules/{schedule_id}")
def get_schedule(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get schedule details"""
    try:
        from ...services.schedule_service import schedule_service
        
        schedule = schedule_service.get_schedule(schedule_id, current_user['id'])
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return schedule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule")


@router.put("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: str,
    updates: ScheduleUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a schedule"""
    try:
        from ...services.schedule_service import schedule_service
        
        result = schedule_service.update_schedule(
            schedule_id=schedule_id,
            user_id=current_user['id'],
            updates=updates.dict(exclude_none=True)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a schedule"""
    try:
        from ...services.schedule_service import schedule_service
        
        success = schedule_service.delete_schedule(schedule_id, current_user['id'])
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


# AMC Workflow Sync Endpoints

@router.post("/{workflow_id}/sync-to-amc")
def sync_workflow_to_amc(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sync a local workflow to AMC, creating it as a saved workflow definition
    """
    try:
        # Get workflow details
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if already synced
        if workflow.get('amc_workflow_id'):
            return {
                "success": True,
                "message": "Workflow already synced to AMC",
                "amc_workflow_id": workflow['amc_workflow_id']
            }
        
        # Get instance details
        instance = workflow.get('amc_instances')
        if not instance:
            raise HTTPException(status_code=400, detail="No AMC instance associated with workflow")
        
        # Get valid token
        import asyncio
        valid_token = asyncio.run(token_service.get_valid_token(current_user['id']))
        if not valid_token:
            raise HTTPException(status_code=401, detail="No valid authentication token")
        
        # Get AMC account details
        account = instance.get('amc_accounts')
        if not account:
            raise HTTPException(status_code=404, detail="AMC account not found")
        
        entity_id = account['account_id']
        marketplace_id = account['marketplace_id']
        
        # Generate AMC-compliant workflow ID
        # AMC requires alphanumeric + periods, dashes, underscores only
        import re
        amc_workflow_id = re.sub(r'[^a-zA-Z0-9._-]', '_', workflow['workflow_id'])
        
        # Extract parameters from SQL query for AMC input parameter definitions
        import re
        param_pattern = r'\{\{(\w+)\}\}'
        param_names = re.findall(param_pattern, workflow['sql_query'])
        
        # Create input parameter definitions for AMC
        input_parameters = []
        for param_name in param_names:
            # Determine parameter type based on name conventions or default to STRING
            param_type = 'STRING'
            if 'date' in param_name.lower() or 'time' in param_name.lower():
                param_type = 'TIMESTAMP'
            elif 'count' in param_name.lower() or 'number' in param_name.lower() or 'id' in param_name.lower():
                param_type = 'INTEGER'
            
            input_parameters.append({
                'name': param_name,
                'type': param_type,
                'required': True
            })
        
        # Create workflow in AMC
        from ...services.amc_api_client import AMCAPIClient
        api_client = AMCAPIClient()
        
        # Get output format from workflow parameters or default to CSV
        output_format = workflow.get('parameters', {}).get('output_format', 'CSV')
        
        response = api_client.create_workflow(
            instance_id=instance['instance_id'],
            workflow_id=amc_workflow_id,
            sql_query=workflow['sql_query'],
            access_token=valid_token,
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            input_parameters=input_parameters if input_parameters else None,
            output_format=output_format
        )
        
        if not response.get('success'):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create workflow in AMC: {response.get('error')}"
            )
        
        # Update local workflow with AMC workflow ID
        update_data = {
            'amc_workflow_id': amc_workflow_id,
            'is_synced_to_amc': True,
            'amc_sync_status': 'synced',
            'last_synced_at': datetime.now(timezone.utc).isoformat()
        }
        
        db_service.update_workflow_sync(workflow_id, update_data)
        
        return {
            "success": True,
            "message": "Workflow successfully synced to AMC",
            "amc_workflow_id": amc_workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing workflow to AMC: {e}")
        # Update sync status to failed
        db_service.update_workflow_sync(workflow_id, {'amc_sync_status': 'sync_failed'})
        raise HTTPException(status_code=500, detail=f"Failed to sync workflow: {str(e)}")


@router.get("/{workflow_id}/amc-status")
def get_workflow_amc_status(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the AMC sync status of a workflow
    """
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "workflow_id": workflow_id,
            "amc_workflow_id": workflow.get('amc_workflow_id'),
            "is_synced_to_amc": workflow.get('is_synced_to_amc', False),
            "amc_sync_status": workflow.get('amc_sync_status', 'not_synced'),
            "last_synced_at": workflow.get('last_synced_at')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow AMC status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AMC status")


@router.delete("/{workflow_id}/amc-sync")
def remove_workflow_from_amc(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Remove a workflow from AMC (delete the saved workflow definition)
    """
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        amc_workflow_id = workflow.get('amc_workflow_id')
        if not amc_workflow_id:
            return {
                "success": True,
                "message": "Workflow is not synced to AMC"
            }
        
        # Get instance details
        instance = workflow.get('amc_instances')
        if not instance:
            raise HTTPException(status_code=400, detail="No AMC instance associated with workflow")
        
        # Get valid token
        import asyncio
        valid_token = asyncio.run(token_service.get_valid_token(current_user['id']))
        if not valid_token:
            raise HTTPException(status_code=401, detail="No valid authentication token")
        
        # Get AMC account details
        account = instance.get('amc_accounts')
        if not account:
            raise HTTPException(status_code=404, detail="AMC account not found")
        
        entity_id = account['account_id']
        marketplace_id = account['marketplace_id']
        
        # Delete workflow from AMC
        from ...services.amc_api_client import AMCAPIClient
        api_client = AMCAPIClient()
        
        response = api_client.delete_workflow(
            instance_id=instance['instance_id'],
            workflow_id=amc_workflow_id,
            access_token=valid_token,
            entity_id=entity_id,
            marketplace_id=marketplace_id
        )
        
        if not response.get('success'):
            # Log the error but continue to update local state
            logger.error(f"Failed to delete workflow from AMC: {response.get('error')}")
        
        # Update local workflow to remove AMC sync
        update_data = {
            'amc_workflow_id': None,
            'is_synced_to_amc': False,
            'amc_sync_status': 'not_synced',
            'last_synced_at': None
        }
        
        db_service.update_workflow_sync(workflow_id, update_data)
        
        return {
            "success": True,
            "message": "Workflow removed from AMC"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing workflow from AMC: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove workflow: {str(e)}")


@router.get("/{workflow_id}/execution-status")
def get_workflow_execution_status(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed execution status for a workflow, showing both internal and AMC execution IDs.
    This helps debug executions that exist in one system but not the other.
    """
    try:
        # Get workflow to verify ownership
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all executions for this workflow from database
        client = SupabaseManager.get_client(use_service_role=True)
        
        db_executions_response = client.table('workflow_executions')\
            .select('*')\
            .eq('workflow_id', workflow['id'])\
            .order('started_at', desc=True)\
            .limit(20)\
            .execute()
        
        db_executions = db_executions_response.data
        
        # Categorize executions
        execution_status = {
            'workflow_id': workflow_id,
            'workflow_name': workflow['name'],
            'instance_id': workflow.get('instance_id'),
            'total_executions': len(db_executions),
            'running_executions': [],
            'recent_executions': [],
            'missing_amc_ids': [],
            'execution_summary': {
                'pending': 0,
                'running': 0,
                'completed': 0,
                'failed': 0,
                'missing_amc_id': 0
            }
        }
        
        for exec in db_executions:
            exec_info = {
                'internal_execution_id': exec.get('execution_id'),
                'amc_execution_id': exec.get('amc_execution_id'),
                'status': exec.get('status'),
                'progress': exec.get('progress', 0),
                'started_at': exec.get('started_at'),
                'completed_at': exec.get('completed_at'),
                'duration_seconds': exec.get('duration_seconds'),
                'error_message': exec.get('error_message'),
                'row_count': exec.get('row_count'),
                'triggered_by': exec.get('triggered_by', 'manual')
            }
            
            # Add to appropriate categories
            if exec.get('status') in ['pending', 'running']:
                execution_status['running_executions'].append(exec_info)
            
            if not exec.get('amc_execution_id'):
                execution_status['missing_amc_ids'].append(exec_info)
            
            execution_status['recent_executions'].append(exec_info)
            
            # Update summary counts
            status = exec.get('status', 'unknown')
            if status in execution_status['execution_summary']:
                execution_status['execution_summary'][status] += 1
            
            if not exec.get('amc_execution_id'):
                execution_status['execution_summary']['missing_amc_id'] += 1
        
        # Add diagnostic information
        execution_status['diagnostics'] = {
            'has_running_executions': len(execution_status['running_executions']) > 0,
            'has_missing_amc_ids': len(execution_status['missing_amc_ids']) > 0,
            'recommendations': []
        }
        
        # Generate recommendations
        if execution_status['running_executions']:
            if any(not exec.get('amc_execution_id') for exec in execution_status['running_executions']):
                execution_status['diagnostics']['recommendations'].append({
                    'type': 'missing_amc_id',
                    'message': 'Some running executions are missing AMC execution IDs. This usually means the AMC API call failed during execution creation.',
                    'action': 'Check the backend logs for AMC API errors around the execution start time.'
                })
            else:
                execution_status['diagnostics']['recommendations'].append({
                    'type': 'check_amc_console',
                    'message': 'Your executions have AMC IDs but may not be visible in AMC console yet.',
                    'action': 'Wait 1-2 minutes for AMC to register the executions, then check the AMC console again.'
                })
        
        if execution_status['missing_amc_ids']:
            execution_status['diagnostics']['recommendations'].append({
                'type': 'authentication_issue',
                'message': f"{len(execution_status['missing_amc_ids'])} executions are missing AMC execution IDs.",
                'action': 'This could indicate authentication issues or AMC API connectivity problems. Check if your Amazon tokens are still valid.'
            })
        
        return execution_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")


@router.get("/executions/cross-reference")
async def cross_reference_executions(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cross-reference executions between internal database and AMC console.
    This helps identify executions that exist in one system but not the other.
    """
    try:
        # Verify user has access to this instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to this instance")
        
        # Get recent executions from database for this instance
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get workflows for this instance
        workflows_response = client.table('workflows')\
            .select('id, workflow_id, name')\
            .eq('instance_id', instance_id)\
            .eq('user_id', current_user['id'])\
            .execute()
        
        workflow_ids = [w['id'] for w in workflows_response.data]
        
        if not workflow_ids:
            return {
                'success': True,
                'instance_id': instance_id,
                'message': 'No workflows found for this instance',
                'database_executions': [],
                'amc_executions': [],
                'cross_reference_results': {
                    'matched': [],
                    'database_only': [],
                    'amc_only': [],
                    'missing_amc_ids': []
                }
            }
        
        # Get recent executions for these workflows
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        
        db_executions_response = client.table('workflow_executions')\
            .select('*, workflows!inner(workflow_id, name)')\
            .in_('workflow_id', workflow_ids)\
            .gte('started_at', yesterday.isoformat())\
            .order('started_at', desc=True)\
            .execute()
        
        db_executions = db_executions_response.data
        
        # Try to get AMC executions
        amc_executions = []
        try:
            # Get valid token
            valid_token = await token_service.get_valid_token(current_user['id'])
            if valid_token:
                # Get instance details
                instance = db_service.get_instance_details_sync(instance_id)
                if instance and instance.get('amc_accounts'):
                    account = instance['amc_accounts']
                    
                    # Get AMC executions
                    from ...services.amc_api_client import AMCAPIClient
                    api_client = AMCAPIClient()
                    
                    response = api_client.list_executions(
                        instance_id=instance_id,
                        access_token=valid_token,
                        entity_id=account['account_id'],
                        marketplace_id=account['marketplace_id'],
                        limit=50
                    )
                    
                    if response.get('success'):
                        amc_executions = response.get('executions', [])
        
        except Exception as e:
            logger.warning(f"Failed to fetch AMC executions: {e}")
        
        # Cross-reference the executions
        cross_ref_results = {
            'matched': [],
            'database_only': [],
            'amc_only': [],
            'missing_amc_ids': []
        }
        
        # Create lookup maps
        db_by_amc_id = {}
        amc_by_id = {}
        
        for db_exec in db_executions:
            amc_exec_id = db_exec.get('amc_execution_id')
            if amc_exec_id:
                db_by_amc_id[amc_exec_id] = db_exec
            else:
                cross_ref_results['missing_amc_ids'].append({
                    'internal_execution_id': db_exec.get('execution_id'),
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'status': db_exec.get('status'),
                    'started_at': db_exec.get('started_at')
                })
        
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id:
                amc_by_id[exec_id] = amc_exec
        
        # Find matches and differences
        for db_exec in db_executions:
            amc_exec_id = db_exec.get('amc_execution_id')
            if amc_exec_id and amc_exec_id in amc_by_id:
                # Matched execution
                amc_exec = amc_by_id[amc_exec_id]
                cross_ref_results['matched'].append({
                    'internal_execution_id': db_exec.get('execution_id'),
                    'amc_execution_id': amc_exec_id,
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'database_status': db_exec.get('status'),
                    'amc_status': amc_exec.get('status'),
                    'started_at': db_exec.get('started_at')
                })
            elif amc_exec_id:
                # In database but not found in AMC (might be too old or failed to create)
                cross_ref_results['database_only'].append({
                    'internal_execution_id': db_exec.get('execution_id'),
                    'amc_execution_id': amc_exec_id,
                    'workflow_name': db_exec.get('workflows', {}).get('name', 'Unknown'),
                    'status': db_exec.get('status'),
                    'started_at': db_exec.get('started_at')
                })
        
        # Find AMC executions not in database
        for amc_exec in amc_executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            if exec_id and exec_id not in db_by_amc_id:
                cross_ref_results['amc_only'].append({
                    'amc_execution_id': exec_id,
                    'workflow_id': amc_exec.get('workflowId'),
                    'amc_status': amc_exec.get('status'),
                    'created_time': amc_exec.get('createdTime')
                })
        
        return {
            'success': True,
            'instance_id': instance_id,
            'database_executions_count': len(db_executions),
            'amc_executions_count': len(amc_executions),
            'cross_reference_results': cross_ref_results,
            'summary': {
                'matched_executions': len(cross_ref_results['matched']),
                'database_only': len(cross_ref_results['database_only']),
                'amc_only': len(cross_ref_results['amc_only']),
                'missing_amc_ids': len(cross_ref_results['missing_amc_ids'])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cross-referencing executions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cross-reference executions: {str(e)}")