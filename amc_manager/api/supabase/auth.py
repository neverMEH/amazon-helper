"""Authentication API endpoints using Supabase"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import jwt
from datetime import datetime, timedelta
import asyncio

from ...config import settings
from ...services.db_service import db_service
from ...services.token_refresh_service import token_refresh_service
from ...core.logger_simple import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Security
security = HTTPBearer()


def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Use sync version
        response = db_service.client.table('users').select('*').eq('id', user_id).execute()
        user = response.data[0] if response.data else None
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login")
async def login(request: Request, email: str, password: Optional[str] = None):
    """
    Simple login endpoint for testing
    In production, this would integrate with Amazon OAuth
    """
    # For now, just check if user exists
    user = db_service.get_user_by_email_sync(email)
    
    if not user:
        # Create user if doesn't exist (for testing)
        user = db_service.create_user_sync({
            "email": email,
            "name": email.split('@')[0],
            "is_active": True
        })
        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Create access token
    access_token = create_access_token(user['id'], user['email'])
    
    # Trigger token refresh on login (for Amazon OAuth tokens if they exist)
    try:
        await token_refresh_service.refresh_on_login(user['id'])
    except Exception as e:
        logger.warning(f"Could not trigger token refresh on login: {e}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name']
        }
    }


@router.get("/me")
def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "name": current_user['name'],
        "is_active": current_user.get('is_active', True),
        "profile_ids": current_user.get('profile_ids', []),
        "marketplace_ids": current_user.get('marketplace_ids', [])
    }


@router.post("/refresh")
def refresh_token(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Refresh access token"""
    access_token = create_access_token(current_user['id'], current_user['email'])
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/token-status")
async def get_token_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Check if user has valid OAuth tokens for AMC API access"""
    from ...services.token_service import token_service
    from ...core.supabase_client import SupabaseManager
    
    try:
        valid_token = await token_service.get_valid_token(current_user['id'])
        has_valid = bool(valid_token)
        
        message = None
        if not has_valid:
            # Check if user ever had tokens
            client = SupabaseManager.get_client(use_service_role=True)
            user_response = client.table('users').select('auth_tokens').eq('id', current_user['id']).single().execute()
            
            if user_response.data and user_response.data.get('auth_tokens'):
                message = "Your Amazon authentication has expired. Please re-authenticate to continue."
            else:
                message = "You need to authenticate with Amazon Advertising API to access AMC features."
        
        return {
            "hasValidToken": has_valid,
            "requiresAuthentication": not has_valid,
            "message": message
        }
    except Exception as e:
        logger.error(f"Error checking token status: {e}")
        return {
            "hasValidToken": False,
            "requiresAuthentication": True,
            "message": "Unable to verify authentication status. Please try re-authenticating."
        }


@router.post("/logout")
def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Logged out successfully"}