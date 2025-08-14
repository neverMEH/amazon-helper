#!/usr/bin/env python3
"""
Update Amazon Prime Video Channel Insights data sources in AMC
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

# Define the Amazon Prime Video Channel Insights data sources
pvc_insights_sources = [
    # Enrollments tables
    {
        "schema_id": "amazon_pvc_enrollments",
        "name": "Amazon PVC Enrollments",
        "description": "Analytics table containing Prime Video Channel subscription enrollment records per benefit ID. Available as AMC Paid Feature for advertisers operating Prime Video Channels in supported marketplaces (US/CA/JP/AU/FR/IT/ES/UK/DE). Use COUNT() or COUNT(DISTINCT) on pv_subscription_id for metrics.",
        "category": "Prime Video Channels",
        "table_type": "Analytics",
        "data_type": "enrollments"
    },
    {
        "schema_id": "amazon_pvc_enrollments_for_audiences",
        "name": "Amazon PVC Enrollments for Audiences",
        "description": "Audience table containing Prime Video Channel subscription enrollment records per benefit ID. Available as AMC Paid Feature for advertisers operating Prime Video Channels. Use for audience creation based on subscription status and behavior.",
        "category": "Prime Video Channels",
        "table_type": "Audience",
        "data_type": "enrollments"
    },
    
    # Streaming events tables
    {
        "schema_id": "amazon_pvc_streaming_events_feed",
        "name": "Amazon PVC Streaming Events Feed",
        "description": "Analytics table containing Prime Video Channel streaming and engagement events. Provides engagement metrics including content metadata, request context, and duration. Events are session-based at PVC benefit-level. Available as AMC Paid Feature. Use COUNT() or COUNT(DISTINCT) on pv_session_id for metrics.",
        "category": "Prime Video Channels",
        "table_type": "Analytics",
        "data_type": "streaming"
    },
    {
        "schema_id": "amazon_pvc_streaming_events_feed_for_audiences",
        "name": "Amazon PVC Streaming Events Feed for Audiences",
        "description": "Audience table containing Prime Video Channel streaming and engagement events. Provides engagement metrics including content metadata, request context, and duration. Events are session-based at PVC benefit-level. Use for audience creation based on viewing behavior.",
        "category": "Prime Video Channels",
        "table_type": "Audience",
        "data_type": "streaming"
    }
]

# Define field counts for each table type
enrollments_field_count = 21
streaming_field_count = 44

def update_pvc_insights():
    """Update Amazon Prime Video Channel Insights data sources"""
    
    print("\n=== Updating Amazon Prime Video Channel Insights Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in pvc_insights_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            # Build tags
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'Prime-Video-Channels',
                'Multi-Marketplace',
                'Streaming-Data'
            ]
            
            # Add specific tags based on data type
            if source.get('data_type') == 'enrollments':
                tags.extend([
                    'Subscription-Data',
                    'Billing-Info',
                    'Free-Trial-Tracking',
                    'Plan-Conversions',
                    'Promo-Tracking'
                ])
                field_count = enrollments_field_count
            else:  # streaming
                tags.extend([
                    'Viewing-Behavior',
                    'Content-Metadata',
                    'Session-Based',
                    'Watch-Time-Metrics',
                    'Live-Content',
                    'VOD-Content'
                ])
                field_count = streaming_field_count
            
            # Add content type tags for streaming
            if 'streaming' in source['schema_id']:
                tags.extend(['AVOD', 'SVOD', 'GTI-Metadata'])
            
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
            print(f"  Type: {source.get('data_type', '').capitalize()} data")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Amazon Prime Video Channel Insights Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Summary
    print("\n💎 PAID FEATURE DETAILS:")
    print("   💰 Requires: AMC Paid Features subscription")
    print("   🌎 Available Marketplaces: US, CA, JP, AU, FR, IT, ES, UK, DE")
    print("   🎬 Eligibility: Advertisers operating Prime Video Channels")
    print("   🔄 Trial Available: Yes, within AMC Paid Features suite")
    
    print("\n📊 Data Sources Overview:")
    print("\n   📋 ENROLLMENTS TABLES:")
    print("      • Subscription lifecycle tracking")
    print("      • Free trial to paid conversions")
    print("      • Billing type changes")
    print("      • Promotional offer tracking")
    print("      • Plan start/end dates")
    print(f"      • {enrollments_field_count} fields per table")
    
    print("\n   🎥 STREAMING EVENTS TABLES:")
    print("      • Session-based viewing data")
    print("      • Content metadata (GTI)")
    print("      • Watch time metrics")
    print("      • Live vs VOD content")
    print("      • AVOD vs SVOD tracking")
    print(f"      • {streaming_field_count} fields per table")
    
    print("\n🎯 Key Enrollment Metrics:")
    print("   • pv_subscription_id: Unique subscription identifier")
    print("   • pv_benefit_id/name: Specific channel benefits")
    print("   • pv_billing_type: Subscription billing details")
    print("   • pv_is_plan_conversion: Free trial conversions")
    print("   • pv_is_plan_start: New subscription starts")
    print("   • pv_is_promo: Promotional subscriptions")
    print("   • pv_enrollment_status: Current subscription status")
    
    print("\n🎬 Key Streaming Metrics:")
    print("   • pv_session_id: Unique streaming session")
    print("   • pv_seconds_viewed: Watch time per event")
    print("   • pv_gti_* fields: Global Title Information")
    print("   • pv_is_live: Live content indicator")
    print("   • pv_is_avod/svod: Monetization model")
    print("   • pv_material_type: full, live, promo, trailer")
    print("   • pv_stream_type: linear TV, live-event, VOD")
    
    print("\n📺 Content Metadata (GTI):")
    print("   • Title & Series Information")
    print("   • Cast & Directors")
    print("   • Genre & Studio")
    print("   • Content Rating")
    print("   • Release Date")
    print("   • Season & Episode")
    print("   • Sports & Events")
    
    print("\n📈 Use Cases:")
    print("   • Subscriber acquisition and retention analysis")
    print("   • Content performance measurement")
    print("   • Viewing behavior segmentation")
    print("   • Free trial conversion optimization")
    print("   • Content recommendation targeting")
    print("   • Churn prediction and prevention")
    print("   • Cross-channel viewing patterns")
    print("   • Live event engagement tracking")
    print("   • Genre preference analysis")
    
    print("\n⚠️  Important Notes:")
    print("   - Use COUNT()/COUNT(DISTINCT) for metric conversion")
    print("   - pv_subscription_id for enrollment metrics")
    print("   - pv_session_id for streaming metrics")
    print("   - no_3p_trackers flag for privacy compliance")
    print("   - user_id has VERY_HIGH threshold (use in CTEs only)")
    print("   - Available only for PVC channel operators")
    
    print("\n🔍 Aggregation Thresholds:")
    print("   • VERY_HIGH: user_id, pv_session_id")
    print("   • INTERNAL: marketplace_id, pv_benefit_id, pv_subscription_id")
    print("   • MEDIUM: pv_billing_type, pv_seconds_viewed, pv_playback_dt_utc")
    print("   • HIGH: pv_offer_name")
    print("   • LOW: Most dimensional fields")
    print("   • NONE: pv_unit_price")
    
    # Verify specific tables
    print("\n=== Verification ===")
    for schema_id in ['amazon_pvc_enrollments', 'amazon_pvc_streaming_events_feed']:
        result = supabase.table('amc_data_sources').select('name, tags, is_paid_feature').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
            print(f"  Tags: {', '.join(result.data[0].get('tags', [])[:5])}...")

if __name__ == "__main__":
    update_pvc_insights()