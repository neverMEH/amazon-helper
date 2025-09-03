"""
API endpoints for Query Flow Templates
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from ..api.supabase.auth import get_current_user, get_current_user_optional
from ..services.query_flow_template_service import QueryFlowTemplateService
from ..services.template_execution_service import TemplateExecutionService
from ..services.parameter_engine import ParameterEngine, ParameterValidationError
from ..core.logger_simple import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/query-flow-templates", tags=["Query Flow Templates"])


# Pydantic models for request/response

class TemplateListResponse(BaseModel):
    templates: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class ExecuteTemplateRequest(BaseModel):
    instance_id: str = Field(..., description="AMC instance ID")
    parameters: Dict[str, Any] = Field(..., description="Template parameters")
    schedule_id: Optional[str] = Field(None, description="Schedule ID if executed from schedule")


class ExecuteTemplateResponse(BaseModel):
    execution_id: str
    template_id: str
    workflow_id: str
    status: str
    created_at: str
    message: str


class ValidateParametersRequest(BaseModel):
    parameters: Dict[str, Any] = Field(..., description="Parameters to validate")


class ValidateParametersResponse(BaseModel):
    valid: bool
    processed_parameters: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class PreviewSQLRequest(BaseModel):
    parameters: Dict[str, Any] = Field(..., description="Parameters for SQL preview")


class PreviewSQLResponse(BaseModel):
    sql: str
    parameter_count: int
    estimated_cost: Optional[float] = None


class RateTemplateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    review: Optional[str] = Field(None, description="Optional review text")


class FavoriteResponse(BaseModel):
    is_favorite: bool
    message: str


# Initialize services
template_service = QueryFlowTemplateService()
execution_service = TemplateExecutionService()
parameter_engine = ParameterEngine()


# Endpoints

@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    include_stats: bool = Query(True, description="Include execution statistics"),
    current_user: Dict = Depends(get_current_user)
) -> TemplateListResponse:
    """
    List available query flow templates with optional filtering
    """
    try:
        result = template_service.list_templates(
            user_id=current_user['id'],
            category=category,
            search=search,
            tags=tags,
            limit=limit,
            offset=offset,
            include_stats=include_stats
        )
        return TemplateListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """
    Get all available template categories
    """
    try:
        categories = template_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=50, description="Number of tags to return"),
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get most popular template tags with counts
    """
    try:
        tags = template_service.get_popular_tags(limit=limit)
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    include_parameters: bool = Query(True, description="Include parameter definitions"),
    include_charts: bool = Query(True, description="Include chart configurations"),
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a single template by ID or template_id string
    """
    try:
        template = template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=include_parameters,
            include_charts=include_charts
        )
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/execute", response_model=ExecuteTemplateResponse, status_code=status.HTTP_201_CREATED)
async def execute_template(
    template_id: str,
    request: ExecuteTemplateRequest,
    current_user: Dict = Depends(get_current_user)
) -> ExecuteTemplateResponse:
    """
    Execute a template with provided parameters
    """
    try:
        # Get template
        template = template_service.get_template(template_id, user_id=current_user['id'])
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Execute template
        execution_result = await execution_service.execute_template(
            template_id=template['id'],
            template_data=template,
            instance_id=request.instance_id,
            parameters=request.parameters,
            user_id=current_user['id'],
            schedule_id=request.schedule_id
        )
        
        return ExecuteTemplateResponse(
            execution_id=execution_result['execution_id'],
            template_id=template['id'],
            workflow_id=execution_result.get('workflow_id', ''),
            status=execution_result['status'],
            created_at=execution_result['created_at'],
            message=f"Template execution started successfully"
        )
        
    except HTTPException:
        raise
    except ParameterValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/validate-parameters", response_model=ValidateParametersResponse)
async def validate_parameters(
    template_id: str,
    request: ValidateParametersRequest,
    current_user: Dict = Depends(get_current_user)
) -> ValidateParametersResponse:
    """
    Validate parameters for a template without executing
    """
    try:
        # Get template
        template = template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=True
        )
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Validate parameters
        try:
            processed = parameter_engine.validate_parameters(
                parameter_definitions=template['parameters'],
                parameter_values=request.parameters
            )
            
            return ValidateParametersResponse(
                valid=True,
                processed_parameters=processed,
                errors=None
            )
        except ParameterValidationError as e:
            return ValidateParametersResponse(
                valid=False,
                processed_parameters=None,
                errors=str(e).split('\n')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating parameters for {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/preview-sql", response_model=PreviewSQLResponse)
async def preview_sql(
    template_id: str,
    request: PreviewSQLRequest,
    current_user: Dict = Depends(get_current_user)
) -> PreviewSQLResponse:
    """
    Preview SQL with parameter substitution
    """
    try:
        # Get template
        template = template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=True
        )
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Process template with parameters
        processed_sql = parameter_engine.process_template(
            sql_template=template['sql_template'],
            parameters=template['parameters'],
            parameter_values=request.parameters
        )
        
        # Count parameters used
        parameter_count = len(request.parameters)
        
        return PreviewSQLResponse(
            sql=processed_sql,
            parameter_count=parameter_count,
            estimated_cost=None  # Could calculate based on query complexity
        )
        
    except HTTPException:
        raise
    except ParameterValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing SQL for {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/executions")
async def get_execution_history(
    template_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get execution history for a template
    """
    try:
        # Get template to verify it exists
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Get executions
        executions = await execution_service.get_executions(
            template_id=template['id'],
            user_id=current_user['id'],
            limit=limit,
            offset=offset,
            status=status
        )
        
        return executions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution history for {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/favorite", response_model=FavoriteResponse)
async def toggle_favorite(
    template_id: str,
    current_user: Dict = Depends(get_current_user)
) -> FavoriteResponse:
    """
    Toggle favorite status for a template
    """
    try:
        # Get template
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Toggle favorite
        is_favorite = template_service.toggle_favorite(
            template_id=template['id'],
            user_id=current_user['id']
        )
        
        return FavoriteResponse(
            is_favorite=is_favorite,
            message=f"Template {'added to' if is_favorite else 'removed from'} favorites"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite for {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/rate")
async def rate_template(
    template_id: str,
    request: RateTemplateRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rate a template
    """
    try:
        # Get template
        template = template_service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {template_id}"
            )
        
        # Rate template
        rating = template_service.rate_template(
            template_id=template['id'],
            user_id=current_user['id'],
            rating=request.rating,
            review=request.review
        )
        
        return rating
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a template (soft delete, only by creator)
    """
    try:
        success = template_service.delete_template(
            template_id=template_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found or unauthorized"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))