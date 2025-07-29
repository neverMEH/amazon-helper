#!/usr/bin/env python3
"""Test AMC integration with corrected API client"""

import json
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amc_manager.core.api_client import AMCAPIClient
from amc_manager.services.instance_service import AMCInstanceService


async def test_amc_instances():
    """Test retrieving AMC instances with the corrected API client"""
    
    print("Testing AMC Instance Retrieval")
    print("="*60)
    
    # Load tokens
    try:
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        print("❌ tokens.json not found")
        return
        
    # Load AMC accounts
    try:
        with open('amc_accounts.json', 'r') as f:
            data = json.load(f)
            amc_accounts = data.get('amcAccounts', [])
    except:
        print("❌ amc_accounts.json not found")
        return
    
    print(f"\n📋 Found {len(amc_accounts)} AMC accounts:")
    for account in amc_accounts:
        print(f"  - {account['accountName']} ({account['accountId']})")
    
    # Initialize API client
    # Using first profile's marketplace for now
    api_client = AMCAPIClient(
        profile_id="2960674956882303",  # US profile
        marketplace_id="ATVPDKIKX0DER"
    )
    
    # Initialize instance service
    instance_service = AMCInstanceService(api_client)
    
    # Test for each AMC account
    all_instances = []
    for account in amc_accounts:
        print(f"\n🔍 Getting instances for: {account['accountName']}")
        print("-"*40)
        
        try:
            # Get instances for this entity
            instances = await instance_service.list_instances(
                user_id="test_user",
                user_token=tokens,
                entity_id=account['accountId']
            )
            
            print(f"✅ Found {len(instances)} instances")
            
            # Display first few instances
            for i, instance in enumerate(instances[:3]):
                print(f"\n  Instance {i+1}:")
                print(f"    ID: {instance.get('instanceId')}")
                print(f"    Name: {instance.get('instanceName')}")
                print(f"    Type: {instance.get('instanceType')}")
                print(f"    Customer: {instance.get('customerCanonicalName')}")
                
            all_instances.extend(instances)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Save summary
    if all_instances:
        summary = {
            'total_instances': len(all_instances),
            'accounts': [
                {
                    'name': acc['accountName'],
                    'id': acc['accountId'],
                    'marketplace': acc['marketplaceId']
                }
                for acc in amc_accounts
            ],
            'instance_count_by_type': {
                'STANDARD': sum(1 for i in all_instances if i.get('instanceType') == 'STANDARD'),
                'SANDBOX': sum(1 for i in all_instances if i.get('instanceType') == 'SANDBOX')
            }
        }
        
        with open('amc_integration_test_results.json', 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n\n{'='*60}")
        print("📊 Summary")
        print(f"{'='*60}")
        print(f"Total AMC instances: {len(all_instances)}")
        print(f"Standard instances: {summary['instance_count_by_type']['STANDARD']}")
        print(f"Sandbox instances: {summary['instance_count_by_type']['SANDBOX']}")
        print("\n✅ Integration test successful!")
        print("💾 Results saved to: amc_integration_test_results.json")
    else:
        print("\n❌ No instances retrieved")


if __name__ == "__main__":
    asyncio.run(test_amc_instances())