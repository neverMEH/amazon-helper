"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..core import auth_manager, get_logger
from ..models import get_db, User
from ..core.exceptions import AuthenticationError


logger = get_logger(__name__)
router = APIRouter()


@router.get("/login")
async def login(state: str = None):
    """
    Initiate OAuth login flow
    
    Returns authorization URL for user to authenticate with Amazon
    """
    try:
        auth_url, state = auth_manager.get_authorization_url(state)
        return {
            "auth_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")


@router.get("/callback")
async def auth_callback(
    code: str = Query(..., description="Authorization code from Amazon"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Amazon
    
    Exchange authorization code for tokens and create/update user
    """
    try:
        # Exchange code for tokens
        token_data = auth_manager.fetch_token(code)
        
        # TODO: Get user info from Amazon API using the token
        # For now, we'll use a placeholder
        user_info = {
            "email": "user@example.com",  # This should come from Amazon API
            "name": "AMC User",
            "amazon_customer_id": "placeholder_id"
        }
        
        # Find or create user
        user = db.query(User).filter_by(email=user_info["email"]).first()
        if not user:
            user = User(
                email=user_info["email"],
                name=user_info["name"],
                amazon_customer_id=user_info.get("amazon_customer_id")
            )
            db.add(user)
        
        # Update auth tokens
        user.auth_tokens = token_data
        db.commit()
        
        # Create JWT for our application
        jwt_token = auth_manager.create_jwt_token({
            "user_id": user.id,
            "email": user.email
        })
        
        # Redirect to frontend with token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        redirect_url = f"{frontend_url}/auth/success?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Auth callback failed: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        redirect_url = f"{frontend_url}/auth/error?message={str(e)}"
        return RedirectResponse(url=redirect_url)


@router.post("/refresh")
async def refresh_token(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Refresh user's access token
    
    Uses stored refresh token to get new access token
    """
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if not user.auth_tokens or 'refresh_token' not in user.auth_tokens:
            raise HTTPException(status_code=401, detail="No refresh token available")
            
        # Refresh the token
        new_tokens = auth_manager.refresh_token(user.auth_tokens['refresh_token'])
        
        # Update stored tokens
        user.auth_tokens = new_tokens
        db.commit()
        
        return {
            "message": "Token refreshed successfully",
            "expires_in": new_tokens.get('expires_in')
        }
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@router.get("/me")
async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get current user information from JWT token
    """
    try:
        # Decode JWT
        payload = auth_manager.decode_jwt_token(token)
        user_id = payload.get('user_id')
        
        # Get user from database
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "profile_ids": user.profile_ids,
            "marketplace_ids": user.marketplace_ids,
            "is_admin": user.is_admin
        }
        
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user information")