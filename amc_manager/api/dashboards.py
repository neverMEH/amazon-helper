"""Dashboard Management API endpoints for Reports & Analytics Platform"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ..services.reporting_database_service import ReportingDatabaseService
from ..core.logger_simple import get_logger
from .supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix='/api/dashboards', tags=['dashboards'])


# ========== Pydantic Models ==========

class DashboardCreate(BaseModel):
    """Model for creating a new dashboard"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    layout_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    filter_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_public: bool = Field(default=False)
    is_template: bool = Field(default=False)
    template_type: Optional[str] = Field(None, max_length=50)


class DashboardUpdate(BaseModel):
    """Model for updating an existing dashboard"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    layout_config: Optional[Dict[str, Any]] = None
    filter_config: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_template: Optional[bool] = None
    template_type: Optional[str] = Field(None, max_length=50)


class DashboardResponse(BaseModel):
    """Model for dashboard response"""
    id: str
    dashboard_id: str
    user_id: str
    name: str
    description: Optional[str]
    category: Optional[str]
    layout_config: Dict[str, Any]
    filter_config: Dict[str, Any]
    is_public: bool
    is_template: bool
    template_type: Optional[str]
    created_at: datetime
    updated_at: datetime
    widgets: Optional[List[Dict[str, Any]]] = None
    is_shared: Optional[bool] = False
    shared_by: Optional[str] = None
    permission_level: Optional[str] = None


class DashboardShareRequest(BaseModel):
    """Model for sharing a dashboard"""
    shared_with_user_id: str
    permission_level: str = Field(default='view', pattern='^(view|edit|admin)$')


class DashboardShareResponse(BaseModel):
    """Model for dashboard share response"""
    id: str
    dashboard_id: str
    owner_id: str
    shared_with_user_id: str
    permission_level: str
    created_at: datetime
    shared_with_email: Optional[str] = None


# ========== Initialize Service ==========

db_service = ReportingDatabaseService()


# ========== Endpoints ==========

@router.get('/', response_model=List[DashboardResponse])
async def get_dashboards(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = Query(None, description='Search in name and description'),
    category: Optional[str] = Query(None, description='Filter by category'),
    include_shared: bool = Query(True, description='Include shared dashboards'),
    include_templates: bool = Query(False, description='Include dashboard templates'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> List[DashboardResponse]:
    """
    Get all dashboards for the current user with optional filtering.
    
    Returns both owned dashboards and optionally shared dashboards.
    """
    try:
        user_id = current_user.get('id')
        
        # Get dashboards from database
        dashboards = db_service.get_user_dashboards(user_id, include_shared=include_shared)
        
        if not dashboards:
            return []
        
        # Apply filters
        filtered = dashboards
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered = [
                d for d in filtered
                if search_lower in d.get('name', '').lower() or
                   search_lower in d.get('description', '').lower()
            ]
        
        # Category filter
        if category:
            filtered = [d for d in filtered if d.get('category') == category]
        
        # Template filter
        if not include_templates:
            filtered = [d for d in filtered if not d.get('is_template', False)]
        
        # Apply pagination
        paginated = filtered[offset:offset + limit]
        
        # Format response
        response = []
        for dashboard in paginated:
            dashboard_response = DashboardResponse(**dashboard)
            
            # Check if this is a shared dashboard
            if dashboard.get('user_id') != user_id:
                dashboard_response.is_shared = True
                dashboard_response.shared_by = dashboard.get('user_id')
                # Permission level would come from dashboard_shares table
                dashboard_response.permission_level = 'view'  # Default for now
            
            response.append(dashboard_response)
        
        return response
        
    except Exception as e:
        logger.error(f'Error fetching dashboards: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch dashboards: {str(e)}'
        )


@router.post('/', response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard: DashboardCreate,
    current_user: dict = Depends(get_current_user)
) -> DashboardResponse:
    """
    Create a new dashboard for the current user.
    """
    try:
        user_id = current_user.get('id')
        
        # Prepare dashboard data
        dashboard_data = {
            'user_id': user_id,
            'name': dashboard.name,
            'description': dashboard.description,
            'category': dashboard.category,
            'layout_config': dashboard.layout_config,
            'filter_config': dashboard.filter_config,
            'is_public': dashboard.is_public,
            'is_template': dashboard.is_template,
            'template_type': dashboard.template_type
        }
        
        # Create dashboard in database
        created_dashboard = db_service.create_dashboard(dashboard_data)
        
        if not created_dashboard:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to create dashboard'
            )
        
        return DashboardResponse(**created_dashboard)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error creating dashboard: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create dashboard: {str(e)}'
        )


@router.get('/{dashboard_id}', response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
) -> DashboardResponse:
    """
    Get a specific dashboard with all its widgets.
    
    Validates that the user has access to the dashboard (owner or shared).
    """
    try:
        user_id = current_user.get('id')
        
        # Check access permissions
        can_access, access_type = db_service.user_can_access_dashboard(user_id, dashboard_id)
        
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have access to this dashboard'
            )
        
        # Get dashboard with widgets
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        # Format response
        response = DashboardResponse(**dashboard)
        
        # Add sharing info if applicable
        if access_type == 'shared':
            response.is_shared = True
            response.shared_by = dashboard.get('user_id')
            
            # Get permission level from shares
            shares = db_service.get_dashboard_shares(dashboard_id)
            for share in shares:
                if share.get('shared_with_user_id') == user_id:
                    response.permission_level = share.get('permission_level', 'view')
                    break
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching dashboard {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch dashboard: {str(e)}'
        )


@router.put('/{dashboard_id}', response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: str,
    updates: DashboardUpdate,
    current_user: dict = Depends(get_current_user)
) -> DashboardResponse:
    """
    Update an existing dashboard.
    
    Only the owner or users with 'edit' or 'admin' permissions can update.
    """
    try:
        user_id = current_user.get('id')
        
        # Check access permissions
        can_access, access_type = db_service.user_can_access_dashboard(user_id, dashboard_id)
        
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have access to this dashboard'
            )
        
        # If shared, check permission level
        if access_type == 'shared':
            shares = db_service.get_dashboard_shares(dashboard_id)
            user_share = next((s for s in shares if s.get('shared_with_user_id') == user_id), None)
            
            if not user_share or user_share.get('permission_level') == 'view':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='You do not have permission to edit this dashboard'
                )
        
        # Prepare update data
        update_data = updates.dict(exclude_unset=True)
        
        # Update dashboard
        updated_dashboard = db_service.update_dashboard(dashboard_id, update_data)
        
        if not updated_dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found or update failed'
            )
        
        # Get full dashboard with widgets for response
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        return DashboardResponse(**dashboard)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error updating dashboard {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to update dashboard: {str(e)}'
        )


@router.delete('/{dashboard_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a dashboard and all its associated widgets.
    
    Only the owner can delete a dashboard.
    """
    try:
        user_id = current_user.get('id')
        
        # Get dashboard to check ownership
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        # Check ownership
        if dashboard.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only the owner can delete this dashboard'
            )
        
        # Delete dashboard (cascade deletes widgets)
        success = db_service.delete_dashboard(dashboard_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to delete dashboard'
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting dashboard {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete dashboard: {str(e)}'
        )


# ========== Sharing Endpoints ==========

@router.post('/{dashboard_id}/share', response_model=DashboardShareResponse, status_code=status.HTTP_201_CREATED)
async def share_dashboard(
    dashboard_id: str,
    share_request: DashboardShareRequest,
    current_user: dict = Depends(get_current_user)
) -> DashboardShareResponse:
    """
    Share a dashboard with another user.
    
    Only the owner can share their dashboard.
    """
    try:
        user_id = current_user.get('id')
        
        # Get dashboard to check ownership
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        # Check ownership
        if dashboard.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only the owner can share this dashboard'
            )
        
        # Share the dashboard
        share_result = db_service.share_dashboard(
            dashboard_id=dashboard_id,
            owner_id=user_id,
            shared_with_user_id=share_request.shared_with_user_id,
            permission_level=share_request.permission_level
        )
        
        if not share_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to share dashboard'
            )
        
        return DashboardShareResponse(**share_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error sharing dashboard {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to share dashboard: {str(e)}'
        )


@router.get('/{dashboard_id}/shares', response_model=List[DashboardShareResponse])
async def get_dashboard_shares(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[DashboardShareResponse]:
    """
    Get all shares for a dashboard.
    
    Only the owner can view dashboard shares.
    """
    try:
        user_id = current_user.get('id')
        
        # Get dashboard to check ownership
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        # Check ownership
        if dashboard.get('user_id') != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only the owner can view dashboard shares'
            )
        
        # Get shares
        shares = db_service.get_dashboard_shares(dashboard_id)
        
        return [DashboardShareResponse(**share) for share in shares]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching dashboard shares for {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch dashboard shares: {str(e)}'
        )


@router.delete('/{dashboard_id}/shares/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def revoke_dashboard_share(
    dashboard_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke dashboard sharing for a specific user.
    
    Only the owner can revoke shares.
    """
    try:
        owner_id = current_user.get('id')
        
        # Get dashboard to check ownership
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        # Check ownership
        if dashboard.get('user_id') != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only the owner can revoke dashboard shares'
            )
        
        # Revoke share
        success = db_service.revoke_dashboard_share(dashboard_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Share not found or already revoked'
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error revoking dashboard share for {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to revoke dashboard share: {str(e)}'
        )


# ========== Template Endpoints ==========

@router.get('/templates/available', response_model=List[DashboardResponse])
async def get_dashboard_templates(
    template_type: Optional[str] = Query(None, description='Filter by template type'),
    current_user: dict = Depends(get_current_user)
) -> List[DashboardResponse]:
    """
    Get available dashboard templates.
    """
    try:
        templates = db_service.get_dashboard_templates(template_type)
        
        return [DashboardResponse(**template) for template in templates]
        
    except Exception as e:
        logger.error(f'Error fetching dashboard templates: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch dashboard templates: {str(e)}'
        )


@router.post('/templates/{template_id}/instantiate', response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard_from_template(
    template_id: str,
    dashboard: DashboardCreate,
    current_user: dict = Depends(get_current_user)
) -> DashboardResponse:
    """
    Create a new dashboard from a template.
    """
    try:
        user_id = current_user.get('id')
        
        # Create dashboard from template
        created_dashboard = db_service.create_dashboard_from_template(
            template_id=template_id,
            user_id=user_id,
            dashboard_name=dashboard.name,
            dashboard_description=dashboard.description
        )
        
        if not created_dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Template not found or creation failed'
            )
        
        return DashboardResponse(**created_dashboard)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error creating dashboard from template {template_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create dashboard from template: {str(e)}'
        )