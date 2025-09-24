"""
Pydantic schemas for Report Configuration API endpoints
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID


class ReportConfigurationBase(BaseModel):
    """Base model for report configuration"""
    dashboard_type: str = Field(
        ...,
        description="Type of dashboard (funnel, performance, trend, comparison, custom)"
    )
    visualization_settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Settings for visualizations and charts"
    )
    data_aggregation_settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Settings for data aggregation and metrics"
    )
    export_settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Settings for export formats and schedules"
    )
    is_enabled: bool = Field(
        default=True,
        description="Whether the report configuration is enabled"
    )

    @validator('dashboard_type')
    def validate_dashboard_type(cls, v):
        """Validate dashboard type"""
        valid_types = ['funnel', 'performance', 'trend', 'comparison', 'custom']
        if v not in valid_types:
            raise ValueError(f"Dashboard type must be one of: {', '.join(valid_types)}")
        return v


class ReportConfigurationCreate(ReportConfigurationBase):
    """Model for creating a report configuration"""
    workflow_id: Optional[UUID] = Field(
        None,
        description="ID of the workflow to configure reports for"
    )
    query_template_id: Optional[UUID] = Field(
        None,
        description="ID of the query template to configure reports for"
    )

    @root_validator(skip_on_failure=True)
    def validate_ids(cls, values):
        """Validate that exactly one of workflow_id or query_template_id is provided"""
        workflow_id = values.get('workflow_id')
        template_id = values.get('query_template_id')

        if workflow_id and template_id:
            raise ValueError("Provide either workflow_id or query_template_id, not both")
        if not workflow_id and not template_id:
            raise ValueError("Either workflow_id or query_template_id is required")

        return values


class ReportConfigurationUpdate(BaseModel):
    """Model for updating a report configuration"""
    dashboard_type: Optional[str] = Field(
        None,
        description="Type of dashboard"
    )
    visualization_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Settings for visualizations and charts"
    )
    data_aggregation_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Settings for data aggregation and metrics"
    )
    export_settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Settings for export formats and schedules"
    )
    is_enabled: Optional[bool] = Field(
        None,
        description="Whether the report configuration is enabled"
    )

    @validator('dashboard_type')
    def validate_dashboard_type(cls, v):
        """Validate dashboard type if provided"""
        if v is not None:
            valid_types = ['funnel', 'performance', 'trend', 'comparison', 'custom']
            if v not in valid_types:
                raise ValueError(f"Dashboard type must be one of: {', '.join(valid_types)}")
        return v


class ReportConfigurationResponse(ReportConfigurationBase):
    """Model for report configuration response"""
    id: UUID
    workflow_id: Optional[UUID]
    query_template_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    created_by: UUID

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ReportConfigurationListResponse(BaseModel):
    """Model for paginated list of report configurations"""
    data: List[ReportConfigurationResponse]
    total: int
    page: int
    page_size: int


class BatchUpdateRequest(BaseModel):
    """Model for batch update request"""
    configuration_ids: List[UUID] = Field(
        ...,
        description="List of configuration IDs to update"
    )
    is_enabled: bool = Field(
        ...,
        description="New enabled status for all configurations"
    )


class BatchUpdateResponse(BaseModel):
    """Model for batch update response"""
    updated: int = Field(
        ...,
        description="Number of configurations successfully updated"
    )
    failed: int = Field(
        ...,
        description="Number of configurations that failed to update"
    )
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Details of any errors that occurred"
    )


class DashboardViewResponse(BaseModel):
    """Model for dashboard view response"""
    id: UUID
    report_configuration_id: UUID
    view_type: str
    chart_configurations: Optional[Dict[str, Any]]
    filter_settings: Optional[Dict[str, Any]]
    layout_settings: Optional[Dict[str, Any]]
    processed_data: Optional[Dict[str, Any]]
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class DashboardInsightResponse(BaseModel):
    """Model for dashboard insight response"""
    id: UUID
    dashboard_view_id: UUID
    insight_type: str
    insight_text: str
    confidence_score: float
    source_data: Optional[Dict[str, Any]]
    ai_model: Optional[str]
    prompt_version: Optional[str]
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ReportExportResponse(BaseModel):
    """Model for report export response"""
    id: UUID
    report_configuration_id: UUID
    export_type: str
    status: str
    file_url: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class GenerateInsightsRequest(BaseModel):
    """Model for generating insights request"""
    force_refresh: bool = Field(
        default=False,
        description="Force regeneration of insights even if recent ones exist"
    )
    insight_types: Optional[List[str]] = Field(
        default=None,
        description="Specific types of insights to generate"
    )


class GenerateInsightsResponse(BaseModel):
    """Model for async insights generation response"""
    task_id: UUID
    status: str
    message: str


class ExportRequest(BaseModel):
    """Model for export request"""
    format: str = Field(
        ...,
        description="Export format (pdf, png, csv, excel)"
    )
    include_insights: bool = Field(
        default=True,
        description="Include AI insights in export"
    )
    date_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range for data export"
    )

    @validator('format')
    def validate_format(cls, v):
        """Validate export format"""
        valid_formats = ['pdf', 'png', 'csv', 'excel']
        if v not in valid_formats:
            raise ValueError(f"Export format must be one of: {', '.join(valid_formats)}")
        return v


class ExportResponse(BaseModel):
    """Model for async export response"""
    export_id: UUID
    status: str
    message: str