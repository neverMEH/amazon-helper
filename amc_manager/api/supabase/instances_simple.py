"""AMC Instances API endpoints using Supabase - Simplified version"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...services.brand_service import brand_service
from ...core.logger_simple import get_logger
from .auth import get_current_user
from ...services.amc_sync_service import amc_sync_service

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


@router.patch("/{instance_id}/status")
def update_instance_status(
    instance_id: str,
    status_update: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update instance active status (activate/deactivate)"""
    try:
        # Verify user has access to instance
        user_instances = db_service.get_user_instances_sync(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied to instance")

        # Get instance details
        instance = db_service.get_instance_details_sync(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")

        # Extract is_active from request body
        is_active = status_update.get('is_active')
        if is_active is None:
            raise HTTPException(status_code=400, detail="is_active field is required")

        # Update instance status in database
        from ...core.supabase_client import SupabaseManager
        client = SupabaseManager.get_client(use_service_role=True)

        new_status = 'active' if is_active else 'inactive'
        result = client.table('amc_instances').update({
            'status': new_status
        }).eq('instance_id', instance_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update instance status")

        logger.info(f"Instance {instance_id} status updated to {new_status} by user {current_user['id']}")

        return {
            "instanceId": instance_id,
            "status": new_status,
            "isActive": is_active,
            "message": f"Instance {'activated' if is_active else 'deactivated'} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instance status {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update instance status")


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
        
        # Get instance details to get the internal ID
        instance = db_service.get_instance_details_sync(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Get Supabase client
        from ...core.supabase_client import SupabaseManager
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get brands associated with this instance from instance_brands table
        brand_result = client.table('instance_brands').select('brand_tag').eq('instance_id', instance['id']).execute()
        instance_brands = [b['brand_tag'] for b in brand_result.data if b.get('brand_tag')]
        
        # If no brands are configured for this instance, return empty
        if not instance_brands and not brand_tag:
            logger.info(f"No brands configured for instance {instance_id}")
            return []
        
        # Build query for campaigns
        query = client.table('campaigns').select('*')
        
        # Apply brand_tag filter if provided, otherwise use instance brands
        if brand_tag:
            # Specific brand requested - use case-insensitive match
            query = query.ilike('brand', brand_tag)
        elif len(instance_brands) == 1:
            # Single brand - use case-insensitive filter
            query = query.ilike('brand', instance_brands[0])
        else:
            # Multiple brands - we'll filter in Python after fetch
            # (Supabase doesn't support OR conditions well)
            pass
        
        # Default to ENABLED campaigns
        query = query.eq('state', 'ENABLED')
        
        # Execute query
        result = query.execute()
        campaigns = result.data
        
        # If we have multiple brands and no specific filter, filter in Python
        if len(instance_brands) > 1 and not brand_tag:
            filtered_campaigns = []
            # Convert instance brands to lowercase for case-insensitive comparison
            instance_brands_lower = [b.lower() for b in instance_brands]
            for campaign in campaigns:
                campaign_brand = (campaign.get('brand') or '').lower()
                if campaign_brand in instance_brands_lower:
                    filtered_campaigns.append(campaign)
            campaigns = filtered_campaigns
        
        # Format response to match frontend expectations
        return [{
            "campaignId": str(campaign.get('campaign_id', '')),
            "name": campaign.get('name', ''),
            "type": campaign.get('type', 'sp').upper() if campaign.get('type') else 'SP',
            "brandTag": campaign.get('brand', ''),
            "asins": campaign.get('asins', []) if campaign.get('asins') else [],
            "marketplaceId": campaign.get('marketplace_id', 'A1AM78C64UM0Y8'),
            "createdAt": campaign.get('created_at', '')
        } for campaign in campaigns]
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


@router.post("/sync")
async def sync_instances(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Sync AMC instances from Amazon API for the current user
    
    This will:
    1. Fetch AMC accounts from Amazon API
    2. For each account, fetch associated AMC instances
    3. Store/update the data in the database
    """
    try:
        logger.info(f"Starting AMC instance sync for user {current_user['id']}")
        
        # Run the sync
        result = await amc_sync_service.sync_user_instances(current_user['id'])
        
        if result['success']:
            logger.info(f"Successfully synced instances: {result['message']}")
            return result
        else:
            logger.error(f"Sync failed: {result['error']}")
            raise HTTPException(
                status_code=400, 
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sync: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to sync instances from Amazon"
        )