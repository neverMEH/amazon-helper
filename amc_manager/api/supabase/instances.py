"""AMC Instances API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...core.supabase_client import SupabaseManager
from ...core.logger_simple import get_logger
from .auth import get_current_user, get_current_user_optional

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_instances(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List all AMC instances accessible to the current user"""
    try:
        instances = await db_service.get_user_instances(current_user['id'])
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Format response with camelCase for frontend and add brands
        formatted_instances = []
        for inst in instances:
            # Get brands for this instance (just the brand tags as strings)
            brands_result = client.table('instance_brands').select('brand_tag').eq('instance_id', inst['id']).execute()
            brands = [b['brand_tag'] for b in brands_result.data] if brands_result.data else []
            
            formatted_instances.append({
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
                "brands": brands,  # Add brands array
                "createdAt": inst.get('created_at', '')
            })
        
        return formatted_instances
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
        
        # Get brands for this instance (just the brand tags as strings)
        client = SupabaseManager.get_client(use_service_role=True)
        brands_result = client.table('instance_brands').select('brand_tag').eq('instance_id', instance['id']).execute()
        brands = [b['brand_tag'] for b in brands_result.data] if brands_result.data else []
        
        return {
            "id": instance['id'],  # Include internal UUID
            "instanceId": instance['instance_id'],
            "instanceName": instance['instance_name'],
            "instanceType": instance.get('capabilities', {}).get('instance_type', 'STANDARD'),
            "region": instance['region'],
            "status": instance['status'],
            "account": {
                "id": instance['amc_accounts']['account_id'],
                "name": instance['amc_accounts']['account_name']
            } if 'amc_accounts' in instance else None,
            "brands": brands,  # Add brands array
            "endpointUrl": instance.get('endpoint_url'),
            "dataUploadAccountId": instance.get('data_upload_account_id'),
            "capabilities": instance.get('capabilities', {}),
            "createdAt": instance.get('created_at'),
            "updatedAt": instance.get('updated_at')
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
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
) -> List[Dict[str, Any]]:
    """Get campaigns associated with an AMC instance based on brand matching"""
    try:
        # Get instance details
        instance = await db_service.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        
        # Temporarily skip auth check for testing
        # TODO: Re-enable auth after testing
        
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get brands associated with this instance from instance_brands table
        brand_result = client.table('instance_brands').select('brand_tag').eq('instance_id', instance['id']).execute()
        instance_brands = [b['brand_tag'] for b in brand_result.data if b.get('brand_tag')]
        
        # If no brands are configured for this instance, return empty
        if not instance_brands and not brand_tag:
            logger.info(f"No brands configured for instance {instance_id}")
            return []
        
        # Query campaigns from campaigns table
        query = client.table('campaigns').select('*', count='exact')
        
        # Apply brand_tag filter if provided, otherwise use instance brands
        if brand_tag:
            query = query.ilike('brand', brand_tag)  # Case-insensitive match
        elif len(instance_brands) == 1:
            # Single brand - use case-insensitive filter
            query = query.ilike('brand', instance_brands[0])
        else:
            # Multiple brands - we'll filter in Python after fetch
            # Supabase doesn't support OR conditions well
            pass
        
        # Default to ENABLED campaigns
        query = query.eq('state', 'ENABLED')
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
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