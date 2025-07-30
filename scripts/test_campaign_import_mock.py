#!/usr/bin/env python3
"""Test campaign import with mock data"""

import os
import sys
import asyncio
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.services.db_service import db_service
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


async def create_mock_campaigns():
    """Create mock campaign data for testing"""
    print("\nCreating mock campaign data for testing...")
    print("=" * 50)
    
    # Get user
    user = await db_service.get_user_by_email("nick@nevermeh.com")
    if not user:
        print("✗ User not found. Please run import_initial_data.py first")
        return
    
    user_id = user['id']
    print(f"✓ Found user: {user['name']}")
    
    # Mock campaigns for different types and brands
    # Using numeric IDs since campaign_id is BIGINT in database
    mock_campaigns = [
        # DSP Campaigns
        {
            "campaign_id": 123450001,
            "campaign_name": "Dirty Labs - Summer Campaign 2024",
            "campaign_type": "DSP",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "1234567890",
            "brand_tag": "dirty labs",
            "asins": ["B08XYZ123", "B08XYZ456"],
            "tags": ["DSP", "summer", "brand awareness"]
        },
        {
            "campaign_id": 678900002,
            "campaign_name": "Planetary Design - Coffee Lovers",
            "campaign_type": "DSP",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "1234567890",
            "brand_tag": "planetary design",
            "asins": ["B09ABC789"],
            "tags": ["DSP", "coffee", "lifestyle"]
        },
        
        # Sponsored Products
        {
            "campaign_id": 111110003,
            "campaign_name": "Supergoop - Sunscreen Bestsellers",
            "campaign_type": "SP",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "2345678901",
            "brand_tag": "supergoop",
            "asins": ["B07DEF123", "B07DEF456", "B07DEF789"],
            "tags": ["SP", "sunscreen", "bestsellers"]
        },
        {
            "campaign_id": 222220004,
            "campaign_name": "OOFOS Recovery Footwear - Running",
            "campaign_type": "SP",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "2345678901",
            "brand_tag": "oofos",
            "asins": ["B08GHI123", "B08GHI456"],
            "tags": ["SP", "footwear", "recovery", "running"]
        },
        
        # Sponsored Display
        {
            "campaign_id": 333330005,
            "campaign_name": "Dr Brandt Skincare - Retargeting",
            "campaign_type": "SD",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "3456789012",
            "brand_tag": "dr brandt",
            "asins": ["B09JKL123"],
            "tags": ["SD", "skincare", "retargeting"]
        },
        {
            "campaign_id": 444440006,
            "campaign_name": "Drunk Elephant - Holiday Gift Sets",
            "campaign_type": "SD",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "3456789012",
            "brand_tag": "drunk elephant",
            "asins": ["B09MNO123", "B09MNO456", "B09MNO789"],
            "tags": ["SD", "holiday", "gift sets"]
        },
        
        # Sponsored Brands
        {
            "campaign_id": 555550007,
            "campaign_name": "Nest New York - Luxury Candles",
            "campaign_type": "SB",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "4567890123",
            "brand_tag": "nest new york",
            "asins": ["B08PQR123", "B08PQR456"],
            "tags": ["SB", "candles", "luxury", "home fragrance"]
        },
        {
            "campaign_id": 666660008,
            "campaign_name": "Beekman 1802 - Goat Milk Collection",
            "campaign_type": "SB",
            "marketplace_id": "ATVPDKIKX0DER",
            "profile_id": "4567890123",
            "brand_tag": "beekman",
            "asins": ["B07STU123", "B07STU456", "B07STU789"],
            "tags": ["SB", "goat milk", "natural", "skincare"]
        }
    ]
    
    # Create campaigns
    created_count = 0
    for campaign in mock_campaigns:
        campaign_data = {
            **campaign,
            "user_id": user_id,
            "original_name": campaign["campaign_name"],
            "first_seen_at": datetime.now(timezone.utc).isoformat(),
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
            "brand_metadata": {
                "mock_data": True,
                "created_for_testing": datetime.now(timezone.utc).isoformat()
            }
        }
        
        result = await db_service.create_campaign_mapping(campaign_data)
        if result:
            created_count += 1
            print(f"✓ Created: {campaign['campaign_type']} - {campaign['campaign_name']}")
        else:
            print(f"✗ Failed: {campaign['campaign_name']}")
    
    print(f"\n✓ Created {created_count} mock campaigns")
    
    # List campaigns by type
    print("\nCampaigns by type:")
    print("-" * 50)
    
    campaigns = await db_service.get_user_campaigns(user_id)
    by_type = {}
    for campaign in campaigns:
        campaign_type = campaign['campaign_type']
        if campaign_type not in by_type:
            by_type[campaign_type] = 0
        by_type[campaign_type] += 1
    
    for campaign_type, count in sorted(by_type.items()):
        print(f"  {campaign_type}: {count} campaigns")
    
    print(f"\nTotal: {len(campaigns)} campaigns")
    
    # Show brand distribution
    print("\nCampaigns by brand:")
    print("-" * 50)
    
    by_brand = {}
    for campaign in campaigns:
        brand = campaign.get('brand_tag', 'Unknown')
        if brand not in by_brand:
            by_brand[brand] = 0
        by_brand[brand] += 1
    
    for brand, count in sorted(by_brand.items()):
        if brand and brand != 'Unknown':
            print(f"  {brand}: {count} campaigns")


async def test_campaign_sync_endpoint():
    """Test the campaign sync API endpoint"""
    print("\n\nTesting Campaign Sync API Endpoint")
    print("=" * 50)
    
    import httpx
    
    # First login to get token
    async with httpx.AsyncClient() as client:
        # Login
        login_response = await client.post(
            "http://localhost:8001/api/auth/login",
            params={"email": "nick@nevermeh.com"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print("✓ Login successful")
            
            # Test campaign sync endpoint
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get campaigns
            campaigns_response = await client.get(
                "http://localhost:8001/api/campaigns",
                headers=headers
            )
            
            if campaigns_response.status_code == 200:
                campaigns = campaigns_response.json()
                print(f"✓ Retrieved {len(campaigns)} campaigns via API")
            else:
                print(f"✗ Failed to get campaigns: {campaigns_response.status_code}")
        else:
            print("✗ Login failed")


async def main():
    """Main function"""
    print("Mock Campaign Import Test")
    print("=" * 50)
    print("This creates mock campaign data for testing purposes")
    
    # Create mock campaigns
    await create_mock_campaigns()
    
    # Test API if server is running
    print("\n\nChecking if API server is running...")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/api/health", timeout=2)
            if response.status_code == 200:
                print("✓ API server is running")
                await test_campaign_sync_endpoint()
            else:
                print("✗ API server returned error")
    except:
        print("✗ API server is not running")
        print("  Start it with: python main_supabase.py")
    
    print("\n✅ Mock campaign import completed!")


if __name__ == "__main__":
    asyncio.run(main())