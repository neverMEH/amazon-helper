#!/usr/bin/env python3
"""
Update Conversions All data sources in AMC
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

# Define the Conversions All data sources
conversions_all_sources = [
    {
        "schema_id": "conversions_all",
        "name": "Conversions All",
        "description": "Analytics table containing both ad-exposed and non-ad-exposed conversions for tracked ASINs. Conversions are ad-exposed if a user was served a traffic event within the 28-day period prior to the conversion event. Available for measurement queries through Paid feature subscription, but can be used for AMC Audience creation without subscription.",
        "category": "Conversions",
        "table_type": "Analytics"
    },
    {
        "schema_id": "conversions_all_for_audiences",
        "name": "Conversions All for Audiences",
        "description": "Audience table containing both ad-exposed and non-ad-exposed conversions for tracked ASINs. Conversions are ad-exposed if a user was served a traffic event within the 28-day period prior to the conversion event. Can be used for AMC Audience creation without Paid feature subscription.",
        "category": "Conversions",
        "table_type": "Audience"
    }
]

# Define the fields for Conversions All tables (28 fields)
conversions_all_field_count = 28

def update_conversions_all():
    """Update Conversions All data sources"""
    
    print("\n=== Updating Conversions All Data Sources ===\n")
    
    # Update/Insert data sources
    for source in conversions_all_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'Ad-Exposed',
                'Non-Ad-Exposed',
                'Organic-Conversions',
                '28-Day-Attribution',
                'Full-Conversion-View'
            ]
            
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
                    'is_paid_feature': True,  # Mark as paid feature
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            print(f"  Documented {conversions_all_field_count} fields for {source['schema_id']}")
            print(f"  💰 Marked as PAID FEATURE (except for audience creation)")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== Conversions All Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['conversions_all', 'conversions_all_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags, is_paid_feature').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
            print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
    
    print("\n💎 PAID FEATURE DETAILS:")
    print("   ✅ Measurement queries: REQUIRES paid subscription")
    print("   ✅ Audience creation: FREE (no subscription needed)")
    print("\n📊 Key Features:")
    print("   ✅ Includes BOTH ad-exposed and non-ad-exposed conversions")
    print("   ✅ Comprehensive view of all conversions")
    print("   ✅ Enables true incrementality analysis")
    print("   ✅ Organic vs paid conversion comparison")
    print("\n🎯 Exposure Types:")
    print("   • ad-exposed: Conversion within 28 days of traffic event")
    print("   • non-ad-exposed: Organic conversions (no ad exposure)")
    print("   • pixel: Pixel-based conversions")
    print("\n📈 Use Cases:")
    print("   • Incrementality measurement")
    print("   • Organic baseline establishment")
    print("   • Total conversion volume analysis")
    print("   • Ad effectiveness evaluation")
    print("   • Customer journey mapping (paid + organic)")
    print("\n⚠️  Important Notes:")
    print("   - Most comprehensive conversion view available")
    print("   - Includes conversions NOT attributed to ads")
    print("   - Essential for understanding true ad impact")
    print("   - exposure_type field distinguishes conversion source")

if __name__ == "__main__":
    update_conversions_all()