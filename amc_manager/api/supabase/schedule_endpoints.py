"""REST API endpoints for schedule management"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ...core.logger_simple import get_logger
from ...services.enhanced_schedule_service import EnhancedScheduleService
from ...services.schedule_executor_service import get_schedule_executor
from .auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(tags=["Schedules"])

# Initialize services
schedule_service = EnhancedScheduleService()


# Pydantic models for request/response
class ScheduleCreatePreset(BaseModel):
    """Model for creating a schedule from preset"""
    preset_type: str = Field(..., description="Preset type: daily, interval, weekly, monthly, custom")
    name: Optional[str] = Field(None, description="Custom name for the schedule")
    description: Optional[str] = Field(None, description="Description or notes about the schedule")
    interval_days: Optional[int] = Field(None, description="Days for interval type (1, 3, 7, 14, 30, 60, 90)")
    timezone: str = Field("UTC", description="Timezone for schedule")
    execute_time: str = Field("02:00", description="Time of day to execute (HH:MM)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Default execution parameters")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification settings")


class ScheduleCreateCustom(BaseModel):
    """Model for creating a schedule with custom CRON"""
    cron_expression: str = Field(..., description="CRON expression")
    name: Optional[str] = Field(None, description="Custom name for the schedule")
    description: Optional[str] = Field(None, description="Description or notes about the schedule")
    timezone: str = Field("UTC", description="Timezone for schedule")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Default execution parameters")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification settings")


class ScheduleUpdate(BaseModel):
    """Model for updating a schedule"""
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None
    notification_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    auto_pause_on_failure: Optional[bool] = None
    failure_threshold: Optional[int] = None
    cost_limit: Optional[float] = None


class ScheduleResponse(BaseModel):
    """Model for schedule response"""
    id: Optional[str] = None
    schedule_id: str
    workflow_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    interval_days: Optional[int] = None
    cron_expression: str
    timezone: str
    default_parameters: Optional[Any] = None  # Can be string or dict
    notification_config: Optional[Any] = None  # Can be string or dict
    is_active: bool
    last_run_at: Optional[Any] = None
    next_run_at: Optional[Any] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None
    workflow: Optional[Dict[str, Any]] = None
    brands: Optional[List[str]] = None  # Extracted from workflow.amc_instances.brands
    
    class Config:
        # Allow any field types for flexibility with Supabase responses
        arbitrary_types_allowed = True


class ScheduleRunResponse(BaseModel):
    """Model for schedule run response"""
    id: str
    schedule_id: str
    run_number: int
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    execution_count: int
    successful_count: int
    failed_count: int
    total_rows: int
    total_cost: float
    error_summary: Optional[str]
    workflow_execution_id: Optional[str]


class ScheduleMetricsResponse(BaseModel):
    """Model for schedule metrics response"""
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    avg_runtime_seconds: Optional[float]
    total_rows_processed: int
    total_cost: float
    next_run: Optional[datetime]
    last_run: Optional[datetime]


@router.post("/test-schedule-validation")
async def test_schedule_validation(
    schedule_data: ScheduleCreatePreset
):
    """Test endpoint to validate schedule data"""
    return {"message": "Validation passed", "data": schedule_data.dict()}


@router.post("/workflows/{workflow_id}/schedules")
async def create_schedule_preset(
    workflow_id: str,
    schedule_data: ScheduleCreatePreset,
    current_user: dict = Depends(get_current_user)
):
    """Create a schedule from a preset"""
    try:
        logger.info(f"Creating preset schedule for workflow {workflow_id}")
        logger.info(f"Schedule data received: {schedule_data.dict()}")
        logger.info(f"Current user: {current_user.get('id', 'Unknown')}")
        
        schedule = schedule_service.create_schedule_from_preset(
            workflow_id=workflow_id,
            preset_type=schedule_data.preset_type,
            user_id=current_user['id'],
            name=schedule_data.name,
            description=schedule_data.description,
            interval_days=schedule_data.interval_days,
            timezone=schedule_data.timezone,
            execute_time=schedule_data.execute_time,
            parameters=schedule_data.parameters,
            notification_config=schedule_data.notification_config
        )
        
        # Get the full schedule with workflow data
        if schedule and 'schedule_id' in schedule:
            full_schedule = schedule_service.get_schedule(schedule['schedule_id'])
            return full_schedule if full_schedule else schedule
        
        return schedule
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"ValueError creating schedule: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.post("/workflows/{workflow_id}/schedules/custom", response_model=ScheduleResponse)
async def create_schedule_custom(
    workflow_id: str,
    schedule_data: ScheduleCreateCustom,
    current_user: dict = Depends(get_current_user)
):
    """Create a schedule with custom CRON expression"""
    try:
        logger.info(f"Creating custom schedule for workflow {workflow_id}")
        
        schedule = schedule_service.create_custom_schedule(
            workflow_id=workflow_id,
            cron_expression=schedule_data.cron_expression,
            user_id=current_user['id'],
            name=schedule_data.name,
            description=schedule_data.description,
            timezone=schedule_data.timezone,
            parameters=schedule_data.parameters,
            notification_config=schedule_data.notification_config
        )
        
        return ScheduleResponse(**schedule)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating custom schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/workflows/{workflow_id}/schedules")
async def list_workflow_schedules(
    workflow_id: str,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List schedules for a workflow"""
    try:
        schedules = schedule_service.list_schedules(
            workflow_id=workflow_id,
            user_id=current_user['id'],
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        # Return raw schedules with workflows data included
        return schedules
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list schedules")


@router.get("/schedules")
async def list_all_schedules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List all schedules for the current user"""
    try:
        schedules = schedule_service.list_schedules(
            user_id=current_user['id'],
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        # Return raw schedules with workflows data included
        return schedules
        
    except Exception as e:
        logger.error(f"Error listing schedules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list schedules")


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule details"""
    try:
        schedule = schedule_service.get_schedule(schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Check ownership
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ScheduleResponse(**schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule")


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    updates: ScheduleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update schedule
        updated_schedule = schedule_service.update_schedule(
            schedule_id,
            updates.dict(exclude_unset=True)
        )
        
        if not updated_schedule:
            raise HTTPException(status_code=500, detail="Failed to update schedule")
        
        return ScheduleResponse(**updated_schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete schedule
        success = schedule_service.delete_schedule(schedule_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete schedule")
        
        return {"message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


@router.post("/schedules/{schedule_id}/enable")
async def enable_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Enable a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Enable schedule
        success = schedule_service.enable_schedule(schedule_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to enable schedule")
        
        return {"message": "Schedule enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to enable schedule")


@router.post("/schedules/{schedule_id}/disable")
async def disable_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Disable a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Disable schedule
        success = schedule_service.disable_schedule(schedule_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to disable schedule")
        
        return {"message": "Schedule disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable schedule")


@router.get("/schedules/{schedule_id}/next-runs")
async def get_next_runs(
    schedule_id: str,
    count: int = Query(10, ge=1, le=100, description="Number of next runs to calculate"),
    current_user: dict = Depends(get_current_user)
):
    """Preview next execution times for a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate next runs
        next_runs = schedule_service.calculate_next_runs(schedule_id, count)
        
        return {
            "schedule_id": schedule_id,
            "next_runs": [run.isoformat() for run in next_runs]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating next runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate next runs")


@router.post("/schedules/{schedule_id}/test-run")
async def test_run_schedule(
    schedule_id: str,
    parameters: Optional[Dict[str, Any]] = Body(None, description="Override parameters for test run"),
    current_user: dict = Depends(get_current_user)
):
    """Execute a schedule immediately for testing"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get executor and run schedule
        executor = get_schedule_executor()
        
        # Override parameters if provided
        if parameters:
            schedule['default_parameters'] = parameters
        
        # Execute the schedule
        await executor.execute_schedule(schedule)
        
        return {"message": "Test run initiated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running test schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to run test schedule")


@router.get("/schedules/{schedule_id}/runs", response_model=List[ScheduleRunResponse])
async def get_schedule_runs(
    schedule_id: str,
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get execution history for a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get schedule runs from database
        from ...core.supabase_client import SupabaseManager
        db = SupabaseManager.get_client()
        
        result = db.table('schedule_runs').select(
            '*',
            'workflow_executions(id, amc_execution_id)'
        ).eq(
            'schedule_id', schedule['id']
        ).order('scheduled_at', desc=True).range(offset, offset + limit - 1).execute()
        
        runs = result.data or []
        
        # Process runs to extract workflow_execution_id
        processed_runs = []
        for run in runs:
            # Get the first workflow execution's AMC execution ID if it exists
            workflow_execution_id = None
            try:
                executions = run.get('workflow_executions', [])
                if executions and isinstance(executions, list) and len(executions) > 0:
                    first_execution = executions[0]
                    if isinstance(first_execution, dict):
                        # Use amc_execution_id for AMC API calls, not the internal id
                        workflow_execution_id = first_execution.get('amc_execution_id')
                        if not workflow_execution_id:
                            # Fallback to internal id if amc_execution_id is not available
                            workflow_execution_id = first_execution.get('id')
            except (KeyError, TypeError, IndexError) as e:
                logger.debug(f"Could not extract workflow_execution_id: {e}")
            
            # Remove the nested workflow_executions from the response
            run_data = {k: v for k, v in run.items() if k != 'workflow_executions'}
            run_data['workflow_execution_id'] = workflow_execution_id
            
            try:
                processed_runs.append(ScheduleRunResponse(**run_data))
            except Exception as e:
                logger.error(f"Error processing run {run.get('id', 'unknown')}: {e}")
                # Skip this run if it can't be processed
                continue
        
        return processed_runs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule runs")


@router.get("/schedules/{schedule_id}/metrics", response_model=ScheduleMetricsResponse)
async def get_schedule_metrics(
    schedule_id: str,
    period_days: int = Query(30, ge=1, le=365, description="Period in days for metrics"),
    current_user: dict = Depends(get_current_user)
):
    """Get performance metrics for a schedule"""
    try:
        # Check ownership
        schedule = schedule_service.get_schedule(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if schedule.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate metrics
        from ...core.supabase_client import SupabaseManager
        from datetime import timedelta
        
        db = SupabaseManager.get_client()
        
        # Get runs within period
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        
        result = db.table('schedule_runs').select('*').eq(
            'schedule_id', schedule['id']
        ).gte('scheduled_at', cutoff_date.isoformat()).execute()
        
        runs = result.data or []
        
        # Calculate metrics
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r['status'] == 'completed')
        failed_runs = sum(1 for r in runs if r['status'] == 'failed')
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        # Calculate average runtime
        runtimes = []
        for run in runs:
            if run['status'] == 'completed' and run['started_at'] and run['completed_at']:
                start = datetime.fromisoformat(run['started_at'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(run['completed_at'].replace('Z', '+00:00'))
                runtimes.append((end - start).total_seconds())
        
        avg_runtime = sum(runtimes) / len(runtimes) if runtimes else None
        
        # Sum totals
        total_rows = sum(r.get('total_rows', 0) for r in runs)
        total_cost = sum(r.get('total_cost', 0) for r in runs)
        
        return ScheduleMetricsResponse(
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=success_rate,
            avg_runtime_seconds=avg_runtime,
            total_rows_processed=total_rows,
            total_cost=total_cost,
            next_run=schedule.get('next_run_at'),
            last_run=schedule.get('last_run_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schedule metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule metrics")