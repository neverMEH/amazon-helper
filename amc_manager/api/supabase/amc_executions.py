"""AMC Executions API endpoints for fetching workflow executions directly from AMC

Note: The AMC API /workflows endpoint returns workflow executions (historical runs),
not workflow definitions. Each execution represents a past run of a workflow."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import logging

from ...services.amc_execution_service import amc_execution_service
from ...services.db_service import db_service
from ...services.token_service import token_service
from ...services.data_analysis_service import data_analysis_service
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
            
            # Build enhanced execution object
            enhanced_exec = {
                **amc_exec,
                'instanceId': instance_id,
                'workflowExecutionId': exec_id or amc_exec.get('id'),
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
        
        # Get associated brands for the instance
        brands = db_service.get_brands_for_instance_sync(instance_id)
        
        # Try to fetch execution details from our database
        client = SupabaseManager.get_client(use_service_role=True)
        
        db_execution = None
        workflow_info = None
        
        try:
            # First try to find by AMC execution ID
            db_response = client.table('workflow_executions')\
                .select('*, workflows!inner(workflow_id, name, description, sql_query, parameters, created_at, updated_at)')\
                .eq('amc_execution_id', execution_id)\
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
                'errorMessage': db_execution.get('error_message')
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