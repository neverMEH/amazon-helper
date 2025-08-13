"""Background token refresh service to keep OAuth tokens fresh"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
import threading

from ..core.logger_simple import get_logger
from .token_service import token_service
from .db_service import db_service

logger = get_logger(__name__)


class TokenRefreshService:
    """Service that runs in background to refresh tokens periodically"""
    
    def __init__(self):
        self.refresh_interval = 600  # 10 minutes in seconds
        self.refresh_buffer = 900  # 15 minutes buffer before expiry
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tracked_users: Set[str] = set()
        self._lock = threading.Lock()
    
    def add_user(self, user_id: str):
        """Add a user to be tracked for token refresh"""
        with self._lock:
            self._tracked_users.add(user_id)
            logger.info(f"Added user {user_id} to token refresh tracking")
    
    def remove_user(self, user_id: str):
        """Remove a user from token refresh tracking"""
        with self._lock:
            self._tracked_users.discard(user_id)
            logger.info(f"Removed user {user_id} from token refresh tracking")
    
    async def refresh_user_token(self, user_id: str) -> bool:
        """Refresh token for a specific user if needed"""
        try:
            # Get user data
            user = db_service.get_user_by_id_sync(user_id)
            if not user or not user.get('auth_tokens'):
                logger.debug(f"No tokens found for user {user_id}")
                # Remove user from tracking if they have no tokens
                self.remove_user(user_id)
                return False
            
            auth_tokens = user['auth_tokens']
            
            # Check if token needs refresh
            expires_at_str = auth_tokens.get('expires_at')
            if not expires_at_str:
                logger.warning(f"No expiry time found for user {user_id}")
                return False
            
            expires_at = datetime.fromisoformat(expires_at_str)
            time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()
            
            # Refresh if token expires within buffer time
            if time_until_expiry < self.refresh_buffer:
                logger.info(f"Token for user {user_id} expires in {time_until_expiry:.0f}s, refreshing...")
                
                # Get valid token (this will refresh if needed)
                valid_token = await token_service.get_valid_token(user_id)
                if valid_token:
                    logger.info(f"Successfully refreshed token for user {user_id}")
                    return True
                else:
                    # Token refresh failed - likely due to decryption issues
                    logger.error(f"Failed to refresh token for user {user_id} - removing from tracking")
                    # Remove user from tracking to prevent repeated failures
                    self.remove_user(user_id)
                    # Note: The token service already clears invalid tokens in get_valid_token
                    return False
            else:
                logger.debug(f"Token for user {user_id} still valid for {time_until_expiry:.0f}s")
                return True
                
        except Exception as e:
            logger.error(f"Error refreshing token for user {user_id}: {e}")
            # Remove user from tracking on persistent errors
            if "decrypt" in str(e).lower() or "invalid token" in str(e).lower():
                logger.info(f"Removing user {user_id} from tracking due to token issues")
                self.remove_user(user_id)
            return False
    
    async def refresh_all_tokens(self):
        """Refresh tokens for all tracked users"""
        users_to_refresh = []
        with self._lock:
            users_to_refresh = list(self._tracked_users)
        
        if not users_to_refresh:
            logger.debug("No users to refresh tokens for")
            return
        
        logger.info(f"Refreshing tokens for {len(users_to_refresh)} users")
        
        # Refresh tokens concurrently
        tasks = [self.refresh_user_token(user_id) for user_id in users_to_refresh]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        success_count = sum(1 for r in results if r is True)
        failure_count = sum(1 for r in results if r is False or isinstance(r, Exception))
        
        logger.info(f"Token refresh completed: {success_count} successful, {failure_count} failed")
    
    async def _refresh_loop(self):
        """Main refresh loop that runs periodically"""
        logger.info(f"Starting token refresh service (interval: {self.refresh_interval}s)")
        
        while self._running:
            try:
                # Refresh all tokens
                await self.refresh_all_tokens()
                
                # Wait for next interval
                await asyncio.sleep(self.refresh_interval)
                
            except asyncio.CancelledError:
                logger.info("Token refresh loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in token refresh loop: {e}")
                # Continue running even if there's an error
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def start(self):
        """Start the background refresh service"""
        if self._running:
            logger.warning("Token refresh service already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._refresh_loop())
        logger.info("Token refresh service started")
    
    async def stop(self):
        """Stop the background refresh service"""
        if not self._running:
            logger.warning("Token refresh service not running")
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Token refresh service stopped")
    
    async def refresh_on_login(self, user_id: str):
        """Refresh token when user logs in"""
        logger.info(f"Refreshing token on login for user {user_id}")
        
        # Add user to tracking
        self.add_user(user_id)
        
        # Immediately refresh token
        await self.refresh_user_token(user_id)
    
    async def refresh_before_workflow(self, user_id: str):
        """Ensure token is fresh before workflow execution"""
        logger.info(f"Ensuring fresh token before workflow execution for user {user_id}")
        
        # Add user to tracking if not already
        self.add_user(user_id)
        
        # Refresh token if needed
        await self.refresh_user_token(user_id)
    
    def get_tracked_users(self) -> list:
        """Get list of currently tracked users"""
        with self._lock:
            return list(self._tracked_users)
    
    def is_running(self) -> bool:
        """Check if the service is running"""
        return self._running


# Global instance
token_refresh_service = TokenRefreshService()