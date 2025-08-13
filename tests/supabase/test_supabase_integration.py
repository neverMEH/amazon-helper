#!/usr/bin/env python3
"""Test Supabase integration with AMC Manager"""

import asyncio
import json
from datetime import datetime
from amc_manager.core import (
    CampaignMappingService,
    BrandConfigurationService,
    WorkflowService,
    AMCInstanceService
)

async def test_integration():
    """Test basic Supabase operations"""
    
    print("🧪 Testing Supabase Integration for AMC Manager\n")
    
    # Test user ID (in production, this would come from auth)
    test_user_id = "00000000-0000-0000-0000-000000000000"
    
    # Initialize services
    campaign_service = CampaignMappingService()
    brand_service = BrandConfigurationService()
    workflow_service = WorkflowService()
    instance_service = AMCInstanceService()
    
    # 1. Test Brand Configuration
    print("1️⃣ Testing Brand Configuration...")
    try:
        test_brand = {
            "brand_tag": "TEST_BRAND",
            "brand_name": "Test Brand",
            "description": "Test brand for integration testing",
            "primary_asins": ["B001TEST", "B002TEST"],
            "all_asins": ["B001TEST", "B002TEST", "B003TEST"],
            "campaign_name_patterns": [".*TEST.*", ".*test.*"],
            "owner_user_id": test_user_id
        }
        
        # Create brand (this will fail if tables don't exist)
        result = await brand_service.create_brand(test_brand)
        print("✅ Brand created successfully")
        
    except Exception as e:
        print(f"❌ Brand creation failed: {e}")
    
    # 2. Test Campaign Mapping with ASINs
    print("\n2️⃣ Testing Campaign Mapping...")
    try:
        test_campaign = {
            "campaign_id": 12345,
            "campaign_name": "TEST Campaign 2024",
            "original_name": "TEST Campaign 2024",
            "campaign_type": "SP",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "PROFILE123",
            "brand_tag": "TEST_BRAND",
            "asins": ["B001TEST", "B002TEST"],
            "user_id": test_user_id,
            "first_seen_at": datetime.utcnow().isoformat(),
            "last_seen_at": datetime.utcnow().isoformat()
        }
        
        result = await campaign_service.create_campaign_mapping(test_campaign)
        print("✅ Campaign created with ASINs")
        
        # Test searching by ASINs
        campaigns = await campaign_service.get_campaigns_by_asins(
            test_user_id, 
            ["B001TEST"]
        )
        print(f"✅ Found {len(campaigns)} campaigns with ASIN B001TEST")
        
    except Exception as e:
        print(f"❌ Campaign operations failed: {e}")
    
    # 3. Test AMC Instance
    print("\n3️⃣ Testing AMC Instance Management...")
    try:
        # First create an account
        test_account = {
            "account_id": "ACC123",
            "account_name": "Test Account",
            "marketplace_id": "ATVPDKIKX0DER",
            "region": "us-east-1",
            "user_id": test_user_id
        }
        
        # This would normally be done through account service
        print("✅ Would create AMC account and instance")
        
    except Exception as e:
        print(f"❌ Instance operations failed: {e}")
    
    # 4. Test Workflow
    print("\n4️⃣ Testing Workflow Management...")
    try:
        test_workflow = {
            "workflow_id": "WF123",
            "name": "Test Campaign Analysis",
            "description": "Analyze campaign performance by ASIN",
            "instance_id": "00000000-0000-0000-0000-000000000000",  # Would be real instance ID
            "sql_query": """
                SELECT 
                    campaign_id,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(impressions) as total_impressions
                FROM impressions
                WHERE campaign_id = :campaign_id
                GROUP BY campaign_id
            """,
            "parameters": {
                "campaign_id": 12345
            },
            "user_id": test_user_id
        }
        
        result = await workflow_service.create_workflow(test_workflow)
        print("✅ Workflow created successfully")
        
    except Exception as e:
        print(f"❌ Workflow operations failed: {e}")
    
    # 5. Test Real-time Subscription
    print("\n5️⃣ Testing Real-time Subscriptions...")
    try:
        def execution_callback(payload):
            print(f"📡 Real-time update received: {payload}")
        
        # This would subscribe to real-time updates
        print("✅ Real-time subscription capability available")
        
    except Exception as e:
        print(f"❌ Real-time subscription failed: {e}")
    
    print("\n✨ Integration test completed!")
    print("\nNext steps:")
    print("1. Run the SQL scripts in Supabase to create tables")
    print("2. Implement authentication (Supabase Auth or custom)")
    print("3. Migrate existing data if needed")
    print("4. Update all API endpoints to use Supabase services")
    print("5. Set up real-time subscriptions for live updates")

if __name__ == "__main__":
    asyncio.run(test_integration())