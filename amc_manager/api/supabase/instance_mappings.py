"""Instance Parameter Mapping API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional

from ...services.instance_mapping_service import instance_mapping_service
from ...schemas.instance_mapping import (
    InstanceMappingsInput,
    InstanceMappingsOutput,
    SaveMappingsResponse,
    BrandsListResponse,
    BrandASINsResponse,
    BrandCampaignsResponse,
    ParameterValuesOutput
)
from ...core.logger_simple import get_logger
from .auth import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{instance_id}/available-brands", response_model=BrandsListResponse)
async def get_available_brands(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all brands available to the user for selection.

    Args:
        instance_id: The instance UUID
        current_user: Authenticated user from JWT token

    Returns:
        List of available brands with metadata
    """
    try:
        brands = instance_mapping_service.get_available_brands(current_user['id'])
        return {"brands": brands}
    except Exception as e:
        logger.error(f"Error fetching available brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch available brands")


@router.get("/{instance_id}/brands/{brand_tag}/asins", response_model=BrandASINsResponse)
async def get_brand_asins(
    instance_id: str,
    brand_tag: str,
    search: Optional[str] = Query(None, description="Search term for filtering ASINs"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all ASINs associated with a specific brand.

    Args:
        instance_id: The instance UUID
        brand_tag: The brand identifier
        search: Optional search term
        limit: Maximum results (1-500)
        offset: Pagination offset
        current_user: Authenticated user

    Returns:
        List of ASINs with pagination metadata
    """
    try:
        result = instance_mapping_service.get_brand_asins(
            brand_tag=brand_tag,
            user_id=current_user['id'],
            search=search,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching ASINs for brand {brand_tag}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brand ASINs")


@router.get("/{instance_id}/brands/{brand_tag}/campaigns", response_model=BrandCampaignsResponse)
async def get_brand_campaigns(
    instance_id: str,
    brand_tag: str,
    search: Optional[str] = Query(None, description="Search term for filtering campaigns"),
    campaign_type: Optional[str] = Query(None, description="Filter by campaign type (SP, SB, SD, DSP)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all campaigns associated with a specific brand.

    Args:
        instance_id: The instance UUID
        brand_tag: The brand identifier
        search: Optional search term
        campaign_type: Optional campaign type filter
        limit: Maximum results (1-500)
        offset: Pagination offset
        current_user: Authenticated user

    Returns:
        List of campaigns with pagination metadata
    """
    try:
        result = instance_mapping_service.get_brand_campaigns(
            brand_tag=brand_tag,
            user_id=current_user['id'],
            search=search,
            campaign_type=campaign_type,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching campaigns for brand {brand_tag}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brand campaigns")


@router.get("/{instance_id}/mappings", response_model=InstanceMappingsOutput)
async def get_instance_mappings(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retrieve current parameter mappings for an instance.

    Args:
        instance_id: The instance UUID
        current_user: Authenticated user

    Returns:
        Instance mappings with brands, ASINs, and campaigns
    """
    try:
        mappings = instance_mapping_service.get_instance_mappings(
            instance_id=instance_id,
            user_id=current_user['id']
        )

        # Check if user has access
        if not mappings['brands'] and mappings.get('error'):
            raise HTTPException(status_code=403, detail="Access denied to this instance")

        return mappings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching instance mappings for {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch instance mappings")


@router.post("/{instance_id}/mappings", response_model=SaveMappingsResponse)
async def save_instance_mappings(
    instance_id: str,
    mappings: InstanceMappingsInput,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Save or update parameter mappings for an instance.

    This is a transactional operation: all existing mappings are deleted
    and replaced with the new mappings.

    Args:
        instance_id: The instance UUID
        mappings: Mapping data with brands, ASINs, and campaigns
        current_user: Authenticated user

    Returns:
        Success status with operation statistics
    """
    try:
        result = instance_mapping_service.save_instance_mappings(
            instance_id=instance_id,
            user_id=current_user['id'],
            mappings=mappings.dict()
        )

        if not result['success']:
            # Check if it's a permission error
            if 'Access denied' in result['message']:
                raise HTTPException(status_code=403, detail=result['message'])
            # Otherwise it's a validation or server error
            raise HTTPException(status_code=400, detail=result['message'])

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving instance mappings for {instance_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save mappings: {str(e)}")


@router.get("/{instance_id}/parameter-values", response_model=ParameterValuesOutput)
async def get_parameter_values(
    instance_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get formatted parameter values for auto-population in query execution.

    This endpoint returns comma-separated strings ready for substitution
    into query parameters like {{brand_list}}, {{asin_list}}, etc.

    Args:
        instance_id: The instance UUID
        current_user: Authenticated user

    Returns:
        Formatted parameter values for auto-population
    """
    try:
        values = instance_mapping_service.get_parameter_values(
            instance_id=instance_id,
            user_id=current_user['id']
        )
        return values
    except Exception as e:
        logger.error(f"Error getting parameter values for {instance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get parameter values")
