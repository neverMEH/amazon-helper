"""
Pydantic schemas for template execution endpoints.

These schemas define the request/response models for immediate template execution
and recurring schedule creation from instance templates.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TemplateExecutionRequest(BaseModel):
    """Request schema for immediate template execution (run once)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Auto-generated execution name: {Brand} - {Template} - {StartDate} - {EndDate}"
    )
    timeWindowStart: str = Field(
        ...,
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="ISO date format: YYYY-MM-DD (e.g., 2025-10-01)"
    )
    timeWindowEnd: str = Field(
        ...,
        pattern=r'^\d{4}-\d{2}-\d{2}$',
        description="ISO date format: YYYY-MM-DD (e.g., 2025-10-31)"
    )
    snowflake_enabled: Optional[bool] = Field(
        default=False,
        description="Whether to upload results to Snowflake after execution"
    )
    snowflake_table_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Snowflake table name (auto-generated if empty)"
    )
    snowflake_schema_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Snowflake schema name (uses default if empty)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nike Brand - Top Products Analysis - 2025-10-01 - 2025-10-31",
                "timeWindowStart": "2025-10-01",
                "timeWindowEnd": "2025-10-31",
                "snowflake_enabled": True,
                "snowflake_table_name": "amc_top_products",
                "snowflake_schema_name": "analytics"
            }
        }


class ScheduleConfigSchema(BaseModel):
    """Configuration schema for recurring schedule creation."""

    frequency: str = Field(
        ...,
        pattern=r'^(daily|weekly|monthly)$',
        description="Schedule frequency: daily, weekly, or monthly"
    )
    time: str = Field(
        ...,
        pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$',
        description="Execution time in HH:mm format (e.g., 09:00)"
    )
    lookback_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Number of days to look back for data (1-365)"
    )
    date_range_type: Optional[str] = Field(
        default=None,
        pattern=r'^(rolling|fixed)$',
        description="How date range is calculated: rolling or fixed"
    )
    window_size_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Explicit window size for clarity (alias for lookback_days)"
    )
    timezone: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Timezone for execution (e.g., America/New_York)"
    )
    day_of_week: Optional[int] = Field(
        default=None,
        ge=0,
        le=6,
        description="For weekly schedules: 0=Sunday, 1=Monday, ..., 6=Saturday"
    )
    day_of_month: Optional[int] = Field(
        default=None,
        ge=1,
        le=31,
        description="For monthly schedules: 1-31"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "frequency": "weekly",
                "time": "09:00",
                "lookback_days": 30,
                "date_range_type": "rolling",
                "window_size_days": 30,
                "timezone": "America/New_York",
                "day_of_week": 1
            }
        }


class TemplateScheduleRequest(BaseModel):
    """Request schema for creating a recurring schedule from a template."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Auto-generated schedule name"
    )
    schedule_config: ScheduleConfigSchema = Field(
        ...,
        description="Schedule configuration details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nike Brand - Weekly Top Products - Rolling 30 Days",
                "schedule_config": {
                    "frequency": "weekly",
                    "time": "09:00",
                    "lookback_days": 30,
                    "date_range_type": "rolling",
                    "timezone": "America/New_York",
                    "day_of_week": 1
                }
            }
        }


class TemplateExecutionResponse(BaseModel):
    """Response schema for immediate template execution."""

    workflow_execution_id: str = Field(
        ...,
        description="UUID of the created workflow execution record"
    )
    amc_execution_id: Optional[str] = Field(
        default=None,
        description="AMC execution ID (null if AMC API call failed)"
    )
    status: str = Field(
        ...,
        description="Execution status: PENDING, RUNNING, COMPLETED, or FAILED"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the execution was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_execution_id": "550e8400-e29b-41d4-a716-446655440000",
                "amc_execution_id": "ae12345678",
                "status": "PENDING",
                "created_at": "2025-10-15T14:30:00Z"
            }
        }


class TemplateScheduleResponse(BaseModel):
    """Response schema for recurring schedule creation."""

    schedule_id: str = Field(
        ...,
        description="Schedule ID (format: sched_<random>)"
    )
    workflow_id: str = Field(
        ...,
        description="Created workflow ID (format: wf_<random>)"
    )
    next_run_at: Optional[datetime] = Field(
        default=None,
        description="ISO 8601 timestamp of next scheduled execution"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the schedule was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sched_123abc456def",
                "workflow_id": "wf_789ghi012jkl",
                "next_run_at": "2025-10-22T09:00:00-04:00",
                "created_at": "2025-10-15T14:30:00Z"
            }
        }
