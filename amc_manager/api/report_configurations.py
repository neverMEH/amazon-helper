"""
Report Configuration API endpoints for enabling/disabling reports on workflows and templates
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks
from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncio
from datetime import datetime

from ..schemas.report_configuration import (
    ReportConfigurationCreate,
    ReportConfigurationUpdate,
    ReportConfigurationResponse,
    ReportConfigurationListResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    DashboardViewResponse,
    DashboardInsightResponse,
    ReportExportResponse,
    GenerateInsightsRequest,
    GenerateInsightsResponse,
    ExportRequest,
    ExportResponse
)
from ..services.report_configuration_service import ReportConfigurationService
from ..services.dashboard_view_service import DashboardViewService
from ..services.dashboard_insight_service import DashboardInsightService
from ..services.report_export_service import ReportExportService
from ..core.logger_simple import get_logger
from .supabase.auth import get_current_user
from ..core.rate_limiter import RateLimiter

logger = get_logger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Report Configurations"])

# Initialize services
report_config_service = ReportConfigurationService()
dashboard_view_service = DashboardViewService()
dashboard_insight_service = DashboardInsightService()
report_export_service = ReportExportService()

# Initialize rate limiter (10 requests per minute for report operations)
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


@router.post("/configure", status_code=status.HTTP_201_CREATED, response_model=ReportConfigurationResponse)
async def create_report_configuration(
    config_data: ReportConfigurationCreate,
    current_user: dict = Depends(get_current_user)
) -> ReportConfigurationResponse:
    """
    Create a new report configuration for a workflow or query template.

    Either workflow_id or query_template_id must be provided, but not both.
    """
    try:
        # Apply rate limiting
        if not rate_limiter.allow_request(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before making another request."
            )

        # Prepare configuration data
        config_dict = config_data.dict(exclude_unset=True)

        # Convert UUIDs to strings for database
        if config_dict.get('workflow_id'):
            config_dict['workflow_id'] = str(config_dict['workflow_id'])
        if config_dict.get('query_template_id'):
            config_dict['query_template_id'] = str(config_dict['query_template_id'])

        # Create the configuration
        result = report_config_service.create_report_config(
            config_data=config_dict,
            user_id=current_user["id"]
        )

        # Convert to response model
        return ReportConfigurationResponse(**result)

    except ValueError as ve:
        logger.error(f"Validation error creating report configuration: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating report configuration: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configurations", response_model=ReportConfigurationListResponse)
async def list_report_configurations(
    dashboard_type: Optional[str] = Query(None, description="Filter by dashboard type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    workflow_id: Optional[UUID] = Query(None, description="Filter by workflow ID"),
    template_id: Optional[UUID] = Query(None, description="Filter by template ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
) -> ReportConfigurationListResponse:
    """
    List all report configurations for the current user with optional filters.
    """
    try:
        result = report_config_service.list_report_configs(
            user_id=current_user["id"],
            dashboard_type=dashboard_type,
            is_enabled=is_enabled,
            workflow_id=str(workflow_id) if workflow_id else None,
            template_id=str(template_id) if template_id else None,
            page=page,
            page_size=page_size
        )

        # Convert to response model
        return ReportConfigurationListResponse(**result)

    except Exception as e:
        logger.error(f"Error listing report configurations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configure/{config_id}", response_model=ReportConfigurationResponse)
async def get_report_configuration(
    config_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> ReportConfigurationResponse:
    """
    Get a specific report configuration by ID.
    """
    try:
        config = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        return ReportConfigurationResponse(**config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/configure/{config_id}", response_model=ReportConfigurationResponse)
async def update_report_configuration(
    config_id: UUID,
    update_data: ReportConfigurationUpdate,
    current_user: dict = Depends(get_current_user)
) -> ReportConfigurationResponse:
    """
    Update a report configuration.
    """
    try:
        # Apply rate limiting
        if not rate_limiter.allow_request(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before making another request."
            )

        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Update the configuration
        update_dict = update_data.dict(exclude_unset=True)
        result = report_config_service.update_report_config(
            config_id=str(config_id),
            update_data=update_dict,
            user_id=current_user["id"]
        )

        return ReportConfigurationResponse(**result)

    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Validation error updating report configuration: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating report configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/configure/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report_configuration(
    config_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a report configuration.
    """
    try:
        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Delete the configuration
        success = report_config_service.delete_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete report configuration"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/configure/{config_id}/toggle", response_model=ReportConfigurationResponse)
async def toggle_report_configuration(
    config_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> ReportConfigurationResponse:
    """
    Toggle the enabled status of a report configuration.
    """
    try:
        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Toggle the status
        result = report_config_service.toggle_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        return ReportConfigurationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling report configuration {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/configure/batch/enable", response_model=BatchUpdateResponse)
async def batch_update_configurations(
    request: BatchUpdateRequest,
    current_user: dict = Depends(get_current_user)
) -> BatchUpdateResponse:
    """
    Batch enable or disable multiple report configurations.
    """
    try:
        # Apply rate limiting
        if not rate_limiter.allow_request(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before making another request."
            )

        # Convert UUIDs to strings
        config_ids = [str(config_id) for config_id in request.configuration_ids]

        # Batch update
        result = report_config_service.batch_update_status(
            config_ids=config_ids,
            is_enabled=request.is_enabled,
            user_id=current_user["id"]
        )

        return BatchUpdateResponse(**result)

    except Exception as e:
        logger.error(f"Error batch updating configurations: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configure/{config_id}/views", response_model=List[DashboardViewResponse])
async def get_dashboard_views(
    config_id: UUID,
    current_user: dict = Depends(get_current_user)
) -> List[DashboardViewResponse]:
    """
    Get all dashboard views for a report configuration.
    """
    try:
        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Get views
        views = dashboard_view_service.get_views_for_configuration(str(config_id))

        return [DashboardViewResponse(**view) for view in views]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard views for config {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configure/{config_id}/insights", response_model=List[DashboardInsightResponse])
async def get_dashboard_insights(
    config_id: UUID,
    insight_type: Optional[str] = Query(None, description="Filter by insight type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of insights"),
    current_user: dict = Depends(get_current_user)
) -> List[DashboardInsightResponse]:
    """
    Get AI-generated insights for a report configuration.
    """
    try:
        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Get insights
        insights = dashboard_insight_service.get_insights_for_configuration(
            config_id=str(config_id),
            insight_type=insight_type,
            limit=limit
        )

        return [DashboardInsightResponse(**insight) for insight in insights]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insights for config {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/configure/{config_id}/insights/generate", status_code=status.HTTP_202_ACCEPTED, response_model=GenerateInsightsResponse)
async def generate_insights_async(
    config_id: UUID,
    request: GenerateInsightsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> GenerateInsightsResponse:
    """
    Asynchronously generate AI insights for a report configuration.
    """
    try:
        # Apply rate limiting
        if not rate_limiter.allow_request(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before making another request."
            )

        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Generate task ID
        task_id = UUID(report_config_service.generate_task_id())

        # Add background task for insight generation
        background_tasks.add_task(
            dashboard_insight_service.generate_insights_async,
            config_id=str(config_id),
            task_id=str(task_id),
            force_refresh=request.force_refresh,
            insight_types=request.insight_types
        )

        return GenerateInsightsResponse(
            task_id=task_id,
            status="processing",
            message="Insight generation started. Check task status for updates."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting insight generation for config {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/configure/{config_id}/exports", response_model=List[ReportExportResponse])
async def get_export_history(
    config_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by export status"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of exports"),
    current_user: dict = Depends(get_current_user)
) -> List[ReportExportResponse]:
    """
    Get export history for a report configuration.
    """
    try:
        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Get exports
        exports = report_export_service.get_exports_for_configuration(
            config_id=str(config_id),
            status=status_filter,
            limit=limit
        )

        return [ReportExportResponse(**export) for export in exports]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exports for config {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/configure/{config_id}/export", status_code=status.HTTP_202_ACCEPTED, response_model=ExportResponse)
async def export_dashboard_async(
    config_id: UUID,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> ExportResponse:
    """
    Asynchronously export a dashboard in the specified format.
    """
    try:
        # Apply rate limiting
        if not rate_limiter.allow_request(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before making another request."
            )

        # Check if configuration exists
        existing = report_config_service.get_report_config(
            config_id=str(config_id),
            user_id=current_user["id"]
        )

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report configuration not found"
            )

        # Create export record
        export_data = {
            "report_configuration_id": str(config_id),
            "export_type": request.format,
            "requested_by": current_user["id"],
            "status": "pending",
            "metadata": {
                "include_insights": request.include_insights,
                "date_range": request.date_range
            }
        }

        export_record = report_export_service.create_export(export_data)

        # Add background task for export generation
        background_tasks.add_task(
            report_export_service.create_export_async,
            export_id=export_record["id"],
            config_id=str(config_id),
            format=request.format,
            include_insights=request.include_insights,
            date_range=request.date_range
        )

        return ExportResponse(
            export_id=UUID(export_record["id"]),
            status="pending",
            message=f"Export generation started. Format: {request.format}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting export for config {config_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))