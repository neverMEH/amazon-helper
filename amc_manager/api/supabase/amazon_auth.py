"""Amazon OAuth authentication endpoints"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import secrets
import requests
from datetime import datetime, timedelta
import jwt

from ...config import settings
from ...services.db_service import db_service
from ...services.token_service import token_service
from ...core.logger_simple import get_logger
from .auth import get_current_user, create_access_token

logger = get_logger(__name__)
router = APIRouter()

# Store state temporarily (in production, use Redis or database)
state_store = {}


@router.get("/login")
async def amazon_login(redirect_uri: Optional[str] = None):
    """
    Initiate Amazon OAuth login flow
    
    Returns authorization URL for user to authenticate with Amazon
    """
    try:
        # Check required configuration
        client_id = settings.amazon_client_id
        if not client_id:
            logger.error("AMAZON_CLIENT_ID environment variable not set")
            raise HTTPException(
                status_code=500, 
                detail="Amazon OAuth not configured. AMAZON_CLIENT_ID is missing."
            )
        
        if not settings.amazon_client_secret:
            logger.error("AMAZON_CLIENT_SECRET environment variable not set")
            raise HTTPException(
                status_code=500, 
                detail="Amazon OAuth not configured. AMAZON_CLIENT_SECRET is missing."
            )
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state temporarily (expires in 10 minutes)
        state_store[state] = {
            "created_at": datetime.utcnow(),
            "redirect_uri": redirect_uri or "/"
        }
        
        # Clean up old states
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        for k in list(state_store.keys()):
            if state_store[k]["created_at"] < cutoff:
                del state_store[k]
        
        # Build authorization URL
        base_url = "https://www.amazon.com/ap/oa"
        
        # Ensure we're using the correct redirect URI
        redirect_uri = settings.amazon_redirect_uri
        if settings.environment == 'production' and 'localhost' in redirect_uri:
            # Override with production URL if not set correctly
            redirect_uri = 'https://web-production-95aa7.up.railway.app/api/auth/amazon/callback'
            logger.warning(f"Overriding localhost redirect URI with production URL")
        
        params = {
            'client_id': client_id,
            'scope': settings.amazon_scope or 'advertising::campaign_management',
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{base_url}?{param_string}"
        
        logger.info(f"Generated Amazon OAuth URL with state: {state[:10]}...")
        logger.info(f"Redirect URI: {redirect_uri}")
        
        return {
            "auth_url": auth_url,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initiate login: {str(e)}"
        )


@router.get("/callback")
async def amazon_callback(
    code: str = Query(..., description="Authorization code from Amazon"),
    state: str = Query(..., description="State parameter for CSRF protection")
):
    """
    Handle OAuth callback from Amazon
    
    Exchange authorization code for tokens and create/update user
    """
    try:
        # Verify state
        if state not in state_store:
            logger.error("Invalid state parameter")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        state_data = state_store.pop(state)
        redirect_uri = state_data.get("redirect_uri", "/")
        
        # Exchange code for tokens
        token_url = "https://api.amazon.com/auth/o2/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.amazon_client_id,
            'client_secret': settings.amazon_client_secret,
            'redirect_uri': settings.amazon_redirect_uri
        }
        
        logger.info("Exchanging authorization code for tokens...")
        
        response = requests.post(token_url, data=token_data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        
        tokens = response.json()
        logger.info("Successfully obtained tokens from Amazon")
        
        # Get user profile information
        profile_headers = {
            'Authorization': f'Bearer {tokens["access_token"]}',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Content-Type': 'application/json'
        }
        
        profile_response = requests.get(
            "https://api.amazon.com/user/profile",
            headers=profile_headers,
            timeout=10
        )
        
        if profile_response.status_code == 200:
            user_profile = profile_response.json()
            email = user_profile.get('email', f"user_{secrets.token_hex(8)}@amazon.com")
            name = user_profile.get('name', 'Amazon User')
        else:
            # Fallback if profile API fails
            logger.warning(f"Failed to get user profile: {profile_response.status_code}")
            email = f"user_{secrets.token_hex(8)}@amazon.com"
            name = "Amazon User"
        
        # Check if user exists
        user = db_service.get_user_by_email_sync(email)
        
        if not user:
            # Create new user
            user = db_service.create_user_sync({
                "email": email,
                "name": name,
                "is_active": True
            })
            if not user:
                raise HTTPException(status_code=500, detail="Failed to create user")
            logger.info(f"Created new user: {email}")
        else:
            logger.info(f"Found existing user: {email}")
        
        # Store Amazon tokens (encrypted)
        success = await token_service.store_user_tokens(user['id'], tokens)
        if not success:
            logger.error("Failed to store tokens")
            raise HTTPException(status_code=500, detail="Failed to store authentication tokens")
        
        # Create our app's JWT token
        app_token = create_access_token(user['id'], user['email'])
        
        # Redirect to frontend with token
        frontend_url = settings.frontend_url or 'http://localhost:5173'
        redirect_url = f"{frontend_url}/auth/success?token={app_token}&redirect={redirect_uri}"
        
        logger.info(f"OAuth flow completed successfully for user: {email}")
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth callback failed: {e}")
        frontend_url = settings.frontend_url or 'http://localhost:5173'
        error_url = f"{frontend_url}/auth/error?message=Authentication%20failed"
        return RedirectResponse(url=error_url)


@router.post("/refresh")
async def refresh_amazon_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Refresh user's Amazon access token
    
    Uses stored refresh token to get new access token
    """
    try:
        # Get valid token (will auto-refresh if needed)
        valid_token = await token_service.get_valid_token(current_user['id'])
        
        if not valid_token:
            raise HTTPException(status_code=401, detail="No valid refresh token available")
        
        return {
            "message": "Token refreshed successfully",
            "has_valid_token": True
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token")


@router.get("/status")
async def amazon_auth_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Check if user has valid Amazon OAuth tokens
    """
    try:
        # Check if user has tokens
        user = await db_service.get_user_by_id(current_user['id'])
        has_tokens = bool(user and user.get('auth_tokens'))
        
        if not has_tokens:
            return {
                "authenticated": False,
                "message": "No Amazon OAuth tokens found"
            }
        
        # Try to get valid token
        valid_token = await token_service.get_valid_token(current_user['id'])
        
        return {
            "authenticated": bool(valid_token),
            "message": "Valid Amazon OAuth token" if valid_token else "Token expired or invalid"
        }
        
    except Exception as e:
        logger.error(f"Failed to check auth status: {e}")
        return {
            "authenticated": False,
            "message": "Error checking authentication status"
        }