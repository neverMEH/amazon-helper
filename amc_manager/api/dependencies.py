"""Common API dependencies"""

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..core import AMCAPIClient, auth_manager, get_logger
from ..models import get_db, User
from ..core.exceptions import AuthenticationError


logger = get_logger(__name__)


async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token in Authorization header
    """
    try:
        # Extract token from Bearer header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
            
        token = authorization.replace("Bearer ", "")
        
        # Decode JWT
        try:
            payload = auth_manager.decode_jwt_token(token)
        except AuthenticationError as e:
            raise HTTPException(status_code=401, detail=str(e))
            
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        # Get user from database
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")
            
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        raise HTTPException(status_code=500, detail="Failed to authenticate user")


async def get_api_client(
    current_user: User = Depends(get_current_user)
) -> AMCAPIClient:
    """
    Get configured AMC API client for the current user
    """
    # Get user's primary profile and marketplace
    profile_id = current_user.get_primary_profile_id()
    if not profile_id:
        raise HTTPException(
            status_code=400,
            detail="User has no advertising profiles configured"
        )
        
    marketplace_id = current_user.marketplace_ids[0] if current_user.marketplace_ids else "ATVPDKIKX0DER"  # Default to US
    
    # Create API client
    return AMCAPIClient(
        profile_id=profile_id,
        marketplace_id=marketplace_id
    )


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require current user to be an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """
    Common pagination parameters
    """
    return {"skip": skip, "limit": limit}