"""Amazon Advertising API Client with rate limiting and retry logic"""

import time
import json
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from ratelimit import limits, sleep_and_retry

from ..config import settings
from .logger import get_logger
from .exceptions import APIError, RateLimitError, AuthenticationError


logger = get_logger(__name__)


class HttpMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class AMCAPIClient:
    """Amazon Marketing Cloud API Client with rate limiting and retry logic"""
    
    def __init__(self, entity_id: str, marketplace_id: str):
        """
        Initialize AMC API Client
        
        Args:
            entity_id: Amazon Advertising entity ID (advertiser account ID)
            marketplace_id: Amazon marketplace ID
        """
        self.base_url = settings.amc_api_base_url
        self.entity_id = entity_id
        self.marketplace_id = marketplace_id
        self.session = requests.Session()
        self._setup_session()
        
    def _setup_session(self):
        """Configure session with default headers"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Amazon-Advertising-API-AdvertiserId': self.entity_id,
            'Amazon-Advertising-API-MarketplaceId': self.marketplace_id
        })
        
    def _update_auth_header(self, access_token: str):
        """Update authorization header with current token"""
        self.session.headers['Authorization'] = f'Bearer {access_token}'
        
    def _log_retry(self, retry_state):
        """Log retry attempts"""
        logger.warning(
            f"Retrying request: attempt {retry_state.attempt_number} "
            f"after {retry_state.outcome.exception()}"
        )
        
    @sleep_and_retry
    @limits(calls=settings.rate_limit_calls, period=settings.rate_limit_period)
    def _make_request(
        self,
        method: HttpMethod,
        endpoint: str,
        access_token: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> requests.Response:
        """
        Make rate-limited HTTP request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            access_token: Valid access token
            params: Query parameters
            json_data: JSON payload
            timeout: Request timeout in seconds
            
        Returns:
            Response object
        """
        self._update_auth_header(access_token)
        
        # Apply custom headers if provided
        if headers:
            request_headers = self.session.headers.copy()
            request_headers.update(headers)
        else:
            request_headers = None
        
        url = f"{self.base_url}/{endpoint}"
        
        logger.debug(f"Making {method.value} request to {endpoint}")
        
        response = self.session.request(
            method=method.value,
            url=url,
            params=params,
            json=json_data,
            headers=request_headers,
            timeout=timeout
        )
        
        return response
        
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.retry_delay, max=60),
        retry=retry_if_exception_type((RateLimitError, requests.exceptions.Timeout))
    )
    def request(
        self,
        method: HttpMethod,
        endpoint: str,
        user_id: str,
        user_token: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make authenticated API request with automatic retry
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            user_id: User identifier
            user_token: User's stored token
            params: Query parameters
            json_data: JSON payload
            timeout: Request timeout
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIError: For API errors
            RateLimitError: For rate limit errors
        """
        # Get valid token - import here to avoid circular dependency
        from .auth import auth_manager
        valid_token = auth_manager.get_valid_token(user_id, user_token)
        access_token = valid_token['access_token']
        
        try:
            response = self._make_request(
                method=method,
                endpoint=endpoint,
                access_token=access_token,
                params=params,
                json_data=json_data,
                headers=headers,
                timeout=timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            
            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                raise APIError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            # Return JSON response
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {endpoint}: {e}")
            raise APIError(f"Request failed: {str(e)}")
    
    # Convenience methods for common HTTP verbs
    def get(self, endpoint: str, user_id: str, user_token: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return self.request(HttpMethod.GET, endpoint, user_id, user_token, **kwargs)
    
    def post(self, endpoint: str, user_id: str, user_token: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return self.request(HttpMethod.POST, endpoint, user_id, user_token, **kwargs)
    
    def put(self, endpoint: str, user_id: str, user_token: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return self.request(HttpMethod.PUT, endpoint, user_id, user_token, **kwargs)
    
    def delete(self, endpoint: str, user_id: str, user_token: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return self.request(HttpMethod.DELETE, endpoint, user_id, user_token, **kwargs)
    
    def patch(self, endpoint: str, user_id: str, user_token: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make PATCH request"""
        return self.request(HttpMethod.PATCH, endpoint, user_id, user_token, **kwargs)


class AMCAPIEndpoints:
    """AMC API endpoint constants"""
    
    # Instance management
    INSTANCES = "amc/instances"
    INSTANCE_DETAIL = "amc/instances/{instance_id}"
    
    # Workflow management
    WORKFLOWS = "amc/instances/{instance_id}/workflows"
    WORKFLOW_DETAIL = "amc/instances/{instance_id}/workflows/{workflow_id}"
    WORKFLOW_EXECUTE = "amc/instances/{instance_id}/workflows/{workflow_id}/executions"
    WORKFLOW_SCHEDULE = "amc/instances/{instance_id}/workflows/{workflow_id}/schedules"
    
    # Execution tracking
    EXECUTIONS = "amc/instances/{instance_id}/executions"
    EXECUTION_DETAIL = "amc/instances/{instance_id}/executions/{execution_id}"
    EXECUTION_STATUS = "amc/instances/{instance_id}/executions/{execution_id}/status"
    
    # Data retrieval
    ADVERTISERS = "amc/instances/{instance_id}/advertisers"
    CAMPAIGNS = "campaigns"
    CAMPAIGN_DETAIL = "campaigns/{campaign_id}"
    
    # Reports
    REPORTS = "reports"
    REPORT_DOWNLOAD = "reports/{report_id}/download"