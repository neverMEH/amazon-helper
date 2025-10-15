"""Instance Templates API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ...services.instance_template_service import instance_template_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


# Pydantic Schemas

class InstanceTemplateCreate(BaseModel):
    """Schema for creating an instance template"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    sql_query: str = Field(..., min_length=1, description="SQL query text")
    tags: List[str] = Field(default_factory=list, description="Optional tags for organization")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Weekly Campaign Report",
                "description": "Standard weekly campaign performance analysis",
                "sql_query": "SELECT campaign_id, impressions, clicks FROM campaigns WHERE date >= '{{start_date}}'",
                "tags": ["weekly", "campaigns"]
            }
        }


class InstanceTemplateUpdate(BaseModel):
    """Schema for updating an instance template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    sql_query: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None


class InstanceTemplateResponse(BaseModel):
    """Schema for instance template response"""
    id: str
    template_id: str
    name: str
    description: Optional[str]
    sql_query: str
    instance_id: str
    user_id: str
    tags: List[str]
    usage_count: int
    created_at: str
    updated_at: str


# API Endpoints

@router.get("/{instance_id}/templates")
def list_instance_templates(
    instance_id: str = Path(..., description="AMC instance UUID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all templates for a specific instance owned by the current user"""
    try:
        templates = instance_template_service.list_templates(
            instance_id=instance_id,
            user_id=current_user['id']
        )

        # Format response
        return [{
            "id": t['template_id'],
            "templateId": t['template_id'],
            "name": t['name'],
            "description": t.get('description'),
            "sqlQuery": t['sql_query'],
            "instanceId": t['instance_id'],
            "tags": t.get('tags', []),
            "usageCount": t.get('usage_count', 0),
            "createdAt": t.get('created_at'),
            "updatedAt": t.get('updated_at')
        } for t in templates]
    except Exception as e:
        logger.error(f"Error listing instance templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance templates")


@router.post("/{instance_id}/templates", status_code=201)
def create_instance_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template: InstanceTemplateCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new template for a specific instance"""
    logger.info(f"Creating instance template - User: {current_user.get('id')}, Instance: {instance_id}, Name: {template.name}")

    try:
        template_data = {
            "name": template.name,
            "description": template.description,
            "sql_query": template.sql_query,
            "instance_id": instance_id,
            "user_id": current_user['id'],
            "tags": template.tags
        }

        created = instance_template_service.create_template(template_data)

        if not created:
            logger.error("Instance template service returned None")
            raise HTTPException(status_code=500, detail="Failed to create instance template")

        logger.info(f"Template created successfully with ID: {created.get('template_id')}")

        return {
            "templateId": created['template_id'],
            "name": created['name'],
            "instanceId": created['instance_id'],
            "createdAt": created['created_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating instance template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create instance template: {str(e)}")


@router.get("/{instance_id}/templates/{template_id}")
def get_instance_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific template by ID"""
    try:
        template = instance_template_service.get_template(template_id, current_user['id'])

        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")

        # Verify template belongs to the specified instance
        if template['instance_id'] != instance_id:
            raise HTTPException(status_code=404, detail="Template not found for this instance")

        return {
            "id": template['template_id'],
            "templateId": template['template_id'],
            "name": template['name'],
            "description": template.get('description'),
            "sqlQuery": template['sql_query'],
            "instanceId": template['instance_id'],
            "tags": template.get('tags', []),
            "usageCount": template.get('usage_count', 0),
            "createdAt": template.get('created_at'),
            "updatedAt": template.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instance template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance template")


@router.put("/{instance_id}/templates/{template_id}")
def update_instance_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier"),
    updates: InstanceTemplateUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update an instance template (owner only)"""
    try:
        update_data = updates.dict(exclude_none=True)

        updated = instance_template_service.update_template(
            template_id=template_id,
            user_id=current_user['id'],
            updates=update_data
        )

        if not updated:
            raise HTTPException(status_code=404, detail="Template not found or access denied")

        # Verify template belongs to the specified instance
        if updated['instance_id'] != instance_id:
            raise HTTPException(status_code=404, detail="Template not found for this instance")

        return {
            "templateId": updated['template_id'],
            "name": updated['name'],
            "updatedAt": updated['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instance template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update instance template")


@router.delete("/{instance_id}/templates/{template_id}")
def delete_instance_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete an instance template (owner only)"""
    try:
        # First verify template belongs to this instance
        template = instance_template_service.get_template(template_id, current_user['id'])
        if template and template['instance_id'] != instance_id:
            raise HTTPException(status_code=404, detail="Template not found for this instance")

        success = instance_template_service.delete_template(template_id, current_user['id'])

        if not success:
            raise HTTPException(status_code=404, detail="Template not found or access denied")

        return {"message": "Instance template deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting instance template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete instance template")


@router.post("/{instance_id}/templates/{template_id}/use")
def use_instance_template(
    instance_id: str = Path(..., description="AMC instance UUID"),
    template_id: str = Path(..., description="Template identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark a template as used (increment usage count)"""
    try:
        # Verify access first
        template = instance_template_service.get_template(template_id, current_user['id'])
        if not template:
            raise HTTPException(status_code=404, detail="Template not found or access denied")

        # Verify template belongs to this instance
        if template['instance_id'] != instance_id:
            raise HTTPException(status_code=404, detail="Template not found for this instance")

        # Increment usage
        instance_template_service.increment_usage(template_id)

        return {
            "templateId": template_id,
            "usageCount": template.get('usage_count', 0) + 1
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking template as used: {e}")
        raise HTTPException(status_code=500, detail="Failed to update usage count")
