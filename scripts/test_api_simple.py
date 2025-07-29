#!/usr/bin/env python3
"""Simple test script to verify Amazon Advertising API credentials"""

import os
from dotenv import load_dotenv

def test_credentials():
    """Test if credentials are properly configured"""
    print("Testing Amazon Advertising API Credentials...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'AMAZON_CLIENT_ID',
        'AMAZON_CLIENT_SECRET',
        'AMAZON_REDIRECT_URI',
        'AMAZON_SCOPE'
    ]
    
    credentials = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            credentials[var] = value
            # Mask sensitive values
            if 'SECRET' in var:
                display_value = value[:10] + '*' * 20 + value[-10:]
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n✗ Missing required variables: {', '.join(missing_vars)}")
        return False, credentials
    
    print("\n✓ All required credentials are configured")
    return True, credentials


def generate_oauth_url(credentials):
    """Generate OAuth authorization URL"""
    print("\nGenerating OAuth Authorization URL...")
    print("=" * 50)
    
    base_url = "https://www.amazon.com/ap/oa"
    
    params = {
        'client_id': credentials['AMAZON_CLIENT_ID'],
        'scope': credentials['AMAZON_SCOPE'],
        'response_type': 'code',
        'redirect_uri': credentials['AMAZON_REDIRECT_URI']
    }
    
    # Build URL
    param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{base_url}?{param_string}"
    
    print("✓ OAuth URL generated successfully!")
    print(f"\nAuthorization URL:")
    print(auth_url)
    
    return auth_url


def main():
    """Run credential tests"""
    print("Amazon Advertising API Credential Test")
    print("=====================================\n")
    
    # Test credentials
    success, credentials = test_credentials()
    
    if not success:
        print("\n⚠️  Please configure your credentials in the .env file")
        return
    
    # Generate OAuth URL
    auth_url = generate_oauth_url(credentials)
    
    print("\n" + "=" * 50)
    print("✓ Credentials are properly configured!")
    print("\nNext steps:")
    print("1. Click the authorization URL above to authenticate")
    print("2. Log in with your Amazon Advertising account")
    print("3. Grant permissions to the application")
    print("4. You'll be redirected to the callback URL")
    print("\nNote: The actual application needs to be running to handle the callback.")
    print("Start it with: python main.py (after installing all dependencies)")


if __name__ == "__main__":
    main()