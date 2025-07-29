"""Application configuration settings"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Amazon Advertising API
    amazon_client_id: str = Field(..., env='AMAZON_CLIENT_ID')
    amazon_client_secret: str = Field(..., env='AMAZON_CLIENT_SECRET')
    amazon_redirect_uri: str = Field(..., env='AMAZON_REDIRECT_URI')
    amazon_scope: str = Field(..., env='AMAZON_SCOPE')
    
    # Database
    database_url: str = Field(..., env='DATABASE_URL')
    redis_url: str = Field(..., env='REDIS_URL')
    
    # Supabase
    supabase_url: str = Field(..., env='SUPABASE_URL')
    supabase_anon_key: str = Field(..., env='SUPABASE_ANON_KEY')
    supabase_service_role_key: str = Field(..., env='SUPABASE_SERVICE_ROLE_KEY')
    
    # Application
    secret_key: str = Field(..., env='SECRET_KEY')
    jwt_secret_key: str = Field(..., env='JWT_SECRET_KEY')
    environment: str = Field('development', env='ENVIRONMENT')
    debug: bool = Field(False, env='DEBUG')
    
    # AWS S3
    aws_access_key_id: Optional[str] = Field(None, env='AWS_ACCESS_KEY_ID')
    aws_secret_access_key: Optional[str] = Field(None, env='AWS_SECRET_ACCESS_KEY')
    aws_region: str = Field('us-east-1', env='AWS_REGION')
    s3_bucket_name: Optional[str] = Field(None, env='S3_BUCKET_NAME')
    
    # API
    api_host: str = Field('0.0.0.0', env='API_HOST')
    api_port: int = Field(8000, env='API_PORT')
    api_workers: int = Field(4, env='API_WORKERS')
    
    # Celery
    celery_broker_url: str = Field(..., env='CELERY_BROKER_URL')
    celery_result_backend: str = Field(..., env='CELERY_RESULT_BACKEND')
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(None, env='SENTRY_DSN')
    
    # AMC
    amc_api_version: str = Field('v1', env='AMC_API_VERSION')
    amc_api_base_url: str = Field('https://advertising-api.amazon.com', env='AMC_API_BASE_URL')
    
    # Rate limiting
    rate_limit_calls: int = 10
    rate_limit_period: int = 1  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Create global settings instance
settings = Settings()