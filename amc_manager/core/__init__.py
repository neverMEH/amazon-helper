"""Core module exports"""

from .auth import auth_manager, AmazonAuthManager
from .api_client import AMCAPIClient, AMCAPIEndpoints, HttpMethod
from .exceptions import (
    AMCManagerError,
    AuthenticationError,
    TokenRefreshError,
    APIError,
    RateLimitError,
    AMCQueryError,
    WorkflowError,
    ValidationError,
    DatabaseError
)
from .logger import get_logger
from .supabase_client import (
    SupabaseManager,
    SupabaseService,
    CampaignMappingService,
    BrandConfigurationService,
    WorkflowService,
    AMCInstanceService
)

__all__ = [
    'auth_manager',
    'AmazonAuthManager',
    'AMCAPIClient',
    'AMCAPIEndpoints',
    'HttpMethod',
    'AMCManagerError',
    'AuthenticationError',
    'TokenRefreshError',
    'APIError',
    'RateLimitError',
    'AMCQueryError',
    'WorkflowError',
    'ValidationError',
    'DatabaseError',
    'get_logger',
    'SupabaseManager',
    'SupabaseService',
    'CampaignMappingService',
    'BrandConfigurationService',
    'WorkflowService',
    'AMCInstanceService'
]