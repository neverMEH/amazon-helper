"""Template Execution API endpoints for immediate and scheduled execution of instance templates"""

from fastapi import APIRouter, HTTPException, Depends, Path, status
from typing import Dict, Any
from datetime import datetime, timezone
import uuid

from ...services.instance_template_service import instance_template_service
from ...services.db_service import db_service
from ...services.token_service import token_service
from ...services.amc_execution_service import amc_execution_service
from ...core.logger_simple import get_logger
from ...core.supabase_client import SupabaseManager
from ...schemas.template_execution import (
    TemplateExecutionRequest,
    TemplateExecutionResponse,
    TemplateScheduleRequest,
    TemplateScheduleResponse,
)
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/instances/{instance_id}/templates/{template_id}/execute",
    response_model=TemplateExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier (tpl_inst_xxx)"),
    request: TemplateExecutionRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Execute an instance template immediately (run once) with specified date range.

    This creates a workflow execution that starts immediately with the template's SQL query.
    No workflow record is created - this is a direct ad-hoc execution.
    """
    try:
        user_id = current_user.get("id")
        logger.info(f"Executing template {template_id} for instance {instance_id}, user {user_id}")

        # 1. Fetch and verify template ownership
        template = instance_template_service.get_template(template_id, user_id)
        if not template:
            logger.warning(f"Template {template_id} not found or access denied for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )

        # Verify template belongs to this instance
        if template.get('instance_id') != instance_id:
            logger.warning(f"Template {template_id} does not belong to instance {instance_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found for this instance"
            )

        # 2. Fetch instance with account details for entity_id
        client = SupabaseManager.get_client()
        instance_response = client.table('amc_instances')\
            .select('*, amc_accounts!inner(*)')\
            .eq('id', instance_id)\
            .single()\
            .execute()

        if not instance_response.data:
            logger.error(f"Instance {instance_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instance not found"
            )

        instance = instance_response.data
        entity_id = instance['amc_accounts']['account_id']
        amc_instance_id = instance['instance_id']  # The AMC string ID (e.g., "amcibersblt")

        # 3. Get valid access token
        valid_token = await token_service.get_valid_token(user_id)
        if not valid_token:
            logger.error(f"No valid token for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid authentication token"
            )

        # 4. Create workflow execution via AMC API
        logger.info(f"Creating AMC execution for template {template['name']} on instance {amc_instance_id}")

        # Use AMC execution service to create execution
        # This handles AMC API communication and database record creation
        from ...services.amc_api_client_with_retry import amc_api_client_with_retry

        execution_result = await amc_api_client_with_retry.create_workflow_execution(
            instance_id=amc_instance_id,
            user_id=user_id,
            entity_id=entity_id,
            sql_query=template['sql_query'],
            time_window_start=request.timeWindowStart,
            time_window_end=request.timeWindowEnd,
            parameters={},  # Templates don't have parameters
        )

        if not execution_result:
            logger.error("AMC API returned empty result")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workflow execution in AMC"
            )

        # 5. Store execution record in database
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        execution_data = {
            'execution_id': execution_id,
            'user_id': user_id,
            'instance_id': instance_id,
            'amc_execution_id': execution_result.get('executionId'),
            'amc_workflow_id': execution_result.get('workflowId'),
            'query_text': template['sql_query'],
            'execution_parameters': {
                'timeWindowStart': request.timeWindowStart,
                'timeWindowEnd': request.timeWindowEnd,
            },
            'status': 'PENDING',
            'triggered_by': 'template_execution',
            'metadata': {
                'execution_name': request.name,
                'template_id': template_id,
                'template_name': template['name'],
                'snowflake_enabled': request.snowflake_enabled,
                'snowflake_table_name': request.snowflake_table_name,
                'snowflake_schema_name': request.snowflake_schema_name,
            }
        }

        # Insert execution record
        exec_response = client.table('workflow_executions').insert(execution_data).execute()

        if not exec_response.data:
            logger.error("Failed to create execution record in database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create execution record"
            )

        execution_record = exec_response.data[0]

        # Increment template usage count
        instance_template_service.increment_usage(template_id)

        logger.info(f"Template execution created successfully: {execution_id}")

        return TemplateExecutionResponse(
            workflow_execution_id=execution_record['execution_id'],
            amc_execution_id=execution_result.get('executionId'),
            status='PENDING',
            created_at=execution_record['created_at'],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute template: {str(e)}"
        )


@router.post(
    "/instances/{instance_id}/templates/{template_id}/schedule",
    response_model=TemplateScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template_schedule(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier (tpl_inst_xxx)"),
    request: TemplateScheduleRequest = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Create a recurring schedule for an instance template.

    This creates a workflow and schedule that will execute the template
    on the specified frequency with rolling date range support.
    """
    try:
        user_id = current_user.get("id")
        logger.info(f"Creating schedule for template {template_id}, instance {instance_id}, user {user_id}")

        # 1. Fetch and verify template ownership
        template = instance_template_service.get_template(template_id, user_id)
        if not template:
            logger.warning(f"Template {template_id} not found or access denied for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or access denied"
            )

        # Verify template belongs to this instance
        if template.get('instance_id') != instance_id:
            logger.warning(f"Template {template_id} does not belong to instance {instance_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found for this instance"
            )

        # 2. Create workflow from template
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        workflow_data = {
            'workflow_id': workflow_id,
            'user_id': user_id,
            'instance_id': instance_id,
            'name': request.name,
            'sql_query': template['sql_query'],
            'description': f"Auto-generated from template: {template['name']}",
            'parameters': {},  # Templates don't have parameters
            'status': 'active',
            'metadata': {
                'source': 'instance_template',
                'template_id': template_id,
                'template_name': template['name'],
            }
        }

        created_workflow = db_service.create_workflow_sync(workflow_data)
        if not created_workflow:
            logger.error("Failed to create workflow from template")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create workflow"
            )

        logger.info(f"Created workflow {workflow_id} from template {template['name']}")

        # 3. Create schedule for the workflow
        schedule_config = request.schedule_config
        schedule_id = f"sched_{uuid.uuid4().hex[:12]}"

        # Build cron expression based on frequency
        cron_expression = _build_cron_expression(
            schedule_config.frequency,
            schedule_config.time,
            schedule_config.day_of_week,
            schedule_config.day_of_month
        )

        schedule_data = {
            'schedule_id': schedule_id,
            'workflow_id': created_workflow['id'],  # Use UUID, not workflow_id string
            'user_id': user_id,
            'name': request.name,
            'schedule_type': schedule_config.frequency,
            'cron_expression': cron_expression,
            'timezone': schedule_config.timezone,
            'lookback_days': schedule_config.lookback_days,
            'date_range_type': schedule_config.date_range_type,
            'window_size_days': schedule_config.window_size_days,
            'default_parameters': {},
            'is_active': True,
            'execution_history_limit': 50,
            'auto_pause_on_failure': False,
            'failure_threshold': 3,
            'consecutive_failures': 0,
        }

        # Add day-specific fields if provided
        if schedule_config.day_of_week is not None:
            schedule_data['day_of_week'] = schedule_config.day_of_week
        if schedule_config.day_of_month is not None:
            schedule_data['day_of_month'] = schedule_config.day_of_month

        client = SupabaseManager.get_client()
        schedule_response = client.table('workflow_schedules').insert(schedule_data).execute()

        if not schedule_response.data:
            logger.error("Failed to create schedule record")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create schedule"
            )

        created_schedule = schedule_response.data[0]

        # Increment template usage count
        instance_template_service.increment_usage(template_id)

        logger.info(f"Created schedule {schedule_id} for template {template['name']}")

        return TemplateScheduleResponse(
            schedule_id=created_schedule['schedule_id'],
            workflow_id=created_workflow['workflow_id'],
            next_run_at=created_schedule.get('next_run_at'),
            created_at=created_schedule['created_at'],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule for template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


def _build_cron_expression(
    frequency: str,
    time: str,
    day_of_week: int = None,
    day_of_month: int = None
) -> str:
    """
    Build a cron expression from schedule configuration.

    Cron format: minute hour day month day_of_week

    Args:
        frequency: 'daily', 'weekly', or 'monthly'
        time: HH:mm format (e.g., '09:00')
        day_of_week: 0-6 (Sunday-Saturday) for weekly schedules
        day_of_month: 1-31 for monthly schedules

    Returns:
        Cron expression string
    """
    # Parse time
    hour, minute = time.split(':')

    if frequency == 'daily':
        # Run every day at specified time
        return f"{minute} {hour} * * *"

    elif frequency == 'weekly':
        # Run on specific day of week at specified time
        dow = day_of_week if day_of_week is not None else 1  # Default to Monday
        return f"{minute} {hour} * * {dow}"

    elif frequency == 'monthly':
        # Run on specific day of month at specified time
        dom = day_of_month if day_of_month is not None else 1  # Default to 1st of month
        return f"{minute} {hour} {dom} * *"

    else:
        raise ValueError(f"Unsupported frequency: {frequency}")
