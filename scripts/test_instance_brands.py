#!/usr/bin/env python3
"""Test instance brands functionality"""

import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.services.db_service import db_service
from amc_manager.services.brand_service import brand_service
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


async def test_instance_brands():
    """Test instance brands functionality"""
    print("\nTesting Instance Brands Feature")
    print("=" * 50)
    
    # Get user
    user = await db_service.get_user_by_email("nick@nevermeh.com")
    if not user:
        print("✗ User not found")
        return
    
    user_id = user['id']
    print(f"✓ Found user: {user['name']}")
    
    # Get user instances
    instances = db_service.get_user_instances_sync(user_id)
    if not instances:
        print("✗ No instances found")
        return
    
    print(f"✓ Found {len(instances)} instances")
    
    # Test with first instance
    test_instance = instances[0]
    instance_id = test_instance['instance_id']
    print(f"\nTesting with instance: {test_instance['instance_name']} ({instance_id})")
    
    # Get current brands (should be from migration)
    print("\n1. Getting current brands...")
    current_brands = brand_service.get_instance_brands_sync(instance_id)
    print(f"   Current brands: {current_brands}")
    
    # Get all available brands
    print("\n2. Getting all available brands...")
    available_brands = brand_service.get_all_brands_sync(user_id)
    print(f"   Found {len(available_brands)} available brands")
    for brand in available_brands[:5]:  # Show first 5
        print(f"   - {brand['brand_name']} ({brand['brand_tag']}) - {brand['source']}")
    
    # Update instance brands
    print("\n3. Updating instance brands...")
    test_brands = ["dirty labs", "supergoop", "oofos"]
    success = brand_service.update_instance_brands_sync(instance_id, test_brands, user_id)
    if success:
        print(f"   ✓ Updated brands to: {test_brands}")
    else:
        print("   ✗ Failed to update brands")
        return
    
    # Verify update
    print("\n4. Verifying update...")
    updated_brands = brand_service.get_instance_brands_sync(instance_id)
    print(f"   New brands: {updated_brands}")
    
    # Get filtered campaigns
    print("\n5. Getting campaigns filtered by instance brands...")
    filtered_campaigns = db_service.get_instance_campaigns_filtered_sync(instance_id, user_id)
    print(f"   Found {len(filtered_campaigns)} campaigns matching instance brands")
    
    # Show campaign breakdown by brand
    by_brand = {}
    for campaign in filtered_campaigns:
        brand = campaign.get('brand_tag', 'Unknown')
        if brand not in by_brand:
            by_brand[brand] = []
        by_brand[brand].append(campaign['campaign_name'])
    
    for brand, campaigns in by_brand.items():
        print(f"   {brand}: {len(campaigns)} campaigns")
        for campaign_name in campaigns[:2]:  # Show first 2
            print(f"     - {campaign_name}")
    
    # Test brand stats
    print("\n6. Getting brand statistics...")
    stats = brand_service.get_brand_stats_sync(user_id)
    for brand in test_brands:
        if brand in stats:
            brand_stats = stats[brand]
            print(f"   {brand}:")
            print(f"     - Campaigns: {brand_stats['campaign_count']}")
            print(f"     - Instances: {brand_stats['instance_count']}")
            print(f"     - ASINs: {brand_stats['asin_count']}")
    
    print("\n✅ Instance brands test completed successfully!")


async def main():
    """Main function"""
    await test_instance_brands()


if __name__ == "__main__":
    asyncio.run(main())