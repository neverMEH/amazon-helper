"""Widget Management API endpoints for dashboard widgets"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from ..services.reporting_database_service import ReportingDatabaseService
from ..services.widget_configuration_service import WidgetConfigurationService, WidgetType
from ..core.logger_simple import get_logger
from .supabase.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix='/api/dashboards/{dashboard_id}/widgets', tags=['widgets'])


# ========== Pydantic Models ==========

class WidgetCreate(BaseModel):
    """Model for creating a new widget"""
    widget_type: str = Field(..., description='Type of widget (line_chart, bar_chart, etc.)')
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    data_source: Optional[Dict[str, Any]] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    layout: Dict[str, Any] = Field(default_factory=lambda: {'x': 0, 'y': 0, 'width': 4, 'height': 4})
    styling: Optional[Dict[str, Any]] = Field(default_factory=dict)
    content: Optional[Dict[str, Any]] = None  # For text widgets


class WidgetUpdate(BaseModel):
    """Model for updating an existing widget"""
    widget_type: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    data_source: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    styling: Optional[Dict[str, Any]] = None
    content: Optional[Dict[str, Any]] = None


class WidgetResponse(BaseModel):
    """Model for widget response"""
    id: str
    widget_id: str
    dashboard_id: str
    widget_type: str
    name: str
    description: Optional[str]
    data_source: Dict[str, Any]
    config: Dict[str, Any]
    layout: Dict[str, Any]
    styling: Dict[str, Any]
    content: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class WidgetPositionUpdate(BaseModel):
    """Model for updating widget positions"""
    widget_id: str
    x: int = Field(ge=0, le=11)
    y: int = Field(ge=0)
    width: int = Field(ge=1, le=12)
    height: int = Field(ge=1, le=100)


class WidgetDataRequest(BaseModel):
    """Model for requesting widget data"""
    date_range: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    refresh: bool = Field(default=False, description='Force refresh of cached data')


# ========== Initialize Services ==========

db_service = ReportingDatabaseService()
config_service = WidgetConfigurationService()


# ========== Helper Functions ==========

async def verify_dashboard_access(
    dashboard_id: str,
    user_id: str,
    require_edit: bool = False
) -> bool:
    """Verify user has access to the dashboard"""
    can_access, access_type = db_service.user_can_access_dashboard(user_id, dashboard_id)
    
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have access to this dashboard'
        )
    
    if require_edit and access_type == 'shared':
        # Check if user has edit permissions
        shares = db_service.get_dashboard_shares(dashboard_id)
        user_share = next((s for s in shares if s.get('shared_with_user_id') == user_id), None)
        
        if not user_share or user_share.get('permission_level') == 'view':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to edit this dashboard'
            )
    
    return True


# ========== Endpoints ==========

@router.get('/', response_model=List[WidgetResponse])
async def get_dashboard_widgets(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user)
) -> List[WidgetResponse]:
    """
    Get all widgets for a dashboard
    """
    try:
        user_id = current_user.get('id')
        
        # Verify access
        await verify_dashboard_access(dashboard_id, user_id)
        
        # Get dashboard with widgets
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Dashboard not found'
            )
        
        widgets = dashboard.get('dashboard_widgets', [])
        
        return [WidgetResponse(**widget) for widget in widgets]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching widgets for dashboard {dashboard_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch widgets: {str(e)}'
        )


@router.post('/', response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def create_widget(
    dashboard_id: str,
    widget: WidgetCreate,
    current_user: dict = Depends(get_current_user)
) -> WidgetResponse:
    """
    Create a new widget in a dashboard
    """
    try:
        user_id = current_user.get('id')
        
        # Verify edit access
        await verify_dashboard_access(dashboard_id, user_id, require_edit=True)
        
        # Prepare widget data
        widget_data = {
            'dashboard_id': dashboard_id,
            'widget_type': widget.widget_type,
            'name': widget.name,
            'description': widget.description,
            'data_source': widget.data_source,
            'config': widget.config,
            'layout': widget.layout,
            'styling': widget.styling,
            'content': widget.content
        }
        
        # Validate widget configuration
        is_valid, error = config_service.validate_widget_configuration(widget_data)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid widget configuration: {error}'
            )
        
        # Validate positioning doesn't overlap
        is_valid, error = config_service.validate_widget_positioning(
            dashboard_id=dashboard_id,
            new_widget_layout=widget.layout
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Widget positioning error: {error}'
            )
        
        # Create widget in database
        created_widget = db_service.create_widget(widget_data)
        
        if not created_widget:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to create widget'
            )
        
        return WidgetResponse(**created_widget)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error creating widget: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to create widget: {str(e)}'
        )


@router.put('/{widget_id}', response_model=WidgetResponse)
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    updates: WidgetUpdate,
    current_user: dict = Depends(get_current_user)
) -> WidgetResponse:
    """
    Update an existing widget
    """
    try:
        user_id = current_user.get('id')
        
        # Verify edit access
        await verify_dashboard_access(dashboard_id, user_id, require_edit=True)
        
        # Prepare update data
        update_data = updates.dict(exclude_unset=True)
        
        # If layout is being updated, validate positioning
        if 'layout' in update_data:
            is_valid, error = config_service.validate_widget_positioning(
                dashboard_id=dashboard_id,
                new_widget_layout=update_data['layout'],
                exclude_widget_id=widget_id
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f'Widget positioning error: {error}'
                )
        
        # Validate and update widget
        is_valid, error = config_service.update_widget_configuration(
            widget_id=widget_id,
            dashboard_id=dashboard_id,
            updates=update_data
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Widget update failed: {error}'
            )
        
        # Get updated widget
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        widget = next((w for w in dashboard.get('dashboard_widgets', []) if w['id'] == widget_id), None)
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Widget not found'
            )
        
        return WidgetResponse(**widget)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error updating widget {widget_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to update widget: {str(e)}'
        )


@router.delete('/{widget_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_widget(
    dashboard_id: str,
    widget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a widget from a dashboard
    """
    try:
        user_id = current_user.get('id')
        
        # Verify edit access
        await verify_dashboard_access(dashboard_id, user_id, require_edit=True)
        
        # Delete widget
        success = db_service.delete_widget(widget_id, dashboard_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Widget not found or deletion failed'
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error deleting widget {widget_id}: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete widget: {str(e)}'
        )


@router.put('/reorder', status_code=status.HTTP_204_NO_CONTENT)
async def reorder_widgets(
    dashboard_id: str,
    positions: List[WidgetPositionUpdate],
    current_user: dict = Depends(get_current_user)
):
    """
    Update positions for multiple widgets at once
    """
    try:
        user_id = current_user.get('id')
        
        # Verify edit access
        await verify_dashboard_access(dashboard_id, user_id, require_edit=True)
        
        # Convert to format expected by service
        widget_positions = [
            {
                'widget_id': pos.widget_id,
                'layout': {
                    'x': pos.x,
                    'y': pos.y,
                    'width': pos.width,
                    'height': pos.height
                }
            }
            for pos in positions
        ]
        
        # Update positions
        success = db_service.reorder_widgets(dashboard_id, widget_positions)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to update widget positions'
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error reordering widgets: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to reorder widgets: {str(e)}'
        )


@router.post('/{widget_id}/data')
async def get_widget_data(
    dashboard_id: str,
    widget_id: str,
    data_request: WidgetDataRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data for a specific widget based on its configuration
    """
    try:
        user_id = current_user.get('id')
        
        # Verify access
        await verify_dashboard_access(dashboard_id, user_id)
        
        # Get widget configuration
        dashboard = db_service.get_dashboard_with_widgets(dashboard_id)
        widget = next((w for w in dashboard.get('dashboard_widgets', []) if w['id'] == widget_id), None)
        
        if not widget:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Widget not found'
            )
        
        # Get data based on widget data source
        data_source = widget.get('data_source', {})
        
        # Apply request filters and date range
        if data_request.date_range:
            data_source['date_range'] = data_request.date_range
        if data_request.filters:
            data_source['filters'] = data_request.filters
        
        # Map data source to actual data
        widget_data = config_service.map_data_source_to_aggregates(
            data_source=data_source,
            dashboard_id=dashboard_id,
            date_range=data_request.date_range
        )
        
        return {
            'widget_id': widget_id,
            'widget_type': widget.get('widget_type'),
            'data': widget_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching widget data: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch widget data: {str(e)}'
        )


@router.get('/templates/{widget_type}')
async def get_widget_template(
    widget_type: str,
    template_name: Optional[str] = Query(None, description='Custom template name'),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a template configuration for a specific widget type
    """
    try:
        # Validate widget type
        if widget_type not in [wt.value for wt in WidgetType]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid widget type: {widget_type}'
            )
        
        # Generate template
        template = config_service.create_widget_template(widget_type, template_name)
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error generating widget template: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to generate widget template: {str(e)}'
        )