"""
Snowflake Sync Monitoring API Endpoints
Provides endpoints for monitoring and managing universal Snowflake sync operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from pydantic import BaseModel

from ..core.auth import get_current_user
from ..core.supabase_client import SupabaseManager
from ..core.logger_simple import get_logger
from ..services.universal_snowflake_sync_service import universal_snowflake_sync_service

logger = get_logger(__name__)
router = APIRouter(prefix="/snowflake-sync", tags=["Snowflake Sync"])


class SyncStatsResponse(BaseModel):
    """Response model for sync statistics"""
    pending: Dict[str, Any]
    processing: Dict[str, Any]
    completed: Dict[str, Any]
    failed: Dict[str, Any]


class FailedSyncResponse(BaseModel):
    """Response model for failed sync details"""
    id: str
    execution_id: str
    user_email: str
    workflow_name: str
    error_message: str
    retry_count: int
    created_at: str
    updated_at: str


class RetrySyncResponse(BaseModel):
    """Response model for retry operation"""
    success: bool
    message: str


@router.get("/stats", response_model=SyncStatsResponse)
async def get_sync_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SyncStatsResponse:
    """Get Snowflake sync queue statistics"""
    try:
        stats = await universal_snowflake_sync_service.get_sync_stats()
        
        # Ensure all statuses are present with default values
        default_stats = {
            'count': 0,
            'oldest_item': None,
            'newest_item': None,
            'avg_retries': 0
        }
        
        return SyncStatsResponse(
            pending=stats.get('pending', default_stats),
            processing=stats.get('processing', default_stats),
            completed=stats.get('completed', default_stats),
            failed=stats.get('failed', default_stats)
        )
        
    except Exception as e:
        logger.error(f"Error getting sync stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync statistics"
        )


@router.get("/failed", response_model=List[FailedSyncResponse])
async def get_failed_syncs(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[FailedSyncResponse]:
    """Get list of failed Snowflake syncs"""
    try:
        failed_syncs = await universal_snowflake_sync_service.get_failed_syncs(limit)
        
        return [
            FailedSyncResponse(
                id=sync['id'],
                execution_id=sync['execution_id'],
                user_email=sync['user_email'],
                workflow_name=sync['workflow_name'],
                error_message=sync['error_message'] or 'Unknown error',
                retry_count=sync['retry_count'],
                created_at=sync['created_at'],
                updated_at=sync['updated_at']
            )
            for sync in failed_syncs
        ]
        
    except Exception as e:
        logger.error(f"Error getting failed syncs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get failed syncs"
        )


@router.post("/retry/{sync_id}", response_model=RetrySyncResponse)
async def retry_failed_sync(
    sync_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> RetrySyncResponse:
    """Retry a failed Snowflake sync"""
    try:
        success = await universal_snowflake_sync_service.retry_failed_sync(sync_id)
        
        if success:
            return RetrySyncResponse(
                success=True,
                message=f"Sync {sync_id} queued for retry"
            )
        else:
            return RetrySyncResponse(
                success=False,
                message=f"Failed to retry sync {sync_id}"
            )
            
    except Exception as e:
        logger.error(f"Error retrying sync {sync_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry sync {sync_id}"
        )


@router.get("/queue")
async def get_sync_queue(
    status_filter: str = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get sync queue items with optional status filter"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        query = client.table('snowflake_sync_queue')\
            .select('*, workflow_executions(*), users(email)')\
            .order('created_at', desc=True)\
            .limit(limit)
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        response = query.execute()
        
        return {
            'items': response.data or [],
            'total_count': len(response.data or [])
        }
        
    except Exception as e:
        logger.error(f"Error getting sync queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sync queue"
        )


@router.get("/execution/{execution_id}/sync-status")
async def get_execution_sync_status(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get Snowflake sync status for a specific execution"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get execution details
        execution_response = client.table('workflow_executions')\
            .select('*, workflows!inner(user_id, name)')\
            .eq('execution_id', execution_id)\
            .execute()
        
        if not execution_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution not found"
            )
        
        execution = execution_response.data[0]
        
        # Verify user has access
        if execution['workflows']['user_id'] != current_user['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get sync queue status
        sync_response = client.table('snowflake_sync_queue')\
            .select('*')\
            .eq('execution_id', execution_id)\
            .execute()
        
        sync_item = sync_response.data[0] if sync_response.data else None
        
        return {
            'execution_id': execution_id,
            'workflow_name': execution['workflows']['name'],
            'execution_status': execution['status'],
            'snowflake_enabled': execution.get('snowflake_enabled', False),
            'snowflake_status': execution.get('snowflake_status'),
            'snowflake_table_name': execution.get('snowflake_table_name'),
            'snowflake_uploaded_at': execution.get('snowflake_uploaded_at'),
            'snowflake_row_count': execution.get('snowflake_row_count'),
            'sync_queue_status': sync_item['status'] if sync_item else None,
            'sync_queue_retry_count': sync_item['retry_count'] if sync_item else None,
            'sync_queue_error': sync_item['error_message'] if sync_item else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution sync status"
        )


@router.post("/backfill")
async def backfill_existing_executions(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Manually trigger sync for existing completed executions"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get completed executions that haven't been synced yet
        response = client.table('workflow_executions')\
            .select('execution_id, workflows!inner(user_id)')\
            .eq('status', 'completed')\
            .not_.is_('result_rows', 'null')\
            .gt('result_total_rows', 0)\
            .eq('workflows.user_id', current_user['id'])\
            .not_.in_('execution_id', 
                     client.table('snowflake_sync_queue')
                     .select('execution_id')
                     .execute()
                     .data or []) \
            .limit(100)\
            .execute()
        
        executions = response.data or []
        
        if not executions:
            return {
                'message': 'No executions found that need syncing',
                'queued_count': 0
            }
        
        # Queue executions for sync
        queue_items = []
        for execution in executions:
            queue_items.append({
                'execution_id': execution['execution_id'],
                'user_id': current_user['id'],
                'status': 'pending'
            })
        
        if queue_items:
            client.table('snowflake_sync_queue').insert(queue_items).execute()
        
        return {
            'message': f'Queued {len(queue_items)} executions for Snowflake sync',
            'queued_count': len(queue_items)
        }
        
    except Exception as e:
        logger.error(f"Error backfilling executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to backfill executions"
        )
