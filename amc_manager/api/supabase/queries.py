"""Query Templates API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/templates")
def list_query_templates(
    include_private: bool = False,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List available query templates"""
    try:
        if include_private:
            # Get user's templates and public ones
            templates = db_service.get_query_templates_sync(user_id=current_user['id'])
        else:
            # Get only public templates
            templates = db_service.get_query_templates_sync(is_public=True)
        
        return [{
            "template_id": t['template_id'],
            "name": t['name'],
            "description": t.get('description'),
            "category": t['category'],
            "parameters_schema": t.get('parameters_schema', {}),
            "default_parameters": t.get('default_parameters', {}),
            "is_public": t.get('is_public', False),
            "tags": t.get('tags', []),
            "usage_count": t.get('usage_count', 0),
            "created_at": t.get('created_at')
        } for t in templates]
    except Exception as e:
        logger.error(f"Error listing query templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")


@router.get("/templates/{template_id}")
def get_query_template(
    template_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific query template"""
    try:
        template = db_service.get_template_by_id_sync(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check access
        if not template.get('is_public', False) and template.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "template_id": template['template_id'],
            "name": template['name'],
            "description": template.get('description'),
            "category": template['category'],
            "sql_template": template['sql_template'],
            "parameters_schema": template.get('parameters_schema', {}),
            "default_parameters": template.get('default_parameters', {}),
            "is_public": template.get('is_public', False),
            "tags": template.get('tags', []),
            "usage_count": template.get('usage_count', 0),
            "created_at": template.get('created_at'),
            "updated_at": template.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch template")


@router.post("/templates/{template_id}/build")
def build_query_from_template(
    template_id: str,
    parameters: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Build a query from a template with given parameters"""
    try:
        template = db_service.get_template_by_id_sync(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check access
        if not template.get('is_public', False) and template.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build query by replacing template variables
        sql_query = template['sql_template']
        
        # Simple template variable replacement
        # In production, use a proper template engine
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


@router.post("/validate")
def validate_query(
    sql_query: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate an AMC SQL query"""
    # TODO: Implement actual AMC SQL validation
    # This would check:
    # 1. SQL syntax
    # 2. AMC-specific functions and tables
    # 3. Parameter placeholders
    
    # For now, just do basic checks
    validation_errors = []
    
    if not sql_query.strip():
        validation_errors.append("Query cannot be empty")
    
    if len(sql_query) > 50000:
        validation_errors.append("Query exceeds maximum length")
    
    # Check for basic SQL keywords
    sql_lower = sql_query.lower()
    if not any(keyword in sql_lower for keyword in ['select', 'with']):
        validation_errors.append("Query must contain SELECT or WITH statement")
    
    return {
        "is_valid": len(validation_errors) == 0,
        "errors": validation_errors,
        "warnings": [],
        "query_length": len(sql_query)
    }