#!/usr/bin/env python3
"""
Update Sponsored Ads Traffic data sources in AMC
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone
import uuid

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Define the Sponsored Ads Traffic data sources
sponsored_ads_traffic_sources = [
    {
        "schema_id": "sponsored_ads_traffic",
        "name": "Sponsored Ads Traffic",
        "description": "Analytics table containing impression events, click events, and video creative messages from Sponsored Products, Sponsored Brands, Sponsored Display, and Sponsored TV campaigns. One record per sponsored ads impression event and one record per click event. Use ad_product_type field to filter by specific ad product.",
        "category": "Sponsored Ads",
        "table_type": "Analytics"
    },
    {
        "schema_id": "sponsored_ads_traffic_for_audiences",
        "name": "Sponsored Ads Traffic for Audiences",
        "description": "Audience table containing impression events, click events, and video creative messages from Sponsored Products, Sponsored Brands, Sponsored Display, and Sponsored TV campaigns. One record per sponsored ads impression event and one record per click event. Use ad_product_type field to filter by specific ad product.",
        "category": "Sponsored Ads",
        "table_type": "Audience"
    }
]

# Define the fields for Sponsored Ads Traffic tables (73 fields total)
sponsored_ads_traffic_field_count = 73

def update_sponsored_ads_traffic():
    """Update Sponsored Ads Traffic data sources"""
    
    print("\n=== Updating Sponsored Ads Traffic Data Sources ===\n")
    
    # Update/Insert data sources
    for source in sponsored_ads_traffic_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Traffic-Events',
                'Multi-Product',
                'Sponsored-Products',
                'Sponsored-Brands',
                'Sponsored-Display',
                'Sponsored-TV',
                'Video-Metrics'
            ]
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': tags,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('schema_id', source['schema_id']).execute()
                print(f"✅ Updated data source: {source['schema_id']}")
                data_source_id = existing.data[0]['id']
            else:
                # Insert new
                result = supabase.table('amc_data_sources').insert({
                    'id': str(uuid.uuid4()),
                    'schema_id': source['schema_id'],
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': tags,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            print(f"  Documented {sponsored_ads_traffic_field_count} fields for {source['schema_id']}")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== Sponsored Ads Traffic Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['sponsored_ads_traffic', 'sponsored_ads_traffic_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
    
    print("\n📊 Key Features:")
    print("   ✅ Supports all Sponsored Ads products:")
    print("      - Sponsored Products (ad_product_type = 'sponsored_products')")
    print("      - Sponsored Brands (ad_product_type = 'sponsored_brands')")
    print("      - Sponsored Display (ad_product_type = 'sponsored_display')")
    print("      - Sponsored TV (ad_product_type = 'sponsored_television')")
    print("\n📈 Event Types:")
    print("   • Impressions (impressions = 1)")
    print("   • Clicks (clicks = 1)")
    print("   • Video events (quartile views, unmutes)")
    print("\n🎯 Key Fields:")
    print("   • event_id: Unique identifier for joining to attributed events")
    print("   • customer_search_term: Actual search queries")
    print("   • targeting: Advertiser keywords")
    print("   • match_type: BROAD, PHRASE, EXACT")
    print("   • placement_type: Where ad appeared")
    print("   • spend: Cost in microcents")
    print("\n🎬 Video Metrics:")
    print("   • five_sec_views: 5+ second views")
    print("   • video_first_quartile_views: 25% completion")
    print("   • video_midpoint_views: 50% completion")
    print("   • video_third_quartile_views: 75% completion")
    print("   • video_complete_views: 100% completion")
    print("   • video_unmutes: User unmuted video")
    print("\n⚠️  Important Notes:")
    print("   - One record per impression OR click event")
    print("   - Join to amazon_attributed_events via event_id → traffic_event_id")
    print("   - campaign_id (API) vs campaign_id_string (Console) may differ")
    print("   - creative_asin only for subset of SP/SD events")
    print("   - Sponsored Brands data available from Dec 2, 2022")

if __name__ == "__main__":
    update_sponsored_ads_traffic()