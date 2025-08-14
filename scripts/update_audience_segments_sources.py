#!/usr/bin/env python3
"""
Update Amazon Audience Segment Membership data sources in AMC
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

# Define the regions and categories
regions = ['amer', 'apac', 'eu']
categories = ['inmarket', 'lifestyle']

# Generate all audience segment data sources
audience_segments_sources = []

# Add regular audience segment tables
for region in regions:
    for category in categories:
        # Analytics table
        audience_segments_sources.append({
            "schema_id": f"audience_segments_{region}_{category}",
            "name": f"Audience Segments {region.upper()} {category.capitalize()}",
            "description": f"Analytics table containing active user-to-segment associations for {region.upper()} {category} segments. Most recent associations, presented as DIMENSION dataset type. Each user-segment association is a distinct row. Note: Workflows using this table will time out over extended periods.",
            "category": "Audience Segments",
            "table_type": "Analytics",
            "region": region.upper(),
            "segment_category": category.capitalize(),
            "is_snapshot": False
        })
        
        # Audience table
        audience_segments_sources.append({
            "schema_id": f"audience_segments_{region}_{category}_for_audiences",
            "name": f"Audience Segments {region.upper()} {category.capitalize()} for Audiences",
            "description": f"Audience table containing active user-to-segment associations for {region.upper()} {category} segments. Most recent associations for audience creation.",
            "category": "Audience Segments",
            "table_type": "Audience",
            "region": region.upper(),
            "segment_category": category.capitalize(),
            "is_snapshot": False
        })
        
        # Snapshot analytics table
        audience_segments_sources.append({
            "schema_id": f"audience_segments_{region}_{category}_snapshot",
            "name": f"Audience Segments {region.upper()} {category.capitalize()} Snapshot",
            "description": f"Historical snapshot of user-segment associations for {region.upper()} {category} segments. Logged monthly on first Thursday, presented as FACT dataset type. Note: Workflows using this table will time out over extended periods.",
            "category": "Audience Segments",
            "table_type": "Analytics",
            "region": region.upper(),
            "segment_category": category.capitalize(),
            "is_snapshot": True
        })
        
        # Snapshot audience table
        audience_segments_sources.append({
            "schema_id": f"audience_segments_{region}_{category}_snapshot_for_audiences",
            "name": f"Audience Segments {region.upper()} {category.capitalize()} Snapshot for Audiences",
            "description": f"Historical snapshot for audience creation. User-segment associations for {region.upper()} {category} segments, logged monthly on first Thursday.",
            "category": "Audience Segments",
            "table_type": "Audience",
            "region": region.upper(),
            "segment_category": category.capitalize(),
            "is_snapshot": True
        })

# Add segment metadata tables
audience_segments_sources.extend([
    {
        "schema_id": "segment_metadata",
        "name": "Segment Metadata",
        "description": "Metadata describing segment_id and segment_marketplace_id from audience segment tables. Includes segment names, descriptions, and taxonomy. Join using both segment_id AND segment_marketplace_id.",
        "category": "Audience Segments",
        "table_type": "Analytics",
        "is_metadata": True
    },
    {
        "schema_id": "segment_metadata_for_audiences",
        "name": "Segment Metadata for Audiences",
        "description": "Metadata for audience creation. Describes segment_id and segment_marketplace_id. Join using both segment_id AND segment_marketplace_id.",
        "category": "Audience Segments",
        "table_type": "Audience",
        "is_metadata": True
    }
])

def update_audience_segments():
    """Update Amazon Audience Segment Membership data sources"""
    
    print("\n=== Updating Amazon Audience Segment Membership Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in audience_segments_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            # Build tags
            tags = [source.get('table_type'), 'Performance-Warning']
            
            if source.get('is_metadata'):
                tags.extend(['Metadata', 'Segment-Taxonomy'])
            else:
                tags.append(f"{source.get('region', 'Global')}-Region")
                tags.append(f"{source.get('segment_category', 'General')}-Segments")
                
                if source.get('is_snapshot'):
                    tags.extend(['Historical-Snapshot', 'FACT-Dataset', 'Monthly-Log', 'First-Thursday'])
                else:
                    tags.extend(['Current-View', 'DIMENSION-Dataset', 'Daily-Refresh'])
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': tags,
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
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created: {source['schema_id']}")
                success_count += 1
                
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Amazon Audience Segments Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Summary
    print("\n📊 Data Source Overview:")
    print("   • 3 Regions: AMER, APAC, EU")
    print("   • 2 Categories per region: In-Market, Lifestyle")
    print("   • 2 Views: Current (DIMENSION) and Historical Snapshot (FACT)")
    print("   • 1 Metadata table for segment details")
    print(f"   • Total: {len(audience_segments_sources)} tables")
    
    print("\n⚠️  CRITICAL BEST PRACTICES:")
    print("   ❌ NEVER query multiple regions in single query")
    print("   ❌ NEVER query multiple category tables in single query")
    print("   ✅ ALWAYS filter by segment_marketplace_id")
    print("   ✅ ALWAYS filter by segment_id when possible")
    print("   ✅ JOIN metadata using BOTH segment_id AND segment_marketplace_id")
    
    print("\n📅 Snapshot Details:")
    print("   • Logged: First Thursday of each month")
    print("   • Type: FACT dataset (historical)")
    print("   • Use: Limit to 1 snapshot per query")
    print("   • Include: First Thursday in date range")
    
    print("\n🎯 Key Fields:")
    print("   • user_id: Customer identifier (VERY_HIGH threshold)")
    print("   • segment_id: Segment code (unique per marketplace)")
    print("   • segment_marketplace_id: Marketplace context")
    print("   • segment_name: Human-readable segment name")
    print("   • snapshot_datetime: For historical snapshots")
    
    print("\n📈 Use Cases:")
    print("   • Audience targeting and expansion")
    print("   • Segment overlap analysis")
    print("   • Market opportunity sizing")
    print("   • Customer profiling")
    print("   • Trend analysis (with snapshots)")

if __name__ == "__main__":
    update_audience_segments()