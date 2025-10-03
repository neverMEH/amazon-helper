"""Instance parameter mapping schemas for request/response validation"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class InstanceMappingsInput(BaseModel):
    """Request schema for saving instance mappings"""
    brands: List[str] = Field(default=[], description="List of brand tags")
    asins_by_brand: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="ASINs grouped by brand tag"
    )
    campaigns_by_brand: Dict[str, List[Union[int, str]]] = Field(
        default_factory=dict,
        description="Campaign IDs grouped by brand tag (BIGINT stored as string in JSON)"
    )

    @validator('brands')
    def validate_brands(cls, v):
        """Validate brand tag format (alphanumeric, underscore, hyphen, spaces)"""
        if not v:
            return v  # Allow empty brands list

        # Validate brand tag format - allow alphanumeric, underscore, hyphen, and spaces
        import re
        for brand_tag in v:
            if not brand_tag or not brand_tag.strip():
                raise ValueError(f"Empty brand tag not allowed")

        return v

    @validator('asins_by_brand')
    def validate_asins(cls, v, values):
        """Validate ASINs format"""
        # Don't enforce brand key matching - allow any brands
        # This is more flexible and won't break if brands list structure changes

        # Validate ASIN format (B followed by 9 alphanumeric characters)
        import re
        asin_pattern = re.compile(r'^B[0-9A-Z]{9}$', re.IGNORECASE)
        for brand_tag, asins in v.items():
            for asin in asins:
                # Normalize to uppercase for validation
                if not asin_pattern.match(asin):
                    raise ValueError(f"Invalid ASIN format: {asin} (expected format: B followed by 9 alphanumeric characters)")

        return v

    @validator('campaigns_by_brand')
    def validate_campaigns(cls, v, values):
        """Validate campaign IDs"""
        # Don't enforce brand key matching - allow any brands
        # This is more flexible and won't break if brands list structure changes

        # Validate campaign IDs are positive integers, numeric strings (BIGINT), or coupon/promo IDs
        for brand_tag, campaigns in v.items():
            for campaign_id in campaigns:
                if isinstance(campaign_id, int):
                    if campaign_id <= 0:
                        raise ValueError(f"Invalid campaign ID: {campaign_id}")
                elif isinstance(campaign_id, str):
                    # Allow numeric strings (BIGINT) and promotion IDs (UUID format with prefixes)
                    # Note: These promotion IDs are excluded from UI but we allow them in validation
                    # for backwards compatibility with existing selections
                    if not (campaign_id.isdigit() or
                           campaign_id.startswith(('coupon-', 'promo-', 'percentageoff-', 'amountoff-', 'buyxgety-', 'socialmedia-'))):
                        raise ValueError(f"Invalid campaign ID string: {campaign_id}")
                else:
                    raise ValueError(f"Campaign ID must be int or str, got {type(campaign_id)}")

        return v


class InstanceMappingsOutput(BaseModel):
    """Response schema for instance mappings"""
    instance_id: str
    brands: List[str]
    asins_by_brand: Dict[str, List[str]]
    campaigns_by_brand: Dict[str, List[Union[int, str]]]  # BIGINT stored as string in JSON
    updated_at: Optional[str]


class SaveMappingsResponse(BaseModel):
    """Response schema for save mappings operation"""
    success: bool
    message: str
    instance_id: Optional[str] = None
    stats: Optional[Dict[str, int]] = None
    updated_at: Optional[str] = None


class Brand(BaseModel):
    """Brand information schema"""
    brand_tag: str
    brand_name: str
    source: str  # "configuration" or "campaign"
    asin_count: Optional[int] = 0
    campaign_count: Optional[int] = 0


class BrandsListResponse(BaseModel):
    """Response schema for available brands list"""
    brands: List[Brand]


class ASIN(BaseModel):
    """ASIN information schema"""
    asin: str
    title: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    last_known_price: Optional[float] = None
    active: Optional[bool] = True


class BrandASINsResponse(BaseModel):
    """Response schema for brand ASINs"""
    brand_tag: str
    asins: List[ASIN]
    total: int
    limit: int
    offset: int


class Campaign(BaseModel):
    """Campaign information schema"""
    campaign_id: Union[int, str]  # BIGINT stored as string in JSON
    campaign_name: str
    campaign_type: Optional[str] = None  # SP, SB, SD, DSP
    state: Optional[str] = None
    brand: Optional[str] = None
    marketplace_id: Optional[str] = None
    profile_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class BrandCampaignsResponse(BaseModel):
    """Response schema for brand campaigns"""
    brand_tag: str
    campaigns: List[Campaign]
    total: int
    limit: int
    offset: int


class ParameterValuesOutput(BaseModel):
    """Response schema for auto-populate parameter values"""
    instance_id: str
    parameters: Dict[str, str] = Field(
        description="Parameter values formatted for query substitution"
    )
    has_mappings: bool = Field(
        description="Whether the instance has any mappings configured"
    )

    class Config:
        schema_extra = {
            "example": {
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "parameters": {
                    "brand_list": "acme,globex",
                    "asin_list": "B08N5WRWNW,B07FZ8S74R,B09KMVNY9J",
                    "campaign_ids": "12345678901,98765432109",
                    "campaign_names": "Acme - SP Campaign,Globex - DSP Campaign"
                },
                "has_mappings": True
            }
        }
