"""Example of migrating API endpoints to use Supabase"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from amc_manager.core import (
    CampaignMappingService,
    BrandConfigurationService,
    WorkflowService,
    AMCInstanceService
)

router = APIRouter()

# Example 1: Get campaigns by brand with ASINs
@router.get("/api/campaigns/by-brand/{brand_tag}")
async def get_campaigns_by_brand(
    brand_tag: str,
    user_id: str = Depends(get_current_user),
    service: CampaignMappingService = Depends()
):
    """Get all campaigns for a specific brand including their ASINs"""
    try:
        campaigns = await service.get_campaigns_by_brand(user_id, brand_tag)
        return {
            "brand_tag": brand_tag,
            "total_campaigns": len(campaigns),
            "campaigns": campaigns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example 2: Search campaigns by ASINs
@router.post("/api/campaigns/search-by-asins")
async def search_campaigns_by_asins(
    asins: List[str],
    user_id: str = Depends(get_current_user),
    service: CampaignMappingService = Depends()
):
    """Find all campaigns that contain any of the specified ASINs"""
    try:
        campaigns = await service.get_campaigns_by_asins(user_id, asins)
        return {
            "search_asins": asins,
            "matching_campaigns": campaigns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example 3: Create a new campaign mapping with ASINs
@router.post("/api/campaigns")
async def create_campaign(
    campaign_data: Dict[str, Any],
    user_id: str = Depends(get_current_user),
    campaign_service: CampaignMappingService = Depends(),
    brand_service: BrandConfigurationService = Depends()
):
    """Create a new campaign mapping with automatic brand tagging"""
    try:
        # Auto-tag the campaign based on name patterns
        brand_tag = await brand_service.auto_tag_campaign(
            campaign_data["campaign_name"],
            user_id
        )
        
        # Add brand tag if found
        if brand_tag:
            campaign_data["brand_tag"] = brand_tag
        
        # Add user_id and timestamps
        campaign_data["user_id"] = user_id
        campaign_data["first_seen_at"] = datetime.utcnow().isoformat()
        campaign_data["last_seen_at"] = datetime.utcnow().isoformat()
        
        # Create the campaign
        result = await campaign_service.create_campaign_mapping(campaign_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example 4: Get AMC instances with real-time status
@router.get("/api/amc-instances")
async def get_amc_instances(
    user_id: str = Depends(get_current_user),
    service: AMCInstanceService = Depends()
):
    """Get all AMC instances accessible to the user"""
    try:
        instances = await service.get_user_instances(user_id)
        return {
            "total_instances": len(instances),
            "instances": instances
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example 5: Execute workflow with real-time updates
@router.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execution_params: Dict[str, Any],
    user_id: str = Depends(get_current_user),
    service: WorkflowService = Depends()
):
    """Execute a workflow and subscribe to real-time updates"""
    try:
        # Create execution record
        execution_data = {
            "workflow_id": workflow_id,
            "execution_id": f"exec_{datetime.utcnow().timestamp()}",
            "status": "pending",
            "execution_parameters": execution_params,
            "triggered_by": user_id
        }
        
        execution = await service.create_execution(execution_data)
        
        # In a real implementation, you would trigger the actual AMC workflow here
        # and update the execution status as it progresses
        
        return {
            "execution_id": execution["execution_id"],
            "status": "started",
            "message": "Workflow execution started. Subscribe to real-time updates for status."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))