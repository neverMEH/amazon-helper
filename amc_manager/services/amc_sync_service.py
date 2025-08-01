"""Service for syncing AMC data from Amazon API to local database"""

import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..core.logger_simple import get_logger
from ..config import settings
from .db_service import db_service
from .token_service import token_service

logger = get_logger(__name__)


class AMCSyncService:
    """Service for syncing AMC instances and accounts from Amazon API"""
    
    def __init__(self):
        self.base_url = "https://advertising-api.amazon.com"
        self.token_service = token_service
        self.db_service = db_service
    
    async def sync_user_instances(self, user_id: str) -> Dict[str, Any]:
        """
        Sync AMC instances for a user from Amazon API
        
        Args:
            user_id: User ID to sync instances for
            
        Returns:
            Dictionary with sync results
        """
        try:
            logger.info(f"Starting sync for user {user_id}")
            
            # Get user's valid token
            access_token = await self.token_service.get_valid_token(user_id)
            if not access_token:
                logger.error(f"No valid token found for user {user_id}")
                return {
                    "success": False,
                    "error": "No valid Amazon OAuth token found. Please reconnect with Amazon."
                }
            
            # First, get AMC accounts
            logger.info(f"Fetching AMC accounts for user {user_id}")
            accounts = await self._fetch_amc_accounts(access_token)
            
            if not accounts:
                return {
                    "success": False,
                    "error": "No AMC accounts found for this user"
                }
            
            logger.info(f"Found {len(accounts)} AMC accounts")
            
            # Store/update accounts in database
            stored_accounts = await self._store_amc_accounts(user_id, accounts)
            
            # For each account, fetch instances
            all_instances = []
            for account in accounts:
                logger.info(f"Fetching instances for account {account['accountId']}")
                instances = await self._fetch_amc_instances(
                    access_token,
                    account['accountId'],
                    account.get('marketplaceId', 'ATVPDKIKX0DER')
                )
                
                if instances:
                    # Add account reference to each instance
                    for instance in instances:
                        instance['account_id'] = account['accountId']
                    all_instances.extend(instances)
            
            logger.info(f"Found total of {len(all_instances)} AMC instances")
            
            # Store instances in database
            stored_instances = await self._store_amc_instances(all_instances, stored_accounts)
            
            return {
                "success": True,
                "accounts_synced": len(accounts),
                "instances_synced": len(all_instances),
                "message": f"Successfully synced {len(accounts)} accounts and {len(all_instances)} instances"
            }
            
        except Exception as e:
            logger.error(f"Error syncing instances: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_amc_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch AMC accounts from Amazon API"""
        url = f"{self.base_url}/amc/accounts"
        
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"AMC accounts API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('amcAccounts', [])
                logger.info(f"AMC accounts API response: {json.dumps(data, indent=2)}")
                logger.info(f"Found {len(accounts)} AMC accounts")
                return accounts
            else:
                logger.error(f"Failed to fetch AMC accounts: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Exception fetching AMC accounts: {e}")
            return []
    
    async def _fetch_amc_instances(self, access_token: str, entity_id: str, marketplace_id: str) -> List[Dict[str, Any]]:
        """Fetch AMC instances for a specific account"""
        # Use nextToken parameter as required by API
        url = f"{self.base_url}/amc/instances?nextToken="
        
        # Critical: entity_id must be passed as header, not query parameter
        headers = {
            'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
            'Authorization': f'Bearer {access_token}',
            'Amazon-Advertising-API-MarketplaceId': marketplace_id,
            'Amazon-Advertising-API-AdvertiserId': entity_id  # This is the key!
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"AMC instances API response status for entity {entity_id}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                instances = data.get('instances', [])
                logger.info(f"AMC instances API response: {json.dumps(data, indent=2)}")
                logger.info(f"Found {len(instances)} instances for entity {entity_id}")
                return instances
            else:
                logger.error(f"Failed to fetch instances for entity {entity_id}: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Exception fetching instances for entity {entity_id}: {e}")
            return []
    
    async def _store_amc_accounts(self, user_id: str, accounts: List[Dict[str, Any]]) -> Dict[str, str]:
        """Store AMC accounts in database and return mapping of accountId to database ID"""
        account_mapping = {}
        
        for account in accounts:
            try:
                # Check if account already exists
                existing = self.db_service.client.table('amc_accounts')\
                    .select('id')\
                    .eq('account_id', account['accountId'])\
                    .eq('user_id', user_id)\
                    .execute()
                
                if existing.data:
                    # Update existing account
                    account_id = existing.data[0]['id']
                    self.db_service.client.table('amc_accounts')\
                        .update({
                            'account_name': account['accountName'],
                            'marketplace_id': account.get('marketplaceId', 'ATVPDKIKX0DER'),
                            'updated_at': datetime.utcnow().isoformat()
                        })\
                        .eq('id', account_id)\
                        .execute()
                else:
                    # Create new account
                    result = self.db_service.client.table('amc_accounts')\
                        .insert({
                            'user_id': user_id,
                            'account_id': account['accountId'],
                            'account_name': account['accountName'],
                            'marketplace_id': account.get('marketplaceId', 'ATVPDKIKX0DER'),
                            'is_active': True
                        })\
                        .execute()
                    account_id = result.data[0]['id']
                
                account_mapping[account['accountId']] = account_id
                
            except Exception as e:
                logger.error(f"Error storing account {account['accountId']}: {e}")
        
        return account_mapping
    
    async def _store_amc_instances(self, instances: List[Dict[str, Any]], account_mapping: Dict[str, str]) -> int:
        """Store AMC instances in database"""
        stored_count = 0
        
        for instance in instances:
            try:
                account_db_id = account_mapping.get(instance['account_id'])
                if not account_db_id:
                    logger.warning(f"No database ID found for account {instance['account_id']}")
                    continue
                
                # Check if instance already exists
                existing = self.db_service.client.table('amc_instances')\
                    .select('id')\
                    .eq('instance_id', instance['instanceId'])\
                    .execute()
                
                instance_data = {
                    'instance_id': instance['instanceId'],
                    'instance_name': instance.get('instanceName', ''),
                    'account_id': account_db_id,
                    'region': instance.get('region', 'us-east-1'),
                    'status': 'active' if instance.get('creationStatus') == 'CREATED' else 'inactive',
                    'endpoint_url': instance.get('apiEndpoint', ''),
                    'data_upload_account_id': instance.get('s3BucketName', ''),
                    'capabilities': {
                        'instance_type': instance.get('instanceType', 'STANDARD'),
                        'datasets': instance.get('optionalDatasets', [])
                    },
                    'metadata': {
                        'customer_name': instance.get('customerCanonicalName', ''),
                        'entities': instance.get('entities', []),
                        'creation_datetime': instance.get('creationDatetime', '')
                    }
                }
                
                if existing.data:
                    # Update existing instance
                    instance_data['updated_at'] = datetime.utcnow().isoformat()
                    self.db_service.client.table('amc_instances')\
                        .update(instance_data)\
                        .eq('id', existing.data[0]['id'])\
                        .execute()
                else:
                    # Create new instance
                    self.db_service.client.table('amc_instances')\
                        .insert(instance_data)\
                        .execute()
                
                stored_count += 1
                
            except Exception as e:
                logger.error(f"Error storing instance {instance.get('instanceId')}: {e}")
        
        return stored_count


# Create singleton instance
amc_sync_service = AMCSyncService()