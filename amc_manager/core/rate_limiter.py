"""
Simple rate limiter implementation for API endpoints
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading


class RateLimiter:
    """
    Token bucket rate limiter implementation.

    Limits the number of requests per user within a time window.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow_request(self, user_id: str) -> bool:
        """
        Check if a request from the user is allowed.

        Args:
            user_id: The user making the request

        Returns:
            True if the request is allowed, False if rate limit is exceeded
        """
        with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Get user's request history
            user_queue = self.user_requests[user_id]

            # Remove old requests outside the window
            while user_queue and user_queue[0] < window_start:
                user_queue.popleft()

            # Check if user has exceeded the limit
            if len(user_queue) >= self.max_requests:
                return False

            # Add current request timestamp
            user_queue.append(now)
            return True

    def reset_user(self, user_id: str):
        """
        Reset rate limit for a specific user.

        Args:
            user_id: The user to reset
        """
        with self.lock:
            if user_id in self.user_requests:
                del self.user_requests[user_id]

    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get the number of remaining requests for a user.

        Args:
            user_id: The user to check

        Returns:
            Number of remaining requests
        """
        with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Get user's request history
            user_queue = self.user_requests[user_id]

            # Remove old requests outside the window
            while user_queue and user_queue[0] < window_start:
                user_queue.popleft()

            return max(0, self.max_requests - len(user_queue))

    def get_reset_time(self, user_id: str) -> Optional[datetime]:
        """
        Get the time when the rate limit resets for a user.

        Args:
            user_id: The user to check

        Returns:
            Reset time or None if no requests have been made
        """
        with self.lock:
            user_queue = self.user_requests.get(user_id)

            if not user_queue:
                return None

            # Reset time is when the oldest request expires
            oldest_request = user_queue[0]
            return oldest_request + timedelta(seconds=self.window_seconds)


class IPRateLimiter(RateLimiter):
    """
    Rate limiter based on IP addresses instead of user IDs.
    """

    def allow_request_ip(self, ip_address: str) -> bool:
        """
        Check if a request from the IP is allowed.

        Args:
            ip_address: The IP address making the request

        Returns:
            True if the request is allowed, False if rate limit is exceeded
        """
        return self.allow_request(ip_address)


class EndpointRateLimiter:
    """
    Rate limiter that can have different limits for different endpoints.
    """

    def __init__(self):
        """Initialize the endpoint rate limiter."""
        self.limiters: Dict[str, RateLimiter] = {}

    def add_endpoint(self, endpoint: str, max_requests: int, window_seconds: int):
        """
        Add rate limiting for a specific endpoint.

        Args:
            endpoint: The endpoint path
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.limiters[endpoint] = RateLimiter(max_requests, window_seconds)

    def allow_request(self, endpoint: str, user_id: str) -> bool:
        """
        Check if a request to the endpoint is allowed.

        Args:
            endpoint: The endpoint being accessed
            user_id: The user making the request

        Returns:
            True if allowed, False if rate limited
        """
        limiter = self.limiters.get(endpoint)
        if not limiter:
            # No rate limit configured for this endpoint
            return True

        return limiter.allow_request(user_id)


# Global endpoint rate limiter instance
endpoint_limiter = EndpointRateLimiter()

# Configure default endpoints
endpoint_limiter.add_endpoint("/api/reports/configure", max_requests=10, window_seconds=60)
endpoint_limiter.add_endpoint("/api/reports/configure/batch", max_requests=5, window_seconds=60)
endpoint_limiter.add_endpoint("/api/reports/insights/generate", max_requests=5, window_seconds=300)
endpoint_limiter.add_endpoint("/api/reports/export", max_requests=5, window_seconds=300)