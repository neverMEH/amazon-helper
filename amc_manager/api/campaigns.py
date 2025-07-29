"""Campaign management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..core import AMCAPIClient, get_logger
from ..models import get_db, User, CampaignMapping, BrandConfiguration
from ..services import DataRetrievalService
from .dependencies import get_current_user, get_api_client


logger = get_logger(__name__)
router = APIRouter()


class CampaignBrandTag(BaseModel):
    campaign_id: str
    brand_tag: str
    metadata: Optional[Dict[str, Any]] = {}


class BrandConfigCreate(BaseModel):
    brand_tag: str
    brand_name: str
    description: Optional[str] = None
    yaml_parameters: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = {}
    primary_asins: Optional[List[str]] = []
    campaign_name_patterns: Optional[List[str]] = []


@router.get("/dsp")
async def get_dsp_campaigns(
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    profile_id: Optional[str] = Query(None, description="Advertising profile ID"),
    status: Optional[str] = Query(None, description="Filter by campaign status")
) -> List[Dict[str, Any]]:
    """
    Retrieve DSP campaign data
    """
    try:
        service = DataRetrievalService(api_client)
        
        # Use provided profile_id or user's primary profile
        profile_id = profile_id or current_user.get_primary_profile_id()
        if not profile_id:
            raise HTTPException(status_code=400, detail="No profile ID available")
            
        filters = {}
        if status:
            filters['status'] = status
            
        campaigns = await service.get_dsp_campaigns(
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            profile_id=profile_id,
            filters=filters
        )
        
        return campaigns
        
    except Exception as e:
        logger.error(f"Failed to get DSP campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sponsored")
async def get_sponsored_campaigns(
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    profile_id: Optional[str] = Query(None, description="Advertising profile ID"),
    ad_type: str = Query("all", description="Type of sponsored ads (products, brands, display, all)"),
    status: Optional[str] = Query(None, description="Filter by campaign status")
) -> List[Dict[str, Any]]:
    """
    Retrieve Sponsored Ads campaigns
    """
    try:
        service = DataRetrievalService(api_client)
        
        profile_id = profile_id or current_user.get_primary_profile_id()
        if not profile_id:
            raise HTTPException(status_code=400, detail="No profile ID available")
            
        filters = {}
        if status:
            filters['status'] = status
            
        campaigns = await service.get_sponsored_ads_campaigns(
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            profile_id=profile_id,
            ad_type=ad_type,
            filters=filters
        )
        
        return campaigns
        
    except Exception as e:
        logger.error(f"Failed to get sponsored campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mapping")
async def get_campaign_mappings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_tag: Optional[str] = Query(None, description="Filter by brand tag"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type")
) -> List[Dict[str, Any]]:
    """
    Get campaign ID to name mappings with brand tags
    """
    try:
        query = db.query(CampaignMapping).filter_by(user_id=current_user.id)
        
        if brand_tag:
            query = query.filter_by(brand_tag=brand_tag)
        if campaign_type:
            query = query.filter_by(campaign_type=campaign_type)
            
        mappings = query.all()
        
        return [mapping.to_dict() for mapping in mappings]
        
    except Exception as e:
        logger.error(f"Failed to get campaign mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mapping/tag")
async def tag_campaign_brand(
    tag_data: CampaignBrandTag,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Tag a campaign with a brand
    """
    try:
        # Find or create campaign mapping
        mapping = db.query(CampaignMapping).filter_by(
            campaign_id=tag_data.campaign_id,
            user_id=current_user.id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Campaign mapping not found")
            
        # Update brand tag
        mapping.brand_tag = tag_data.brand_tag
        mapping.brand_metadata = tag_data.metadata
        
        db.commit()
        
        return mapping.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to tag campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brands")
async def list_brand_configurations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all brand configurations
    """
    try:
        brands = db.query(BrandConfiguration).filter(
            (BrandConfiguration.owner_user_id == current_user.id) |
            (BrandConfiguration.shared_with_users.contains([current_user.id]))
        ).all()
        
        return [brand.to_dict() for brand in brands]
        
    except Exception as e:
        logger.error(f"Failed to list brand configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brands")
async def create_brand_configuration(
    brand_data: BrandConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new brand configuration
    """
    try:
        # Check if brand tag already exists
        existing = db.query(BrandConfiguration).filter_by(
            brand_tag=brand_data.brand_tag
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Brand tag already exists")
            
        # Create new brand configuration
        brand = BrandConfiguration(
            brand_tag=brand_data.brand_tag,
            brand_name=brand_data.brand_name,
            description=brand_data.description,
            yaml_parameters=brand_data.yaml_parameters,
            default_parameters=brand_data.default_parameters,
            primary_asins=brand_data.primary_asins,
            campaign_name_patterns=brand_data.campaign_name_patterns,
            owner_user_id=current_user.id
        )
        
        db.add(brand)
        db.commit()
        
        return brand.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create brand configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brands/{brand_tag}")
async def get_brand_configuration(
    brand_tag: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific brand configuration
    """
    try:
        brand = db.query(BrandConfiguration).filter_by(brand_tag=brand_tag).filter(
            (BrandConfiguration.owner_user_id == current_user.id) |
            (BrandConfiguration.shared_with_users.contains([current_user.id]))
        ).first()
        
        if not brand:
            raise HTTPException(status_code=404, detail="Brand configuration not found")
            
        return brand.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get brand configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_campaigns(
    current_user: User = Depends(get_current_user),
    api_client: AMCAPIClient = Depends(get_api_client),
    db: Session = Depends(get_db),
    profile_id: Optional[str] = Query(None, description="Advertising profile ID")
) -> Dict[str, Any]:
    """
    Sync campaigns from Amazon Advertising API to local database
    """
    try:
        service = DataRetrievalService(api_client)
        
        profile_id = profile_id or current_user.get_primary_profile_id()
        if not profile_id:
            raise HTTPException(status_code=400, detail="No profile ID available")
            
        # Get all campaigns
        all_campaigns = []
        
        # Get DSP campaigns
        dsp_campaigns = await service.get_dsp_campaigns(
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            profile_id=profile_id
        )
        all_campaigns.extend(dsp_campaigns)
        
        # Get Sponsored Ads campaigns
        sponsored_campaigns = await service.get_sponsored_ads_campaigns(
            user_id=current_user.id,
            user_token=current_user.auth_tokens,
            profile_id=profile_id,
            ad_type='all'
        )
        all_campaigns.extend(sponsored_campaigns)
        
        # Update database
        synced_count = 0
        for campaign in all_campaigns:
            # Find existing mapping
            mapping = db.query(CampaignMapping).filter_by(
                campaign_id=campaign.get('campaignId'),
                user_id=current_user.id
            ).first()
            
            if mapping:
                # Update existing
                if mapping.campaign_name != campaign.get('name'):
                    mapping.add_name_to_history(mapping.campaign_name)
                    mapping.campaign_name = campaign.get('name')
                mapping.last_seen_at = datetime.utcnow().isoformat()
            else:
                # Create new
                mapping = CampaignMapping(
                    campaign_id=campaign.get('campaignId'),
                    campaign_name=campaign.get('name'),
                    original_name=campaign.get('originalName', campaign.get('name')),
                    campaign_type=campaign.get('campaignType'),
                    marketplace_id=api_client.marketplace_id,
                    profile_id=profile_id,
                    user_id=current_user.id,
                    first_seen_at=datetime.utcnow().isoformat(),
                    last_seen_at=datetime.utcnow().isoformat()
                )
                db.add(mapping)
                
            synced_count += 1
            
        db.commit()
        
        return {
            "total_campaigns": len(all_campaigns),
            "synced": synced_count,
            "message": f"Successfully synced {synced_count} campaigns"
        }
        
    except Exception as e:
        logger.error(f"Failed to sync campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))