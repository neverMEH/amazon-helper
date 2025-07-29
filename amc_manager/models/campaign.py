"""Campaign mapping and brand tagging models"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class CampaignMapping(BaseModel):
    """Campaign ID to name mapping with brand tags"""
    __tablename__ = 'campaign_mappings'
    
    # Campaign identification
    campaign_id = Column(String(100), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)  # Original name when first seen
    
    # Campaign metadata
    campaign_type = Column(String(50), nullable=False)  # DSP, Sponsored Products, etc.
    marketplace_id = Column(String(50), nullable=False)
    profile_id = Column(String(100), nullable=False)
    
    # Brand association
    brand_tag = Column(String(100), nullable=True, index=True)
    brand_metadata = Column(JSONB, default=dict)  # Additional brand-specific data
    
    # Tracking
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    first_seen_at = Column(String(50), nullable=False)
    last_seen_at = Column(String(50), nullable=False)
    
    # Historical names (for tracking renames)
    name_history = Column(JSON, default=list)
    
    # Custom tags and metadata
    tags = Column(JSON, default=list)
    custom_parameters = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="campaign_mappings")
    
    __table_args__ = (
        UniqueConstraint('campaign_id', 'marketplace_id', name='uq_campaign_marketplace'),
        Index('idx_campaign_user_brand', 'user_id', 'brand_tag'),
        Index('idx_campaign_type', 'campaign_type'),
        Index('idx_campaign_name', 'campaign_name'),
    )
    
    def __repr__(self):
        return f"<CampaignMapping(campaign_id='{self.campaign_id}', name='{self.campaign_name}', brand='{self.brand_tag}')>"
        
    def add_name_to_history(self, name: str):
        """Add a campaign name to the history if it's different"""
        if name != self.campaign_name and name not in self.name_history:
            self.name_history.append({
                'name': name,
                'seen_at': self.last_seen_at
            })


class BrandConfiguration(BaseModel):
    """Brand-specific configuration and YAML parameters"""
    __tablename__ = 'brand_configurations'
    
    # Brand identification
    brand_tag = Column(String(100), unique=True, nullable=False, index=True)
    brand_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # YAML parameter templates
    yaml_parameters = Column(Text, nullable=True)  # YAML string
    
    # Common query parameters for this brand
    default_parameters = Column(JSONB, default=dict)
    
    # Associated ASINs
    primary_asins = Column(JSON, default=list)
    all_asins = Column(JSON, default=list)
    
    # Campaign patterns (for auto-tagging)
    campaign_name_patterns = Column(JSON, default=list)  # Regex patterns
    
    # Metadata
    owner_user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    shared_with_users = Column(JSON, default=list)  # User IDs who can use this brand config
    
    # Relationships
    owner = relationship("User")
    
    def __repr__(self):
        return f"<BrandConfiguration(brand_tag='{self.brand_tag}', name='{self.brand_name}')>"
        
    def matches_campaign_name(self, campaign_name: str) -> bool:
        """Check if campaign name matches any brand patterns"""
        import re
        for pattern in self.campaign_name_patterns:
            if re.match(pattern, campaign_name, re.IGNORECASE):
                return True
        return False