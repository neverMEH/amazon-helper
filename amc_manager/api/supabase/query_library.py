"""Enhanced Query Library API endpoints with parameter management and dashboard generation"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, status
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ...services.query_template_service import query_template_service
from ...services.template_parameter_service import template_parameter_service
from ...services.template_report_service import template_report_service
from ...services.parameter_engine import parameter_engine
from ...services.amc_api_client_with_retry import amc_api_client_with_retry
from ...core.logger_simple import get_logger
from ...core.supabase_client import SupabaseManager
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/query-library", tags=["query-library"])


# Request/Response Models
class TemplateCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "Custom"
    sql_template: str
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    default_parameters: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    tags: List[str] = Field(default_factory=list)
    auto_detect_parameters: bool = True


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sql_template: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class ForkTemplateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ParameterCreateRequest(BaseModel):
    parameter_name: str
    parameter_type: str
    display_name: str
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[Any] = None
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    ui_config: Dict[str, Any] = Field(default_factory=dict)
    group_name: Optional[str] = None
    display_order: int = 1


class ParameterUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None
    ui_config: Optional[Dict[str, Any]] = None
    group_name: Optional[str] = None
    display_order: Optional[int] = None


class ExecuteTemplateRequest(BaseModel):
    instance_id: str
    parameters: Dict[str, Any]
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None


class InstanceCreateRequest(BaseModel):
    instance_name: str
    description: Optional[str] = None
    parameter_values: Dict[str, Any]
    is_default: bool = False


class DashboardGenerationRequest(BaseModel):
    execution_id: str
    report_config: Dict[str, Any]


class DetectParametersRequest(BaseModel):
    sql_template: str


# Template Endpoints
@router.get("/templates")
def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    include_public: bool = Query(True, description="Include public templates"),
    sort_by: str = Query("execution_count", description="Sort field: execution_count, created_at, name"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List query templates with advanced filtering and sorting"""
    try:
        # Get templates from service
        templates = query_template_service.list_templates(
            user_id=current_user['id'],
            include_public=include_public,
            category=category
        )
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.get('name', '').lower() or
                search_lower in t.get('description', '').lower()
            ]
        
        # Apply tag filter
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.get('tags', []) for tag in tags)
            ]
        
        # Sort templates
        reverse = (sort_order == "desc")
        if sort_by == "name":
            templates.sort(key=lambda x: x.get('name', ''), reverse=reverse)
        elif sort_by == "created_at":
            templates.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
        else:  # execution_count
            templates.sort(key=lambda x: x.get('execution_count', 0), reverse=reverse)
        
        # Apply pagination
        paginated = templates[offset:offset + limit]
        
        # Format response
        return [{
            "templateId": t['template_id'],
            "name": t['name'],
            "description": t.get('description'),
            "category": t['category'],
            "tags": t.get('tags', []),
            "isPublic": t.get('is_public', False),
            "isOwner": t['user_id'] == current_user['id'],
            "version": t.get('version', 1),
            "executionCount": t.get('execution_count', 0),
            "createdAt": t.get('created_at'),
            "updatedAt": t.get('updated_at'),
            "totalCount": len(templates)
        } for t in paginated]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    request: TemplateCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new query template with auto-parameter detection"""
    try:
        # Create template
        template_data = {
            "name": request.name,
            "description": request.description,
            "category": request.category,
            "sql_template": request.sql_template,
            "parameters_schema": request.parameters_schema,
            "default_parameters": request.default_parameters,
            "user_id": current_user['id'],
            "is_public": request.is_public,
            "tags": request.tags
        }
        
        template = query_template_service.create_template(template_data)
        if not template:
            raise HTTPException(status_code=500, detail="Failed to create template")
        
        # Auto-detect and create parameters if requested
        if request.auto_detect_parameters:
            detected = template_parameter_service.detect_parameters_from_sql(request.sql_template)
            if detected:
                parameters_list = list(detected.values())
                template_parameter_service.bulk_create_parameters(template['template_id'], parameters_list)
        
        return {
            "templateId": template['template_id'],
            "name": template['name'],
            "category": template['category'],
            "createdAt": template['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific template"""
    try:
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        return {
            "templateId": template['template_id'],
            "name": template['name'],
            "description": template.get('description'),
            "category": template['category'],
            "sqlTemplate": template['sql_template'],
            "parametersSchema": template.get('parameters_schema', {}),
            "defaultParameters": template.get('default_parameters', {}),
            "isPublic": template.get('is_public', False),
            "tags": template.get('tags', []),
            "version": template.get('version', 1),
            "executionCount": template.get('execution_count', 0),
            "isOwner": template['user_id'] == current_user['id'],
            "createdAt": template.get('created_at'),
            "updatedAt": template.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template")


@router.get("/templates/{template_id}/full")
def get_template_full(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get template with all related data (parameters, reports, instances)"""
    try:
        template = query_template_service.get_template_full(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        return {
            "templateId": template['template_id'],
            "name": template['name'],
            "description": template.get('description'),
            "category": template['category'],
            "sqlTemplate": template['sql_template'],
            "parametersSchema": template.get('parameters_schema', {}),
            "defaultParameters": template.get('default_parameters', {}),
            "isPublic": template.get('is_public', False),
            "tags": template.get('tags', []),
            "version": template.get('version', 1),
            "executionCount": template.get('execution_count', 0),
            "isOwner": template['user_id'] == current_user['id'],
            "parameters": template.get('query_template_parameters', []),
            "reports": template.get('query_template_reports', []),
            "instances": template.get('query_template_instances', []),
            "createdAt": template.get('created_at'),
            "updatedAt": template.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting full template: {e}")
        raise HTTPException(status_code=500, detail="Failed to get template details")


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    request: TemplateUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a template (owner only)"""
    try:
        updates = request.dict(exclude_none=True)
        
        updated = query_template_service.update_template(
            template_id=template_id,
            user_id=current_user['id'],
            updates=updates
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        # Increment version if SQL changed
        if 'sql_template' in updates:
            query_template_service.increment_version(template_id, current_user['id'])
        
        return {
            "templateId": updated['template_id'],
            "name": updated['name'],
            "updatedAt": updated['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to update template")


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a template (owner only)"""
    try:
        success = query_template_service.delete_template(template_id, current_user['id'])
        if not success:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete template")


@router.post("/templates/{template_id}/fork", status_code=status.HTTP_201_CREATED)
def fork_template(
    template_id: str,
    request: ForkTemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Fork a template to create your own version"""
    try:
        forked = query_template_service.fork_template(
            template_id=template_id,
            user_id=current_user['id'],
            new_name=request.name
        )
        
        if not forked:
            raise HTTPException(status_code=404, detail="Template not found or fork failed")
        
        return {
            "templateId": forked['template_id'],
            "name": forked['name'],
            "parentTemplateId": forked.get('parent_template_id'),
            "createdAt": forked['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forking template: {e}")
        raise HTTPException(status_code=500, detail="Failed to fork template")


# Parameter Management Endpoints
@router.get("/templates/{template_id}/parameters")
def get_template_parameters(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all parameters for a template"""
    try:
        # Verify template access
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        parameters = template_parameter_service.get_template_parameters(template_id)
        
        return [{
            "parameterId": p['id'],
            "parameterName": p['parameter_name'],
            "parameterType": p['parameter_type'],
            "displayName": p['display_name'],
            "description": p.get('description'),
            "required": p.get('required', True),
            "defaultValue": p.get('default_value'),
            "validationRules": p.get('validation_rules', {}),
            "uiConfig": p.get('ui_config', {}),
            "groupName": p.get('group_name'),
            "displayOrder": p.get('display_order', 1)
        } for p in parameters]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get parameters")


@router.post("/templates/{template_id}/parameters", status_code=status.HTTP_201_CREATED)
def create_template_parameter(
    template_id: str,
    request: ParameterCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new parameter for a template"""
    try:
        # Verify template ownership
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template or template['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this template")
        
        # Get default UI config for parameter type
        ui_config = request.ui_config or template_parameter_service.get_ui_config_for_type(request.parameter_type)
        
        parameter_data = {
            "template_id": template_id,
            "parameter_name": request.parameter_name,
            "parameter_type": request.parameter_type,
            "display_name": request.display_name,
            "description": request.description,
            "required": request.required,
            "default_value": request.default_value,
            "validation_rules": request.validation_rules,
            "ui_config": ui_config,
            "group_name": request.group_name,
            "display_order": request.display_order
        }
        
        created = template_parameter_service.create_parameter(parameter_data)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create parameter")
        
        return {
            "parameterId": created['id'],
            "parameterName": created['parameter_name'],
            "createdAt": created.get('created_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating parameter: {e}")
        raise HTTPException(status_code=500, detail="Failed to create parameter")


@router.put("/templates/{template_id}/parameters/{parameter_id}")
def update_template_parameter(
    template_id: str,
    parameter_id: str,
    request: ParameterUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a template parameter"""
    try:
        # Verify template ownership
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template or template['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this template")
        
        updates = request.dict(exclude_none=True)
        updated = template_parameter_service.update_parameter(parameter_id, updates)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Parameter not found")
        
        return {
            "parameterId": updated['id'],
            "updatedAt": updated.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating parameter: {e}")
        raise HTTPException(status_code=500, detail="Failed to update parameter")


@router.delete("/templates/{template_id}/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template_parameter(
    template_id: str,
    parameter_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a template parameter"""
    try:
        # Verify template ownership
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template or template['user_id'] != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to modify this template")
        
        success = template_parameter_service.delete_parameter(parameter_id)
        if not success:
            raise HTTPException(status_code=404, detail="Parameter not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting parameter: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete parameter")


# Execution and Validation Endpoints
@router.post("/templates/{template_id}/validate-parameters")
def validate_parameters(
    template_id: str,
    parameters: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate parameters against template requirements"""
    try:
        # Get template parameters
        param_definitions = template_parameter_service.get_template_parameters(template_id)
        
        errors = []
        warnings = []
        
        # Check each defined parameter
        for param_def in param_definitions:
            param_name = param_def['parameter_name']
            param_value = parameters.get(param_name)
            
            # Check required parameters
            if param_def.get('required', False) and param_name not in parameters:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            # Validate parameter value
            if param_name in parameters:
                is_valid = template_parameter_service.validate_parameter_value(param_def, param_value)
                if not is_valid:
                    errors.append(f"Invalid value for parameter '{param_name}'")
        
        # Check for unknown parameters
        defined_names = {p['parameter_name'] for p in param_definitions}
        for param_name in parameters:
            if param_name not in defined_names:
                warnings.append(f"Unknown parameter '{param_name}'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    except Exception as e:
        logger.error(f"Error validating parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate parameters")


@router.post("/templates/{template_id}/execute")
async def execute_template(
    template_id: str,
    request: ExecuteTemplateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a template with given parameters"""
    try:
        # Get template
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        # Validate parameters
        param_definitions = template_parameter_service.get_template_parameters(template_id)
        for param_def in param_definitions:
            param_name = param_def['parameter_name']
            if param_def.get('required', False) and param_name not in request.parameters:
                raise HTTPException(status_code=400, detail=f"Required parameter '{param_name}' missing")
            
            if param_name in request.parameters:
                is_valid = template_parameter_service.validate_parameter_value(
                    param_def, 
                    request.parameters[param_name]
                )
                if not is_valid:
                    raise HTTPException(status_code=400, detail=f"Invalid value for parameter '{param_name}'")
        
        # Inject parameters into SQL
        final_sql = parameter_engine.inject_parameters(
            template['sql_template'],
            request.parameters
        )
        
        # Get instance details
        manager = SupabaseManager()
        client = manager.get_client()
        instance_response = client.table('amc_instances').select('*, amc_accounts(*)').eq('instance_id', request.instance_id).execute()
        
        if not instance_response.data:
            raise HTTPException(status_code=404, detail="AMC instance not found")
        
        instance = instance_response.data[0]
        entity_id = instance['amc_accounts']['account_id']
        
        # Execute via AMC API
        result = await amc_api_client_with_retry.create_workflow_execution(
            instance_id=request.instance_id,
            user_id=current_user['id'],
            entity_id=entity_id,
            sql_query=final_sql,
            time_window_start=request.time_window_start,
            time_window_end=request.time_window_end
        )
        
        # Increment execution count
        query_template_service.increment_execution_count(template_id)
        
        return {
            "executionId": result.get('executionId'),
            "templateId": template_id,
            "instanceId": request.instance_id,
            "status": "PENDING"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing template: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute template")


# Instance Management Endpoints  
@router.post("/templates/{template_id}/instances", status_code=status.HTTP_201_CREATED)
def create_template_instance(
    template_id: str,
    request: InstanceCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Save a template instance with specific parameter values"""
    try:
        # Verify template access
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        # Validate parameters
        param_definitions = template_parameter_service.get_template_parameters(template_id)
        for param_def in param_definitions:
            param_name = param_def['parameter_name']
            if param_name in request.parameter_values:
                is_valid = template_parameter_service.validate_parameter_value(
                    param_def,
                    request.parameter_values[param_name]
                )
                if not is_valid:
                    raise HTTPException(status_code=400, detail=f"Invalid value for parameter '{param_name}'")
        
        # Create instance
        manager = SupabaseManager()
        client = manager.get_client()
        instance_data = {
            "template_id": template_id,
            "instance_name": request.instance_name,
            "description": request.description,
            "parameter_values": request.parameter_values,
            "user_id": current_user['id'],
            "is_default": request.is_default
        }
        
        response = client.table('query_template_instances').insert(instance_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create instance")
        
        created = response.data[0]
        return {
            "instanceId": created['id'],
            "instanceName": created['instance_name'],
            "createdAt": created['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template instance: {e}")
        raise HTTPException(status_code=500, detail="Failed to create instance")


# Dashboard Generation Endpoints
@router.post("/templates/{template_id}/generate-dashboard")
def generate_dashboard(
    template_id: str,
    request: DashboardGenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Generate a dashboard from template execution results"""
    try:
        # Get execution results
        manager = SupabaseManager()
        client = manager.get_client()
        execution_response = client.table('workflow_executions')\
            .select('*')\
            .eq('execution_id', request.execution_id)\
            .eq('user_id', current_user['id'])\
            .execute()
        
        if not execution_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        execution = execution_response.data[0]
        
        if execution['status'] != 'SUCCEEDED':
            raise HTTPException(status_code=400, detail="Execution has not succeeded")
        
        if not execution.get('result_data'):
            raise HTTPException(status_code=400, detail="No results available")
        
        # Generate dashboard
        dashboard = template_report_service.generate_dashboard_from_results(
            query_results=execution['result_data'],
            report_config=request.report_config
        )
        
        # Save dashboard configuration
        report_data = {
            "template_id": template_id,
            "report_name": request.report_config.get('title', 'Template Report'),
            "report_config": dashboard,
            "user_id": current_user['id']
        }
        
        report_response = client.table('query_template_reports').insert(report_data).execute()
        
        if report_response.data:
            dashboard['reportId'] = report_response.data[0]['id']
        
        return {
            "dashboardId": dashboard.get('dashboard_id'),
            "widgets": dashboard.get('widgets', []),
            "reportId": dashboard.get('reportId')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")


# Utility Endpoints
@router.post("/templates/detect-parameters")
def detect_parameters(
    request: DetectParametersRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Detect parameters from SQL template"""
    try:
        detected = template_parameter_service.detect_parameters_from_sql(request.sql_template)
        
        return {
            "parameters": detected,
            "count": len(detected)
        }
    except Exception as e:
        logger.error(f"Error detecting parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to detect parameters")


@router.get("/templates/{template_id}/versions")
def get_template_versions(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get all versions of a template"""
    try:
        versions = query_template_service.get_template_versions(template_id)
        
        return [{
            "templateId": v['template_id'],
            "name": v['name'],
            "version": v.get('version', 1),
            "parentTemplateId": v.get('parent_template_id'),
            "createdAt": v.get('created_at'),
            "isOwner": v['user_id'] == current_user['id']
        } for v in versions]
    except Exception as e:
        logger.error(f"Error getting template versions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get versions")


@router.post("/templates/{template_id}/suggest-widgets")
def suggest_widgets(
    template_id: str,
    sample_data: List[Dict[str, Any]] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Suggest appropriate widgets based on data structure"""
    try:
        suggestions = template_report_service.suggest_widgets_from_data(sample_data)
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Error suggesting widgets: {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest widgets")