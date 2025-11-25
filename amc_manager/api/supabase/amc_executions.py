"""AMC Executions API endpoints for fetching workflow executions directly from AMC

Note: The AMC API /workflows endpoint returns workflow executions (historical runs),
not workflow definitions. Each execution represents a past run of a workflow."""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import uuid

from ...services.amc_execution_service import amc_execution_service
from ...services.db_service import db_service
from ...services.token_service import token_service
from ...services.data_analysis_service import data_analysis_service
from ...services.enhanced_schedule_service import EnhancedScheduleService
from ...core.supabase_client import SupabaseManager
from .auth import get_current_user


# Pydantic model for schedule-from-execution request
class ScheduleFromExecutionRequest(BaseModel):
    """Request model for creating a schedule from an execution"""
    preset_type: str = Field(..., description="Schedule type: daily, weekly, monthly")
    name: str = Field(..., description="Name for the schedule")
    description: Optional[str] = Field(None, description="Description of the schedule")
    timezone: str = Field("UTC", description="Timezone for schedule execution")
    execute_time: str = Field("02:00", description="Time of day to execute (HH:MM)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week for weekly (0=Sun)")
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month for monthly")
    lookback_days: int = Field(30, ge=1, le=365, description="Number of days to look back")
    date_range_type: str = Field("rolling", description="Date range type: rolling or fixed")
    snowflake_enabled: bool = Field(False, description="Enable Snowflake upload")
    snowflake_table_name: Optional[str] = Field(None, description="Snowflake table name")
    snowflake_schema_name: Optional[str] = Field(None, description="Snowflake schema name")
    snowflake_strategy: Optional[str] = Field("upsert", description="Upload strategy")

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/all/stored")
async def list_all_stored_executions(
    limit: int = 100,
    instance_ids: str = None,  # Comma-separated list of instance IDs
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List all workflow executions for a user from local database.
    This is much more efficient than calling AMC API for each instance.
    
    Args:
        limit: Maximum number of executions to return
        instance_ids: Optional comma-separated list of instance IDs to filter
        current_user: The authenticated user
        
    Returns:
        List of all executions from database across all user's instances
    """
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get all workflows for the user with instance information
        workflows_response = client.table('workflows')\
            .select('id, workflow_id, name, amc_workflow_id, instance_id, amc_instances(instance_id, instance_name)')\
            .eq('user_id', current_user['id'])\
            .execute()
        
        # Filter by instance IDs if provided
        instance_filter = []
        if instance_ids:
            instance_filter = instance_ids.split(',')
        
        # Get executions for all workflows
        all_executions = []
        for workflow in workflows_response.data:
            # Skip if instance filter is applied and this instance is not in the filter
            if instance_filter and workflow.get('amc_instances', {}).get('instance_id') not in instance_filter:
                continue
            
            # Get executions for this workflow
            executions_response = client.table('workflow_executions')\
                .select('*')\
                .eq('workflow_id', workflow['id'])\
                .order('started_at', desc=True)\
                .limit(20)\
                .execute()  # Limit per workflow to avoid too much data
            
            for execution in executions_response.data:
                # Map database status to AMC-style status for consistency
                db_status = execution.get('status', 'pending').lower()
                amc_status = {
                    'pending': 'PENDING',
                    'running': 'RUNNING',
                    'completed': 'SUCCEEDED',  # Map completed to SUCCEEDED for AMC compatibility
                    'failed': 'FAILED',
                    'cancelled': 'CANCELLED'
                }.get(db_status, db_status.upper())
                
                all_executions.append({
                    'workflowExecutionId': execution.get('execution_id'),
                    'workflowId': workflow.get('amc_workflow_id') or workflow.get('workflow_id'),
                    'workflowName': workflow.get('name'),
                    'status': amc_status,  # Use mapped status
                    'startTime': execution.get('started_at'),
                    'endTime': execution.get('completed_at'),
                    'sqlQuery': execution.get('sql_query'),
                    'triggeredBy': execution.get('triggered_by', 'manual'),
                    'amcExecutionId': execution.get('amc_execution_id'),
                    'rowCount': execution.get('row_count'),
                    'errorMessage': execution.get('error_message'),
                    'instanceInfo': {
                        'id': workflow.get('amc_instances', {}).get('instance_id'),
                        'name': workflow.get('amc_instances', {}).get('instance_name')
                    } if workflow.get('amc_instances') else None,
                    'isStoredLocally': True
                })
        
        # Sort all executions by start time
        all_executions.sort(key=lambda x: x.get('startTime', ''), reverse=True)
        
        # Apply overall limit
        all_executions = all_executions[:limit]
        
        return {
            'success': True,
            'executions': all_executions,
            'total': len(all_executions),
            'source': 'database',
            'message': 'Fetched from local database for better performance'
        }
        
    except Exception as e:
        logger.error(f"Error listing all stored executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stored/{instance_id}")
async def list_stored_executions(
    instance_id: str,
    limit: int = 50,
    sync_if_empty: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List AMC workflow executions from local database first.
    Only syncs with AMC API if no data exists or explicitly requested.
    
    Args:
        instance_id: The AMC instance ID
        limit: Maximum number of executions to return
        sync_if_empty: Whether to sync from AMC if no local data exists
        current_user: The authenticated user
        
    Returns:
        List of executions from database, potentially synced from AMC
    """
    try:
        # Verify user has access to this instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to this instance")

        # First, try to get executions from our database
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get workflows for this instance that belong to the user
        workflows_response = client.table('workflows')\
            .select('id, workflow_id, name, amc_workflow_id')\
            .eq('user_id', current_user['id'])\
            .execute()
        
        # Get instance's internal ID
        instance_data = next((inst for inst in user_instances if inst['instance_id'] == instance_id), None)
        if instance_data:
            # Filter workflows for this instance
            instance_workflows = []
            for workflow in workflows_response.data:
                # Check if workflow belongs to this instance
                workflow_instance = client.table('workflows')\
                    .select('instance_id')\
                    .eq('id', workflow['id'])\
                    .execute()
                
                if workflow_instance.data and workflow_instance.data[0].get('instance_id') == instance_data.get('id'):
                    instance_workflows.append(workflow)
        else:
            instance_workflows = []
        
        # Get all executions for these workflows
        all_executions = []
        for workflow in instance_workflows:
            executions_response = client.table('workflow_executions')\
                .select('*')\
                .eq('workflow_id', workflow['id'])\
                .order('started_at', desc=True)\
                .limit(limit)\
                .execute()
            
            for execution in executions_response.data:
                # Map database status to AMC-style status for consistency
                db_status = execution.get('status', 'pending').lower()
                amc_status = {
                    'pending': 'PENDING',
                    'running': 'RUNNING',
                    'completed': 'SUCCEEDED',  # Map completed to SUCCEEDED for AMC compatibility
                    'failed': 'FAILED',
                    'cancelled': 'CANCELLED'
                }.get(db_status, db_status.upper())
                
                # Format execution data
                all_executions.append({
                    'workflowExecutionId': execution.get('execution_id'),
                    'workflowId': workflow.get('amc_workflow_id') or workflow.get('workflow_id'),
                    'workflowName': workflow.get('name'),
                    'status': amc_status,  # Use mapped status
                    'startTime': execution.get('started_at'),
                    'endTime': execution.get('completed_at'),
                    'sqlQuery': execution.get('sql_query'),
                    'triggeredBy': execution.get('triggered_by', 'manual'),
                    'amcExecutionId': execution.get('amc_execution_id'),
                    'rowCount': execution.get('row_count'),
                    'errorMessage': execution.get('error_message'),
                    'isStoredLocally': True
                })
        
        # Sort by start time
        all_executions.sort(key=lambda x: x.get('startTime', ''), reverse=True)
        
        # If no local data and sync requested, fetch from AMC
        if not all_executions and sync_if_empty:
            logger.info(f"No local executions found for instance {instance_id}, syncing from AMC")
            
            # Get instance details for AMC API call
            instance = db_service.get_instance_details_sync(instance_id)
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")
            
            account = instance.get('amc_accounts')
            if not account:
                logger.warning(f"No AMC account found for instance {instance_id}")
                return {
                    'success': True,
                    'executions': [],
                    'total': 0,
                    'source': 'local'
                }
            
            # Get valid token
            valid_token = await token_service.get_valid_token(current_user['id'])
            if not valid_token:
                logger.warning("No valid authentication token available")
                return {
                    'success': True,
                    'executions': [],
                    'total': 0,
                    'source': 'local',
                    'error': 'Authentication required'
                }
            
            # Fetch from AMC API
            from ...services.amc_api_client import AMCAPIClient
            api_client = AMCAPIClient()
            
            response = api_client.list_executions(
                instance_id=instance_id,
                access_token=valid_token,
                entity_id=account['account_id'],
                marketplace_id=account['marketplace_id'],
                limit=limit
            )
            
            if response.get('success'):
                all_executions = response.get('executions', [])
                # Mark as from AMC
                for exec in all_executions:
                    exec['isStoredLocally'] = False
                
                # TODO: Store these executions in database for future use
                logger.info(f"Synced {len(all_executions)} executions from AMC for instance {instance_id}")
        
        return {
            'success': True,
            'executions': all_executions[:limit],
            'total': len(all_executions),
            'source': 'local' if any(e.get('isStoredLocally') for e in all_executions) else 'amc'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing stored executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            # Clear any invalid tokens
            try:
                client = SupabaseManager.get_client(use_service_role=True)
                client.table('users').update({'auth_tokens': None}).eq('id', current_user['id']).execute()
            except Exception as e:
                logger.error(f"Failed to clear invalid tokens: {e}")
            
            raise HTTPException(
                status_code=401, 
                detail="Authentication token is invalid or expired. Please re-authenticate in your profile settings."
            )
        
        # Get AMC account details
        account = instance.get('amc_accounts')
        if not account:
            raise HTTPException(status_code=404, detail="AMC account not found")
        
        entity_id = account['account_id']
        marketplace_id = account['marketplace_id']
        
        # Log the entity ID being used for debugging
        logger.info(f"Using entity_id: {entity_id} for instance: {instance_id}")
        logger.info(f"Token starts with: {valid_token[:20]}..." if len(str(valid_token)) > 20 else f"Token: {valid_token}")
        
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
            error_msg = response.get('error', 'Unknown error')
            # Check for common authentication/authorization issues
            if '403' in str(error_msg) or 'Unauthorized' in str(error_msg):
                # Log more details about the 403 error
                logger.error(f"Got 403 error for user {current_user['id']}")
                logger.error(f"Instance: {instance_id}, Entity ID: {entity_id}")
                logger.error(f"Full error: {error_msg}")
                
                # Check if it's a permission issue vs token issue
                if "entity" in str(error_msg).lower() or "advertiser" in str(error_msg).lower():
                    # Entity ID mismatch - user doesn't have access to this advertiser
                    raise HTTPException(
                        status_code=403,
                        detail=f"You don't have permission to access advertiser {entity_id}. Please ensure your Amazon account has access to this advertiser."
                    )
                else:
                    # Token issue - clear tokens to force re-authentication
                    logger.warning(f"Clearing tokens for user {current_user['id']} due to 403 error")
                    try:
                        # Clear tokens in database
                        client = SupabaseManager.get_client(use_service_role=True)
                        client.table('users').update({'auth_tokens': None}).eq('id', current_user['id']).execute()
                        
                        # Remove from token refresh tracking
                        from ...services.token_refresh_service import token_refresh_service
                        token_refresh_service.remove_user(current_user['id'])
                    except Exception as e:
                        logger.error(f"Failed to clear tokens: {e}")
                    
                    raise HTTPException(
                        status_code=401,
                        detail="AMC API authorization failed. Your authentication has expired. Please re-authenticate in your profile settings."
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch AMC executions: {error_msg}"
                )
        
        executions = response.get('executions', [])
        
        # Log the first execution to see its structure
        if executions:
            logger.info(f"Sample execution data: {executions[0]}")
        
        # Fetch execution details from our database to enrich the AMC data
        # Get database client (SupabaseManager already imported at top)
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Build list of AMC execution IDs to query
        amc_execution_ids = []
        for exec in executions:
            exec_id = exec.get('workflowExecutionId') or exec.get('executionId')
            if exec_id:
                amc_execution_ids.append(exec_id)
        
        # Fetch our database records for these executions
        db_executions = {}
        if amc_execution_ids:
            try:
                db_response = client.table('workflow_executions')\
                    .select('*, workflows!inner(workflow_id, name, description, sql_query, parameters)')\
                    .in_('amc_execution_id', amc_execution_ids)\
                    .execute()
                
                # Create a map of amc_execution_id -> database record
                for db_exec in db_response.data:
                    if db_exec.get('amc_execution_id'):
                        db_executions[db_exec['amc_execution_id']] = db_exec
            except Exception as e:
                logger.warning(f"Failed to fetch database execution records: {e}")
        
        # Enhance executions with database information
        enhanced_executions = []
        for amc_exec in executions:
            exec_id = amc_exec.get('workflowExecutionId') or amc_exec.get('executionId')
            db_exec = db_executions.get(exec_id)
            
            # Normalize the status to be consistent across all views
            # AMC returns PENDING, RUNNING, SUCCEEDED, FAILED
            # We normalize to: pending, running, completed, failed
            amc_status = amc_exec.get('status', 'UNKNOWN')
            normalized_status = {
                'PENDING': 'pending',
                'RUNNING': 'running', 
                'SUCCEEDED': 'completed',
                'FAILED': 'failed',
                'CANCELLED': 'failed',
                'COMPLETED': 'completed'  # Sometimes AMC returns this
            }.get(amc_status.upper(), amc_status.lower())
            
            # Build enhanced execution object
            enhanced_exec = {
                **amc_exec,
                'instanceId': instance_id,
                'workflowExecutionId': exec_id or amc_exec.get('id'),
                'status': amc_status,  # Keep original AMC status for display
                'normalizedStatus': normalized_status,  # Add normalized status for consistency
                'amcStatus': amc_status  # Also keep original as amcStatus
            }
            
            # Add database information if available
            if db_exec:
                workflow = db_exec.get('workflows', {})
                enhanced_exec.update({
                    'workflowName': workflow.get('name') or amc_exec.get('workflowName') or 'Query',
                    'workflowDescription': workflow.get('description'),
                    'sqlQuery': workflow.get('sql_query'),
                    'executionParameters': db_exec.get('execution_parameters'),
                    'triggeredBy': db_exec.get('triggered_by', 'Manual'),
                    'rowCount': db_exec.get('row_count'),
                    'durationSeconds': db_exec.get('duration_seconds'),
                    'createdAt': db_exec.get('created_at'),
                    'completedAt': db_exec.get('completed_at'),
                })
            else:
                # Use default values for executions not in our database
                enhanced_exec['workflowName'] = amc_exec.get('workflowName') or 'Ad-hoc Query'
                enhanced_exec['triggeredBy'] = amc_exec.get('triggeredBy', 'External')
            
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


@router.post("/refresh-status/{execution_id}")
async def refresh_execution_status(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually refresh the status of a specific execution
    
    Args:
        execution_id: The execution ID to refresh
        current_user: The authenticated user
        
    Returns:
        Updated execution status
    """
    try:
        from ...services.amc_execution_service import amc_execution_service
        
        # Poll and update the execution status
        status = await amc_execution_service.poll_and_update_execution(execution_id, current_user['id'])
        
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "success": True,
            "execution": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing execution status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh-all")
async def refresh_all_executions(
    instance_id: str = None,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Refresh status for all pending/running executions
    
    Args:
        instance_id: Optional - filter by instance ID
        limit: Maximum number of executions to refresh (default 50)
        current_user: The authenticated user
        
    Returns:
        Summary of refreshed executions
    """
    try:
        from ...services.amc_execution_service import amc_execution_service
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Build the query for pending/running executions
        query = client.table('workflow_executions')\
            .select('execution_id, status, workflow_id, workflows!inner(user_id, instance_id, amc_instances!inner(instance_id))')\
            .in_('status', ['pending', 'running'])\
            .eq('workflows.user_id', current_user['id'])\
            .order('started_at', desc=True)\
            .limit(limit)
        
        # Filter by instance if provided
        if instance_id:
            query = query.eq('workflows.amc_instances.instance_id', instance_id)
        
        response = query.execute()
        
        if not response.data:
            return {
                "success": True,
                "message": "No pending or running executions to refresh",
                "refreshed": 0,
                "updated": 0
            }
        
        # Track refresh statistics
        refreshed = 0
        updated = 0
        failed = 0
        updates = []
        
        logger.info(f"Refreshing {len(response.data)} pending/running executions")
        
        for execution in response.data:
            execution_id = execution['execution_id']
            old_status = execution['status']
            
            try:
                # Poll and update the execution
                result = await amc_execution_service.poll_and_update_execution(
                    execution_id=execution_id,
                    user_id=current_user['id']
                )
                
                refreshed += 1
                
                if result and result.get('status') != old_status:
                    updated += 1
                    updates.append({
                        "execution_id": execution_id,
                        "old_status": old_status,
                        "new_status": result.get('status')
                    })
                    logger.info(f"Updated {execution_id}: {old_status} -> {result.get('status')}")
                    
            except Exception as e:
                logger.error(f"Failed to refresh execution {execution_id}: {e}")
                failed += 1
        
        return {
            "success": True,
            "message": f"Refreshed {refreshed} executions, {updated} status changes",
            "refreshed": refreshed,
            "updated": updated,
            "failed": failed,
            "updates": updates
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_all_executions: {e}")
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
        execution_id: The AMC execution ID or internal execution ID (exec_*)
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

        # Check if this is an internal execution ID (starts with exec_)
        # If so, look up the AMC execution ID from our database
        amc_execution_id = execution_id
        if execution_id.startswith('exec_'):
            client = SupabaseManager.get_client(use_service_role=True)
            try:
                db_response = client.table('workflow_executions')\
                    .select('amc_execution_id')\
                    .eq('execution_id', execution_id)\
                    .single()\
                    .execute()
                
                if db_response.data:
                    if db_response.data.get('amc_execution_id'):
                        amc_execution_id = db_response.data['amc_execution_id']
                        logger.info(f"Mapped internal ID {execution_id} to AMC ID {amc_execution_id}")
                    else:
                        # Execution exists but has no AMC ID (likely failed before AMC submission)
                        # Return the failure details instead of trying to fetch from AMC
                        logger.warning(f"Execution {execution_id} has no AMC execution ID - returning local status")
                        
                        # Get the full execution record with error details
                        full_exec = client.table('workflow_executions')\
                            .select('*')\
                            .eq('execution_id', execution_id)\
                            .single()\
                            .execute()
                        
                        if full_exec.data:
                            return {
                                "execution_id": execution_id,
                                "status": full_exec.data.get('status', 'failed'),
                                "error_message": full_exec.data.get('error_message', 'Execution failed before submission to AMC'),
                                "created_at": full_exec.data.get('created_at'),
                                "updated_at": full_exec.data.get('updated_at'),
                                "amc_execution_id": None,
                                "amcStatus": "NOT_SUBMITTED",
                                "message": "This execution failed before being submitted to AMC. Please check the error message for details."
                            }
                        else:
                            raise HTTPException(
                                status_code=404,
                                detail=f"Execution {execution_id} was not submitted to AMC (likely failed during preparation)"
                            )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Execution with ID {execution_id} not found in database"
                    )
            except Exception as e:
                if "not found" in str(e).lower():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Execution with ID {execution_id} not found"
                    )
                logger.error(f"Error looking up AMC execution ID: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to lookup execution: {str(e)}"
                )
        
        # Get valid token
        valid_token = await token_service.get_valid_token(current_user['id'])
        
        if not valid_token:
            # Clear any invalid tokens
            try:
                client = SupabaseManager.get_client(use_service_role=True)
                client.table('users').update({'auth_tokens': None}).eq('id', current_user['id']).execute()
            except Exception as e:
                logger.error(f"Failed to clear invalid tokens: {e}")
            
            raise HTTPException(
                status_code=401, 
                detail="Authentication token is invalid or expired. Please re-authenticate in your profile settings."
            )
        
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
            execution_id=amc_execution_id,  # Use the AMC execution ID
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
        # Check both normalized status and AMC status for completion
        result_data = None
        is_completed = (
            status_response.get('status') == 'completed' or 
            status_response.get('amcStatus') == 'SUCCEEDED' or
            status_response.get('amcStatus') == 'COMPLETED'
        )
        
        if is_completed:
            logger.info(f"Execution {amc_execution_id} is completed, fetching download URLs")
            download_response = api_client.get_download_urls(
                execution_id=amc_execution_id,  # Use the AMC execution ID
                access_token=valid_token,
                entity_id=entity_id,
                marketplace_id=marketplace_id,
                instance_id=instance_id
            )
            
            if download_response.get('success'):
                urls = download_response.get('downloadUrls', [])
                logger.info(f"Got {len(urls)} download URLs for execution {amc_execution_id}")
                if urls:
                    # Download and parse the first CSV file
                    csv_response = api_client.download_and_parse_csv(urls[0])
                    if csv_response.get('success'):
                        result_data = csv_response.get('data')
                        logger.info(f"Successfully fetched {len(result_data) if result_data else 0} rows for execution {amc_execution_id}")
                    else:
                        logger.warning(f"Failed to parse CSV for execution {amc_execution_id}: {csv_response.get('error')}")
                else:
                    logger.warning(f"No download URLs available for completed execution {amc_execution_id}")
            else:
                logger.warning(f"Failed to get download URLs for execution {amc_execution_id}: {download_response.get('error')}")
        
        # Get associated brands for the instance
        brands = db_service.get_brands_for_instance_sync(instance_id)
        
        # Try to fetch execution details from our database
        client = SupabaseManager.get_client(use_service_role=True)
        
        db_execution = None
        workflow_info = None
        
        try:
            # Look up by the appropriate field based on the ID type
            if execution_id.startswith('exec_'):
                # Use internal execution ID
                db_response = client.table('workflow_executions')\
                    .select('*, workflows!inner(workflow_id, name, description, sql_query, parameters, created_at, updated_at)')\
                    .eq('execution_id', execution_id)\
                    .single()\
                    .execute()
            else:
                # Use AMC execution ID
                db_response = client.table('workflow_executions')\
                    .select('*, workflows!inner(workflow_id, name, description, sql_query, parameters, created_at, updated_at)')\
                    .eq('amc_execution_id', amc_execution_id)\
                    .single()\
                    .execute()
            
            if db_response.data:
                db_execution = db_response.data
                workflow = db_execution.get('workflows', {})
                workflow_info = {
                    'id': workflow.get('workflow_id'),
                    'name': workflow.get('name'),
                    'description': workflow.get('description'),
                    'sqlQuery': workflow.get('sql_query'),
                    'parameters': workflow.get('parameters'),
                    'createdAt': workflow.get('created_at'),
                    'updatedAt': workflow.get('updated_at')
                }
        except Exception as e:
            logger.warning(f"Failed to get execution from database: {e}")
        
        # Build enhanced execution response
        execution_detail = {
            **status_response,
            "resultData": result_data,
            "instanceInfo": {
                "instanceId": instance.get('instance_id'),
                "instanceName": instance.get('instance_name'),
                "region": instance.get('region', 'us-east-1'),
                "accountId": account.get('account_id'),
                "accountName": account.get('account_name', 'N/A'),
                "marketplaceId": marketplace_id
            },
            "brands": brands,
            "workflowInfo": workflow_info
        }
        
        # Add database execution details if available
        if db_execution:
            execution_detail.update({
                'sqlQuery': workflow_info.get('sqlQuery') if workflow_info else None,
                'executionParameters': db_execution.get('execution_parameters'),
                'triggeredBy': db_execution.get('triggered_by', 'Manual'),
                'rowCount': db_execution.get('row_count'),
                'durationSeconds': db_execution.get('duration_seconds'),
                'createdAt': db_execution.get('created_at'),
                'startedAt': db_execution.get('started_at'),
                'completedAt': db_execution.get('completed_at'),
                'errorMessage': db_execution.get('error_message'),
                # Add execution IDs for schedule creation
                'executionId': db_execution.get('execution_id'),  # e.g., "exec_db67423d"
                'workflowExecutionId': db_execution.get('execution_id'),  # Same, for compatibility
                'localExecutionId': db_execution.get('id'),  # UUID
                # Add Snowflake export fields
                'snowflake_enabled': db_execution.get('snowflake_enabled'),
                'snowflake_status': db_execution.get('snowflake_status'),
                'snowflake_table_name': db_execution.get('snowflake_table_name'),
                'snowflake_schema_name': db_execution.get('snowflake_schema_name'),
                'snowflake_row_count': db_execution.get('snowflake_row_count'),
                'snowflake_error': db_execution.get('snowflake_error')
            })
        
        return {
            "success": True,
            "execution": execution_detail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AMC execution details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{instance_id}/{execution_id}/analysis")
async def analyze_execution_data(
    instance_id: str,
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze execution result data and provide insights
    
    Args:
        instance_id: The AMC instance ID
        execution_id: The AMC execution ID
        current_user: The authenticated user
        
    Returns:
        Analysis results including statistics and insights
    """
    try:
        # First get the execution details to get the data
        execution_details = await get_amc_execution_details(
            instance_id, execution_id, current_user
        )
        
        if not execution_details.get("success"):
            raise HTTPException(status_code=404, detail="Execution not found")
        
        execution = execution_details.get("execution", {})
        result_data = execution.get("resultData")
        
        if not result_data:
            return {
                "success": True,
                "analysis": {
                    "summary": {
                        "row_count": 0,
                        "column_count": 0,
                        "data_quality": "No data available"
                    },
                    "message": "No result data available for analysis"
                }
            }
        
        # Perform data analysis
        analysis = data_analysis_service.analyze_data(result_data)
        
        return {
            "success": True,
            "executionId": execution_id,
            "instanceId": instance_id,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing execution data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{execution_id}/schedule")
async def create_schedule_from_execution(
    execution_id: str,
    request: ScheduleFromExecutionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a workflow and schedule from an ad-hoc execution.

    This endpoint:
    1. Fetches the execution details (SQL, parameters, instance, Snowflake config)
    2. Creates a new workflow from the execution's SQL
    3. Creates a schedule attached to that workflow

    Args:
        execution_id: The execution ID to create schedule from
        request: Schedule configuration
        current_user: The authenticated user

    Returns:
        Created workflow and schedule details
    """
    try:
        client = SupabaseManager.get_client(use_service_role=True)

        # Step 1: Get execution with all related data
        # Try to find by execution_id first, then by id (UUID)
        exec_response = client.table('workflow_executions')\
            .select('*, workflows!inner(id, workflow_id, name, sql_query, parameters, instance_id, user_id, amc_instances(id, instance_id, instance_name))')\
            .eq('execution_id', execution_id)\
            .execute()

        # If not found by execution_id, try by id (UUID)
        if not exec_response.data:
            logger.info(f"Execution not found by execution_id, trying by id: {execution_id}")
            exec_response = client.table('workflow_executions')\
                .select('*, workflows!inner(id, workflow_id, name, sql_query, parameters, instance_id, user_id, amc_instances(id, instance_id, instance_name))')\
                .eq('id', execution_id)\
                .execute()

        if not exec_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Get the first (and should be only) result
        execution = exec_response.data[0] if isinstance(exec_response.data, list) else exec_response.data
        workflow_data = execution.get('workflows', {})

        # Verify ownership
        if workflow_data.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")

        # Extract data for new workflow
        sql_query = workflow_data.get('sql_query')
        instance_id = workflow_data.get('instance_id')  # UUID
        execution_parameters = execution.get('execution_parameters', {})
        instance_info = workflow_data.get('amc_instances', {})

        if not sql_query:
            raise HTTPException(status_code=400, detail="Execution has no SQL query")

        if not instance_id:
            raise HTTPException(status_code=400, detail="Execution has no instance")

        # Step 2: Create a new workflow from the execution
        workflow_name = request.name or f"Scheduled Query - {instance_info.get('instance_name', 'Unknown')}"

        new_workflow_data = {
            'id': str(uuid.uuid4()),
            'workflow_id': f"wf_{uuid.uuid4().hex[:8]}",
            'name': workflow_name,
            'description': request.description or f"Created from execution {execution_id}",
            'instance_id': instance_id,
            'sql_query': sql_query,
            'parameters': execution_parameters,
            'user_id': current_user['id'],
            'status': 'active',
            'is_synced_to_amc': False,
            'tags': ['from-execution', 'scheduled'],
        }

        workflow_result = client.table('workflows').insert(new_workflow_data).execute()

        if not workflow_result.data:
            raise HTTPException(status_code=500, detail="Failed to create workflow")

        created_workflow = workflow_result.data[0]
        logger.info(f"Created workflow {created_workflow['workflow_id']} from execution {execution_id}")

        # Step 3: Create schedule for the new workflow
        schedule_service = EnhancedScheduleService()

        # Determine interval_days for certain preset types
        interval_days = None
        if request.preset_type == 'interval':
            interval_days = request.lookback_days

        schedule = schedule_service.create_schedule_from_preset(
            workflow_id=created_workflow['workflow_id'],
            preset_type=request.preset_type,
            user_id=current_user['id'],
            name=request.name,
            description=request.description,
            interval_days=interval_days,
            lookback_days=request.lookback_days,
            timezone=request.timezone,
            execute_time=request.execute_time,
            parameters=execution_parameters,
            snowflake_enabled=request.snowflake_enabled,
            snowflake_table_name=request.snowflake_table_name,
            snowflake_schema_name=request.snowflake_schema_name
        )

        logger.info(f"Created schedule {schedule.get('schedule_id')} for workflow {created_workflow['workflow_id']}")

        return {
            "success": True,
            "message": "Schedule created successfully",
            "workflow": {
                "id": created_workflow['id'],
                "workflow_id": created_workflow['workflow_id'],
                "name": created_workflow['name']
            },
            "schedule": {
                "id": schedule.get('id'),
                "schedule_id": schedule.get('schedule_id'),
                "name": schedule.get('name'),
                "next_run_at": schedule.get('next_run_at'),
                "cron_expression": schedule.get('cron_expression'),
                "timezone": schedule.get('timezone'),
                "snowflake_enabled": schedule.get('snowflake_enabled'),
                "snowflake_table_name": schedule.get('snowflake_table_name')
            }
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating schedule from execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule from execution: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))