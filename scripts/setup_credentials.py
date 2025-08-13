#!/usr/bin/env python3
"""Interactive script to help set up Amazon Advertising API credentials"""

import os
import sys
from pathlib import Path
from getpass import getpass


def setup_credentials():
    """Interactive credential setup"""
    print("Amazon Advertising API Credential Setup")
    print("======================================\n")
    
    print("This script will help you set up your API credentials.")
    print("You'll need the following from your Amazon Developer Console:\n")
    
    # Get credentials
    print("1. Client ID (format: amzn1.application-oa2-client.xxxxx)")
    client_id = input("   Enter your Client ID: ").strip()
    
    print("\n2. Client Secret (will be hidden)")
    client_secret = getpass("   Enter your Client Secret: ").strip()
    
    print("\n3. Redirect URI (press Enter for default: http://localhost:8000/api/auth/callback)")
    redirect_uri = input("   Enter your Redirect URI: ").strip()
    if not redirect_uri:
        redirect_uri = "http://localhost:8000/api/auth/callback"
    
    print("\n4. OAuth Scopes (press Enter for default: cpc_advertising:campaign_management)")
    scope = input("   Enter scopes (space-separated): ").strip()
    if not scope:
        scope = "cpc_advertising:campaign_management"
    
    # Database configuration
    print("\n5. Database Configuration")
    print("   Default: postgresql://user:password@localhost:5432/amc_manager")
    use_default_db = input("   Use default database URL? (y/n): ").lower() == 'y'
    
    if use_default_db:
        db_url = "postgresql://user:password@localhost:5432/amc_manager"
    else:
        db_user = input("   Database user: ").strip()
        db_pass = getpass("   Database password: ").strip()
        db_host = input("   Database host (default: localhost): ").strip() or "localhost"
        db_port = input("   Database port (default: 5432): ").strip() or "5432"
        db_name = input("   Database name (default: amc_manager): ").strip() or "amc_manager"
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Redis configuration
    print("\n6. Redis Configuration (for task queue)")
    print("   Default: redis://localhost:6379")
    use_default_redis = input("   Use default Redis URL? (y/n): ").lower() == 'y'
    
    if use_default_redis:
        redis_url = "redis://localhost:6379"
    else:
        redis_host = input("   Redis host (default: localhost): ").strip() or "localhost"
        redis_port = input("   Redis port (default: 6379): ").strip() or "6379"
        redis_url = f"redis://{redis_host}:{redis_port}"
    
    # AWS S3 configuration (optional)
    print("\n7. AWS S3 Configuration (optional, for result storage)")
    configure_s3 = input("   Configure S3? (y/n): ").lower() == 'y'
    
    aws_access_key = ""
    aws_secret_key = ""
    s3_bucket = ""
    aws_region = "us-east-1"
    
    if configure_s3:
        aws_access_key = input("   AWS Access Key ID: ").strip()
        aws_secret_key = getpass("   AWS Secret Access Key: ").strip()
        s3_bucket = input("   S3 Bucket Name: ").strip()
        aws_region = input("   AWS Region (default: us-east-1): ").strip() or "us-east-1"
    
    # Generate secret keys
    import secrets
    secret_key = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)
    
    # Create .env file
    env_content = f"""# Amazon Advertising API Configuration
AMAZON_CLIENT_ID={client_id}
AMAZON_CLIENT_SECRET={client_secret}
AMAZON_REDIRECT_URI={redirect_uri}
AMAZON_SCOPE={scope}

# Database Configuration
DATABASE_URL={db_url}
REDIS_URL={redis_url}

# Application Configuration
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}
ENVIRONMENT=development
DEBUG=True

# AWS Configuration for S3 Results
AWS_ACCESS_KEY_ID={aws_access_key}
AWS_SECRET_ACCESS_KEY={aws_secret_key}
AWS_REGION={aws_region}
S3_BUCKET_NAME={s3_bucket}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Celery Configuration
CELERY_BROKER_URL={redis_url}/0
CELERY_RESULT_BACKEND={redis_url}/0

# Monitoring
SENTRY_DSN=

# AMC Configuration
AMC_API_VERSION=v1
AMC_API_BASE_URL=https://advertising-api.amazon.com
"""
    
    # Write to file
    env_path = Path(__file__).parent.parent / '.env'
    
    if env_path.exists():
        overwrite = input("\n.env file already exists. Overwrite? (y/n): ").lower() == 'y'
        if not overwrite:
            print("\nSetup cancelled.")
            return
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n✓ Configuration saved to {env_path}")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Set up databases (PostgreSQL and Redis)")
    print("3. Run migrations: alembic upgrade head")
    print("4. Test connection: python scripts/test_api_connection.py")
    print("5. Start the application: python main.py")


if __name__ == "__main__":
    setup_credentials()