"""Report Builder API endpoints for the enhanced 4-step flow"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
import json
from croniter import croniter

from ..core.logger_simple import get_logger
from ..schemas.report_builder import (
    ReportBuilderParametersRequest,
    ReportBuilderScheduleRequest,
    ReportBuilderReviewRequest,
    ReportBuilderSubmitRequest,
    ReportBuilderSubmitResponse,
    ReportBuilderAuditCreate,
    LookbackConfig,
    ScheduleConfig,
    BackfillConfig
)
from ..services.db_service import db_service
from ..services.workflow_service import WorkflowService
from ..services.enhanced_schedule_service import EnhancedScheduleService
from ..services.historical_collection_service import historical_collection_service
from ..services.parameter_processor import ParameterProcessor
from .supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/report-builder", tags=["Report Builder"])

# Initialize services
workflow_service = WorkflowService()
schedule_service = EnhancedScheduleService()
parameter_processor = ParameterProcessor()


def calculate_date_range(lookback_config: LookbackConfig) -> Dict[str, Any]:
    """Calculate date range from lookback configuration"""
    if lookback_config.type == 'custom':
        return {
            'start_date': lookback_config.start_date.isoformat(),
            'end_date': lookback_config.end_date.isoformat(),
            'days': (lookback_config.end_date - lookback_config.start_date).days
        }
    else:  # relative
        end_date = date.today()

        if lookback_config.unit == 'months':
            # Approximate months to days
            days = lookback_config.value * 30
        elif lookback_config.unit == 'weeks':
            days = lookback_config.value * 7
        else:  # days
            days = lookback_config.value

        start_date = end_date - timedelta(days=days)

        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        }


def create_cron_expression(schedule_config: ScheduleConfig) -> str:
    """Create CRON expression from schedule configuration"""
    if not schedule_config:
        return None

    # Parse time
    hour, minute = schedule_config.time.split(':')

    if schedule_config.frequency == 'daily':
        return f"{minute} {hour} * * *"
    elif schedule_config.frequency == 'weekly':
        if schedule_config.days_of_week:
            days = ','.join(str(d) for d in schedule_config.days_of_week)
            return f"{minute} {hour} * * {days}"
        else:
            return f"{minute} {hour} * * 1"  # Default to Monday
    elif schedule_config.frequency == 'monthly':
        day = schedule_config.day_of_month or 1
        return f"{minute} {hour} {day} * *"
    else:  # once
        return None


def create_audit_entry(
    user_id: str,
    workflow_id: Optional[str],
    step: str,
    configuration: Dict[str, Any]
):
    """Create an audit trail entry for Report Builder steps"""
    try:
        audit_data = {
            'user_id': user_id,
            'workflow_id': workflow_id,
            'step_completed': step,
            'configuration': configuration
        }

        result = db_service.client.table('report_builder_audit').insert(audit_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Failed to create audit entry: {e}")
        # Don't fail the request if audit fails
        return None


@router.post("/validate-parameters")
async def validate_parameters(
    request: ReportBuilderParametersRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Step 1: Validate parameters and lookback configuration

    This endpoint validates:
    - Workflow exists and user has access
    - Instance exists and user has access
    - Lookback window is within AMC's 14-month limit
    - Parameters are properly formatted
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Verify workflow exists and user has access
        workflow = db_service.get_workflow_by_id_sync(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.get('user_id') != user_id:
            # Check if user has shared access
            if not db_service.user_has_workflow_access_sync(user_id, request.workflow_id):
                raise HTTPException(status_code=403, detail="Access denied to workflow")

        # Verify instance access
        if not db_service.user_has_instance_access_sync(user_id, request.instance_id):
            raise HTTPException(status_code=403, detail="Access denied to instance")

        # Calculate date range
        date_range = calculate_date_range(request.lookback_config)

        # Validate AMC retention limit (14 months ~ 425 days)
        if date_range['days'] > 425:
            raise HTTPException(
                status_code=400,
                detail="Lookback window exceeds AMC's 14-month data retention limit"
            )

        # Process parameters and format SQL
        sql_query = workflow.get('sql_query', '')
        formatted_params = parameter_processor.process_parameters(
            request.parameters,
            sql_query
        )

        # Add date range to parameters
        formatted_params['start_date'] = date_range['start_date']
        formatted_params['end_date'] = date_range['end_date']

        # Format SQL with parameters
        formatted_sql = parameter_processor.format_sql_with_parameters(
            sql_query,
            formatted_params
        )

        # Create audit entry
        create_audit_entry(
            user_id=user_id,
            workflow_id=request.workflow_id,
            step='parameters',
            configuration={
                'lookback_config': request.lookback_config.dict(),
                'parameters': request.parameters,
                'instance_id': request.instance_id
            }
        )

        return {
            'valid': True,
            'formatted_sql': formatted_sql,
            'date_range': date_range,
            'processed_parameters': formatted_params,
            'message': 'Parameters validated successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-schedule")
async def preview_schedule(
    request: ReportBuilderScheduleRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Step 2: Preview schedule configuration

    This endpoint provides:
    - CRON expression for scheduled runs
    - Next 5 execution times
    - Backfill segmentation plan
    - Estimated completion time
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Verify workflow exists
        workflow = db_service.get_workflow_by_id_sync(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        response = {
            'schedule_type': request.schedule_type,
            'workflow_id': request.workflow_id
        }

        if request.schedule_type == 'once':
            # One-time execution
            response.update({
                'estimated_execution_time': '5-10 minutes',
                'next_run': datetime.now().isoformat()
            })

        elif request.schedule_type == 'scheduled':
            # Recurring schedule
            if not request.schedule_config:
                raise HTTPException(status_code=400, detail="Schedule configuration required")

            cron_expr = create_cron_expression(request.schedule_config)
            response.update({
                'frequency': request.schedule_config.frequency,
                'cron_expression': cron_expr,
                'timezone': request.schedule_config.timezone,
                'time': request.schedule_config.time
            })

            # Calculate next 5 runs
            if cron_expr:
                cron = croniter(cron_expr, datetime.now())
                next_runs = []
                for _ in range(5):
                    next_runs.append(cron.get_next(datetime).isoformat())
                response['next_5_runs'] = next_runs

        elif request.schedule_type == 'backfill_with_schedule':
            # Backfill with ongoing schedule
            if not request.backfill_config:
                raise HTTPException(status_code=400, detail="Backfill configuration required")

            # Calculate backfill segments
            if request.backfill_config.segment_type == 'daily':
                total_segments = 365
            elif request.backfill_config.segment_type == 'monthly':
                total_segments = 12
            else:  # weekly
                total_segments = 52

            # Estimate completion time
            segments_per_batch = request.backfill_config.parallel_limit
            total_batches = (total_segments + segments_per_batch - 1) // segments_per_batch
            estimated_hours = total_batches * 0.5  # Assume 30 minutes per batch

            response.update({
                'backfill_info': {
                    'total_segments': total_segments,
                    'segment_type': request.backfill_config.segment_type,
                    'parallel_limit': request.backfill_config.parallel_limit,
                    'estimated_completion_hours': estimated_hours,
                    'total_batches': total_batches
                }
            })

            # Add schedule info if provided
            if request.schedule_config:
                cron_expr = create_cron_expression(request.schedule_config)
                response['schedule_info'] = {
                    'frequency': request.schedule_config.frequency,
                    'cron_expression': cron_expr,
                    'starts_after_backfill': True
                }

        # Create audit entry
        create_audit_entry(
            user_id=user_id,
            workflow_id=request.workflow_id,
            step='schedule',
            configuration={
                'schedule_type': request.schedule_type,
                'schedule_config': request.schedule_config.dict() if request.schedule_config else None,
                'backfill_config': request.backfill_config.dict() if request.backfill_config else None
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit", response_model=ReportBuilderSubmitResponse)
async def submit_report(
    request: ReportBuilderSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> ReportBuilderSubmitResponse:
    """
    Step 4: Submit the report for execution

    This endpoint:
    - Validates all parameters
    - Creates execution/schedule/collection as needed
    - Returns appropriate redirect URL
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Verify workflow and instance access
        workflow = db_service.get_workflow_by_id_sync(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        instance = db_service.get_instance_by_id_sync(request.instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")

        # Validate lookback limit
        date_range = calculate_date_range(request.lookback_config)
        if date_range['days'] > 425:
            raise HTTPException(
                status_code=400,
                detail="Lookback window exceeds AMC's 14-month data retention limit"
            )

        # Process parameters
        formatted_params = parameter_processor.process_parameters(
            request.parameters,
            workflow.get('sql_query', '')
        )
        formatted_params['start_date'] = date_range['start_date']
        formatted_params['end_date'] = date_range['end_date']

        response = ReportBuilderSubmitResponse(
            success=False,
            message="",
            execution_id=None,
            schedule_id=None,
            collection_id=None,
            redirect_url=None
        )

        if request.schedule_type == 'once':
            # Execute immediately
            execution_result = await workflow_service.execute(
                instance_id=request.instance_id,
                workflow_id=request.workflow_id,
                user_id=user_id,
                user_token=current_user.get('tokens', {}),
                parameters=formatted_params
            )

            response.success = True
            response.message = "Report execution started successfully"
            response.execution_id = execution_result.get('execution_id')
            response.redirect_url = f"/executions/{response.execution_id}"

        elif request.schedule_type == 'scheduled':
            # Create recurring schedule
            if not request.schedule_config:
                raise HTTPException(status_code=400, detail="Schedule configuration required")

            cron_expr = create_cron_expression(request.schedule_config)

            schedule_result = await schedule_service.create_schedule(
                user_id=user_id,
                workflow_id=request.workflow_id,
                cron_expression=cron_expr,
                timezone=request.schedule_config.timezone,
                description=f"Scheduled report with {request.schedule_config.frequency} frequency",
                parameters=formatted_params,
                schedule_config=request.schedule_config.dict()
            )

            response.success = True
            response.message = "Schedule created successfully"
            response.schedule_id = schedule_result.get('id')
            response.redirect_url = f"/schedules/{response.schedule_id}"

        elif request.schedule_type == 'backfill_with_schedule':
            # Start backfill and create schedule
            if not request.backfill_config:
                raise HTTPException(status_code=400, detail="Backfill configuration required")

            # Start backfill collection
            collection_result = await historical_collection_service.start_backfill(
                workflow_id=request.workflow_id,
                instance_id=request.instance_id,
                user_id=user_id,
                target_weeks=52,
                collection_type='backfill',
                lookback_config=request.lookback_config.dict(),
                segmentation_config={
                    'type': request.backfill_config.segment_type,
                    'parallel_limit': request.backfill_config.parallel_limit,
                    'retry_failed': True
                }
            )

            response.collection_id = collection_result.get('collection_id')

            # Create schedule for ongoing updates
            if request.schedule_config:
                cron_expr = create_cron_expression(request.schedule_config)

                schedule_result = await schedule_service.create_schedule(
                    user_id=user_id,
                    workflow_id=request.workflow_id,
                    cron_expression=cron_expr,
                    timezone=request.schedule_config.timezone,
                    description=f"Ongoing schedule after backfill",
                    parameters=formatted_params,
                    schedule_config=request.schedule_config.dict(),
                    backfill_status='in_progress',
                    backfill_collection_id=response.collection_id
                )

                response.schedule_id = schedule_result.get('id')

            response.success = True
            response.message = "Backfill started and schedule created successfully"
            response.redirect_url = f"/collections/{response.collection_id}"

        # Create final audit entry
        create_audit_entry(
            user_id=user_id,
            workflow_id=request.workflow_id,
            step='submit',
            configuration={
                'lookback_config': request.lookback_config.dict(),
                'parameters': request.parameters,
                'schedule_type': request.schedule_type,
                'schedule_config': request.schedule_config.dict() if request.schedule_config else None,
                'backfill_config': request.backfill_config.dict() if request.backfill_config else None,
                'execution_id': response.execution_id,
                'schedule_id': response.schedule_id,
                'collection_id': response.collection_id
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review")
async def review_configuration(
    request: ReportBuilderReviewRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Step 3: Review complete configuration before submission

    This endpoint provides:
    - Formatted SQL query with parameters
    - Complete configuration summary
    - Validation of all settings
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get workflow
        workflow = db_service.get_workflow_by_id_sync(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Calculate date range
        date_range = calculate_date_range(request.lookback_config)

        # Process parameters
        formatted_params = parameter_processor.process_parameters(
            request.parameters,
            workflow.get('sql_query', '')
        )
        formatted_params['start_date'] = date_range['start_date']
        formatted_params['end_date'] = date_range['end_date']

        # Format SQL
        formatted_sql = parameter_processor.format_sql_with_parameters(
            workflow.get('sql_query', ''),
            formatted_params
        )

        # Build review summary
        review_summary = {
            'workflow': {
                'id': request.workflow_id,
                'name': workflow.get('name'),
                'description': workflow.get('description')
            },
            'instance_id': request.instance_id,
            'lookback_window': {
                'config': request.lookback_config.dict(),
                'date_range': date_range
            },
            'parameters': formatted_params,
            'formatted_sql': formatted_sql,
            'schedule': {
                'type': request.schedule_type
            }
        }

        # Add schedule details
        if request.schedule_config:
            review_summary['schedule']['configuration'] = request.schedule_config.dict()
            review_summary['schedule']['cron_expression'] = create_cron_expression(request.schedule_config)

        # Add backfill details
        if request.backfill_config:
            total_segments = 52 if request.backfill_config.segment_type == 'weekly' else (
                365 if request.backfill_config.segment_type == 'daily' else 12
            )
            review_summary['backfill'] = {
                'configuration': request.backfill_config.dict(),
                'estimated_segments': total_segments,
                'estimated_hours': (total_segments / request.backfill_config.parallel_limit) * 0.5
            }

        # Create audit entry
        create_audit_entry(
            user_id=user_id,
            workflow_id=request.workflow_id,
            step='review',
            configuration=review_summary
        )

        return review_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))