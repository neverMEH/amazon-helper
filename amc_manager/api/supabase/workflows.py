"""Workflows API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import re

from ...services.db_service import db_service
from ...services.token_service import token_service
from ...services.batch_execution_service import BatchExecutionService
from ...services.parameter_detection_service import ParameterDetectionService
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


# Schedule models - DISABLED: Using schedule_endpoints.py instead
# class ScheduleCreate(BaseModel):
#     cron_expression: str
#     timezone: Optional[str] = "UTC"
#     default_parameters: Optional[Dict[str, Any]] = {}
# 
# 
# class ScheduleUpdate(BaseModel):
#     cron_expression: Optional[str] = None
#     timezone: Optional[str] = None
#     default_parameters: Optional[Dict[str, Any]] = None
#     is_active: Optional[bool] = None


@router.get("/")
def list_workflows(
    instance_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all workflows for the current user"""
    try:
        logger.info(f"Listing workflows for user {current_user['id']}, instance_id filter: {instance_id}")
        
        # Get workflows with instance data
        workflows = db_service.get_user_workflows_sync(current_user['id'])
        logger.info(f"Found {len(workflows)} total workflows for user")
        
        # Get last execution for each workflow
        client = SupabaseManager.get_client()
        
        # CRITICAL: Use UUID 'id' field, not string 'workflow_id'
        # workflow_executions.workflow_id is a foreign key to workflows.id (UUID)
        # See /docs/ID_FIELD_REFERENCE.md for complete ID field documentation
        workflow_uuids = [w['id'] for w in workflows]  # Extract UUIDs
        
        # Fetch last executions for all workflows in one query
        last_executions = {}
        if workflow_uuids:
            # Query executions using UUID foreign key relationship
            exec_response = client.table('workflow_executions')\
                .select('workflow_id, started_at, status')\
                .in_('workflow_id', workflow_uuids)\
                .execute()
            
            # Sort by started_at descending and group by workflow_id
            executions = sorted(exec_response.data or [], 
                              key=lambda x: x.get('started_at', ''), 
                              reverse=True)
            
            # Take the most recent execution for each workflow
            for execution in executions:
                wf_uuid = execution['workflow_id']
                if wf_uuid not in last_executions:
                    last_executions[wf_uuid] = execution['started_at']
        
        # Filter by instance if provided
        if instance_id:
            logger.info(f"Filtering workflows by instance_id: {instance_id}")
            workflows = [w for w in workflows if 'amc_instances' in w and w['amc_instances'].get('instance_id') == instance_id]
            logger.info(f"After filtering: {len(workflows)} workflows for instance {instance_id}")
        
        return [{
            "id": w['id'],  # Return UUID as id for proper database lookups
            "workflow_id": w['workflow_id'],  # Keep string workflow_id for display
            "workflowId": w['workflow_id'],  # Legacy field for compatibility
            "name": w['name'],
            "description": w.get('description'),
            "sqlQuery": w.get('sql_query', ''),
            "parameters": w.get('parameters', {}),
            "instance": {
                "id": w['amc_instances']['instance_id'],
                "instanceId": w['amc_instances']['instance_id'],  # Add this for compatibility
                "instanceName": w['amc_instances']['instance_name']
            } if 'amc_instances' in w else None,
            "status": w.get('status', 'active'),
            "isTemplate": w.get('is_template', False),
            "tags": w.get('tags', []),
            "createdAt": w.get('created_at', ''),
            "updatedAt": w.get('updated_at', ''),
            "lastExecutedAt": last_executions.get(w['id'])  # Use UUID (not workflow_id) to match executions
        } for w in workflows]
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch workflows")


@router.post("/")
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new workflow - saves to AMC first, then syncs to backend

    WORKFLOW CREATION STRATEGY:
    ---------------------------
    1. For template-based workflows:
       - Fetch SQL template with {{placeholders}}
       - Process placeholders to create valid SQL for AMC
       - Store BOTH template SQL (for future params) and processed SQL

    2. For direct SQL workflows:
       - Use provided SQL as-is
       - Still check for placeholders and process if needed

    3. AMC Workflow Creation:
       - Creates a SAVED workflow in AMC (not ad-hoc)
       - Gets a permanent workflow_id
       - Can be executed multiple times with different parameters
       - Executions reference the workflow_id, not SQL directly
    """
    try:
        # Verify user has access to the instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == workflow.instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get the internal instance ID
        instance = next((inst for inst in user_instances if inst['instance_id'] == workflow.instance_id), None)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
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

        # Import needed modules at the top
        import uuid
        import re

        # If template_id is provided and sql_query is empty, fetch SQL from template
        sql_query = workflow.sql_query
        sql_template = None  # Keep original template for reference

        if workflow.template_id and not sql_query:
            from ...services.query_template_service import query_template_service
            template = query_template_service.get_template(workflow.template_id, current_user['id'])
            if template:
                # Get the template SQL
                sql_template = template.get('sql_template') or template.get('sql_query') or ''
                sql_query = sql_template
                logger.info(f"Fetched SQL from template {workflow.template_id}, length: {len(sql_query)}")
            else:
                logger.warning(f"Template {workflow.template_id} not found or access denied")

        if not sql_query:
            raise HTTPException(status_code=400, detail="SQL query is required")

        # Process parameters if SQL has placeholders
        # CRITICAL FOR TEMPLATE-BASED WORKFLOWS:
        # When creating a workflow from a template, the SQL contains placeholders like {{param}}
        # AMC doesn't understand this syntax, so we must process it before submission
        # We provide default values just to create valid SQL for the workflow creation
        # The actual parameter values will be provided during execution
        if '{{' in sql_query:
            from ...utils.parameter_processor import ParameterProcessor

            def _apply_sql_injection(sql_text: str, param_name: str, param_value: Any) -> str:
                """Replace SQL injection placeholder with an inline VALUES clause."""
                values_clause_body = None
                explicit_values = None

                if isinstance(param_value, dict):
                    values_clause_body = param_value.get('_valuesClause')
                    explicit_values = param_value.get('_values')
                    if values_clause_body:
                        values_clause_body = values_clause_body.strip()
                elif isinstance(param_value, list):
                    explicit_values = param_value
                elif param_value not in (None, ''):
                    explicit_values = [param_value]

                if not values_clause_body:
                    values_clause_body = ParameterProcessor.build_values_clause(
                        sql_text,
                        param_name,
                        explicit_values,
                    )

                logger.debug(
                    "Generated VALUES clause for %s (%d rows)",
                    param_name,
                    values_clause_body.count("\n") + 1,
                )

                values_pattern = re.compile(
                    rf'(VALUES\s*)\{{\{{{param_name}\}}\}}',
                    re.IGNORECASE,
                )

                match = values_pattern.search(sql_text)
                if match:
                    line_start = sql_text.rfind('\n', 0, match.start()) + 1
                    indent = sql_text[line_start:match.start()]

                    cte_pattern = re.compile(
                        rf'([A-Za-z_][\w]*)\s*\(([^)]+)\)\s*AS\s*\(\s*VALUES\s*\{{\{{{param_name}\}}\}}',
                        re.IGNORECASE,
                    )
                    cte_match = cte_pattern.search(sql_text)
                    cte_columns = []
                    if cte_match:
                        cte_columns = [c.strip() for c in cte_match.group(2).split(',') if c.strip()]

                    column_count = max(
                        len(cte_columns) or 1,
                        ParameterProcessor._infer_placeholder_column_count(sql_text, param_name),
                    )

                    internal_columns = [f"col{i+1}" for i in range(column_count)]
                    if not cte_columns:
                        cte_columns = [f"{param_name}_{i+1}" for i in range(column_count)]

                    select_assignments = ', '.join(
                        f"{internal_columns[i]} AS {cte_columns[i]}"
                        if i < len(cte_columns)
                        else internal_columns[i]
                        for i in range(column_count)
                    )

                    clause_lines = values_clause_body.splitlines()
                    indented_clause = '\n'.join(
                        indent + '        ' + line.strip()
                        for line in clause_lines
                    )

                    replacement = (
                        f"SELECT {select_assignments}\n"
                        f"{indent}FROM (\n"
                        f"{indent}    VALUES\n"
                        f"{indented_clause}\n"
                        f"{indent}) AS __values_{param_name}({', '.join(internal_columns)})"
                    )

                    return values_pattern.sub(replacement, sql_text, count=1)

                placeholder_regex = re.compile(rf"\{{\{{{param_name}\}}\}}")
                return placeholder_regex.sub(f"VALUES\n{values_clause_body}", sql_text)

            # Use provided parameters or empty defaults for workflow creation
            # This creates a valid SQL for AMC workflow creation
            params_to_use = {}
            provided_params = workflow.parameters or {}

            param_pattern = r'\{\{(\w+)\}\}'
            param_names = list(set(re.findall(param_pattern, sql_query)))
            sql_injection_params = set()

            for param_name in param_names:
                param_value = provided_params.get(param_name)
                values_context = re.search(
                    rf"VALUES\s*\{{\{{{param_name}\}}\}}",
                    sql_query,
                    re.IGNORECASE,
                )

                is_sql_inject = bool(
                    (isinstance(param_value, dict) and param_value.get('_sqlInject'))
                    or values_context
                )

                if is_sql_inject:
                    sql_injection_params.add(param_name)
                    sql_query = _apply_sql_injection(sql_query, param_name, param_value)
                    logger.info(f"Applied SQL injection default for {param_name}")
                    continue

                if param_value and isinstance(param_value, dict) and 'value' in param_value:
                    actual_value = param_value.get('value')
                    if isinstance(actual_value, dict) and actual_value.get('_sqlInject'):
                        sql_injection_params.add(param_name)
                        sql_query = _apply_sql_injection(sql_query, param_name, actual_value)
                        logger.info(f"Applied nested SQL injection default for {param_name}")
                        continue
                    if actual_value not in (None, ''):
                        params_to_use[param_name] = actual_value
                        continue

                if param_name in provided_params and param_name not in params_to_use:
                    params_to_use[param_name] = provided_params[param_name]
                    continue

                # Provide sensible defaults for missing parameters
                default_values = ParameterProcessor.default_values_for(param_name)
                if len(default_values) == 1:
                    params_to_use[param_name] = default_values[0]
                else:
                    params_to_use[param_name] = default_values

            # Remove injection placeholders from params_to_use to avoid accidental substitution
            for injection_param in sql_injection_params:
                params_to_use.pop(injection_param, None)

            # Process the SQL with standard template parameters
            if params_to_use:
                try:
                    sql_query = ParameterProcessor.process_sql_parameters(
                        sql_query,
                        params_to_use,
                        validate_all=False,  # Allow partial processing
                    )
                    logger.info(
                        f"Processed SQL query for AMC workflow creation, final length: {len(sql_query)}"
                    )
                except Exception as e:
                    logger.error(f"Failed to process SQL parameters: {e}")
                    # If processing fails, we'll try with the original SQL
                    pass

        # Generate unique workflow ID for AMC
        base_workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        amc_workflow_id = re.sub(r'[^a-zA-Z0-9._-]', '_', base_workflow_id)

        # Extract parameters from ORIGINAL template SQL (if we have one) for metadata
        # But don't include them in the AMC workflow creation since we've already processed the SQL
        param_pattern = r'\{\{(\w+)\}\}'

        # Check if we used a template and extract params from the original
        param_names = []
        if sql_template:
            param_names = list(set(re.findall(param_pattern, sql_template)))
        elif '{{' not in sql_query:  # Only check processed SQL if we didn't process parameters
            param_names = list(set(re.findall(param_pattern, sql_query)))

        # IMPORTANT: Parameter Strategy for AMC
        # --------------------------------------
        # Check if there are still any unprocessed placeholders in the SQL
        # If yes, we need to declare them as input parameters for AMC
        remaining_placeholders = re.findall(param_pattern, sql_query)

        if remaining_placeholders:
            # Create input parameter declarations for any remaining placeholders
            input_parameters = []
            for param_name in set(remaining_placeholders):
                # Determine parameter type based on name
                param_type = 'STRING'  # Default type
                param_lower = param_name.lower()

                if 'date' in param_lower or 'time' in param_lower:
                    param_type = 'DATE'
                elif 'count' in param_lower or 'number' in param_lower or 'qty' in param_lower:
                    param_type = 'INTEGER'
                elif 'price' in param_lower or 'cost' in param_lower or 'amount' in param_lower:
                    param_type = 'DECIMAL'
                elif 'id' in param_lower and 'product' not in param_lower:
                    param_type = 'STRING'
                # Special case for ad_product_type
                elif param_name == 'ad_product_type':
                    param_type = 'STRING'

                input_parameters.append({
                    'name': param_name,
                    'dataType': param_type,
                    'required': False,
                    'defaultValue': params_to_use.get(param_name, '')
                })

            logger.info(f"Found {len(remaining_placeholders)} unprocessed placeholders, creating input parameters for AMC")
        else:
            # No remaining placeholders, no need for input parameters
            input_parameters = None
            logger.info("All placeholders processed, no input parameters needed for AMC")
        
        # Create SAVED workflow in AMC first
        # This is different from ad-hoc execution:
        # - Ad-hoc: Sends sql_query parameter directly to each execution (no workflow created)
        # - Saved: Creates workflow first, then executions reference the workflow_id
        # We're doing the SAVED approach here for reusability and version control
        from ...services.amc_api_client import AMCAPIClient
        api_client = AMCAPIClient()
        
        amc_response = api_client.create_workflow(
            instance_id=instance['instance_id'],
            workflow_id=amc_workflow_id,
            sql_query=sql_query,
            access_token=valid_token,
            entity_id=entity_id,
            marketplace_id=marketplace_id,
            input_parameters=input_parameters if input_parameters else None,
            output_format=workflow.parameters.get('output_format', 'CSV') if workflow.parameters else 'CSV'
        )
        
        if not amc_response.get('success'):
            logger.error(f"Failed to create workflow in AMC: {amc_response.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create workflow in AMC: {amc_response.get('error')}"
            )
        
        # If template_id is provided, increment its usage count
        if workflow.template_id:
            from ...services.query_template_service import query_template_service
            query_template_service.increment_usage(workflow.template_id)
        
        # Create workflow in backend with AMC workflow ID
        workflow_data = {
            "workflow_id": base_workflow_id,  # Use the base ID as our internal ID
            "name": workflow.name,
            "description": workflow.description,
            "instance_id": instance['id'],  # Use internal UUID
            "sql_query": sql_template or sql_query,  # Store ORIGINAL template SQL if available for execution
            "parameters": workflow.parameters,
            "tags": workflow.tags,
            "user_id": current_user['id'],
            "status": "active",
            "amc_workflow_id": amc_workflow_id,  # Store AMC's workflow ID
            "is_synced_to_amc": True,
            "amc_sync_status": "synced",
            "amc_synced_at": datetime.now(timezone.utc).isoformat(),
        }

        # Note: template_id column isn't present in workflows table yet, so we avoid persisting it here.
        # Add a migration before storing template references directly in the workflows row.
        
        # Use sync version
        created = db_service.create_workflow_sync(workflow_data)
        if not created:
            # Try to delete from AMC if backend creation fails
            logger.error(f"Failed to create workflow in backend, attempting to delete from AMC: {amc_workflow_id}")
            # Note: We'd need a delete_workflow method in AMCAPIClient
            raise HTTPException(status_code=500, detail="Failed to create workflow in backend")
        
        return {
            "id": created['workflow_id'],  # Frontend expects 'id' field
            "workflow_id": created['workflow_id'],
            "name": created['name'],
            "description": created.get('description'),
            "status": created['status'],
            "created_at": created['created_at'],
            "amc_workflow_id": amc_workflow_id,
            "is_synced_to_amc": True
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
        
        # Get last execution for this workflow
        client = SupabaseManager.get_client()
        last_execution = None
        try:
            # Get all executions and sort in Python to avoid order syntax issues
            exec_response = client.table('workflow_executions')\
                .select('started_at')\
                .eq('workflow_id', workflow['id'])\
                .limit(10)\
                .execute()
            
            if exec_response.data:
                # Sort by started_at and take the most recent
                sorted_execs = sorted(exec_response.data, 
                                    key=lambda x: x.get('started_at', ''), 
                                    reverse=True)
                if sorted_execs:
                    last_execution = sorted_execs[0]['started_at']
        except Exception as e:
            logger.warning(f"Could not fetch last execution for workflow {workflow_id}: {e}")
        
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
            "lastExecuted": last_execution  # Use the fetched last execution timestamp
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workflow")


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    updates: WorkflowUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a workflow - updates AMC first if synced, then backend"""
    try:
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # If workflow is synced to AMC and SQL query is being updated, update AMC first
        if workflow.get('amc_workflow_id') and updates.sql_query:
            # Get valid token
            valid_token = await token_service.get_valid_token(current_user['id'])
            if not valid_token:
                raise HTTPException(status_code=401, detail="No valid authentication token")
            
            # Get instance and account details
            instance = workflow.get('amc_instances')
            if not instance:
                raise HTTPException(status_code=400, detail="No AMC instance associated with workflow")
            
            account = instance.get('amc_accounts')
            if not account:
                raise HTTPException(status_code=404, detail="AMC account not found")
            
            entity_id = account['account_id']
            marketplace_id = account['marketplace_id']
            
            # Extract parameters from new SQL query if provided
            import re
            if updates.sql_query:
                param_pattern = r'\{\{(\w+)\}\}'
                param_names = re.findall(param_pattern, updates.sql_query)
                
                # Create input parameter definitions for AMC
                input_parameters = []
                for param_name in param_names:
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
            else:
                input_parameters = None
            
            # Update workflow in AMC
            from ...services.amc_api_client import AMCAPIClient
            api_client = AMCAPIClient()
            
            amc_response = api_client.update_workflow(
                instance_id=instance['instance_id'],
                workflow_id=workflow['amc_workflow_id'],
                sql_query=updates.sql_query,
                access_token=valid_token,
                entity_id=entity_id,
                marketplace_id=marketplace_id,
                input_parameters=input_parameters if input_parameters else None
            )
            
            if not amc_response.get('success'):
                logger.error(f"Failed to update workflow in AMC: {amc_response.get('error')}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update workflow in AMC: {amc_response.get('error')}"
                )
        
        # Prepare updates for backend
        update_data = updates.dict(exclude_none=True)
        if workflow.get('amc_workflow_id'):
            update_data['amc_last_updated_at'] = datetime.now(timezone.utc).isoformat()
        
        updated = db_service.update_workflow_sync(workflow_id, update_data)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update workflow")
        
        return {
            "workflow_id": updated['workflow_id'],
            "name": updated['name'],
            "status": updated['status'],
            "updated_at": updated['updated_at'],
            "amc_workflow_id": updated.get('amc_workflow_id'),
            "is_synced_to_amc": updated.get('is_synced_to_amc', False)
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
async def execute_workflow(
    workflow_id: str,
    body: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a workflow on AMC instance"""
    try:
        # Extract instance_id and parameters from body
        instance_id = body.get('instance_id')
        parameters = {k: v for k, v in body.items() if k not in {'instance_id', 'execution_parameters'}}

        # Support new payload shape where parameters are nested under execution_parameters
        nested_parameters = body.get('execution_parameters')
        if isinstance(nested_parameters, dict):
            # Nested values take precedence over top-level duplicates
            parameters = {**parameters, **nested_parameters}

        logger.info(f"Executing workflow {workflow_id} with instance_id: {instance_id}, parameters: {parameters}")
        
        # The workflow_id parameter here is actually the workflow_id field (e.g., "wf_883e6982")
        # not the UUID id field, so we need to query by workflow_id
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        
        if not workflow:
            logger.error(f"Workflow {workflow_id} not found")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"Found workflow: id={workflow['id']}, workflow_id={workflow['workflow_id']}, name={workflow['name']}, is_template={workflow.get('is_template', False)}")
        
        # Verify ownership
        if workflow['user_id'] != current_user['id']:
            logger.error(f"Access denied: workflow user_id={workflow['user_id']}, current user_id={current_user['id']}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Import here to avoid circular import
        from ...services.amc_execution_service import amc_execution_service
        
        # Execute workflow using AMC execution service
        logger.info(f"Calling execution service with workflow UUID: {workflow['id']}")
        result = await amc_execution_service.execute_workflow(
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
async def get_execution_status(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get execution status"""
    try:
        from ...services.amc_execution_service import amc_execution_service
        
        # Poll AMC for latest status and update database
        status = await amc_execution_service.poll_and_update_execution(execution_id, current_user['id'])
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


# Schedule endpoints - DISABLED: Using schedule_endpoints.py instead
# These endpoints are now handled by schedule_endpoints.py which has more comprehensive functionality
"""
@router.post("/{workflow_id}/schedules")
def create_workflow_schedule(
    workflow_id: str,
    schedule: ScheduleCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    # Create a schedule for a workflow
    try:
        from ...services.enhanced_schedule_service import EnhancedScheduleService
        schedule_service = EnhancedScheduleService()
        
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
    # List schedules for a workflow
    try:
        from ...services.enhanced_schedule_service import EnhancedScheduleService
        schedule_service = EnhancedScheduleService()
        
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
    # Get schedule details
    try:
        from ...services.enhanced_schedule_service import EnhancedScheduleService
        schedule_service = EnhancedScheduleService()
        
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
    # Update a schedule
    try:
        from ...services.enhanced_schedule_service import EnhancedScheduleService
        schedule_service = EnhancedScheduleService()
        
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
    # Delete a schedule
    try:
        from ...services.enhanced_schedule_service import EnhancedScheduleService
        schedule_service = EnhancedScheduleService()
        
        success = schedule_service.delete_schedule(schedule_id, current_user['id'])
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")
"""  # End of commented schedule endpoints

# AMC Workflow Sync Endpoints

@router.post("/{workflow_id}/sync-to-amc")
def sync_workflow_to_amc(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sync a local workflow to AMC, creating it as a SAVED workflow definition

    IMPORTANT: Saved Workflow vs Ad-hoc Execution
    ---------------------------------------------
    This endpoint creates a SAVED WORKFLOW in AMC that can be reused:
    1. Workflow is created once with POST /workflows API
    2. Gets a permanent workflow_id in AMC
    3. Can be executed multiple times with different parameters
    4. Executions reference the workflow_id, not SQL directly

    This is different from ad-hoc execution where:
    - SQL is passed directly to each execution
    - No workflow is created in AMC
    - Each execution is independent
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
        
        # Get executions without order clause, sort in Python
        db_executions_response = client.table('workflow_executions')\
            .select('*')\
            .eq('workflow_id', workflow['id'])\
            .limit(100)\
            .execute()
        
        # Sort by started_at descending and take first 20
        db_executions = sorted(db_executions_response.data or [], 
                              key=lambda x: x.get('started_at', ''), 
                              reverse=True)[:20]
        
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
        
        # Get recent executions without order, sort in Python
        db_executions_response = client.table('workflow_executions')\
            .select('*, workflows!inner(workflow_id, name)')\
            .in_('workflow_id', workflow_ids)\
            .gte('started_at', yesterday.isoformat())\
            .execute()
        
        # Sort by started_at descending
        db_executions = sorted(db_executions_response.data or [], 
                              key=lambda x: x.get('started_at', ''), 
                              reverse=True)
        
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


# Batch Execution Models
class BatchExecuteRequest(BaseModel):
    """Request model for batch execution"""
    instance_ids: List[str]
    parameters: Dict[str, Any] = {}
    instance_parameters: Optional[Dict[str, Dict[str, Any]]] = None
    name: Optional[str] = None
    description: Optional[str] = None


# Batch Execution Endpoints
@router.post("/{workflow_id}/batch-execute")
async def batch_execute_workflow(
    workflow_id: str,
    request: BatchExecuteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute a workflow across multiple AMC instances as a batch.
    
    Args:
        workflow_id: The workflow UUID to execute
        request: Batch execution request containing instance IDs and parameters
        current_user: Authenticated user
        
    Returns:
        Batch execution details with individual execution IDs
    """
    # Input validation
    MAX_BATCH_SIZE = 100  # Match the service constant
    
    if not request.instance_ids:
        raise HTTPException(status_code=400, detail="At least one instance ID must be provided")
    
    if len(request.instance_ids) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Batch size exceeds maximum of {MAX_BATCH_SIZE} instances"
        )
    
    try:
        # Verify user has access to the workflow
        client = SupabaseManager.get_client(use_service_role=True)
        workflow_response = client.table('workflows')\
            .select('*')\
            .eq('id', workflow_id)\
            .eq('user_id', current_user['id'])\
            .single()\
            .execute()
        
        if not workflow_response.data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Verify user has access to all instances
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        user_instance_ids = [inst['id'] for inst in user_instances]
        
        for instance_id in request.instance_ids:
            if instance_id not in user_instance_ids:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied to instance"  # Don't expose instance ID
                )
        
        # Initialize batch execution service
        batch_service = BatchExecutionService()
        
        # Execute batch
        result = await batch_service.execute_batch(
            workflow_id=workflow_id,
            instance_ids=request.instance_ids,
            parameters=request.parameters,
            instance_parameters=request.instance_parameters,
            name=request.name,
            description=request.description,
            user_id=current_user['id']
        )
        
        return {
            'success': True,
            'batch': result
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors from service
        logger.warning(f"Validation error in batch execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing batch workflow: {e}")
        # Don't expose internal error details
        raise HTTPException(status_code=500, detail="Failed to execute batch workflow")


@router.get("/batch/{batch_id}/status")
async def get_batch_execution_status(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the status of a batch execution including all individual executions.
    
    Args:
        batch_id: The batch execution ID (format: batch_XXXXXXXX)
        current_user: Authenticated user
        
    Returns:
        Batch status with individual execution details
    """
    try:
        # Verify user has access to this batch
        client = SupabaseManager.get_client(use_service_role=True)
        batch_response = client.table('batch_executions')\
            .select('*')\
            .eq('batch_id', batch_id)\
            .eq('user_id', current_user['id'])\
            .single()\
            .execute()
        
        if not batch_response.data:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        # Get batch status
        batch_service = BatchExecutionService()
        status = await batch_service.get_batch_status(batch_id)
        
        return {
            'success': True,
            'batch_status': status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@router.get("/batch/{batch_id}/results")
async def get_batch_execution_results(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated results from a batch execution.
    
    Args:
        batch_id: The batch execution ID (format: batch_XXXXXXXX)
        current_user: Authenticated user
        
    Returns:
        Aggregated results with per-instance breakdown
    """
    try:
        # Verify user has access to this batch
        client = SupabaseManager.get_client(use_service_role=True)
        batch_response = client.table('batch_executions')\
            .select('*')\
            .eq('batch_id', batch_id)\
            .eq('user_id', current_user['id'])\
            .single()\
            .execute()
        
        if not batch_response.data:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        # Get batch results
        batch_service = BatchExecutionService()
        results = await batch_service.get_batch_results(batch_id)
        
        return {
            'success': True,
            'batch_results': results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch results: {str(e)}")


@router.post("/batch/{batch_id}/cancel")
async def cancel_batch_execution(
    batch_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a batch execution and all its child executions.
    
    Args:
        batch_id: The batch execution ID to cancel
        current_user: Authenticated user
        
    Returns:
        Cancellation status
    """
    try:
        # Verify user has access to this batch
        client = SupabaseManager.get_client(use_service_role=True)
        batch_response = client.table('batch_executions')\
            .select('*')\
            .eq('batch_id', batch_id)\
            .eq('user_id', current_user['id'])\
            .single()\
            .execute()
        
        if not batch_response.data:
            raise HTTPException(status_code=404, detail="Batch execution not found")
        
        # Cancel the batch
        batch_service = BatchExecutionService()
        cancelled = await batch_service.cancel_batch_execution(batch_id)
        
        return {
            'success': cancelled,
            'message': 'Batch execution cancelled successfully' if cancelled else 'Failed to cancel batch'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling batch execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel batch: {str(e)}")


@router.get("/batch/list")
async def list_batch_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List batch executions with optional filters.
    
    Args:
        workflow_id: Optional workflow UUID to filter by
        status: Optional status to filter by
        limit: Maximum number of results
        offset: Offset for pagination
        current_user: Authenticated user
        
    Returns:
        List of batch execution records
    """
    try:
        batch_service = BatchExecutionService()
        batches = await batch_service.list_batch_executions(
            workflow_id=workflow_id,
            user_id=current_user['id'],
            status=status,
            limit=limit,
            offset=offset
        )
        
        return {
            'success': True,
            'batch_executions': batches,
            'total': len(batches)
        }
        
    except Exception as e:
        logger.error(f"Error listing batch executions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list batch executions: {str(e)}")


@router.get("/{workflow_id}/parameters")
async def detect_workflow_parameters(
    workflow_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Detect and classify parameters in a workflow's SQL query.
    
    Args:
        workflow_id: The workflow UUID
        current_user: Authenticated user
        
    Returns:
        List of detected parameters with their types and positions
    """
    try:
        # Get workflow to verify ownership
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Detect parameters in the SQL query
        detection_service = ParameterDetectionService()
        parameters = detection_service.detect_parameters(workflow['sql_query'])
        
        return {
            'success': True,
            'parameters': parameters,
            'workflow_id': workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting parameters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect parameters: {str(e)}")


@router.post("/{workflow_id}/validate-parameters")
async def validate_workflow_parameters(
    workflow_id: str,
    parameters: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate parameter values for a workflow execution.
    
    Args:
        workflow_id: The workflow UUID
        parameters: Dictionary of parameter values to validate
        current_user: Authenticated user
        
    Returns:
        Validation results with formatted parameters
    """
    try:
        # Get workflow to verify ownership
        workflow = db_service.get_workflow_by_id_sync(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Validate parameters
        detection_service = ParameterDetectionService()
        validation_result = detection_service.validate_parameters(parameters)
        
        if not validation_result['valid']:
            raise HTTPException(
                status_code=422,
                detail={
                    'message': 'Parameter validation failed',
                    'errors': validation_result['errors']
                }
            )
        
        return {
            'success': True,
            'valid': validation_result['valid'],
            'formatted_parameters': validation_result['formatted_parameters'],
            'workflow_id': workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating parameters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate parameters: {str(e)}")
