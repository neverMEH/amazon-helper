#!/usr/bin/env python3
"""
Update Amazon Brand Store Insights data sources in AMC
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

# Define the Amazon Brand Store Insights data sources
brand_store_sources = [
    # Endemic advertisers - Page Views
    {
        "schema_id": "amazon_brand_store_page_views",
        "name": "Amazon Brand Store Page Views",
        "description": "Analytics table containing Brand Store page view events with dwell time. Events are at Store page-level. Available as AMC Paid Feature for endemic advertisers in supported marketplaces (US/CA/JP/AU/FR/IT/ES/UK/DE). Use COUNT() or COUNT(DISTINCT) on visit_id or session_id for metrics.",
        "category": "Brand Store",
        "table_type": "Analytics",
        "advertiser_type": "endemic"
    },
    {
        "schema_id": "amazon_brand_store_page_views_for_audiences",
        "name": "Amazon Brand Store Page Views for Audiences",
        "description": "Audience table containing Brand Store page view events with dwell time. Events are at Store page-level. Available as AMC Paid Feature for endemic advertisers. Use for audience creation based on store visitor behavior.",
        "category": "Brand Store",
        "table_type": "Audience",
        "advertiser_type": "endemic"
    },
    
    # Non-endemic advertisers - Page Views
    {
        "schema_id": "amazon_brand_store_page_views_non_endemic",
        "name": "Amazon Brand Store Page Views (Non-Endemic)",
        "description": "Analytics table containing Brand Store page view events with dwell time for non-endemic advertisers. Events are at Store page-level. Available as AMC Paid Feature in supported marketplaces (US/CA/JP/AU/FR/IT/ES/UK/DE). Use COUNT() or COUNT(DISTINCT) on visit_id or session_id for metrics.",
        "category": "Brand Store",
        "table_type": "Analytics",
        "advertiser_type": "non-endemic"
    },
    {
        "schema_id": "amazon_brand_store_page_views_non_endemic_for_audiences",
        "name": "Amazon Brand Store Page Views (Non-Endemic) for Audiences",
        "description": "Audience table containing Brand Store page view events with dwell time for non-endemic advertisers. Events are at Store page-level. Available as AMC Paid Feature. Use for audience creation based on store visitor behavior.",
        "category": "Brand Store",
        "table_type": "Audience",
        "advertiser_type": "non-endemic"
    },
    
    # Endemic advertisers - Engagement Events
    {
        "schema_id": "amazon_brand_store_engagement_events",
        "name": "Amazon Brand Store Engagement Events",
        "description": "Analytics table containing Brand Store web engagement metrics including page views and clicks. Events are interaction-based at Store widget-level. Available as AMC Paid Feature for endemic advertisers in supported marketplaces. Use COUNT() or COUNT(DISTINCT) on visit_id or session_id for metrics.",
        "category": "Brand Store",
        "table_type": "Analytics",
        "advertiser_type": "endemic"
    },
    {
        "schema_id": "amazon_brand_store_engagement_events_for_audiences",
        "name": "Amazon Brand Store Engagement Events for Audiences",
        "description": "Audience table containing Brand Store web engagement metrics including page views and clicks. Events are interaction-based at Store widget-level. Available as AMC Paid Feature for endemic advertisers. Use for audience creation based on engagement behavior.",
        "category": "Brand Store",
        "table_type": "Audience",
        "advertiser_type": "endemic"
    },
    
    # Non-endemic advertisers - Engagement Events
    {
        "schema_id": "amazon_brand_store_engagement_events_non_endemic",
        "name": "Amazon Brand Store Engagement Events (Non-Endemic)",
        "description": "Analytics table containing Brand Store web engagement metrics for non-endemic advertisers. Events are interaction-based at Store widget-level. Available as AMC Paid Feature in supported marketplaces. Use COUNT() or COUNT(DISTINCT) on visit_id or session_id for metrics.",
        "category": "Brand Store",
        "table_type": "Analytics",
        "advertiser_type": "non-endemic"
    },
    {
        "schema_id": "amazon_brand_store_engagement_events_non_endemic_for_audiences",
        "name": "Amazon Brand Store Engagement Events (Non-Endemic) for Audiences",
        "description": "Audience table containing Brand Store web engagement metrics for non-endemic advertisers. Events are interaction-based at Store widget-level. Available as AMC Paid Feature. Use for audience creation based on engagement behavior.",
        "category": "Brand Store",
        "table_type": "Audience",
        "advertiser_type": "non-endemic"
    }
]

# Define field counts for each table type
page_views_field_count = 18
engagement_events_field_count = 21

def update_brand_store():
    """Update Amazon Brand Store Insights data sources"""
    
    print("\n=== Updating Amazon Brand Store Insights Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in brand_store_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            # Build tags
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'Brand-Store-Insights',
                'Multi-Marketplace'
            ]
            
            # Add specific tags based on table type
            if 'page_views' in source['schema_id']:
                tags.extend(['Page-Views', 'Dwell-Time', 'Page-Level'])
                field_count = page_views_field_count
            else:
                tags.extend(['Engagement-Events', 'Widget-Level', 'Clicks'])
                field_count = engagement_events_field_count
            
            # Add advertiser type tag
            if source.get('advertiser_type') == 'non-endemic':
                tags.append('Non-Endemic')
            else:
                tags.append('Endemic')
            
            # Add ingress type tracking
            tags.extend(['Traffic-Source-Tracking', 'Session-Tracking'])
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': tags,
                    'is_paid_feature': True,  # Mark as paid feature
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('schema_id', source['schema_id']).execute()
                print(f"✅ Updated: {source['schema_id']}")
                success_count += 1
            else:
                # Insert new
                result = supabase.table('amc_data_sources').insert({
                    'id': str(uuid.uuid4()),
                    'schema_id': source['schema_id'],
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': tags,
                    'is_paid_feature': True,  # Mark as paid feature
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created: {source['schema_id']}")
                success_count += 1
            
            print(f"  Documented {field_count} fields")
            print(f"  💰 Marked as PAID FEATURE")
            print(f"  Type: {source.get('advertiser_type', 'endemic').capitalize()} advertisers")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Amazon Brand Store Insights Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Summary
    print("\n💎 PAID FEATURE DETAILS:")
    print("   💰 Requires: AMC Paid Features subscription")
    print("   🌎 Available Marketplaces: US, CA, JP, AU, FR, IT, ES, UK, DE")
    print("   👥 Advertiser Types: Both endemic and non-endemic")
    print("   🔄 Trial Available: Yes, within AMC Paid Features suite")
    
    print("\n📊 Table Types:")
    print("   📄 Page Views Tables:")
    print("      • Page-level events")
    print("      • Dwell time tracking")
    print("      • Session and visit tracking")
    print(f"      • {page_views_field_count} fields per table")
    print("   🎯 Engagement Events Tables:")
    print("      • Widget-level interactions")
    print("      • Click tracking")
    print("      • ASIN-level engagement")
    print(f"      • {engagement_events_field_count} fields per table")
    
    print("\n🚦 Traffic Sources (ingress_type):")
    print("   • 0 - Uncategorized/Default")
    print("   • 1 - Search")
    print("   • 2 - Detail page byline")
    print("   • 4 - Ads (with reference_id)")
    print("   • 6 - Store recommendations")
    print("   • 7-11 - Experimentation")
    
    print("\n🎯 Key Metrics:")
    print("   • visit_id: Store visit identifier")
    print("   • session_id: Store session identifier")
    print("   • dwell_time: Time spent on page (seconds)")
    print("   • page_id: Specific store page")
    print("   • widget_type: UI component type")
    print("   • event_type/sub_type: Interaction details")
    
    print("\n📈 Use Cases:")
    print("   • Store visitor behavior analysis")
    print("   • Engagement funnel optimization")
    print("   • Traffic source attribution")
    print("   • Content performance measurement")
    print("   • Widget effectiveness tracking")
    print("   • Cross-device journey analysis")
    print("   • Ad-driven store traffic measurement")
    print("   • Store layout optimization")
    
    print("\n⚠️  Important Notes:")
    print("   - Use COUNT() or COUNT(DISTINCT) on visit_id/session_id for metrics")
    print("   - Page views: Page-level granularity")
    print("   - Engagement: Widget-level granularity")
    print("   - reference_id links to ad campaigns (when ingress_type = 4)")
    print("   - no_3p_trackers flag for privacy compliance")
    print("   - Separate tables for endemic vs non-endemic advertisers")
    
    print("\n🔍 Aggregation Thresholds:")
    print("   • VERY_HIGH: user_id, session_id, visit_id")
    print("   • MEDIUM: device_type, ingress_type")
    print("   • LOW: Most dimensional fields")
    print("   • INTERNAL: marketplace_id")
    print("   • NONE: no_3p_trackers")
    
    # Verify specific tables
    print("\n=== Verification ===")
    sample_tables = [
        'amazon_brand_store_page_views',
        'amazon_brand_store_engagement_events',
        'amazon_brand_store_page_views_non_endemic',
        'amazon_brand_store_engagement_events_non_endemic'
    ]
    
    for schema_id in sample_tables:
        result = supabase.table('amc_data_sources').select('name, tags, is_paid_feature').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
            print(f"  Tags: {', '.join(result.data[0].get('tags', [])[:5])}...")

if __name__ == "__main__":
    update_brand_store()