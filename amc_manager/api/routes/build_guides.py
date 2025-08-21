"""Build Guides API Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ...core.logger_simple import get_logger
from ...services.build_guide_service import BuildGuideService
from ..supabase.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/build-guides", tags=["Build Guides"])

# Initialize services
build_guide_service = BuildGuideService()


class GuideProgressUpdate(BaseModel):
    """Model for updating guide progress"""
    section_id: Optional[str] = None
    query_id: Optional[str] = None
    mark_complete: bool = False


class GuideQueryExecution(BaseModel):
    """Model for executing a guide query"""
    instance_id: str
    parameters: Dict[str, Any] = {}


@router.get("/")
async def list_guides(
    category: Optional[str] = Query(None, description="Filter by category"),
    show_unpublished: bool = Query(False, description="Include unpublished guides (admin only)"),
    current_user: dict = Depends(get_current_user)
):
    """List all available build guides"""
    try:
        # Check admin status for unpublished guides
        is_published = not show_unpublished or not current_user.get('is_admin', False)
        
        guides = await build_guide_service.list_guides(
            user_id=current_user['id'],
            category=category,
            is_published=is_published
        )
        
        return guides
        
    except Exception as e:
        logger.error(f"Error listing guides: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_guide_categories(current_user: dict = Depends(get_current_user)):
    """Get all available guide categories"""
    try:
        categories = await build_guide_service.get_guide_categories()
        return categories
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/progress")
async def get_user_progress(current_user: dict = Depends(get_current_user)):
    """Get user's progress on all guides"""
    try:
        progress = await build_guide_service.get_user_progress(current_user['id'])
        return progress
        
    except Exception as e:
        logger.error(f"Error getting user progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{guide_id}")
async def get_guide(
    guide_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific guide with all its content"""
    try:
        guide = await build_guide_service.get_guide(
            guide_id=guide_id,
            user_id=current_user['id']
        )
        
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        # Check if guide is published or user is admin
        if not guide.get('is_published', False) and not current_user.get('is_admin', False):
            raise HTTPException(status_code=403, detail="Guide is not published")
        
        return guide
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guide {guide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{guide_id}/queries")
async def get_guide_queries(
    guide_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all queries for a specific guide"""
    try:
        guide = await build_guide_service.get_guide(
            guide_id=guide_id,
            user_id=current_user['id']
        )
        
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        return guide.get('queries', [])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting guide queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{guide_id}/start")
async def start_guide(
    guide_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start or resume a guide"""
    try:
        progress = await build_guide_service.start_guide(
            guide_id=guide_id,
            user_id=current_user['id']
        )
        
        return progress
        
    except Exception as e:
        logger.error(f"Error starting guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{guide_id}/progress")
async def update_guide_progress(
    guide_id: str,
    update: GuideProgressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update progress on a guide"""
    try:
        progress = await build_guide_service.update_progress(
            guide_id=guide_id,
            user_id=current_user['id'],
            section_id=update.section_id,
            query_id=update.query_id,
            mark_complete=update.mark_complete
        )
        
        return progress
        
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{guide_id}/queries/{query_id}/execute")
async def execute_guide_query(
    guide_id: str,
    query_id: str,
    execution: GuideQueryExecution,
    current_user: dict = Depends(get_current_user)
):
    """Execute a query from a guide"""
    try:
        # Get the guide query
        guide = await build_guide_service.get_guide(guide_id, current_user['id'])
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        # Find the specific query
        query = next((q for q in guide.get('queries', []) if q['id'] == query_id), None)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found in guide")
        
        # Update guide progress to mark query as executed
        await build_guide_service.update_progress(
            guide_id=guide_id,
            user_id=current_user['id'],
            query_id=query_id
        )
        
        # Return the query details for frontend to handle execution
        return {
            'query': {
                'title': query['title'],
                'sql_query': query['sql_query'],
                'parameters': execution.parameters,
                'instance_id': execution.instance_id
            },
            'status': 'ready_to_execute',
            'message': 'Query prepared for execution in Query Builder'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error preparing guide query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{guide_id}/queries/{query_id}/create-template")
async def create_template_from_query(
    guide_id: str,
    query_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a reusable template from a guide query"""
    try:
        template = await build_guide_service.create_guide_query_template(
            guide_id=guide_id,
            query_id=query_id,
            user_id=current_user['id']
        )
        
        if not template:
            raise HTTPException(status_code=500, detail="Failed to create template")
        
        return template
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{guide_id}/favorite")
async def toggle_guide_favorite(
    guide_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Toggle favorite status for a guide"""
    try:
        is_favorite = await build_guide_service.toggle_favorite(
            guide_id=guide_id,
            user_id=current_user['id']
        )
        
        return {'is_favorite': is_favorite}
        
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{guide_id}/sections/{section_id}")
async def get_guide_section(
    guide_id: str,
    section_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific section of a guide"""
    try:
        guide = await build_guide_service.get_guide(
            guide_id=guide_id,
            user_id=current_user['id']
        )
        
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        section = next((s for s in guide.get('sections', []) if s['section_id'] == section_id), None)
        if not section:
            raise HTTPException(status_code=404, detail="Section not found")
        
        return section
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting section: {e}")
        raise HTTPException(status_code=500, detail=str(e))