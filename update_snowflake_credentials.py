#!/usr/bin/env python3
"""
Update Snowflake credentials for the user
"""

import os
import sys
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amc_manager.core.supabase_client import SupabaseManager
from cryptography.fernet import Fernet
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_snowflake_credentials():
    """Update Snowflake credentials with proper encryption"""

    # Snowflake credentials
    credentials = {
        "account": "MUMZYBN-CN28961",
        "user": "NICK_PADILLA",
        "password": "6O[B%Vke@>6xB8IYcBCG",
        "role": "AMC_DB_OWNER_ROLE",
        "warehouse": "AMC_WH",
        "database": "AMC_DB",
        "schema": "PUBLIC"
    }

    logger.info("Updating Snowflake credentials...")

    client = SupabaseManager.get_client(use_service_role=True)

    try:
        # Get the existing configuration
        response = client.table('snowflake_configurations')\
            .select('*')\
            .eq('is_active', True)\
            .execute()

        if not response.data:
            logger.error("No active Snowflake configuration found")

            # Create new configuration
            logger.info("Creating new Snowflake configuration...")

            # Get the user ID (we know it from the logs)
            user_id = "fe841586-7807-48b1-8808-02877834fce0"

            # Get FERNET_KEY from environment
            fernet_key = os.getenv('FERNET_KEY')
            if not fernet_key:
                logger.error("FERNET_KEY not found in environment")
                return

            # Create Fernet cipher
            cipher = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)

            # Encrypt password
            encrypted_password = cipher.encrypt(credentials["password"].encode()).decode()

            # Prepare insert data
            insert_data = {
                'user_id': user_id,
                'account_identifier': credentials["account"],
                'warehouse': credentials["warehouse"],
                'database': credentials["database"],
                'schema': credentials["schema"],
                'role': credentials["role"],
                'username': credentials["user"],
                'password_encrypted': encrypted_password,
                'is_active': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            result = client.table('snowflake_configurations').insert(insert_data).execute()

            if result.data:
                logger.info("✓ Successfully created Snowflake configuration")
            else:
                logger.error("Failed to create configuration")

        else:
            config = response.data[0]
            config_id = config['id']

            logger.info(f"Found existing configuration: {config_id}")
            logger.info(f"Current account: {config['account_identifier']}")

            # Get FERNET_KEY from environment
            fernet_key = os.getenv('FERNET_KEY')
            if not fernet_key:
                logger.error("FERNET_KEY not found in environment")
                return

            # Create Fernet cipher
            cipher = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)

            # Encrypt password
            encrypted_password = cipher.encrypt(credentials["password"].encode()).decode()

            # Update configuration
            update_data = {
                'account_identifier': credentials["account"],
                'warehouse': credentials["warehouse"],
                'database': credentials["database"],
                'schema': credentials["schema"],
                'role': credentials["role"],
                'username': credentials["user"],
                'password_encrypted': encrypted_password,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }

            result = client.table('snowflake_configurations')\
                .update(update_data)\
                .eq('id', config_id)\
                .execute()

            if result.data:
                logger.info("✓ Successfully updated Snowflake configuration")
                logger.info(f"  Account: {credentials['account']}")
                logger.info(f"  User: {credentials['user']}")
                logger.info(f"  Database: {credentials['database']}")
                logger.info(f"  Warehouse: {credentials['warehouse']}")
                logger.info(f"  Role: {credentials['role']}")
            else:
                logger.error("Failed to update configuration")

    except Exception as e:
        logger.error(f"Error updating Snowflake credentials: {e}")
        import traceback
        traceback.print_exc()

def test_snowflake_connection():
    """Test the Snowflake connection with updated credentials"""
    logger.info("\nTesting Snowflake connection...")

    try:
        import snowflake.connector
        from amc_manager.services.snowflake_service import SnowflakeService

        # Initialize service
        snowflake_service = SnowflakeService()

        # Get the configuration
        user_id = "fe841586-7807-48b1-8808-02877834fce0"
        config = snowflake_service.get_user_snowflake_config(user_id)

        if not config:
            logger.error("No configuration found")
            return

        logger.info("Testing connection with updated credentials...")

        # Test connection
        result = snowflake_service.test_connection(config)

        if result['success']:
            logger.info(f"✓ Connection successful: {result['message']}")
        else:
            logger.error(f"✗ Connection failed: {result['error']}")

    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run credential update"""
    logger.info("=" * 80)
    logger.info("SNOWFLAKE CREDENTIAL UPDATE")
    logger.info("=" * 80)

    # Update credentials
    update_snowflake_credentials()

    # Test connection
    test_snowflake_connection()

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETED")
    logger.info("=" * 80)

    logger.info("""
Credential update completed. The sync service should now be able to connect to Snowflake.

Monitor the server.log file to see if executions are being successfully uploaded.
""")

if __name__ == "__main__":
    main()