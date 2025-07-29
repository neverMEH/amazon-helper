"""Amazon Advertising API OAuth 2.0 Authentication"""

import time
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import jwt

from ..config import settings
from .logger import get_logger
from .exceptions import AuthenticationError, TokenRefreshError


logger = get_logger(__name__)


class AmazonAuthManager:
    """Manages OAuth 2.0 authentication with Amazon Advertising API"""
    
    AUTHORIZATION_BASE_URL = 'https://www.amazon.com/ap/oa'
    TOKEN_URL = 'https://api.amazon.com/auth/o2/token'
    
    def __init__(self):
        self.client_id = settings.amazon_client_id
        self.client_secret = settings.amazon_client_secret
        self.redirect_uri = settings.amazon_redirect_uri
        self.scope = settings.amazon_scope.split()
        self._token_cache = {}
        
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Generate authorization URL for OAuth flow
        
        Returns:
            Tuple of (authorization_url, state)
        """
        oauth = OAuth2Session(
            self.client_id,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            state=state
        )
        
        authorization_url, state = oauth.authorization_url(
            self.AUTHORIZATION_BASE_URL,
            access_type='offline',
            prompt='consent'
        )
        
        logger.info("Generated authorization URL")
        return authorization_url, state
    
    def fetch_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            authorization_code: Code received from authorization callback
            
        Returns:
            Token response dictionary
        """
        oauth = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri
        )
        
        try:
            token = oauth.fetch_token(
                self.TOKEN_URL,
                authorization_response=authorization_code,
                client_secret=self.client_secret,
                include_client_id=True
            )
            
            # Add timestamp for expiry calculation
            token['obtained_at'] = time.time()
            
            logger.info("Successfully fetched access token")
            return token
            
        except Exception as e:
            logger.error(f"Failed to fetch token: {e}")
            raise AuthenticationError(f"Token fetch failed: {str(e)}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            New token response dictionary
        """
        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
            )
            response.raise_for_status()
            
            token = response.json()
            token['obtained_at'] = time.time()
            token['refresh_token'] = refresh_token  # Preserve refresh token
            
            logger.info("Successfully refreshed access token")
            return token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh token: {e}")
            raise TokenRefreshError(f"Token refresh failed: {str(e)}")
    
    def is_token_expired(self, token: Dict[str, Any]) -> bool:
        """
        Check if token is expired or about to expire
        
        Args:
            token: Token dictionary with 'expires_in' and 'obtained_at'
            
        Returns:
            True if token is expired or expires in less than 5 minutes
        """
        if 'obtained_at' not in token or 'expires_in' not in token:
            return True
            
        expires_at = token['obtained_at'] + token['expires_in']
        current_time = time.time()
        
        # Consider token expired if less than 5 minutes remaining
        return current_time >= (expires_at - 300)
    
    def get_valid_token(self, user_id: str, stored_token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a valid token, refreshing if necessary
        
        Args:
            user_id: User identifier for caching
            stored_token: Currently stored token
            
        Returns:
            Valid token dictionary
        """
        # Check cache first
        if user_id in self._token_cache:
            cached_token = self._token_cache[user_id]
            if not self.is_token_expired(cached_token):
                return cached_token
        
        # Check if stored token is valid
        if not self.is_token_expired(stored_token):
            self._token_cache[user_id] = stored_token
            return stored_token
        
        # Refresh the token
        if 'refresh_token' not in stored_token:
            raise TokenRefreshError("No refresh token available")
            
        new_token = self.refresh_token(stored_token['refresh_token'])
        self._token_cache[user_id] = new_token
        
        return new_token
    
    def create_jwt_token(self, user_data: Dict[str, Any], expires_in: int = 3600) -> str:
        """
        Create JWT token for internal authentication
        
        Args:
            user_data: User data to encode
            expires_in: Token expiry in seconds
            
        Returns:
            Encoded JWT token
        """
        payload = {
            **user_data,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm='HS256'
        )
    
    def decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded payload
        """
        try:
            return jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")


# Global auth manager instance
auth_manager = AmazonAuthManager()