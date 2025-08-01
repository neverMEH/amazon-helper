"""AMC Instances API endpoints using Supabase - Simplified version"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...services.brand_service import brand_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
def list_instances(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List all AMC instances accessible to the current user with optimized query"""
    try:
        # Use the new optimized method
        instances = db_service.get_user_instances_with_data_sync(current_user['id'])
        
        # Apply pagination
        paginated = instances[offset:offset + limit]
        
        # Format response with camelCase for frontend
        result = []
        for inst in paginated:
            account_id = inst['amc_accounts']['account_id'] if 'amc_accounts' in inst else None
            
            result.append({
                "id": inst['id'],
                "instanceId": inst['instance_id'],
                "instanceName": inst['instance_name'],
                "type": inst.get('capabilities', {}).get('instance_type', 'STANDARD'),
                "region": inst['region'],
                "status": inst['status'],
                "isActive": inst['status'] == 'active',
                "accountId": account_id,
                "accountName": inst['amc_accounts']['account_name'] if 'amc_accounts' in inst else None,
                "endpointUrl": inst.get('endpoint_url'),
                "dataUploadAccountId": inst.get('data_upload_account_id'),
                "createdAt": inst.get('created_at', ''),
                "brands": inst.get('brands', []),
                "stats": inst.get('stats', {
                    "totalCampaigns": 0,
                    "totalWorkflows": 0,
                    "activeWorkflows": 0
                })
            })
        
        return result
    except Exception as e:
        logger.error(f"Error listing instances: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instances")


@router.get("/{instance_id}")
def get_instance(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed information about a specific AMC instance"""
    try:
        # Get instance details
        instance = db_service.get_instance_details_sync(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Verify user has access
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get stats
        stats = db_service.get_instance_stats_sync(instance_id)
        
        # Get brands directly associated with this instance
        brands = brand_service.get_instance_brands_sync(instance_id)
        
        return {
            "id": instance['id'],
            "instanceId": instance['instance_id'],
            "instanceName": instance['instance_name'],
            "type": instance.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": instance['region'],
            "status": instance['status'],
            "isActive": instance['status'] == 'active',
            "account": {
                "accountId": instance['amc_accounts']['account_id'] if 'amc_accounts' in instance else None,
                "accountName": instance['amc_accounts']['account_name'] if 'amc_accounts' in instance else None,
                "marketplaceId": instance['amc_accounts']['marketplace_id'] if 'amc_accounts' in instance else None
            },
            "endpointUrl": instance.get('endpoint_url'),
            "dataUploadAccountId": instance.get('data_upload_account_id'),
            "capabilities": instance.get('capabilities', {}),
            "createdAt": instance.get('created_at', ''),
            "updatedAt": instance.get('updated_at', ''),
            "brands": brands,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance")


@router.get("/{instance_id}/campaigns")
def get_instance_campaigns(
    instance_id: str,
    brand_tag: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get campaigns associated with an instance"""
    try:
        # Verify user has access to instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get campaigns filtered by instance brands
        campaigns = db_service.get_instance_campaigns_filtered_sync(instance_id, current_user['id'])
        
        # Additional filtering by specific brand if requested
        if brand_tag:
            campaigns = [c for c in campaigns if c.get('brand_tag') == brand_tag]
        return [{
            "campaignId": str(c['campaign_id']),
            "name": c['campaign_name'],
            "type": c['campaign_type'],
            "brandTag": c.get('brand_tag'),
            "asins": c.get('asins', []),
            "marketplaceId": c['marketplace_id'],
            "createdAt": c.get('created_at', '')
        } for c in campaigns]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaigns for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")


@router.get("/{instance_id}/workflows")
def get_instance_workflows(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get workflows available for an instance (includes all templates)"""
    try:
        # Verify user has access
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get all workflows for user
        workflows = db_service.get_user_workflows_sync(current_user['id'])
        
        # Include workflows that are either:
        # 1. Templates (available for all instances)
        # 2. Specifically created for this instance
        available_workflows = []
        for w in workflows:
            if w.get('is_template', False):
                # Templates are available on all instances
                available_workflows.append(w)
            elif 'amc_instances' in w and w['amc_instances'].get('instance_id') == instance_id:
                # Instance-specific workflows
                available_workflows.append(w)
        
        # Get last execution time for each workflow on this instance
        from ...core.supabase_client import SupabaseManager
        client = SupabaseManager.get_client(use_service_role=True)
        
        result = []
        for w in available_workflows:
            # Get last execution for this workflow on this instance if possible
            last_executed = None
            try:
                exec_response = client.table('workflow_executions')\
                    .select('started_at')\
                    .eq('workflow_id', w['id'])\
                    .order('started_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if exec_response.data:
                    last_executed = exec_response.data[0]['started_at']
            except:
                pass
            
            result.append({
                "workflowId": w['workflow_id'],
                "name": w['name'],
                "description": w.get('description'),
                "status": w.get('status', 'active'),
                "isTemplate": w.get('is_template', False),
                "tags": w.get('tags', []),
                "createdAt": w.get('created_at', ''),
                "lastExecutedAt": last_executed,
                "sourceInstanceId": w.get('instance_id') if not w.get('is_template') else None
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflows for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch workflows")


@router.get("/{instance_id}/brands")
def get_instance_brands(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[str]:
    """Get brands associated with an instance"""
    try:
        # Verify user has access
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Get brands for this instance
        brands = brand_service.get_instance_brands_sync(instance_id)
        return brands
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brands for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")


@router.put("/{instance_id}/brands")
def update_instance_brands(
    instance_id: str,
    brand_tags: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update brands associated with an instance"""
    try:
        # Verify user has access
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")
        
        # Validate brands
        for brand_tag in brand_tags:
            is_valid, error = brand_service.validate_brand_tag(brand_tag)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid brand tag '{brand_tag}': {error}")
        
        # Update brands
        success = brand_service.update_instance_brands_sync(instance_id, brand_tags, current_user['id'])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update brands")
        
        return {"success": True, "brands": brand_tags}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating brands for instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update brands")