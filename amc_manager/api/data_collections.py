"""Data Collections API endpoints for historical data backfill"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
import asyncio

from ..core.logger_simple import get_logger
from ..services.historical_collection_service import historical_collection_service
from ..services.reporting_database_service import reporting_db_service
from ..services.db_service import db_service
from ..api.supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(tags=["data-collections"])


class CollectionCreate(BaseModel):
    """Request model for creating a data collection"""
    workflow_id: str = Field(..., description="UUID of the workflow to execute")
    instance_id: str = Field(..., description="UUID of the AMC instance")
    target_weeks: int = Field(52, ge=1, le=52, description="Number of weeks to collect")
    end_date: Optional[date] = Field(None, description="End date for collection (defaults to 14 days ago)")
    collection_type: str = Field("backfill", description="Type of collection: backfill or weekly_update")
    
    @validator('collection_type')
    def validate_collection_type(cls, v):
        if v not in ['backfill', 'weekly_update']:
            raise ValueError('Collection type must be either backfill or weekly_update')
        return v


class CollectionPause(BaseModel):
    """Request model for pausing/resuming a collection"""
    action: str = Field(..., description="Action to perform: pause or resume")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['pause', 'resume']:
            raise ValueError('Action must be either pause or resume')
        return v


class CollectionResponse(BaseModel):
    """Response model for collection operations"""
    collection_id: str
    status: str
    target_weeks: int
    start_date: str
    end_date: str
    instance_id: Optional[str] = None
    progress_percentage: Optional[int] = 0
    weeks_completed: Optional[int] = 0
    message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CollectionProgress(BaseModel):
    """Detailed progress model for a collection"""
    collection_id: str
    status: str
    progress_percentage: int
    instance_id: Optional[str] = None
    statistics: Dict[str, int]
    next_week: Optional[Dict[str, str]]
    weeks: List[Dict[str, Any]]
    started_at: str
    updated_at: str


@router.post("/", response_model=CollectionResponse)
async def create_data_collection(
    collection_data: CollectionCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> CollectionResponse:
    """
    Start a new historical data collection (52-week backfill)
    
    This endpoint initiates a background process to collect historical data
    for a workflow, executing it week-by-week to build up historical data.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Verify user has access to the workflow
        workflow = db_service.get_workflow_by_id_sync(collection_data.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied to workflow")
        
        # Verify user has access to the instance
        if not db_service.user_has_instance_access_sync(user_id, collection_data.instance_id):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Start the backfill process
        result = await historical_collection_service.start_backfill(
            workflow_id=collection_data.workflow_id,
            instance_id=collection_data.instance_id,
            user_id=user_id,
            target_weeks=collection_data.target_weeks,
            end_date=collection_data.end_date,
            collection_type=collection_data.collection_type
        )
        
        # Add background task to start processing (optional - can be handled by separate service)
        # background_tasks.add_task(process_collection, result['collection_id'])
        
        return CollectionResponse(
            collection_id=result['collection_id'],
            status=result['status'],
            target_weeks=result['target_weeks'],
            start_date=result['start_date'],
            end_date=result['end_date'],
            message=result.get('message', 'Collection started successfully')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CollectionResponse])
async def list_data_collections(
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
) -> List[CollectionResponse]:
    """
    List all data collections for the current user
    
    Returns a list of all data collection jobs initiated by the user,
    with optional filtering by status or workflow.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get user's collections
        collections = reporting_db_service.get_user_collections(user_id, status)
        
        # Filter by workflow if specified
        if workflow_id:
            collections = [c for c in collections if c.get('workflow_id') == workflow_id]
        
        # Limit results
        collections = collections[:limit]
        
        # Format response
        response = []
        for collection in collections:
            response.append(CollectionResponse(
                collection_id=collection['collection_id'],
                status=collection['status'],
                target_weeks=collection['target_weeks'],
                start_date=collection['start_date'].isoformat() if isinstance(collection['start_date'], date) else collection['start_date'],
                end_date=collection['end_date'].isoformat() if isinstance(collection['end_date'], date) else collection['end_date'],
                instance_id=collection.get('amc_instance_id') or collection.get('instance_id'),
                progress_percentage=collection.get('progress_percentage', 0),
                weeks_completed=collection.get('weeks_completed', 0),
                created_at=collection.get('created_at'),
                updated_at=collection.get('updated_at')
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing data collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{collection_id}", response_model=CollectionProgress)
async def get_collection_progress(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> CollectionProgress:
    """
    Get detailed progress for a specific data collection
    
    Returns comprehensive progress information including week-by-week status,
    completion statistics, and next scheduled week.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection details
        collection = reporting_db_service.get_collection_status(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Verify user owns the collection
        if collection.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to collection")
        
        # Get detailed progress
        progress = await historical_collection_service.get_collection_progress(collection_id)
        
        return CollectionProgress(
            collection_id=progress['collection_id'],
            status=progress['status'],
            progress_percentage=progress['progress_percentage'],
            instance_id=collection.get('instance_id'),
            statistics=progress['statistics'],
            next_week=progress['next_week'],
            weeks=progress['weeks'],
            started_at=progress['started_at'],
            updated_at=progress['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{collection_id}/pause")
async def pause_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Pause an active data collection
    
    Pauses a running collection, which can be resumed later.
    Week executions currently in progress will complete.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection details
        collection = reporting_db_service.get_collection_status(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Verify user owns the collection
        if collection.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to collection")
        
        # Check if collection is pauseable
        if collection['status'] not in ['pending', 'running']:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot pause collection in status: {collection['status']}"
            )
        
        # Pause the collection
        success = await historical_collection_service.pause_collection(collection_id)
        
        if success:
            return {"message": "Collection paused successfully", "status": "paused"}
        else:
            raise HTTPException(status_code=500, detail="Failed to pause collection")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{collection_id}/resume")
async def resume_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Resume a paused data collection
    
    Resumes a previously paused collection from where it left off.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection details
        collection = reporting_db_service.get_collection_status(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Verify user owns the collection
        if collection.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to collection")
        
        # Check if collection is resumeable
        if collection['status'] != 'paused':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resume collection in status: {collection['status']}"
            )
        
        # Resume the collection
        success = await historical_collection_service.resume_collection(collection_id)
        
        if success:
            return {"message": "Collection resumed successfully", "status": "pending"}
        else:
            raise HTTPException(status_code=500, detail="Failed to resume collection")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{collection_id}")
async def cancel_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Cancel and delete a data collection
    
    Cancels an active collection and removes it from the system.
    This action cannot be undone.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection details
        collection = reporting_db_service.get_collection_status(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Verify user owns the collection
        if collection.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to collection")
        
        # Update status to cancelled
        reporting_db_service.update_collection_progress(
            collection_id,
            {'status': 'cancelled', 'error_message': 'Cancelled by user'}
        )
        
        return {"message": "Collection cancelled successfully", "status": "cancelled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{collection_id}/retry-failed")
async def retry_failed_weeks(
    collection_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retry failed weeks in a collection
    
    Identifies and retries any weeks that failed during the collection process.
    """
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Get collection details
        collection = reporting_db_service.get_collection_status(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Verify user owns the collection
        if collection.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to collection")
        
        # Get failed weeks
        weeks_query = reporting_db_service.client.table('report_data_weeks')\
            .select('*')\
            .eq('collection_id', collection['id'])\
            .eq('status', 'failed')\
            .execute()
        
        failed_weeks = weeks_query.data or []
        
        if not failed_weeks:
            return {
                "message": "No failed weeks to retry",
                "failed_count": 0,
                "retrying": []
            }
        
        # Update failed weeks to pending for retry
        for week in failed_weeks:
            reporting_db_service.update_week_status(
                week['id'],
                'pending',
                error_message=None
            )
        
        # Update collection status if it was failed
        if collection['status'] == 'failed':
            reporting_db_service.update_collection_progress(
                collection_id,
                {'status': 'pending'}
            )
        
        return {
            "message": f"Retrying {len(failed_weeks)} failed weeks",
            "failed_count": len(failed_weeks),
            "retrying": [
                {
                    "week_start": week['week_start_date'],
                    "week_end": week['week_end_date']
                }
                for week in failed_weeks
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying failed weeks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function for background processing (optional)
async def process_collection(collection_id: str):
    """
    Background task to process a collection
    This would typically be handled by a separate background service
    """
    try:
        logger.info(f"Starting background processing for collection {collection_id}")
        # The actual processing would be done by the background executor service
        # This is just a placeholder for the API endpoint
    except Exception as e:
        logger.error(f"Error in background collection processing: {e}")