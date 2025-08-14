#!/usr/bin/env python3
"""
Update DSP Impressions by Segments data sources in AMC
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

# Define the DSP Impressions by Segments data sources
dsp_segments_sources = [
    {
        "schema_id": "dsp_impressions_by_matched_segments",
        "name": "Amazon DSP Impressions by Matched Segments",
        "description": "Analytics table with the same structure as dsp_impressions but provides segment level information for segments that were both targeted by the ad AND included the user at impression time. Each impression appears multiple times if multiple segments matched. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Analytics"
    },
    {
        "schema_id": "dsp_impressions_by_matched_segments_for_audiences",
        "name": "Amazon DSP Impressions by Matched Segments for Audiences",
        "description": "Audience table with the same structure as dsp_impressions but provides segment level information for segments that were both targeted by the ad AND included the user at impression time. Each impression appears multiple times if multiple segments matched. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Audience"
    },
    {
        "schema_id": "dsp_impressions_by_user_segments",
        "name": "Amazon DSP Impressions by User Segments",
        "description": "Analytics table with the same structure as dsp_impressions but shows ALL segments that include the user, with behavior_segment_matched indicating if the segment was targeted by the ad. Each impression appears multiple times for each user segment. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Analytics"
    },
    {
        "schema_id": "dsp_impressions_by_user_segments_for_audiences",
        "name": "Amazon DSP Impressions by User Segments for Audiences",
        "description": "Audience table with the same structure as dsp_impressions but shows ALL segments that include the user, with behavior_segment_matched indicating if the segment was targeted by the ad. Each impression appears multiple times for each user segment. Note: Workflows using this table will time out when run over extended periods.",
        "category": "DSP",
        "table_type": "Audience"
    }
]

# Define the additional fields for DSP segments tables (in addition to all dsp_impressions fields)
dsp_segments_additional_fields = [
    {
        "name": "behavior_segment_description", 
        "data_type": "STRING", 
        "field_type": "Dimension", 
        "description": "Description of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. This field contains explanations of the characteristics that define each segment, such as shopping behaviors, demographics, and interests.", 
        "aggregation_threshold": "LOW"
    },
    {
        "name": "behavior_segment_id", 
        "data_type": "INTEGER", 
        "field_type": "Dimension", 
        "description": "Unique identifier for the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression. Example value: '123456'.", 
        "aggregation_threshold": "LOW"
    },
    {
        "name": "behavior_segment_matched", 
        "data_type": "LONG", 
        "field_type": "Metric", 
        "description": "Indicator of whether the behavior segment was targeted by the Amazon DSP line item and matched to the user at the time of impression. For matched_segments tables, this will always be '1'. For user_segments tables, '1' indicates targeted and matched, '0' indicates the user belonged to the segment but it wasn't targeted.", 
        "aggregation_threshold": "LOW"
    },
    {
        "name": "behavior_segment_name", 
        "data_type": "STRING", 
        "field_type": "Dimension", 
        "description": "Name of the audience segment, for segments both targeted by the Amazon DSP line item and matched to the user at the time of impression.", 
        "aggregation_threshold": "LOW"
    }
]

def update_dsp_segments():
    """Update DSP Impressions by Segments data sources"""
    
    print("\n=== Updating DSP Impressions by Segments Data Sources ===\n")
    
    # Update/Insert data sources
    for source in dsp_segments_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type'), 'Segment-Level', 'Performance-Warning'] if source.get('table_type') else ['Segment-Level', 'Performance-Warning'],
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
                    'tags': [source.get('table_type'), 'Segment-Level', 'Performance-Warning'] if source.get('table_type') else ['Segment-Level', 'Performance-Warning'],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            # Note: These tables have all fields from dsp_impressions PLUS the segment fields
            print(f"  Inherits all fields from dsp_impressions")
            print(f"  Plus {len(dsp_segments_additional_fields)} segment-specific fields")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== DSP Segments Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['dsp_impressions_by_matched_segments', 'dsp_impressions_by_matched_segments_for_audiences', 
                      'dsp_impressions_by_user_segments', 'dsp_impressions_by_user_segments_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
    
    print("\n⚠️  Important Note: These tables have performance limitations and will time out when run over extended periods.")
    print("   Each impression appears multiple times (once per segment), which significantly increases data volume.")

if __name__ == "__main__":
    update_dsp_segments()