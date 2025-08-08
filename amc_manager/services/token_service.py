"""Token validation and management service for Amazon OAuth"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from cryptography.fernet import Fernet

from ..core.logger_simple import get_logger
from ..config.settings import settings
from .db_service import db_service

logger = get_logger(__name__)


class TokenService:
    """Service for managing Amazon OAuth tokens"""
    
    def __init__(self):
        # Generate or load encryption key
        self.fernet = self._get_fernet()
        self.token_endpoint = "https://api.amazon.com/auth/o2/token"
        self.profile_endpoint = "https://advertising-api.amazon.com/v2/profiles"
    
    def _get_fernet(self) -> Optional[Fernet]:
        """Get or create Fernet encryption instance"""
        try:
            # Try both possible environment variable names
            key = settings.fernet_key or os.getenv('FERNET_KEY') or os.getenv('ENCRYPTION_KEY')
            if not key:
                # Generate a new key if none exists
                key = Fernet.generate_key().decode()
                logger.warning("Generated new encryption key. Set FERNET_KEY env var for persistence.")
                logger.info(f"Generated key (for debugging): {key}")
            else:
                logger.info("Using existing FERNET_KEY from environment")
                key = key.encode() if isinstance(key, str) else key
            
            fernet = Fernet(key)
            logger.info("Fernet encryption initialized successfully")
            return fernet
        except ValueError as e:
            logger.error(f"Invalid Fernet key format: {e}")
            logger.error("This will prevent token encryption/decryption from working!")
            return None
        except TypeError as e:
            logger.error(f"Type error in encryption setup: {e}")
            logger.error("This will prevent token encryption/decryption from working!")
            return None
        except Exception as e:
            logger.error(f"Unexpected error initializing encryption: {type(e).__name__}: {e}")
            logger.error("This will prevent token encryption/decryption from working!")
            raise  # Re-raise unexpected errors for debugging
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage"""
        if not self.fernet:
            logger.warning("Fernet not initialized, returning token as-is")
            return token
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token"""
        if not self.fernet:
            logger.error("CRITICAL: Fernet not initialized, cannot decrypt token!")
            raise ValueError("Encryption not properly initialized. Check FERNET_KEY environment variable.")
        
        try:
            decrypted = self.fernet.decrypt(encrypted_token.encode()).decode()
            # Validate the decrypted token looks like an Amazon token
            # Access tokens start with 'Atza|' and refresh tokens start with 'Atzr|'
            if not (decrypted.startswith('Atza|') or decrypted.startswith('Atzr|')):
                logger.warning(f"Decrypted token doesn't look like Amazon token. First 20 chars: {decrypted[:20]}")
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            logger.error(f"Encrypted token first 20 chars: {encrypted_token[:20]}")
            raise ValueError(f"Failed to decrypt token: {e}")
    
    async def validate_token(self, access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an access token by making a test API call
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(self.profile_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, None
            elif response.status_code == 401:
                return False, "Token is expired or invalid"
            else:
                return False, f"API returned status {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating token: {e}")
            return False, f"Network error: {str(e)}"
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token using refresh token
        
        Returns:
            New token data or None if refresh failed
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.amazon_client_id,
            'client_secret': settings.amazon_client_secret
        }
        
        try:
            response = requests.post(self.token_endpoint, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info("Successfully refreshed access token")
                return token_data
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    async def store_user_tokens(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Store encrypted tokens for a user
        
        Args:
            user_id: User ID in database
            token_data: Token data from Amazon OAuth
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt tokens
            encrypted_tokens = {
                'access_token': self.encrypt_token(token_data['access_token']),
                'refresh_token': self.encrypt_token(token_data.get('refresh_token', '')),
                'token_type': token_data.get('token_type', 'bearer'),
                'expires_at': (
                    datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
                ).isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Update user record
            result = await db_service.update_user(user_id, {
                'auth_tokens': encrypted_tokens
            })
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error storing tokens: {e}")
            return False
    
    async def get_valid_token(self, user_id: str) -> Optional[str]:
        """
        Get a valid access token for a user, refreshing if necessary
        
        Args:
            user_id: User ID in database
            
        Returns:
            Valid access token or None
        """
        try:
            # Get user data
            user = await db_service.get_user_by_id(user_id)
            if not user or not user.get('auth_tokens'):
                logger.error(f"No tokens found for user {user_id}")
                return None
            
            auth_tokens = user['auth_tokens']
            
            # Decrypt access token
            try:
                access_token = self.decrypt_token(auth_tokens['access_token'])
            except Exception as e:
                logger.error(f"Error decrypting access token: {e}")
                return None
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(auth_tokens.get('expires_at', ''))
            if expires_at > datetime.utcnow() + timedelta(minutes=5):
                # Token is still valid (with 5-minute buffer)
                return access_token
            
            # Token is expired or about to expire, refresh it
            logger.info("Access token expired, attempting refresh...")
            
            try:
                refresh_token = self.decrypt_token(auth_tokens['refresh_token'])
            except Exception as e:
                logger.error(f"Error decrypting refresh token: {e}")
                return None
            
            # Refresh the token
            new_token_data = await self.refresh_access_token(refresh_token)
            if not new_token_data:
                logger.error("Failed to refresh token")
                return None
            
            # Store new tokens
            await self.store_user_tokens(user_id, new_token_data)
            
            return new_token_data['access_token']
            
        except Exception as e:
            logger.error(f"Error getting valid token: {e}")
            return None
    
    async def get_user_profiles(self, access_token: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get advertising profiles for a user
        
        Args:
            access_token: Valid access token
            
        Returns:
            List of profiles or None
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(self.profile_endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get profiles: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting profiles: {e}")
            return None

# Global instance
token_service = TokenService()