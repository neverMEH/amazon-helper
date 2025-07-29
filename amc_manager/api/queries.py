"""Query builder and templates API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import yaml

from ..core import get_logger
from ..models import get_db, User, QueryTemplate as QueryTemplateModel
from ..services import AMCQueryBuilder, QueryTemplate
from .dependencies import get_current_user


logger = get_logger(__name__)
router = APIRouter()


class QueryBuildRequest(BaseModel):
    template_name: Optional[str] = None
    base_query: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}
    yaml_config: Optional[str] = None


class QueryValidateRequest(BaseModel):
    sql_query: str


class QueryTemplateSave(BaseModel):
    name: str
    query: str
    description: str
    parameters: Optional[Dict[str, Any]] = {}
    tags: Optional[List[str]] = []
    category: Optional[str] = None
    is_public: bool = False
    example_parameters: Optional[Dict[str, Any]] = {}


@router.get("/templates")
async def list_query_templates(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    List available query templates (built-in)
    """
    try:
        builder = AMCQueryBuilder()
        
        templates = []
        for template_key, template_data in builder.templates.items():
            templates.append({
                'key': template_key,
                'name': template_data['name'],
                'description': template_data['description'],
                'parameters': template_data['parameters']
            })
            
        return {
            'templates': templates,
            'total': len(templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_query(
    request: QueryBuildRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Build AMC SQL query from template or custom base query
    """
    try:
        builder = AMCQueryBuilder()
        
        if request.template_name:
            # Build from template
            sql_query = builder.build_from_template(
                template_name=request.template_name,
                parameters=request.parameters
            )
        elif request.base_query:
            # Build custom query
            sql_query = builder.build_custom_query(
                base_query=request.base_query,
                parameters=request.parameters,
                yaml_config=request.yaml_config
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either template_name or base_query must be provided"
            )
            
        # Validate the generated query
        validation_result = builder.validate_query(sql_query)
        
        return {
            'sql_query': sql_query,
            'validation': validation_result,
            'parameters_used': request.parameters
        }
        
    except Exception as e:
        logger.error(f"Failed to build query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_query(
    request: QueryValidateRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Validate AMC SQL query syntax and structure
    """
    try:
        builder = AMCQueryBuilder()
        validation_result = builder.validate_query(request.sql_query)
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved")
async def list_saved_queries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_public: Optional[bool] = Query(None, description="Filter by public visibility"),
    search: Optional[str] = Query(None, description="Search in name and description")
) -> List[Dict[str, Any]]:
    """
    List saved query templates
    """
    try:
        query = db.query(QueryTemplateModel).filter(
            (QueryTemplateModel.user_id == current_user.id) |
            (QueryTemplateModel.is_public == True) |
            (QueryTemplateModel.is_system == True)
        )
        
        if category:
            query = query.filter_by(category=category)
        if is_public is not None:
            query = query.filter_by(is_public=is_public)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (QueryTemplateModel.template_name.ilike(search_pattern)) |
                (QueryTemplateModel.description.ilike(search_pattern))
            )
            
        templates = query.order_by(QueryTemplateModel.created_at.desc()).all()
        
        return [template.to_dict() for template in templates]
        
    except Exception as e:
        logger.error(f"Failed to list saved queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_query_template(
    template_data: QueryTemplateSave,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Save a query as a reusable template
    """
    try:
        # Validate the query
        builder = AMCQueryBuilder()
        validation = builder.validate_query(template_data.query)
        
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query: {validation['errors']}"
            )
            
        # Check if template name already exists for user
        existing = db.query(QueryTemplateModel).filter_by(
            template_name=template_data.name,
            user_id=current_user.id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Template name already exists"
            )
            
        # Create new template
        template = QueryTemplateModel(
            template_name=template_data.name,
            description=template_data.description,
            sql_query=template_data.query,
            parameter_definitions=template_data.parameters,
            tags=template_data.tags,
            category=template_data.category,
            user_id=current_user.id,
            is_public=template_data.is_public,
            example_parameters=template_data.example_parameters
        )
        
        db.add(template)
        db.commit()
        
        return template.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save query template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved/{template_id}")
async def get_saved_query(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific saved query template
    """
    try:
        template = db.query(QueryTemplateModel).filter_by(id=template_id).filter(
            (QueryTemplateModel.user_id == current_user.id) |
            (QueryTemplateModel.is_public == True) |
            (QueryTemplateModel.is_system == True)
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
            
        # Increment usage count
        template.increment_usage()
        db.commit()
        
        return template.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get saved query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{template_id}")
async def delete_saved_query(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """
    Delete a saved query template
    """
    try:
        template = db.query(QueryTemplateModel).filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template not found or you don't have permission to delete it"
            )
            
        db.delete(template)
        db.commit()
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete saved query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_query_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[str]:
    """
    List all query categories
    """
    try:
        categories = db.query(QueryTemplateModel.category).distinct().filter(
            QueryTemplateModel.category.isnot(None)
        ).all()
        
        return [cat[0] for cat in categories]
        
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))