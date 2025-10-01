#!/usr/bin/env python3
"""
Seed test data for instance parameter mapping tables.
Creates sample brand, ASIN, and campaign associations for testing.
"""
import os
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


def seed_instance_parameter_mappings():
    """Seed instance parameter mapping test data"""
    print("\nSeeding Instance Parameter Mapping Data")
    print("=" * 60)

    # Get Supabase client with service role
    client = SupabaseManager.get_client(use_service_role=True)

    # Step 1: Get or create a test user
    print("\n1. Getting test user...")
    users_result = client.table('users').select('id, email').limit(1).execute()

    if not users_result.data:
        print("   No users found. Creating test user...")
        test_user = {
            'id': str(uuid4()),
            'email': 'test@example.com',
            'name': 'Test User',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        user_result = client.table('users').insert(test_user).execute()
        user_id = user_result.data[0]['id']
        print(f"   ✓ Created test user: {user_id}")
    else:
        user_id = users_result.data[0]['id']
        print(f"   ✓ Using existing user: {users_result.data[0]['email']}")

    # Step 2: Get or create a test AMC instance
    print("\n2. Getting test AMC instance...")
    instances_result = client.table('amc_instances').select('id, instance_id, instance_name').limit(1).execute()

    if not instances_result.data:
        print("   No instances found. You need to create an AMC instance first.")
        print("   Skipping seed data creation.")
        return False
    else:
        instance_id = instances_result.data[0]['id']
        instance_name = instances_result.data[0]['instance_name']
        print(f"   ✓ Using instance: {instance_name} ({instance_id})")

    # Step 3: Create brand associations
    print("\n3. Creating brand associations...")
    brands = [
        {'brand_tag': 'acme', 'brand_name': 'Acme Products'},
        {'brand_tag': 'globex', 'brand_name': 'Globex Corporation'},
        {'brand_tag': 'initech', 'brand_name': 'Initech Software'}
    ]

    brand_ids = []
    for brand in brands:
        # Check if brand already exists for this instance
        existing = client.table('instance_brands')\
            .select('id')\
            .eq('instance_id', instance_id)\
            .eq('brand_tag', brand['brand_tag'])\
            .execute()

        if existing.data:
            brand_ids.append(existing.data[0]['id'])
            print(f"   • Brand '{brand['brand_tag']}' already exists")
        else:
            brand_data = {
                'id': str(uuid4()),
                'instance_id': instance_id,
                'brand_tag': brand['brand_tag'],
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            result = client.table('instance_brands').insert(brand_data).execute()
            brand_ids.append(result.data[0]['id'])
            print(f"   ✓ Created brand: {brand['brand_tag']}")

    # Step 4: Create ASIN associations
    print("\n4. Creating ASIN associations...")
    asin_mappings = [
        {'brand_tag': 'acme', 'asins': ['B08N5WRWNW', 'B07FZ8S74R', 'B09KMVNY9J']},
        {'brand_tag': 'globex', 'asins': ['B08X1Q2B9T', 'B07H8QWXYZ', 'B09LMNOPQR']},
        {'brand_tag': 'initech', 'asins': ['B08A1B2C3D', 'B07E4F5G6H']}
    ]

    asin_count = 0
    for mapping in asin_mappings:
        for asin in mapping['asins']:
            # Check if mapping already exists
            existing = client.table('instance_brand_asins')\
                .select('id')\
                .eq('instance_id', instance_id)\
                .eq('brand_tag', mapping['brand_tag'])\
                .eq('asin', asin)\
                .execute()

            if existing.data:
                print(f"   • ASIN {asin} ({mapping['brand_tag']}) already exists")
            else:
                asin_data = {
                    'id': str(uuid4()),
                    'instance_id': instance_id,
                    'brand_tag': mapping['brand_tag'],
                    'asin': asin,
                    'user_id': user_id,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                client.table('instance_brand_asins').insert(asin_data).execute()
                asin_count += 1
                print(f"   ✓ Created ASIN: {asin} → {mapping['brand_tag']}")

    print(f"\n   Total ASINs created: {asin_count}")

    # Step 5: Create campaign associations
    print("\n5. Creating campaign associations...")
    campaign_mappings = [
        {'brand_tag': 'acme', 'campaigns': [12345678901, 12345678902, 12345678903]},
        {'brand_tag': 'globex', 'campaigns': [98765432101, 98765432102]},
        {'brand_tag': 'initech', 'campaigns': [11111111111, 22222222222, 33333333333]}
    ]

    campaign_count = 0
    for mapping in campaign_mappings:
        for campaign_id in mapping['campaigns']:
            # Check if mapping already exists
            existing = client.table('instance_brand_campaigns')\
                .select('id')\
                .eq('instance_id', instance_id)\
                .eq('brand_tag', mapping['brand_tag'])\
                .eq('campaign_id', campaign_id)\
                .execute()

            if existing.data:
                print(f"   • Campaign {campaign_id} ({mapping['brand_tag']}) already exists")
            else:
                campaign_data = {
                    'id': str(uuid4()),
                    'instance_id': instance_id,
                    'brand_tag': mapping['brand_tag'],
                    'campaign_id': campaign_id,
                    'user_id': user_id,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                client.table('instance_brand_campaigns').insert(campaign_data).execute()
                campaign_count += 1
                print(f"   ✓ Created campaign: {campaign_id} → {mapping['brand_tag']}")

    print(f"\n   Total campaigns created: {campaign_count}")

    # Step 6: Verify data
    print("\n6. Verifying seeded data...")
    brands_check = client.table('instance_brands')\
        .select('*')\
        .eq('instance_id', instance_id)\
        .execute()
    asins_check = client.table('instance_brand_asins')\
        .select('*')\
        .eq('instance_id', instance_id)\
        .execute()
    campaigns_check = client.table('instance_brand_campaigns')\
        .select('*')\
        .eq('instance_id', instance_id)\
        .execute()

    print(f"   ✓ Brands: {len(brands_check.data)}")
    print(f"   ✓ ASINs: {len(asins_check.data)}")
    print(f"   ✓ Campaigns: {len(campaigns_check.data)}")

    print("\n" + "=" * 60)
    print("✅ Seed data created successfully!")
    print("\nSummary:")
    print(f"  Instance: {instance_name}")
    print(f"  Brands: {len(brands_check.data)}")
    print(f"  ASINs: {len(asins_check.data)}")
    print(f"  Campaigns: {len(campaigns_check.data)}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = seed_instance_parameter_mappings()
        if not success:
            print("\n⚠️  Seed data creation incomplete")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error seeding data: {e}")
        logger.error(f"Seed data creation failed: {e}", exc_info=True)
        sys.exit(1)
