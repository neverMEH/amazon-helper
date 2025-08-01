#!/usr/bin/env python3
"""Create test AMC data for development"""

from amc_manager.services.db_service import db_service
from amc_manager.core.supabase_client import SupabaseManager
import uuid
from datetime import datetime

def create_test_data():
    """Create test AMC accounts and instances"""
    
    # Get user
    user = db_service.get_user_by_email_sync('nick@nevermeh.com')
    if not user:
        print("User not found!")
        return
        
    user_id = user['id']
    print(f"Creating test data for user: {user['email']} (ID: {user_id})")
    
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Clean up existing test data
    print("\nCleaning up existing test data...")
    # Get existing account IDs
    existing_accounts = client.table('amc_accounts').select('id').eq('user_id', user_id).execute()
    if existing_accounts.data:
        account_ids_to_delete = [acc['id'] for acc in existing_accounts.data]
        # Delete related data
        client.table('instance_brands').delete().eq('user_id', user_id).execute()
        client.table('amc_instances').delete().in_('account_id', account_ids_to_delete).execute()
    client.table('amc_accounts').delete().eq('user_id', user_id).execute()
    print("✓ Cleaned up existing data")
    
    # Create test AMC accounts
    accounts = [
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_id": "ENTITY1234567890",
            "marketplace_id": "ATVPDKIKX0DER",
            "account_name": "Test AMC Account 1",
            "status": "active",
            "region": "us-east-1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "account_id": "ENTITY0987654321",
            "marketplace_id": "ATVPDKIKX0DER",
            "account_name": "Test AMC Account 2",
            "status": "active",
            "region": "us-west-2",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Insert accounts
    account_ids = []
    for account in accounts:
        response = client.table('amc_accounts').insert(account).execute()
        if response.data:
            account_ids.append(response.data[0]['id'])
            print(f"✓ Created account: {account['account_name']}")
        else:
            print(f"✗ Failed to create account: {account['account_name']}")
    
    # Create test AMC instances
    instances = [
        {
            "id": str(uuid.uuid4()),
            "account_id": account_ids[0],
            "instance_id": "amctest1234",
            "instance_name": "Test AMC Instance 1",
            "data_upload_account_id": "123456789",
            "status": "active",
            "region": "us-east-1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": account_ids[0],
            "instance_id": "amctest5678",
            "instance_name": "Test AMC Instance 2",
            "data_upload_account_id": "987654321",
            "status": "active",
            "region": "us-east-1",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "account_id": account_ids[1],
            "instance_id": "amctest9999",
            "instance_name": "Test AMC Instance 3",
            "data_upload_account_id": "555555555",
            "status": "active",
            "region": "us-west-2",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Insert instances
    instance_ids = []
    for instance in instances:
        response = client.table('amc_instances').insert(instance).execute()
        if response.data:
            instance_ids.append(response.data[0]['id'])
            print(f"✓ Created instance: {instance['instance_name']}")
        else:
            print(f"✗ Failed to create instance: {instance['instance_name']}")
    
    # Create instance brands
    brands = [
        {"instance_id": instance_ids[0], "brand_tag": "TestBrand1", "user_id": user_id},
        {"instance_id": instance_ids[0], "brand_tag": "TestBrand2", "user_id": user_id},
        {"instance_id": instance_ids[1], "brand_tag": "TestBrand3", "user_id": user_id},
        {"instance_id": instance_ids[2], "brand_tag": "TestBrand4", "user_id": user_id},
    ]
    
    for brand in brands:
        response = client.table('instance_brands').insert(brand).execute()
        if response.data:
            print(f"✓ Added brand {brand['brand_tag']} to instance")
        else:
            print(f"✗ Failed to add brand {brand['brand_tag']}")
    
    print("\nTest data created successfully!")
    print(f"Created {len(accounts)} accounts and {len(instances)} instances")
    
    # Verify
    user_instances = db_service.get_user_instances_sync(user_id)
    print(f"\nVerification - User now has {len(user_instances)} instances")

if __name__ == "__main__":
    create_test_data()