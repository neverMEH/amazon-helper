"""Report Builder API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from ...services.report_service import ReportService
from ...services.report_execution_service import ReportExecutionService
from ...services.report_schedule_service import ReportScheduleService
from ...services.report_backfill_service import ReportBackfillService
from ...services.query_template_service import query_template_service
from ...utils.parameter_processor import ParameterProcessor
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()

# Initialize services
report_service = ReportService()
execution_service = ReportExecutionService()
schedule_service = ReportScheduleService()
backfill_service = ReportBackfillService()


# Pydantic models for request/response
class ReportCreate(BaseModel):
    """Model for creating a report"""
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    template_id: str = Field(..., description="Query template ID")
    instance_id: str = Field(..., description="AMC instance ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    frequency: Optional[str] = Field(None, description="Report frequency")
    create_dashboard: bool = Field(False, description="Create dashboard with report")


class ReportUpdate(BaseModel):
    """Model for updating a report"""
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    frequency: Optional[str] = None
    is_active: Optional[bool] = None


class ReportExecute(BaseModel):
    """Model for executing a report"""
    parameters: Optional[Dict[str, Any]] = Field(None, description="Override parameters")
    time_window_start: Optional[str] = Field(None, description="Start of time window")
    time_window_end: Optional[str] = Field(None, description="End of time window")


class ScheduleCreate(BaseModel):
    """Model for creating a schedule"""
    schedule_type: str = Field(..., description="Schedule type (daily, weekly, monthly)")
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field("UTC", description="Timezone")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    is_active: bool = Field(True, description="Schedule active status")


class BackfillCreate(BaseModel):
    """Model for creating a backfill"""
    start_date: str = Field(..., description="Start date for backfill")
    end_date: str = Field(..., description="End date for backfill")
    segment_type: str = Field("daily", description="Segment type (daily, weekly, monthly)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Override parameters")


class DashboardLink(BaseModel):
    """Model for linking dashboard"""
    dashboard_id: str = Field(..., description="Dashboard ID to link")


# Report CRUD endpoints
@router.get("/")
async def list_reports(
    instance_id: Optional[str] = Query(None, description="Filter by AMC instance"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all reports for the current user"""
    try:
        result = report_service.list_reports(
            user_id=current_user["id"],
            instance_id=instance_id,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific report with details"""
    try:
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Check if user has access to this report
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    report_data: ReportCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new report"""
    try:
        # Create report with or without dashboard
        if report_data.create_dashboard:
            result = report_service.create_report_with_dashboard({
                "owner_id": current_user["id"],
                "name": report_data.name,
                "description": report_data.description,
                "template_id": report_data.template_id,
                "instance_id": report_data.instance_id,
                "parameters": report_data.parameters,
                "frequency": report_data.frequency
            })
        else:
            result = report_service.create_report({
                "owner_id": current_user["id"],
                "name": report_data.name,
                "description": report_data.description,
                "template_id": report_data.template_id,
                "instance_id": report_data.instance_id,
                "parameters": report_data.parameters,
                "frequency": report_data.frequency
            })

        return result
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{report_id}")
async def update_report(
    report_id: str,
    update_data: ReportUpdate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update report
        updated_report = report_service.update_report(
            report_id=report_id,
            update_data=update_data.dict(exclude_unset=True)
        )

        return updated_report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete report
        report_service.delete_report(report_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Execution endpoints
@router.post("/{report_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_report(
    report_id: str,
    execution_data: ReportExecute,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a report ad-hoc"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get the template SQL
        template = query_template_service.get_template(report["template_id"])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Debug logging for template
        logger.info(f"Template ID: {report.get('template_id')}")
        logger.info(f"Template found: {template is not None}")
        logger.info(f"Template keys: {list(template.keys()) if template else 'None'}")

        # Check for sql_template or sql_query field
        sql_query = template.get("sql_template") or template.get("sql_query") or ""
        logger.info(f"SQL field name check - sql_template: {template.get('sql_template') is not None}, sql_query: {template.get('sql_query') is not None}")
        logger.info(f"Raw SQL query length: {len(sql_query)}")

        if not sql_query:
            logger.error(f"Template {report['template_id']} has no SQL query!")
            logger.error(f"Template data: {template}")
            raise HTTPException(status_code=500, detail="Template has no SQL query")

        # Merge report parameters with execution parameters
        final_parameters = {**report.get("parameters", {})}
        if execution_data.parameters:
            final_parameters.update(execution_data.parameters)

        logger.info(f"Final parameters: {final_parameters}")

        # DEBUG: Check parameter values for quotes
        for key, value in final_parameters.items():
            if isinstance(value, str):
                if value.startswith("'") and value.endswith("'"):
                    logger.warning(f"PARAMETER DEBUG: '{key}' is pre-quoted: {repr(value)}")
                if value.startswith("''") or value.endswith("''"):
                    logger.error(f"PARAMETER ERROR: '{key}' has double quotes: {repr(value)}")

        # Process the SQL query with parameters using shared processor
        try:
            processed_sql = ParameterProcessor.process_sql_parameters(
                sql_query,
                final_parameters
            )
            logger.info(f"ParameterProcessor returned SQL of length: {len(processed_sql) if processed_sql else 0}")
            if processed_sql:
                logger.info(f"First 200 chars of processed SQL: {processed_sql[:200]}")

                # DEBUG: Check for double quotes in processed SQL
                import re
                date_patterns = re.findall(r"event_date\s*[><=]+\s*'[^']*'", processed_sql)
                if date_patterns:
                    logger.info(f"DATE PATTERN DEBUG: Found date clauses: {date_patterns}")
                    for pattern in date_patterns:
                        if "''" in pattern:
                            logger.error(f"DOUBLE QUOTE ERROR in processed SQL: {pattern}")
        except Exception as e:
            logger.error(f"Error processing SQL parameters: {e}")
            processed_sql = sql_query  # Fall back to raw SQL
            logger.info(f"Falling back to raw SQL due to parameter processing error")

        logger.info(f"Executing report {report_id}")
        logger.info(f"Template SQL length: {len(sql_query)}")
        logger.info(f"Processed SQL length: {len(processed_sql) if processed_sql else 0}")
        logger.info(f"Time window: {execution_data.time_window_start} to {execution_data.time_window_end}")

        # Get instance details for entity_id
        instance = report_service.get_instance_with_entity(report["instance_id"])
        if not instance:
            raise HTTPException(status_code=404, detail="AMC instance not found")

        # Execute report with processed SQL
        execution = await execution_service.execute_report_adhoc(
            report_id=report_id,
            instance_id=instance["instance_id"],  # AMC instance ID string
            sql_query=processed_sql,
            parameters=final_parameters,
            user_id=current_user["id"],
            entity_id=instance["entity_id"],
            time_window_start=execution_data.time_window_start,
            time_window_end=execution_data.time_window_end
        )

        return execution
    except ValueError as ve:
        # Parameter processing errors
        logger.error(f"Parameter processing error for report {report_id}: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/executions")
async def list_executions(
    report_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Limit results"),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List executions for a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get executions
        executions = report_service.list_executions(
            report_id=report_id,
            status=status,
            limit=limit
        )

        return executions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions for report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get execution details"""
    try:
        execution = report_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Check if user has access to this execution's report
        report = report_service.get_report_with_details(execution["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel a pending or running execution"""
    try:
        # Get execution to check ownership
        execution = report_service.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Check if user owns the report
        report = report_service.get_report_with_details(execution["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Cancel execution
        result = await execution_service.cancel_execution(execution_id)
        if result:
            return {"message": "Execution cancelled"}
        else:
            raise HTTPException(status_code=400, detail="Cannot cancel execution")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Schedule endpoints
@router.post("/{report_id}/schedules", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    report_id: str,
    schedule_data: ScheduleCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a schedule for a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create schedule
        schedule = schedule_service.create_schedule(
            report_id=report_id,
            schedule_type=schedule_data.schedule_type,
            cron_expression=schedule_data.cron_expression,
            timezone=schedule_data.timezone,
            default_parameters=schedule_data.default_parameters,
            is_active=schedule_data.is_active
        )

        return schedule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule for report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/schedules")
async def list_schedules(
    report_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List schedules for a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get schedules
        schedules = schedule_service.list_schedules(report_id)

        return schedules
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing schedules for report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Pause a schedule"""
    try:
        # Get schedule and check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check if user owns the report
        report = report_service.get_report_with_details(schedule["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Pause schedule
        result = schedule_service.pause_schedule(schedule_id)

        return {"message": "Schedule paused", "schedule": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Resume a paused schedule"""
    try:
        # Get schedule and check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check if user owns the report
        report = report_service.get_report_with_details(schedule["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Resume schedule
        result = schedule_service.resume_schedule(schedule_id)

        return {"message": "Schedule resumed", "schedule": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        # Get schedule and check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Check if user owns the report
        report = report_service.get_report_with_details(schedule["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete schedule
        schedule_service.delete_schedule(schedule_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Template endpoints for reports
@router.get("/templates/")
async def list_report_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List available report templates"""
    try:
        templates = query_template_service.list_report_templates(
            user_id=current_user["id"],
            category=category,
            report_type=report_type
        )
        return templates
    except Exception as e:
        logger.error(f"Error listing report templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific template with report metadata"""
    try:
        template = query_template_service.get_template_with_report_config(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Metadata endpoints
@router.get("/overview")
async def get_report_overview(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get overview of all reports for the user"""
    try:
        overview = report_service.get_user_report_overview(current_user["id"])
        return overview
    except Exception as e:
        logger.error(f"Error getting report overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_execution_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for stats"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get execution statistics for reports"""
    try:
        stats = report_service.get_execution_stats(
            user_id=current_user["id"],
            days=days
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting execution stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard integration endpoints
@router.post("/{report_id}/dashboard")
async def link_dashboard(
    report_id: str,
    link_data: DashboardLink,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Link a dashboard to a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Link dashboard
        result = report_service.link_dashboard(
            report_id=report_id,
            dashboard_id=link_data.dashboard_id
        )

        return {"message": "Dashboard linked", "report": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking dashboard to report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}/dashboard", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_dashboard(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unlink dashboard from a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Unlink dashboard
        report_service.unlink_dashboard(report_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking dashboard from report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Backfill endpoints
@router.post("/{report_id}/backfill", status_code=status.HTTP_202_ACCEPTED)
async def create_backfill(
    report_id: str,
    backfill_data: BackfillCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a backfill job for a report"""
    try:
        # Check if user owns the report
        report = report_service.get_report_with_details(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create backfill
        backfill = await backfill_service.create_backfill(
            report_id=report_id,
            user_id=current_user["id"],
            start_date=backfill_data.start_date,
            end_date=backfill_data.end_date,
            segment_type=backfill_data.segment_type,
            parameters=backfill_data.parameters
        )

        return backfill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backfill for report {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backfill/{backfill_id}")
async def get_backfill_progress(
    backfill_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get backfill progress"""
    try:
        progress = backfill_service.get_backfill_progress(backfill_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Backfill not found")

        # Check if user has access
        report = report_service.get_report_with_details(progress["report_id"])
        if report["owner_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backfill progress {backfill_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))