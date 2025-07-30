"""Campaigns API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional

from ...services.db_service import db_service
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
def list_campaigns(
    brand_tag: Optional[str] = Query(None, description="Filter by brand tag"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """List campaigns for the current user"""
    try:
        campaigns = db_service.get_user_campaigns_sync(current_user['id'], brand_tag)
        
        # Filter by campaign type if provided
        if campaign_type:
            campaigns = [c for c in campaigns if c.get('campaign_type') == campaign_type]
        
        return [{
            "id": str(c.get('id', '')),
            "campaignId": str(c['campaign_id']),
            "name": c['campaign_name'],
            "originalName": c.get('original_name', c['campaign_name']),
            "campaignType": c['campaign_type'],
            "brandTag": c.get('brand_tag'),
            "marketplaceId": c['marketplace_id'],
            "profileId": c['profile_id'],
            "asins": c.get('asins', []),
            "firstSeenAt": c.get('first_seen_at'),
            "lastSeenAt": c.get('last_seen_at'),
            "createdAt": c.get('created_at', ''),
            "tags": c.get('tags', [])
        } for c in campaigns]
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch campaigns")


@router.post("/sync")
def sync_campaigns(
    profile_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Sync campaigns from Amazon API"""
    # TODO: Implement actual campaign sync from Amazon API
    # This would:
    # 1. Call Amazon Advertising API to get campaigns
    # 2. Process and store in Supabase
    # 3. Auto-tag based on brand configurations
    
    return {
        "status": "pending",
        "message": "Campaign sync initiated",
        "profile_id": profile_id,
        "note": "This endpoint is not yet implemented"
    }


@router.get("/brands")
def list_brands(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """List unique brand tags from campaigns"""
    try:
        campaigns = db_service.get_user_campaigns_sync(current_user['id'])
        
        # Extract unique brand tags
        brand_tags = set()
        for campaign in campaigns:
            if campaign.get('brand_tag'):
                brand_tags.add(campaign['brand_tag'])
        
        return [{"brand_tag": tag} for tag in sorted(brand_tags)]
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")


@router.get("/stats")
def get_campaign_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get campaign statistics"""
    try:
        campaigns = db_service.get_user_campaigns_sync(current_user['id'])
        
        # Calculate stats
        stats = {
            "total_campaigns": len(campaigns),
            "by_type": {},
            "by_brand": {},
            "by_marketplace": {}
        }
        
        for campaign in campaigns:
            # By type
            camp_type = campaign.get('campaign_type', 'unknown')
            stats['by_type'][camp_type] = stats['by_type'].get(camp_type, 0) + 1
            
            # By brand
            brand = campaign.get('brand_tag', 'untagged')
            stats['by_brand'][brand] = stats['by_brand'].get(brand, 0) + 1
            
            # By marketplace
            marketplace = campaign.get('marketplace_id', 'unknown')
            stats['by_marketplace'][marketplace] = stats['by_marketplace'].get(marketplace, 0) + 1
        
        return stats
    except Exception as e:
        logger.error(f"Error calculating campaign stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate stats")