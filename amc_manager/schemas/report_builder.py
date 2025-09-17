"""Pydantic schemas for Report Builder Flow Update"""

from typing import Optional, Dict, Any, List, Literal
from datetime import date, datetime
from pydantic import BaseModel, Field, validator


class LookbackConfig(BaseModel):
    """Lookback window configuration for report data collections"""
    type: Literal['relative', 'custom'] = Field(..., description="Type of lookback: relative or custom")
    value: Optional[int] = Field(None, description="Number for relative lookback (e.g., 7, 14, 30)")
    unit: Optional[Literal['days', 'weeks', 'months']] = Field('days', description="Unit for relative lookback")
    start_date: Optional[date] = Field(None, description="Start date for custom lookback")
    end_date: Optional[date] = Field(None, description="End date for custom lookback")

    @validator('value')
    def validate_value_for_relative(cls, v, values):
        if values.get('type') == 'relative' and v is None:
            raise ValueError('Value is required for relative lookback type')
        return v

    @validator('start_date')
    def validate_dates_for_custom(cls, v, values):
        if values.get('type') == 'custom' and v is None:
            raise ValueError('Start date is required for custom lookback type')
        return v

    @validator('end_date')
    def validate_end_date_for_custom(cls, v, values):
        if values.get('type') == 'custom' and v is None:
            raise ValueError('End date is required for custom lookback type')
        if values.get('start_date') and v and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('value')
    def validate_amc_retention_limit(cls, v, values):
        """Validate that lookback doesn't exceed AMC's 14-month (425 days) retention limit"""
        if values.get('type') == 'relative' and v:
            if values.get('unit') == 'months' and v > 14:
                raise ValueError('Lookback cannot exceed 14 months (AMC retention limit)')
            elif values.get('unit') == 'weeks' and v > 60:
                raise ValueError('Lookback cannot exceed 60 weeks (AMC retention limit)')
            elif values.get('unit') == 'days' and v > 425:
                raise ValueError('Lookback cannot exceed 425 days (AMC retention limit)')
        return v


class SegmentationConfig(BaseModel):
    """Segmentation configuration for data collection backfill"""
    type: Literal['daily', 'weekly', 'monthly'] = Field('weekly', description="Segmentation granularity")
    parallel_limit: int = Field(10, ge=1, le=10, description="Number of parallel segments to process")
    retry_failed: bool = Field(True, description="Whether to retry failed segments automatically")


class ScheduleConfig(BaseModel):
    """Enhanced schedule configuration for workflow schedules"""
    frequency: Literal['once', 'daily', 'weekly', 'monthly'] = Field(..., description="Schedule frequency")
    time: Optional[str] = Field(None, description="Time of day in HH:MM format")
    timezone: str = Field('America/New_York', description="Timezone for schedule")
    days_of_week: Optional[List[int]] = Field(None, description="Days of week for weekly schedules (1=Mon, 7=Sun)")
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="Day of month for monthly schedules")

    @validator('time')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('Time must be in HH:MM format')
        return v

    @validator('days_of_week')
    def validate_days_of_week(cls, v, values):
        if values.get('frequency') == 'weekly' and v:
            for day in v:
                if day < 1 or day > 7:
                    raise ValueError('Days of week must be between 1 (Monday) and 7 (Sunday)')
        return v


class BackfillConfig(BaseModel):
    """Configuration for 365-day historical backfill"""
    enabled: bool = Field(False, description="Whether backfill is enabled")
    segment_type: Literal['daily', 'weekly', 'monthly'] = Field('weekly', description="How to segment the backfill")
    parallel_limit: int = Field(5, ge=1, le=10, description="Number of parallel backfills")
    include_current: bool = Field(True, description="Include current period in backfill")


class ReportBuilderAudit(BaseModel):
    """Audit trail entry for Report Builder flow"""
    user_id: str = Field(..., description="User ID")
    workflow_id: Optional[str] = Field(None, description="Associated workflow ID")
    step_completed: Literal['parameters', 'schedule', 'review', 'submit'] = Field(..., description="Completed step")
    configuration: Dict[str, Any] = Field(..., description="Configuration for this step")


class ReportBuilderAuditCreate(ReportBuilderAudit):
    """Create request for Report Builder audit entry"""
    pass


class ReportBuilderValidateRequest(BaseModel):
    """Request for validating report builder parameters"""
    workflow_id: str = Field(..., description="Workflow ID to validate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    lookback_config: LookbackConfig = Field(..., description="Lookback window configuration")


class ReportBuilderPreviewRequest(BaseModel):
    """Request for previewing schedule configuration"""
    workflow_id: str = Field(..., description="Workflow ID")
    instance_id: str = Field(..., description="AMC instance ID")
    lookback_config: LookbackConfig = Field(..., description="Lookback window configuration")
    schedule_config: ScheduleConfig = Field(..., description="Schedule configuration")


class ReportBuilderSubmitRequest(BaseModel):
    """Request for submitting report builder configuration"""
    workflow_id: str = Field(..., description="Workflow ID")
    instance_id: str = Field(..., description="AMC instance ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")
    lookback_config: LookbackConfig = Field(..., description="Lookback window configuration")
    schedule_config: ScheduleConfig = Field(..., description="Schedule configuration")
    backfill_config: Optional[BackfillConfig] = Field(None, description="Backfill configuration if applicable")


class ReportBuilderAuditResponse(ReportBuilderAudit):
    """Response model for Report Builder audit entry"""
    id: str
    created_at: datetime


class CollectionCreateWithLookback(BaseModel):
    """Enhanced data collection creation with lookback config"""
    workflow_id: str = Field(..., description="UUID of the workflow to execute")
    instance_id: str = Field(..., description="UUID of the AMC instance")
    lookback_config: LookbackConfig = Field(..., description="Lookback window configuration")
    segmentation_config: Optional[SegmentationConfig] = Field(None, description="Segmentation configuration")
    collection_type: Literal['backfill', 'weekly_update', 'custom'] = Field('custom', description="Type of collection")


class WorkflowScheduleCreateWithBackfill(BaseModel):
    """Enhanced workflow schedule creation with backfill support"""
    workflow_id: str = Field(..., description="UUID of the workflow to schedule")
    schedule_config: ScheduleConfig = Field(..., description="Schedule configuration")
    backfill_config: Optional[BackfillConfig] = Field(None, description="Backfill configuration")
    is_active: bool = Field(True, description="Whether schedule is active")


class WorkflowScheduleUpdateWithBackfill(BaseModel):
    """Update model for workflow schedule with backfill"""
    schedule_config: Optional[ScheduleConfig] = None
    backfill_status: Optional[Literal['pending', 'in_progress', 'completed', 'failed', 'partial']] = None
    backfill_collection_id: Optional[str] = None
    is_active: Optional[bool] = None


class ReportBuilderParametersRequest(BaseModel):
    """Request for Report Builder Step 1: Parameters"""
    workflow_id: str
    instance_id: str
    lookback_config: LookbackConfig
    parameters: Dict[str, Any] = Field(default_factory=dict, description="AMC query parameters")


class ReportBuilderScheduleRequest(BaseModel):
    """Request for Report Builder Step 2: Schedule"""
    workflow_id: str
    schedule_type: Literal['once', 'scheduled', 'backfill_with_schedule']
    schedule_config: Optional[ScheduleConfig] = None
    backfill_config: Optional[BackfillConfig] = None


class ReportBuilderReviewRequest(BaseModel):
    """Request for Report Builder Step 3: Review"""
    workflow_id: str
    instance_id: str
    lookback_config: LookbackConfig
    parameters: Dict[str, Any]
    schedule_type: Literal['once', 'scheduled', 'backfill_with_schedule']
    schedule_config: Optional[ScheduleConfig] = None
    backfill_config: Optional[BackfillConfig] = None
    preview_sql: Optional[str] = None


class ReportBuilderSubmitRequest(BaseModel):
    """Request for Report Builder Step 4: Submit"""
    workflow_id: str
    instance_id: str
    lookback_config: LookbackConfig
    parameters: Dict[str, Any]
    schedule_type: Literal['once', 'scheduled', 'backfill_with_schedule']
    schedule_config: Optional[ScheduleConfig] = None
    backfill_config: Optional[BackfillConfig] = None


class ReportBuilderSubmitResponse(BaseModel):
    """Response for Report Builder submission"""
    success: bool
    message: str
    execution_id: Optional[str] = None
    schedule_id: Optional[str] = None
    collection_id: Optional[str] = None
    redirect_url: Optional[str] = None