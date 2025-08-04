"""Amazon OAuth authentication endpoints"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import secrets
import requests
from datetime import datetime, timedelta
import jwt
import os

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
        
        # Force correct redirect URI in production (Railway)
        if os.getenv('RAILWAY_ENVIRONMENT'):
            redirect_uri = 'https://web-production-95aa7.up.railway.app/api/auth/amazon/callback'
            logger.info(f"Using Railway production redirect URI")
        else:
            # Check if we're using the wrong callback path
            if '/api/auth/callback' in redirect_uri and '/api/auth/amazon/callback' not in redirect_uri:
                redirect_uri = redirect_uri.replace('/api/auth/callback', '/api/auth/amazon/callback')
                logger.warning(f"Fixed incorrect callback path in redirect URI: {redirect_uri}")
            
            # Override localhost URLs in non-debug mode
            if 'localhost' in redirect_uri and not settings.debug:
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
        
        # Use the same redirect URI that was used in the authorization request
        exchange_redirect_uri = settings.amazon_redirect_uri
        if os.getenv('RAILWAY_ENVIRONMENT'):
            exchange_redirect_uri = 'https://web-production-95aa7.up.railway.app/api/auth/amazon/callback'
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.amazon_client_id,
            'client_secret': settings.amazon_client_secret,
            'redirect_uri': exchange_redirect_uri
        }
        
        logger.info(f"Exchanging authorization code for tokens...")
        logger.info(f"Token exchange redirect_uri: {exchange_redirect_uri}")
        logger.info(f"Client ID: {settings.amazon_client_id[:10]}...")
        
        response = requests.post(token_url, data=token_data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            logger.error(f"Request data: redirect_uri={exchange_redirect_uri}")
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
        
        # Add user to token refresh tracking
        from ...services.token_refresh_service import token_refresh_service
        token_refresh_service.add_user(user['id'])
        logger.info(f"Added user {user['id']} to token refresh tracking")
        
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
        
        # Check if user is being tracked for auto-refresh
        from ...services.token_refresh_service import token_refresh_service
        is_tracked = current_user['id'] in token_refresh_service.get_tracked_users()
        
        # Get token expiry info
        token_info = {}
        if user.get('auth_tokens'):
            auth_tokens = user['auth_tokens']
            expires_at = auth_tokens.get('expires_at')
            if expires_at:
                from datetime import datetime
                expiry = datetime.fromisoformat(expires_at)
                now = datetime.utcnow()
                seconds_until_expiry = (expiry - now).total_seconds()
                token_info = {
                    "expires_at": expires_at,
                    "expires_in_seconds": max(0, seconds_until_expiry),
                    "is_expired": seconds_until_expiry <= 0
                }
        
        return {
            "authenticated": bool(valid_token),
            "message": "Valid Amazon OAuth token" if valid_token else "Token expired or invalid",
            "auto_refresh_enabled": is_tracked,
            "token_info": token_info
        }
        
    except Exception as e:
        logger.error(f"Failed to check auth status: {e}")
        return {
            "authenticated": False,
            "message": "Error checking authentication status"
        }


@router.get("/refresh-status")
async def get_refresh_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get token refresh service status
    """
    from ...services.token_refresh_service import token_refresh_service
    
    return {
        "service_running": token_refresh_service.is_running(),
        "tracked_users": len(token_refresh_service.get_tracked_users()),
        "user_tracked": current_user['id'] in token_refresh_service.get_tracked_users(),
        "refresh_interval_seconds": token_refresh_service.refresh_interval,
        "refresh_buffer_seconds": token_refresh_service.refresh_buffer
    }