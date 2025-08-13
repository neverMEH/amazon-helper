"""Authentication schemas for input validation"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request validation"""
    email: EmailStr
    password: Optional[str] = Field(None, min_length=0, max_length=256)
    
    @validator('email')
    def validate_email(cls, v):
        if not v:
            raise ValueError('Email is required')
        # Additional email validation if needed
        return v.lower()


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: EmailStr
    name: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None