"""Instance parameter mapping schemas for request/response validation"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime


class InstanceMappingsInput(BaseModel):
    """Request schema for saving instance mappings"""
    brands: List[str] = Field(..., min_items=1, description="List of brand tags")
    asins_by_brand: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="ASINs grouped by brand tag"
    )
    campaigns_by_brand: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Campaign IDs grouped by brand tag"
    )

    @validator('brands')
    def validate_brands(cls, v):
        """Ensure brands list is not empty and contains valid brand tags"""
        if not v:
            raise ValueError("At least one brand must be provided")

        # Validate brand tag format (alphanumeric, underscore, hyphen)
        import re
        for brand_tag in v:
            if not re.match(r'^[a-zA-Z0-9_-]+$', brand_tag):
                raise ValueError(f"Invalid brand tag format: {brand_tag}")

        return v

    @validator('asins_by_brand')
    def validate_asins(cls, v, values):
        """Ensure all ASIN keys match provided brands"""
        brands = values.get('brands', [])
        for brand_tag in v.keys():
            if brand_tag not in brands:
                raise ValueError(f"ASIN brand '{brand_tag}' not in brands list")

        # Validate ASIN format (B followed by 9 alphanumeric characters)
        import re
        asin_pattern = re.compile(r'^B[0-9A-Z]{9}$')
        for brand_tag, asins in v.items():
            for asin in asins:
                if not asin_pattern.match(asin.upper()):
                    raise ValueError(f"Invalid ASIN format: {asin}")

        return v

    @validator('campaigns_by_brand')
    def validate_campaigns(cls, v, values):
        """Ensure all campaign keys match provided brands"""
        brands = values.get('brands', [])
        for brand_tag in v.keys():
            if brand_tag not in brands:
                raise ValueError(f"Campaign brand '{brand_tag}' not in brands list")

        # Validate campaign IDs are positive integers
        for brand_tag, campaigns in v.items():
            for campaign_id in campaigns:
                if not isinstance(campaign_id, int) or campaign_id <= 0:
                    raise ValueError(f"Invalid campaign ID: {campaign_id}")

        return v


class InstanceMappingsOutput(BaseModel):
    """Response schema for instance mappings"""
    instance_id: str
    brands: List[str]
    asins_by_brand: Dict[str, List[str]]
    campaigns_by_brand: Dict[str, List[int]]
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
    brand: str
    image_url: Optional[str] = None
    last_known_price: Optional[float] = None
    active: bool = True


class BrandASINsResponse(BaseModel):
    """Response schema for brand ASINs"""
    brand_tag: str
    asins: List[ASIN]
    total: int
    limit: int
    offset: int


class Campaign(BaseModel):
    """Campaign information schema"""
    campaign_id: int
    campaign_name: str
    campaign_type: str  # SP, SB, SD, DSP
    marketplace_id: str
    profile_id: str
    status: Optional[str] = "active"
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
