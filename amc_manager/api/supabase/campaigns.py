"""Campaigns API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from math import ceil

from ...core.supabase_client import SupabaseManager
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
def list_campaigns(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in campaign name"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    state: Optional[str] = Query("ENABLED", description="Filter by campaign state (defaults to ENABLED)"),
    type: Optional[str] = Query(None, description="Filter by campaign type"),
    sort_by: str = Query("name", description="Sort by field: name, brand, state, campaign_id"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    show_all_states: bool = Query(False, description="Show all campaign states, not just ENABLED"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List campaigns with filtering, sorting and pagination
    
    By default shows only ENABLED campaigns to improve performance.
    Set show_all_states=true or state='' to see all campaigns.
    """
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Build query
        query = client.table('campaigns').select('*', count='exact')
        
        # Apply filters
        if search:
            query = query.ilike('name', f'%{search}%')
        if brand:
            query = query.eq('brand', brand)
        
        # State filter - default to ENABLED unless explicitly showing all
        if show_all_states or state == '':
            # Don't filter by state - show all
            pass
        elif state:
            # Apply the state filter (defaults to ENABLED)
            query = query.eq('state', state)
            
        if type:
            query = query.eq('type', type)
        
        # Apply sorting
        order_column = {
            'name': 'name',
            'brand': 'brand', 
            'state': 'state',
            'campaign_id': 'campaign_id'
        }.get(sort_by, 'name')
        
        query = query.order(order_column, desc=(sort_order == 'desc'))
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        # Execute query
        result = query.execute()
        
        # Get total count for pagination
        total_count = result.count if hasattr(result, 'count') else len(result.data)
        total_pages = ceil(total_count / page_size) if total_count else 0
        
        # Format response
        campaigns = [{
            "id": str(c.get('id', '')),
            "campaignId": str(c['campaign_id']),
            "name": c['name'],
            "brand": c.get('brand', 'Unknown'),
            "state": c.get('state', 'UNKNOWN'),
            "type": c.get('type', 'sp'),
            "targetingType": c.get('targeting_type', ''),
            "biddingStrategy": c.get('bidding_strategy', ''),
            "portfolioId": c.get('portfolio_id', ''),
            "createdAt": c.get('created_at', ''),
            "updatedAt": c.get('updated_at', '')
        } for c in result.data]
        
        return {
            "campaigns": campaigns,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages,
                "hasNext": page < total_pages,
                "hasPrev": page > 1
            }
        }
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
) -> List[Dict[str, Any]]:
    """List unique brands from campaigns table"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get total count first
        count_result = client.table('campaigns').select('*', count='exact').limit(1).execute()
        total_count = count_result.count if hasattr(count_result, 'count') else 0
        
        # Extract all unique brands by fetching in batches
        brands = set()
        batch_size = 1000
        offset = 0
        
        while offset < total_count:
            result = client.table('campaigns').select('brand').range(offset, offset + batch_size - 1).execute()
            
            if not result.data:
                break
                
            for campaign in result.data:
                if campaign.get('brand'):
                    brands.add(campaign['brand'])
            
            offset += batch_size
        
        # Count campaigns per brand (these counts use Supabase's count feature which works correctly)
        brand_counts = {}
        for brand in brands:
            count_result = client.table('campaigns').select('*', count='exact').eq('brand', brand).limit(1).execute()
            brand_counts[brand] = count_result.count if hasattr(count_result, 'count') else 0
        
        return [
            {"brand": brand, "campaign_count": brand_counts[brand]} 
            for brand in sorted(brands)
        ]
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")


@router.get("/stats")
def get_campaign_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get campaign statistics from campaigns table"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get total count first
        count_result = client.table('campaigns').select('*', count='exact').limit(1).execute()
        total_count = count_result.count if hasattr(count_result, 'count') else 0
        
        # Initialize stats
        stats = {
            "total_campaigns": total_count,
            "by_state": {},
            "by_type": {},
            "by_brand": {},
            "by_targeting": {}
        }
        
        # Fetch campaigns in batches to avoid the 1000 row limit
        batch_size = 1000
        offset = 0
        
        while offset < total_count:
            result = client.table('campaigns').select('*').range(offset, offset + batch_size - 1).execute()
            campaigns = result.data
            
            if not campaigns:
                break
                
            for campaign in campaigns:
                # By state
                state = campaign.get('state', 'UNKNOWN')
                stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
                
                # By type
                camp_type = campaign.get('type', 'unknown')
                stats['by_type'][camp_type] = stats['by_type'].get(camp_type, 0) + 1
                
                # By brand
                brand = campaign.get('brand', 'untagged')
                stats['by_brand'][brand] = stats['by_brand'].get(brand, 0) + 1
                
                # By targeting type
                targeting = campaign.get('targeting_type', 'unknown')
                stats['by_targeting'][targeting] = stats['by_targeting'].get(targeting, 0) + 1
            
            offset += batch_size
        
        return stats
    except Exception as e:
        logger.error(f"Error calculating campaign stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate stats")