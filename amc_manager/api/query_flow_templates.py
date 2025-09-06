"""
API endpoints for Query Flow Templates
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from ..api.supabase.auth import get_current_user, get_current_user_optional
from ..services.query_flow_template_service import QueryFlowTemplateService
from ..services.template_execution_service import TemplateExecutionService
from ..services.parameter_engine import ParameterEngine, ParameterValidationError
from ..services.flow_composition_service import FlowCompositionService
from ..services.composition_execution_service import CompositionExecutionService
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


class CreateTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Unique template identifier (lowercase, underscores)")
    name: str = Field(..., description="Template display name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., description="Template category")
    sql_template: str = Field(..., description="SQL template with parameters")
    parameters: Optional[List[Dict[str, Any]]] = Field(None, description="Parameter configurations")
    chart_configs: Optional[List[Dict[str, Any]]] = Field(None, description="Visualization configurations")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    is_public: bool = Field(True, description="Whether template is public")
    is_active: bool = Field(True, description="Whether template is active")


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Template display name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, description="Template category")
    sql_template: Optional[str] = Field(None, description="SQL template with parameters")
    parameters: Optional[List[Dict[str, Any]]] = Field(None, description="Parameter configurations")
    chart_configs: Optional[List[Dict[str, Any]]] = Field(None, description="Visualization configurations")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    is_public: Optional[bool] = Field(None, description="Whether template is public")
    is_active: Optional[bool] = Field(None, description="Whether template is active")


class DuplicateTemplateRequest(BaseModel):
    name: str = Field(..., description="Name for the duplicated template")
    template_id: Optional[str] = Field(None, description="Custom ID for the duplicate")


# Flow Composition Models

class CompositionListResponse(BaseModel):
    compositions: List[Dict[str, Any]]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class CreateCompositionRequest(BaseModel):
    composition_id: str = Field(..., description="Unique composition identifier (comp_*)")
    name: str = Field(..., description="Composition display name")
    description: Optional[str] = Field(None, description="Composition description")
    canvas_state: Dict[str, Any] = Field(default_factory=lambda: {
        "viewport": {"x": 0, "y": 0, "zoom": 1},
        "nodes": [],
        "edges": []
    }, description="React Flow canvas state")
    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Flow-level parameters")
    tags: Optional[List[str]] = Field(None, description="Composition tags")
    is_public: bool = Field(False, description="Whether composition is public")


class UpdateCompositionRequest(BaseModel):
    name: Optional[str] = Field(None, description="Composition display name")
    description: Optional[str] = Field(None, description="Composition description")
    canvas_state: Optional[Dict[str, Any]] = Field(None, description="React Flow canvas state")
    global_parameters: Optional[Dict[str, Any]] = Field(None, description="Flow-level parameters")
    tags: Optional[List[str]] = Field(None, description="Composition tags")
    is_public: Optional[bool] = Field(None, description="Whether composition is public")


class AddNodeRequest(BaseModel):
    node_id: str = Field(..., description="Unique node identifier within composition")
    template_id: str = Field(..., description="Reference to query flow template")
    position: Dict[str, float] = Field(..., description="Node position on canvas {x, y}")
    parameter_overrides: Dict[str, Any] = Field(default_factory=dict, description="User-configured parameter values")
    parameter_mappings: Dict[str, Any] = Field(default_factory=dict, description="Parameter mappings from other nodes")


class UpdateNodeRequest(BaseModel):
    position: Optional[Dict[str, float]] = Field(None, description="Node position on canvas")
    parameter_overrides: Optional[Dict[str, Any]] = Field(None, description="User-configured parameter values")
    parameter_mappings: Optional[Dict[str, Any]] = Field(None, description="Parameter mappings from other nodes")


class CreateConnectionRequest(BaseModel):
    connection_id: str = Field(..., description="Unique connection identifier")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    field_mappings: Dict[str, str] = Field(..., description="Source field to target parameter mappings")
    transformation_rules: Dict[str, Any] = Field(default_factory=dict, description="Optional data transformations")
    is_required: bool = Field(True, description="Whether connection is required for execution")


class ExecuteCompositionRequest(BaseModel):
    instance_id: str = Field(..., description="AMC instance ID")
    global_parameters: Dict[str, Any] = Field(default_factory=dict, description="Global parameter overrides")
    node_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Per-node parameter overrides")


class ExecuteCompositionResponse(BaseModel):
    composition_execution_id: str
    composition_id: str
    status: str
    started_at: str
    node_executions: List[Dict[str, Any]]


# Initialize services
template_service = QueryFlowTemplateService()
execution_service = TemplateExecutionService()
parameter_engine = ParameterEngine()
composition_service = FlowCompositionService()
composition_execution_service = CompositionExecutionService()


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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new query flow template
    """
    try:
        # Validate template_id format
        import re
        if not re.match(r'^[a-z0-9_]+$', request.template_id):
            raise HTTPException(
                status_code=400,
                detail="Template ID must contain only lowercase letters, numbers, and underscores"
            )
        
        # Create template
        template = template_service.create_template(
            template_data={
                'template_id': request.template_id,
                'name': request.name,
                'description': request.description,
                'category': request.category,
                'sql_template': request.sql_template,
                'tags': request.tags or [],
                'is_public': request.is_public,
                'is_active': request.is_active
            },
            parameters=request.parameters or [],
            chart_configs=request.chart_configs or [],
            user_id=current_user['id']
        )
        
        # Return the created template
        return template_service.get_template(
            template_id=request.template_id,
            user_id=current_user['id'],
            include_parameters=True,
            include_charts=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
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


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing query flow template
    """
    try:
        # Get existing template to verify ownership
        existing = template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=False,
            include_charts=False
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check ownership
        if existing['created_by'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this template")
        
        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.category is not None:
            update_data['category'] = request.category
        if request.sql_template is not None:
            update_data['sql_template'] = request.sql_template
        if request.tags is not None:
            update_data['tags'] = request.tags
        if request.is_public is not None:
            update_data['is_public'] = request.is_public
        if request.is_active is not None:
            update_data['is_active'] = request.is_active
        
        # Update template
        if update_data:
            template_service.update_template(
                template_id=template_id,
                user_id=current_user['id'],
                updates=update_data
            )
        
        # Update parameters if provided
        if request.parameters is not None:
            # Delete existing parameters
            template_service.delete_parameters(template_id=existing['id'])
            # Add new parameters
            for idx, param in enumerate(request.parameters):
                template_service.add_parameter(
                    template_id=existing['id'],
                    parameter_data={
                        **param,
                        'order_index': idx
                    }
                )
        
        # Update chart configs if provided
        if request.chart_configs is not None:
            # Delete existing chart configs
            template_service.delete_chart_configs(template_id=existing['id'])
            # Add new chart configs
            for idx, chart in enumerate(request.chart_configs):
                template_service.add_chart_config(
                    template_id=existing['id'],
                    chart_data={
                        **chart,
                        'order_index': idx
                    }
                )
        
        # Return the updated template
        return template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=True,
            include_charts=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
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


@router.post("/{template_id}/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate_template(
    template_id: str,
    request: DuplicateTemplateRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Duplicate an existing template
    """
    try:
        # Get the original template
        original = template_service.get_template(
            template_id=template_id,
            user_id=current_user['id'],
            include_parameters=True,
            include_charts=True
        )
        
        if not original:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Generate new template_id if not provided
        new_template_id = request.template_id
        if not new_template_id:
            import time
            new_template_id = f"{template_id}_copy_{int(time.time())}"
        
        # Validate template_id format
        import re
        if not re.match(r'^[a-z0-9_]+$', new_template_id):
            raise HTTPException(
                status_code=400,
                detail="Template ID must contain only lowercase letters, numbers, and underscores"
            )
        
        # Prepare parameters for duplication
        duplicate_params = []
        if original.get('parameters'):
            for param in original['parameters']:
                duplicate_params.append({
                    'parameter_name': param['parameter_name'],
                    'display_name': param['display_name'],
                    'parameter_type': param['parameter_type'],
                    'required': param.get('required', False),
                    'default_value': param.get('default_value'),
                    'validation_rules': param.get('validation_rules', {}),
                    'ui_component': param.get('ui_component'),
                    'ui_config': param.get('ui_config', {}),
                    'order_index': param.get('order_index', 0)
                })
        
        # Prepare chart configs for duplication
        duplicate_charts = []
        if original.get('chart_configs'):
            for chart in original['chart_configs']:
                duplicate_charts.append({
                    'chart_name': chart['chart_name'],
                    'chart_type': chart['chart_type'],
                    'chart_config': chart.get('chart_config', {}),
                    'data_mapping': chart.get('data_mapping', {}),
                    'is_default': chart.get('is_default', False),
                    'order_index': chart.get('order_index', 0)
                })
        
        # Create the duplicate
        duplicate = template_service.create_template(
            template_data={
                'template_id': new_template_id,
                'name': request.name,
                'description': original.get('description'),
                'category': original['category'],
                'sql_template': original['sql_template'],
                'tags': original.get('tags', []),
                'is_public': False,  # Duplicates start as private
                'is_active': True
            },
            parameters=duplicate_params,
            chart_configs=duplicate_charts,
            user_id=current_user['id']
        )
        
        # Return the duplicated template
        return template_service.get_template(
            template_id=new_template_id,
            user_id=current_user['id'],
            include_parameters=True,
            include_charts=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating template {template_id}: {e}")
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


# Flow Composition Endpoints

@router.get("/compositions/", response_model=CompositionListResponse)
async def list_compositions(
    search: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    is_public: Optional[bool] = Query(None, description="Filter public/private compositions"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Dict = Depends(get_current_user)
) -> CompositionListResponse:
    """
    List flow compositions with optional filtering
    """
    try:
        result = composition_service.list_compositions(
            user_id=current_user['id'],
            search=search,
            tags=tags,
            is_public=is_public,
            limit=limit,
            offset=offset
        )
        return CompositionListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing compositions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compositions/", status_code=status.HTTP_201_CREATED)
async def create_composition(
    request: CreateCompositionRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new flow composition
    """
    try:
        # Validate composition_id format
        if not request.composition_id.startswith('comp_'):
            raise HTTPException(
                status_code=400,
                detail="Composition ID must start with 'comp_' prefix"
            )
        
        import re
        if not re.match(r'^comp_[a-z0-9_]+$', request.composition_id):
            raise HTTPException(
                status_code=400,
                detail="Composition ID must contain only lowercase letters, numbers, and underscores after 'comp_' prefix"
            )
        
        # Create composition
        composition = composition_service.create_composition(
            composition_data={
                'composition_id': request.composition_id,
                'name': request.name,
                'description': request.description,
                'canvas_state': request.canvas_state,
                'global_parameters': request.global_parameters,
                'tags': request.tags or [],
                'is_public': request.is_public
            },
            user_id=current_user['id']
        )
        
        return composition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating composition: {e}")
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Composition ID already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compositions/{composition_id}")
async def get_composition(
    composition_id: str,
    include_nodes: bool = Query(True, description="Include node details"),
    include_connections: bool = Query(True, description="Include connection details"),
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a single composition with all details
    """
    try:
        composition = composition_service.get_composition_by_id(
            composition_id=composition_id,
            user_id=current_user['id'],
            include_nodes=include_nodes,
            include_connections=include_connections
        )
        
        if not composition:
            raise HTTPException(
                status_code=404,
                detail=f"Composition not found: {composition_id}"
            )
        
        return composition
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/compositions/{composition_id}")
async def update_composition(
    composition_id: str,
    request: UpdateCompositionRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update an existing flow composition
    """
    try:
        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data['name'] = request.name
        if request.description is not None:
            update_data['description'] = request.description
        if request.canvas_state is not None:
            update_data['canvas_state'] = request.canvas_state
        if request.global_parameters is not None:
            update_data['global_parameters'] = request.global_parameters
        if request.tags is not None:
            update_data['tags'] = request.tags
        if request.is_public is not None:
            update_data['is_public'] = request.is_public
        
        # Update composition
        composition = composition_service.update_composition(
            composition_id=composition_id,
            updates=update_data,
            user_id=current_user['id']
        )
        
        if not composition:
            raise HTTPException(
                status_code=404,
                detail="Composition not found or unauthorized"
            )
        
        return composition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compositions/{composition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_composition(
    composition_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a composition (soft delete, only by creator)
    """
    try:
        success = composition_service.delete_composition(
            composition_id=composition_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Composition not found or unauthorized"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compositions/{composition_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_node_to_composition(
    composition_id: str,
    request: AddNodeRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Add a node to a composition
    """
    try:
        # Verify template exists
        template = template_service.get_template(
            template_id=request.template_id,
            user_id=current_user['id'],
            include_parameters=False,
            include_charts=False
        )
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found: {request.template_id}"
            )
        
        # Add node
        node = composition_service.add_node_to_composition(
            composition_id=composition_id,
            node_data={
                'node_id': request.node_id,
                'template_id': request.template_id,
                'position': request.position,
                'parameter_overrides': request.parameter_overrides,
                'parameter_mappings': request.parameter_mappings
            },
            user_id=current_user['id']
        )
        
        return node
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding node to composition {composition_id}: {e}")
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Node ID already exists in composition")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/compositions/{composition_id}/nodes/{node_id}")
async def update_node(
    composition_id: str,
    node_id: str,
    request: UpdateNodeRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update a node in a composition
    """
    try:
        # Prepare update data
        update_data = {}
        if request.position is not None:
            update_data['position'] = request.position
        if request.parameter_overrides is not None:
            update_data['parameter_overrides'] = request.parameter_overrides
        if request.parameter_mappings is not None:
            update_data['parameter_mappings'] = request.parameter_mappings
        
        # Update node
        node = composition_service.update_node(
            composition_id=composition_id,
            node_id=node_id,
            updates=update_data,
            user_id=current_user['id']
        )
        
        if not node:
            raise HTTPException(
                status_code=404,
                detail="Node not found or unauthorized"
            )
        
        return node
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node {node_id} in composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compositions/{composition_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_node_from_composition(
    composition_id: str,
    node_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Remove a node from a composition
    """
    try:
        success = composition_service.remove_node_from_composition(
            composition_id=composition_id,
            node_id=node_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Node not found or unauthorized"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing node {node_id} from composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compositions/{composition_id}/connections", status_code=status.HTTP_201_CREATED)
async def create_connection(
    composition_id: str,
    request: CreateConnectionRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a connection between nodes in a composition
    """
    try:
        # Create connection
        connection = composition_service.create_connection(
            composition_id=composition_id,
            connection_data={
                'connection_id': request.connection_id,
                'source_node_id': request.source_node_id,
                'target_node_id': request.target_node_id,
                'field_mappings': request.field_mappings,
                'transformation_rules': request.transformation_rules,
                'is_required': request.is_required
            },
            user_id=current_user['id']
        )
        
        return connection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection in composition {composition_id}: {e}")
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Source or target node not found in composition")
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=409, detail="Connection ID already exists in composition")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compositions/{composition_id}/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connection(
    composition_id: str,
    connection_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Remove a connection from a composition
    """
    try:
        success = composition_service.remove_connection(
            composition_id=composition_id,
            connection_id=connection_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Connection not found or unauthorized"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing connection {connection_id} from composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compositions/{composition_id}/execution-summary")
async def get_composition_execution_summary(
    composition_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get execution summary for a composition
    """
    try:
        summary = composition_service.get_composition_execution_summary(
            composition_id=composition_id,
            user_id=current_user['id']
        )
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail="Composition not found or no executions yet"
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution summary for composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compositions/{composition_id}/execute", response_model=ExecuteCompositionResponse, status_code=status.HTTP_201_CREATED)
async def execute_composition(
    composition_id: str,
    request: ExecuteCompositionRequest,
    current_user: Dict = Depends(get_current_user)
) -> ExecuteCompositionResponse:
    """
    Execute a flow composition (placeholder for future implementation)
    """
    try:
        # Execute the composition using the execution service
        result = await composition_execution_service.execute_composition(
            composition_id=composition_id,
            instance_id=request.instance_id,
            user_id=current_user['id'],
            parameters=request.parameters,
            schedule_id=request.schedule_id
        )
        
        return ExecuteCompositionResponse(
            composition_execution_id=result['composition_execution_id'],
            composition_id=result['composition_id'],
            status=result['status'],
            started_at=result['started_at'],
            node_executions=[
                {
                    "node_id": node['node_id'],
                    "status": node['status'],
                    "execution_id": node.get('execution_id'),
                    "error": node.get('error')
                }
                for node in result['nodes']
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing composition {composition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))