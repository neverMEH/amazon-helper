"""AMC Instances API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...services.instance_brand_mapping import get_brands_for_instance
from ...core.supabase_client import SupabaseManager
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_instances(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all AMC instances accessible to the current user"""
    try:
        instances = await db_service.get_user_instances(current_user['id'])
        
        # Format response with camelCase for frontend
        return [{
            "id": inst['id'],
            "instanceId": inst['instance_id'],
            "instanceName": inst['instance_name'],
            "type": inst.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": inst['region'],
            "status": inst['status'],
            "isActive": inst['status'] == 'active',
            "accountId": inst['amc_accounts']['account_id'] if 'amc_accounts' in inst else None,
            "accountName": inst['amc_accounts']['account_name'] if 'amc_accounts' in inst else None,
            "endpointUrl": inst.get('endpoint_url'),
            "dataUploadAccountId": inst.get('data_upload_account_id'),
            "createdAt": inst.get('created_at', '')
        } for inst in instances]
    except Exception as e:
        logger.error(f"Error listing instances: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instances")


@router.get("/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get details for a specific AMC instance"""
    try:
        instance = await db_service.get_instance_by_id(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Verify user has access
        user_instances = await db_service.get_user_instances(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "instance_id": instance['instance_id'],
            "instance_name": instance['instance_name'],
            "instance_type": instance.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": instance['region'],
            "status": instance['status'],
            "account": {
                "id": instance['amc_accounts']['account_id'],
                "name": instance['amc_accounts']['account_name']
            } if 'amc_accounts' in instance else None,
            "endpoint_url": instance.get('endpoint_url'),
            "data_upload_account_id": instance.get('data_upload_account_id'),
            "capabilities": instance.get('capabilities', {}),
            "created_at": instance.get('created_at'),
            "updated_at": instance.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instance {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance")


@router.get("/{instance_id}/campaigns")
async def get_instance_campaigns(
    instance_id: str,
    brand_tag: Optional[str] = Query(None, description="Filter by brand tag"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get campaigns associated with an AMC instance based on brand matching"""
    try:
        # Get instance details
        instance = await db_service.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Verify user has access
        user_instances = await db_service.get_user_instances(current_user['id'])
        if not any(inst['instance_id'] == instance_id for inst in user_instances):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get brand keywords from instance name
        instance_name = instance.get('instance_name', '')
        brand_keywords = get_brands_for_instance(instance_name)
        
        # Query campaigns from campaigns table
        client = SupabaseManager.get_client(use_service_role=True)
        query = client.table('campaigns').select('*')
        
        # Filter by brand if we have keywords
        if brand_keywords and len(brand_keywords) > 0:
            # Use OR condition for multiple brand matches
            brand_filters = []
            for brand in brand_keywords:
                brand_filters.append(f"brand.ilike.%{brand}%")
            
            if len(brand_filters) == 1:
                query = query.ilike('brand', f'%{brand_keywords[0]}%')
            else:
                # For multiple brands, we need to fetch all and filter in Python
                # since Supabase doesn't support complex OR conditions easily
                pass
        
        # Apply brand_tag filter if provided
        if brand_tag:
            query = query.eq('brand', brand_tag)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        # Default to ENABLED campaigns
        query = query.eq('state', 'ENABLED')
        
        result = query.execute()
        campaigns = result.data
        
        # If we have multiple brand keywords, filter in Python
        if brand_keywords and len(brand_keywords) > 1 and not brand_tag:
            filtered_campaigns = []
            for campaign in campaigns:
                campaign_brand = (campaign.get('brand') or '').lower()
                if any(keyword.lower() in campaign_brand for keyword in brand_keywords):
                    filtered_campaigns.append(campaign)
            campaigns = filtered_campaigns
        
        # Format response to match frontend expectations
        return [{
            "campaignId": str(campaign.get('campaign_id', '')),
            "name": campaign.get('name', ''),
            "type": campaign.get('type', 'sp').upper(),
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


@router.get("/{instance_id}/metrics")
async def get_instance_metrics(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get metrics for an AMC instance"""
    # Verify access
    instance = await db_service.get_instance_by_id(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    user_instances = await db_service.get_user_instances(current_user['id'])
    if not any(inst['instance_id'] == instance_id for inst in user_instances):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Implement actual metrics fetching from AMC API
    # For now, return mock data
    return {
        "instance_id": instance_id,
        "metrics": {
            "total_workflows": 0,
            "active_workflows": 0,
            "executions_today": 0,
            "executions_this_week": 0,
            "storage_used_gb": 0,
            "last_execution": None
        }
    }