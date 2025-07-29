#!/usr/bin/env python3
"""Import initial data into Supabase - user, AMC accounts, and instances"""

import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def create_user():
    """Create initial user record"""
    print("\n1. Creating user record...")
    
    # Load profiles to get user info
    with open('profiles.json', 'r') as f:
        profiles = json.load(f)
    
    # Get the first profile's email as the user email
    user_email = "nick@nevermeh.com"  # From the git config
    
    # Extract profile IDs and marketplace IDs
    profile_ids = [str(p['profileId']) for p in profiles]
    marketplace_ids = list(set(p['accountInfo']['marketplaceStringId'] for p in profiles))
    
    # Create user data
    user_data = {
        'id': str(uuid.uuid4()),
        'email': user_email,
        'name': 'neverMEH',
        'amazon_customer_id': None,  # Will be updated later from OAuth
        'auth_tokens': {},  # Will store encrypted tokens later
        'preferences': {},
        'is_active': True,
        'is_admin': True,
        'profile_ids': profile_ids,
        'marketplace_ids': marketplace_ids
    }
    
    try:
        # Check if user already exists
        existing = supabase.table('users').select('*').eq('email', user_email).execute()
        
        if existing.data:
            print(f"✓ User already exists: {user_email}")
            return existing.data[0]['id']
        else:
            # Insert new user
            response = supabase.table('users').insert(user_data).execute()
            print(f"✓ Created user: {user_email}")
            return response.data[0]['id']
    except Exception as e:
        print(f"✗ Error creating user: {str(e)}")
        return None

def import_amc_accounts(user_id):
    """Import AMC accounts"""
    print("\n2. Importing AMC accounts...")
    
    # Load AMC accounts
    with open('amc_accounts.json', 'r') as f:
        amc_data = json.load(f)
    
    account_ids = {}
    
    for account in amc_data['amcAccounts']:
        account_data = {
            'id': str(uuid.uuid4()),
            'account_id': account['accountId'],
            'account_name': account['accountName'],
            'marketplace_id': account['marketplaceId'],
            'region': 'us-east-1',  # Default region
            'status': 'active',
            'metadata': {},
            'user_id': user_id
        }
        
        try:
            # Check if account already exists
            existing = supabase.table('amc_accounts').select('*').eq('account_id', account['accountId']).execute()
            
            if existing.data:
                print(f"✓ Account already exists: {account['accountName']}")
                account_ids[account['accountId']] = existing.data[0]['id']
            else:
                # Insert new account
                response = supabase.table('amc_accounts').insert(account_data).execute()
                print(f"✓ Created account: {account['accountName']}")
                account_ids[account['accountId']] = response.data[0]['id']
        except Exception as e:
            print(f"✗ Error creating account {account['accountName']}: {str(e)}")
    
    return account_ids

def import_amc_instances(account_ids):
    """Import AMC instances"""
    print("\n3. Importing AMC instances...")
    
    instance_count = 0
    
    # Import instances for each account
    for entity_id, account_uuid in account_ids.items():
        filename = f'amc_instances_{entity_id}.json'
        
        if not os.path.exists(filename):
            print(f"✗ File not found: {filename}")
            continue
            
        with open(filename, 'r') as f:
            instances_data = json.load(f)
        
        for instance in instances_data['instances']:
            instance_data = {
                'id': str(uuid.uuid4()),
                'instance_id': instance['instanceId'],
                'instance_name': instance['instanceName'],
                'region': 'us-east-1',  # Extract from endpoint if needed
                'endpoint_url': instance.get('apiEndpoint'),
                'account_id': account_uuid,
                'status': 'active' if instance.get('creationStatus') == 'COMPLETED' else 'inactive',
                'capabilities': {
                    'instance_type': instance.get('instanceType', 'PRODUCTION'),
                    's3_bucket': instance.get('s3BucketName'),
                    'aws_account_id': instance.get('awsAccountId'),
                    'entities': instance.get('entities', []),
                    'optional_datasets': instance.get('optionalDatasets', [])
                },
                'data_upload_account_id': instance.get('dataUploadAwsAccountId')
            }
            
            try:
                # Check if instance already exists
                existing = supabase.table('amc_instances').select('*').eq('instance_id', instance['instanceId']).execute()
                
                if existing.data:
                    print(f"  ✓ Instance already exists: {instance['instanceName']}")
                else:
                    # Insert new instance
                    response = supabase.table('amc_instances').insert(instance_data).execute()
                    print(f"  ✓ Created instance: {instance['instanceName']} ({instance['instanceType']})")
                    instance_count += 1
            except Exception as e:
                print(f"  ✗ Error creating instance {instance['instanceName']}: {str(e)}")
    
    print(f"\n✓ Total instances imported: {instance_count}")

def main():
    """Main import function"""
    print("Starting initial data import...")
    
    # Create user
    user_id = create_user()
    if not user_id:
        print("Failed to create user. Exiting.")
        return
    
    # Import AMC accounts
    account_ids = import_amc_accounts(user_id)
    if not account_ids:
        print("No accounts imported. Exiting.")
        return
    
    # Import AMC instances
    import_amc_instances(account_ids)
    
    print("\n✅ Initial data import completed!")
    print(f"\nSummary:")
    print(f"- User ID: {user_id}")
    print(f"- AMC Accounts: {len(account_ids)}")
    print(f"- AMC Instances: Check logs above for count")

if __name__ == "__main__":
    main()