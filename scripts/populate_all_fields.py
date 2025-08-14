#!/usr/bin/env python3
"""
Populate all field data for AMC data sources
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import Dict, List, Any

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

def insert_fields_for_data_source(schema_id: str, fields: List[Dict[str, Any]]):
    """Insert fields for a data source"""
    
    # Get the data source
    ds_result = supabase.table('amc_data_sources').select('id').eq('schema_id', schema_id).execute()
    
    if not ds_result.data:
        print(f"  ⚠️  Data source '{schema_id}' not found")
        return False
    
    data_source_id = ds_result.data[0]['id']
    
    # Delete existing fields
    supabase.table('amc_schema_fields').delete().eq('data_source_id', data_source_id).execute()
    
    # Insert new fields
    for idx, field in enumerate(fields):
        field_data = {
            'id': str(uuid.uuid4()),
            'data_source_id': data_source_id,
            'field_name': field.get('name', ''),
            'data_type': field.get('data_type', 'STRING'),
            'dimension_or_metric': field.get('field_type', 'Dimension'),
            'description': field.get('description', ''),
            'aggregation_threshold': field.get('aggregation_threshold'),
            'field_order': idx,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table('amc_schema_fields').insert(field_data).execute()
    
    print(f"  ✅ Inserted {len(fields)} fields for '{schema_id}'")
    return True

def main():
    """Main function to populate all fields"""
    
    print("\n=== Populating All AMC Data Source Fields ===\n")
    
    # Import field definitions from all update scripts
    from scripts.update_dsp_impressions_sources import dsp_impressions_fields
    from scripts.update_conversions_sources import conversions_fields
    from scripts.update_dsp_clicks_sources import dsp_clicks_fields
    from scripts.update_dsp_views_sources import dsp_views_fields
    from scripts.update_dsp_video_sources import dsp_video_additional_fields
    from scripts.update_dsp_segments_sources import dsp_segments_additional_fields
    from scripts.update_retail_purchases_sources import retail_purchases_fields
    from scripts.update_your_garage_sources import your_garage_fields
    from scripts.update_experian_vehicle_sources import experian_vehicle_fields
    from scripts.update_ncs_cpg_insights_sources import ncs_cpg_fields
    from scripts.update_conversions_relevance_sources import conversions_relevance_fields
    
    # Map schema_ids to their field definitions
    field_mappings = {
        # DSP Impressions
        'dsp_impressions': dsp_impressions_fields,
        'dsp_impressions_for_advertisers': dsp_impressions_fields,
        'dsp_impressions_for_audiences': dsp_impressions_fields,
        'dsp_impressions_for_optimization': dsp_impressions_fields,
        'dsp_impressions_for_path_to_conversion': dsp_impressions_fields,
        
        # Conversions
        'conversions': conversions_fields,
        'conversions_for_advertisers': conversions_fields,
        'conversions_for_audiences': conversions_fields,
        'conversions_for_optimization': conversions_fields,
        'conversions_for_path_to_conversion': conversions_fields,
        'conversions_all': conversions_fields,
        'conversions_relevance': conversions_relevance_fields,
        
        # DSP Clicks
        'dsp_clicks': dsp_clicks_fields,
        'dsp_clicks_for_audiences': dsp_clicks_fields,
        
        # DSP Views
        'dsp_views': dsp_views_fields,
        
        # DSP Video
        'dsp_video_events_feed': dsp_video_additional_fields,
        'dsp_video_events_feed_for_audiences': dsp_video_additional_fields,
        
        # DSP Segments
        'dsp_impressions_by_matched_segments': dsp_segments_additional_fields,
        'dsp_impressions_by_matched_segments_for_audiences': dsp_segments_additional_fields,
        'dsp_impressions_by_user_segments': dsp_segments_additional_fields,
        'dsp_impressions_by_user_segments_for_audiences': dsp_segments_additional_fields,
        
        # DSP Views
        'dsp_views': dsp_views_fields,
        
        # Retail
        'retail_purchases': retail_purchases_fields,
        'retail_purchases_aggregated': retail_purchases_fields,
        
        # Vehicle
        'your_garage': your_garage_fields,
        'your_garage_audiences': your_garage_fields,
        'experian_vehicle': experian_vehicle_fields,
        
        # Offline Sales
        'ncs_cpg_insights': ncs_cpg_fields,
    }
    
    # Process each mapping
    success_count = 0
    error_count = 0
    
    for schema_id, fields in field_mappings.items():
        try:
            if insert_fields_for_data_source(schema_id, fields):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"  ❌ Error processing '{schema_id}': {e}")
            error_count += 1
    
    print(f"\n=== Summary ===")
    print(f"✅ Successfully populated: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"Total processed: {success_count + error_count}")

if __name__ == "__main__":
    main()