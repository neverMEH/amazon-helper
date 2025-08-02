"""Query Templates API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...services.query_template_service import query_template_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


class QueryTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "Custom"
    sql_template: str
    parameters_schema: Dict[str, Any] = {}
    default_parameters: Dict[str, Any] = {}
    is_public: bool = False
    tags: List[str] = []


class QueryTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sql_template: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None


class CreateFromWorkflow(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    category: str = "Custom"
    parameters_schema: Dict[str, Any] = {}
    is_public: bool = False
    tags: List[str] = []


@router.get("")
def list_query_templates(
    include_public: bool = Query(default=True, description="Include public templates"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all query templates accessible to the current user"""
    try:
        templates = query_template_service.list_templates(
            user_id=current_user['id'],
            include_public=include_public,
            category=category
        )
        
        # Format response
        return [{
            "id": t['template_id'],
            "templateId": t['template_id'],
            "name": t['name'],
            "description": t.get('description'),
            "category": t['category'],
            "sqlTemplate": t['sql_template'],
            "parametersSchema": t.get('parameters_schema', {}),
            "defaultParameters": t.get('default_parameters', {}),
            "isPublic": t.get('is_public', False),
            "tags": t.get('tags', []),
            "usageCount": t.get('usage_count', 0),
            "isOwner": t['user_id'] == current_user['id'],
            "createdAt": t.get('created_at'),
            "updatedAt": t.get('updated_at')
        } for t in templates]
    except Exception as e:
        logger.error(f"Error listing query templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch query templates")


@router.get("/categories")
def list_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[str]:
    """Get all unique template categories accessible to user"""
    try:
        categories = query_template_service.get_categories(current_user['id'])
        return categories
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.post("")
def create_query_template(
    template: QueryTemplateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new query template"""
    try:
        template_data = {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "sql_template": template.sql_template,
            "parameters_schema": template.parameters_schema,
            "default_parameters": template.default_parameters,
            "user_id": current_user['id'],
            "is_public": template.is_public,
            "tags": template.tags
        }
        
        created = query_template_service.create_template(template_data)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create query template")
        
        return {
            "templateId": created['template_id'],
            "name": created['name'],
            "category": created['category'],
            "createdAt": created['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating query template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create query template")


@router.post("/from-workflow")
def create_from_workflow(
    data: CreateFromWorkflow,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a query template from an existing workflow"""
    try:
        template_data = {
            "name": data.name,
            "description": data.description,
            "category": data.category,
            "parameters_schema": data.parameters_schema,
            "is_public": data.is_public,
            "tags": data.tags
        }
        
        created = query_template_service.create_from_workflow(
            workflow_id=data.workflow_id,
            user_id=current_user['id'],
            template_data=template_data
        )
        
        if not created:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        return {
            "templateId": created['template_id'],
            "name": created['name'],
            "category": created['category'],
            "createdAt": created['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template from workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template from workflow")


@router.get("/{template_id}")
def get_query_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific query template"""
    try:
        template = query_template_service.get_template(template_id, current_user['id'])
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        return {
            "id": template['template_id'],
            "templateId": template['template_id'],
            "name": template['name'],
            "description": template.get('description'),
            "category": template['category'],
            "sqlTemplate": template['sql_template'],
            "parametersSchema": template.get('parameters_schema', {}),
            "defaultParameters": template.get('default_parameters', {}),
            "isPublic": template.get('is_public', False),
            "tags": template.get('tags', []),
            "usageCount": template.get('usage_count', 0),
            "isOwner": template['user_id'] == current_user['id'],
            "createdAt": template.get('created_at'),
            "updatedAt": template.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching query template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch query template")


@router.put("/{template_id}")
def update_query_template(
    template_id: str,
    updates: QueryTemplateUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update a query template (owner only)"""
    try:
        update_data = updates.dict(exclude_none=True)
        
        updated = query_template_service.update_template(
            template_id=template_id,
            user_id=current_user['id'],
            updates=update_data
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        return {
            "templateId": updated['template_id'],
            "name": updated['name'],
            "updatedAt": updated['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating query template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update query template")


@router.delete("/{template_id}")
def delete_query_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a query template (owner only)"""
    try:
        success = query_template_service.delete_template(template_id, current_user['id'])
        
        if not success:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        return {"message": "Query template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting query template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete query template")


@router.post("/{template_id}/use")
def use_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark a template as used (increment usage count)"""
    try:
        # Verify access first
        template = query_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        # Increment usage
        query_template_service.increment_usage(template_id)
        
        return {
            "templateId": template_id,
            "usageCount": template.get('usage_count', 0) + 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking template as used: {e}")
        raise HTTPException(status_code=500, detail="Failed to update usage count")


@router.post("/{template_id}/build")
def build_query_from_template(
    template_id: str,
    parameters: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Build a query from a template with given parameters"""
    try:
        template = query_template_service.get_template(template_id, current_user['id'])
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        # Build query by replacing template variables
        sql_query = template['sql_template']
        
        # Simple template variable replacement
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"  # {{variable}}
            if placeholder in sql_query:
                if isinstance(value, list):
                    # Handle list parameters (e.g., ASIN lists)
                    value_str = ", ".join(f"'{v}'" for v in value)
                    sql_query = sql_query.replace(placeholder, value_str)
                else:
                    sql_query = sql_query.replace(placeholder, str(value))
        
        return {
            "template_id": template_id,
            "template_name": template['name'],
            "sql_query": sql_query,
            "parameters_used": parameters
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building query from template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to build query")