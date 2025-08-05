"""Profile API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime

from ...services.db_service import db_service
from ...services.token_service import token_service
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's profile information
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User profile data including Amazon connection status
    """
    try:
        user_id = current_user['id']
        
        # Get user details from database
        user_data = db_service.get_user_by_id_sync(user_id)
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check Amazon connection status
        amazon_connected = False
        token_expires_at = None
        refresh_token_valid = False
        
        # Check if user has auth tokens
        if user_data.get('auth_tokens'):
            try:
                auth_tokens = user_data['auth_tokens']
                # Check if tokens exist
                if auth_tokens.get('access_token'):
                    amazon_connected = True
                    # Check token expiry
                    if 'expires_at' in auth_tokens:
                        expires_at_str = auth_tokens['expires_at']
                        expires_dt = datetime.fromisoformat(expires_at_str)
                        token_expires_at = expires_dt.timestamp()
                        if expires_dt > datetime.utcnow():
                            refresh_token_valid = True
            except Exception as e:
                logger.warning(f"Could not check token status: {e}")
        
        # Get connected AMC accounts
        accounts = []
        try:
            user_accounts = db_service.get_user_accounts_sync(user_id)
            accounts = [
                {
                    'account_id': acc.get('account_id'),
                    'account_name': acc.get('account_name', 'Unknown'),
                    'marketplace_id': acc.get('marketplace_id', 'ATVPDKIKX0DER')
                }
                for acc in user_accounts
            ]
        except Exception as e:
            logger.error(f"Error fetching user accounts: {e}")
        
        # Build profile response
        profile = {
            'id': user_data.get('id'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'created_at': user_data.get('created_at'),
            'last_login': user_data.get('last_login'),
            'amazon_connected': amazon_connected,
            'token_expires_at': datetime.fromtimestamp(token_expires_at).isoformat() if token_expires_at else None,
            'refresh_token_valid': refresh_token_valid,
            'accounts': accounts
        }
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update user profile information
    
    Args:
        profile_data: Profile fields to update
        current_user: The authenticated user
        
    Returns:
        Updated profile data
    """
    try:
        user_id = current_user['id']
        
        # Only allow updating certain fields
        allowed_fields = ['name', 'notification_preferences']
        update_data = {
            k: v for k, v in profile_data.items() 
            if k in allowed_fields
        }
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update user in database
        updated = db_service.update_user_sync(user_id, update_data)
        
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        # Return updated profile
        return await get_user_profile(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))