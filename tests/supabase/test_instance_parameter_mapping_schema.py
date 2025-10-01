#!/usr/bin/env python3
"""
Test suite for Instance Parameter Mapping database schema
Tests the new tables and indexes for brand-ASIN-campaign associations
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def supabase_client():
    """Create Supabase client for testing"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        pytest.skip("Missing Supabase credentials")

    return create_client(url, key)


@pytest.fixture
def test_user_id(supabase_client):
    """Create a test user and return ID"""
    user_data = {
        'id': str(uuid4()),
        'email': f'test_{uuid4().hex[:8]}@test.com',
        'name': 'Test User - Instance Mapping',
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase_client.table('users').insert(user_data).execute()
    user_id = result.data[0]['id']

    yield user_id

    # Cleanup
    supabase_client.table('users').delete().eq('id', user_id).execute()


@pytest.fixture
def test_account_id(supabase_client, test_user_id):
    """Create a test AMC account and return ID"""
    account_data = {
        'id': str(uuid4()),
        'account_id': f'test_account_{uuid4().hex[:8]}',
        'account_name': 'Test AMC Account',
        'marketplace_id': 'ATVPDKIKX0DER',
        'region': 'na',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase_client.table('amc_accounts').insert(account_data).execute()
    account_id = result.data[0]['id']

    yield account_id

    # Cleanup
    supabase_client.table('amc_accounts').delete().eq('id', account_id).execute()


@pytest.fixture
def test_instance_id(supabase_client, test_account_id):
    """Create a test AMC instance and return ID"""
    instance_data = {
        'id': str(uuid4()),
        'instance_id': f'testinst{uuid4().hex[:8]}',
        'instance_name': 'Test Instance - Mapping',
        'region': 'na',
        'account_id': test_account_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase_client.table('amc_instances').insert(instance_data).execute()
    instance_id = result.data[0]['id']

    yield instance_id

    # Cleanup
    supabase_client.table('amc_instances').delete().eq('id', instance_id).execute()


# ============================================================================
# Table Existence Tests
# ============================================================================

def test_instance_brand_asins_table_exists(supabase_client):
    """Verify instance_brand_asins table exists with correct structure"""
    # Try to query the table
    result = supabase_client.table('instance_brand_asins').select('*').limit(0).execute()
    assert result is not None, "instance_brand_asins table should exist"


def test_instance_brand_campaigns_table_exists(supabase_client):
    """Verify instance_brand_campaigns table exists with correct structure"""
    # Try to query the table
    result = supabase_client.table('instance_brand_campaigns').select('*').limit(0).execute()
    assert result is not None, "instance_brand_campaigns table should exist"


# ============================================================================
# CRUD Operations Tests - instance_brand_asins
# ============================================================================

def test_insert_instance_brand_asin(supabase_client, test_instance_id, test_user_id):
    """Test inserting an ASIN mapping"""
    asin_mapping = {
        'id': str(uuid4()),
        'instance_id': test_instance_id,
        'brand_tag': 'test_brand',
        'asin': 'B08N5WRWNW',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()

    assert len(result.data) == 1
    assert result.data[0]['brand_tag'] == 'test_brand'
    assert result.data[0]['asin'] == 'B08N5WRWNW'
    assert result.data[0]['instance_id'] == test_instance_id

    # Cleanup
    supabase_client.table('instance_brand_asins').delete().eq('id', result.data[0]['id']).execute()


def test_unique_constraint_instance_brand_asin(supabase_client, test_instance_id, test_user_id):
    """Test that duplicate instance-brand-ASIN combinations are rejected"""
    asin_mapping = {
        'id': str(uuid4()),
        'instance_id': test_instance_id,
        'brand_tag': 'test_brand',
        'asin': 'B08N5WRWNW',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    # Insert first record
    result1 = supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()
    first_id = result1.data[0]['id']

    # Try to insert duplicate (different ID)
    asin_mapping['id'] = str(uuid4())
    with pytest.raises(Exception) as exc_info:
        supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()

    # Should raise error about unique constraint violation
    assert 'unique' in str(exc_info.value).lower() or 'duplicate' in str(exc_info.value).lower()

    # Cleanup
    supabase_client.table('instance_brand_asins').delete().eq('id', first_id).execute()


def test_foreign_key_instance_id_asins(supabase_client, test_user_id):
    """Test that foreign key constraint on instance_id works"""
    # Try to insert with non-existent instance_id
    fake_instance_id = str(uuid4())
    asin_mapping = {
        'id': str(uuid4()),
        'instance_id': fake_instance_id,
        'brand_tag': 'test_brand',
        'asin': 'B08N5WRWNW',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    with pytest.raises(Exception) as exc_info:
        supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()

    # Should raise error about foreign key violation
    assert 'foreign key' in str(exc_info.value).lower() or 'violates' in str(exc_info.value).lower()


def test_cascade_delete_instance_asins(supabase_client, test_account_id, test_user_id):
    """Test that deleting an instance cascades to delete ASIN mappings"""
    # Create a temporary instance
    instance_data = {
        'id': str(uuid4()),
        'instance_id': f'tempinst{uuid4().hex[:8]}',
        'instance_name': 'Temp Instance',
        'region': 'na',
        'account_id': test_account_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    inst_result = supabase_client.table('amc_instances').insert(instance_data).execute()
    temp_instance_id = inst_result.data[0]['id']

    # Create ASIN mapping
    asin_mapping = {
        'id': str(uuid4()),
        'instance_id': temp_instance_id,
        'brand_tag': 'test_brand',
        'asin': 'B08N5WRWNW',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    asin_result = supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()
    asin_mapping_id = asin_result.data[0]['id']

    # Delete instance
    supabase_client.table('amc_instances').delete().eq('id', temp_instance_id).execute()

    # Verify ASIN mapping was also deleted (cascade)
    check_result = supabase_client.table('instance_brand_asins').select('*').eq('id', asin_mapping_id).execute()
    assert len(check_result.data) == 0, "ASIN mapping should be deleted when instance is deleted"


# ============================================================================
# CRUD Operations Tests - instance_brand_campaigns
# ============================================================================

def test_insert_instance_brand_campaign(supabase_client, test_instance_id, test_user_id):
    """Test inserting a campaign mapping"""
    campaign_mapping = {
        'id': str(uuid4()),
        'instance_id': test_instance_id,
        'brand_tag': 'test_brand',
        'campaign_id': 12345678901,
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()

    assert len(result.data) == 1
    assert result.data[0]['brand_tag'] == 'test_brand'
    assert result.data[0]['campaign_id'] == 12345678901
    assert result.data[0]['instance_id'] == test_instance_id

    # Cleanup
    supabase_client.table('instance_brand_campaigns').delete().eq('id', result.data[0]['id']).execute()


def test_unique_constraint_instance_brand_campaign(supabase_client, test_instance_id, test_user_id):
    """Test that duplicate instance-brand-campaign combinations are rejected"""
    campaign_mapping = {
        'id': str(uuid4()),
        'instance_id': test_instance_id,
        'brand_tag': 'test_brand',
        'campaign_id': 12345678901,
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    # Insert first record
    result1 = supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()
    first_id = result1.data[0]['id']

    # Try to insert duplicate (different ID)
    campaign_mapping['id'] = str(uuid4())
    with pytest.raises(Exception) as exc_info:
        supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()

    # Should raise error about unique constraint violation
    assert 'unique' in str(exc_info.value).lower() or 'duplicate' in str(exc_info.value).lower()

    # Cleanup
    supabase_client.table('instance_brand_campaigns').delete().eq('id', first_id).execute()


def test_foreign_key_instance_id_campaigns(supabase_client, test_user_id):
    """Test that foreign key constraint on instance_id works"""
    # Try to insert with non-existent instance_id
    fake_instance_id = str(uuid4())
    campaign_mapping = {
        'id': str(uuid4()),
        'instance_id': fake_instance_id,
        'brand_tag': 'test_brand',
        'campaign_id': 12345678901,
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    with pytest.raises(Exception) as exc_info:
        supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()

    # Should raise error about foreign key violation
    assert 'foreign key' in str(exc_info.value).lower() or 'violates' in str(exc_info.value).lower()


def test_cascade_delete_instance_campaigns(supabase_client, test_account_id, test_user_id):
    """Test that deleting an instance cascades to delete campaign mappings"""
    # Create a temporary instance
    instance_data = {
        'id': str(uuid4()),
        'instance_id': f'tempinst{uuid4().hex[:8]}',
        'instance_name': 'Temp Instance',
        'region': 'na',
        'account_id': test_account_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    inst_result = supabase_client.table('amc_instances').insert(instance_data).execute()
    temp_instance_id = inst_result.data[0]['id']

    # Create campaign mapping
    campaign_mapping = {
        'id': str(uuid4()),
        'instance_id': temp_instance_id,
        'brand_tag': 'test_brand',
        'campaign_id': 12345678901,
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    campaign_result = supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()
    campaign_mapping_id = campaign_result.data[0]['id']

    # Delete instance
    supabase_client.table('amc_instances').delete().eq('id', temp_instance_id).execute()

    # Verify campaign mapping was also deleted (cascade)
    check_result = supabase_client.table('instance_brand_campaigns').select('*').eq('id', campaign_mapping_id).execute()
    assert len(check_result.data) == 0, "Campaign mapping should be deleted when instance is deleted"


# ============================================================================
# Query Performance Tests
# ============================================================================

def test_query_asins_by_instance(supabase_client, test_instance_id, test_user_id):
    """Test querying ASINs by instance_id (uses index)"""
    # Insert multiple ASIN mappings
    asins = ['B001', 'B002', 'B003']
    mapping_ids = []

    for asin in asins:
        mapping = {
            'id': str(uuid4()),
            'instance_id': test_instance_id,
            'brand_tag': 'test_brand',
            'asin': asin,
            'user_id': test_user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        result = supabase_client.table('instance_brand_asins').insert(mapping).execute()
        mapping_ids.append(result.data[0]['id'])

    # Query by instance_id
    result = supabase_client.table('instance_brand_asins')\
        .select('*')\
        .eq('instance_id', test_instance_id)\
        .execute()

    assert len(result.data) >= 3
    retrieved_asins = [item['asin'] for item in result.data]
    for asin in asins:
        assert asin in retrieved_asins

    # Cleanup
    for mapping_id in mapping_ids:
        supabase_client.table('instance_brand_asins').delete().eq('id', mapping_id).execute()


def test_query_campaigns_by_brand(supabase_client, test_instance_id, test_user_id):
    """Test querying campaigns by brand_tag (uses index)"""
    # Insert multiple campaign mappings for same brand
    campaigns = [111, 222, 333]
    mapping_ids = []

    for campaign_id in campaigns:
        mapping = {
            'id': str(uuid4()),
            'instance_id': test_instance_id,
            'brand_tag': 'test_brand',
            'campaign_id': campaign_id,
            'user_id': test_user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        result = supabase_client.table('instance_brand_campaigns').insert(mapping).execute()
        mapping_ids.append(result.data[0]['id'])

    # Query by brand_tag
    result = supabase_client.table('instance_brand_campaigns')\
        .select('*')\
        .eq('brand_tag', 'test_brand')\
        .execute()

    assert len(result.data) >= 3
    retrieved_campaigns = [item['campaign_id'] for item in result.data]
    for campaign_id in campaigns:
        assert campaign_id in retrieved_campaigns

    # Cleanup
    for mapping_id in mapping_ids:
        supabase_client.table('instance_brand_campaigns').delete().eq('id', mapping_id).execute()


def test_composite_index_query(supabase_client, test_instance_id, test_user_id):
    """Test query using composite index (instance_id + brand_tag)"""
    # Insert mappings for multiple brands
    brands = ['brand_a', 'brand_b']
    mapping_ids = []

    for brand in brands:
        for i in range(2):
            mapping = {
                'id': str(uuid4()),
                'instance_id': test_instance_id,
                'brand_tag': brand,
                'asin': f'B00{i}',
                'user_id': test_user_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            result = supabase_client.table('instance_brand_asins').insert(mapping).execute()
            mapping_ids.append(result.data[0]['id'])

    # Query using composite index (instance_id + brand_tag)
    result = supabase_client.table('instance_brand_asins')\
        .select('*')\
        .eq('instance_id', test_instance_id)\
        .eq('brand_tag', 'brand_a')\
        .execute()

    assert len(result.data) == 2
    assert all(item['brand_tag'] == 'brand_a' for item in result.data)

    # Cleanup
    for mapping_id in mapping_ids:
        supabase_client.table('instance_brand_asins').delete().eq('id', mapping_id).execute()


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_mapping_workflow(supabase_client, test_instance_id, test_user_id):
    """Test complete workflow: insert, query, update, delete mappings"""
    # 1. Insert brand mappings (using existing instance_brands table)
    brand_mapping = {
        'id': str(uuid4()),
        'instance_id': test_instance_id,
        'brand_tag': 'acme',
        'user_id': test_user_id,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    brand_result = supabase_client.table('instance_brands').insert(brand_mapping).execute()
    brand_id = brand_result.data[0]['id']

    # 2. Insert ASIN mappings
    asin_ids = []
    for asin in ['B001', 'B002']:
        asin_mapping = {
            'id': str(uuid4()),
            'instance_id': test_instance_id,
            'brand_tag': 'acme',
            'asin': asin,
            'user_id': test_user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        result = supabase_client.table('instance_brand_asins').insert(asin_mapping).execute()
        asin_ids.append(result.data[0]['id'])

    # 3. Insert campaign mappings
    campaign_ids = []
    for campaign_id in [111, 222]:
        campaign_mapping = {
            'id': str(uuid4()),
            'instance_id': test_instance_id,
            'brand_tag': 'acme',
            'campaign_id': campaign_id,
            'user_id': test_user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        result = supabase_client.table('instance_brand_campaigns').insert(campaign_mapping).execute()
        campaign_ids.append(result.data[0]['id'])

    # 4. Query all mappings for instance
    brand_query = supabase_client.table('instance_brands')\
        .select('*').eq('instance_id', test_instance_id).execute()
    asin_query = supabase_client.table('instance_brand_asins')\
        .select('*').eq('instance_id', test_instance_id).execute()
    campaign_query = supabase_client.table('instance_brand_campaigns')\
        .select('*').eq('instance_id', test_instance_id).execute()

    assert len(brand_query.data) >= 1
    assert len(asin_query.data) >= 2
    assert len(campaign_query.data) >= 2

    # 5. Cleanup (delete in reverse order of dependencies)
    for campaign_id in campaign_ids:
        supabase_client.table('instance_brand_campaigns').delete().eq('id', campaign_id).execute()
    for asin_id in asin_ids:
        supabase_client.table('instance_brand_asins').delete().eq('id', asin_id).execute()
    supabase_client.table('instance_brands').delete().eq('id', brand_id).execute()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
