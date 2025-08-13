"""User and authentication models"""

from sqlalchemy import Column, String, Boolean, JSON, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amazon_customer_id = Column(String(255), unique=True, nullable=True)
    
    # OAuth tokens stored as encrypted JSON
    auth_tokens = Column(JSON, nullable=True)
    
    # User preferences
    preferences = Column(JSON, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Profile information
    profile_ids = Column(JSON, default=list)  # List of Amazon Advertising profile IDs
    marketplace_ids = Column(JSON, default=list)  # List of marketplace IDs
    
    # Relationships
    workflows = relationship("Workflow", back_populates="user", cascade="all, delete-orphan")
    campaign_mappings = relationship("CampaignMapping", back_populates="user", cascade="all, delete-orphan")
    query_templates = relationship("QueryTemplate", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_customer_id', 'amazon_customer_id'),
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"
        
    def has_valid_token(self):
        """Check if user has valid auth tokens"""
        return bool(self.auth_tokens and 'access_token' in self.auth_tokens)
        
    def get_primary_profile_id(self):
        """Get primary advertising profile ID"""
        return self.profile_ids[0] if self.profile_ids else None