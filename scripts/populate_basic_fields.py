#!/usr/bin/env python3
"""
Populate basic field data for AMC data sources
"""

import os
import sys
from pathlib import Path
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

# Import available field definitions
from scripts.update_dsp_impressions_sources import dsp_impressions_fields
from scripts.update_conversions_sources import conversions_fields
from scripts.update_dsp_clicks_sources import dsp_clicks_fields
from scripts.update_dsp_views_sources import dsp_views_fields
from scripts.update_retail_purchases_sources import retail_purchases_fields
from scripts.update_your_garage_sources import your_garage_fields
from scripts.update_experian_vehicle_sources import experian_vehicle_fields

def insert_fields_for_data_source(schema_id, fields):
    """Insert fields for a data source"""
    
    # Get the data source
    ds_result = supabase.table('amc_data_sources').select('id').eq('schema_id', schema_id).execute()
    
    if not ds_result.data:
        print(f"  ⚠️  Data source '{schema_id}' not found")
        return False
    
    data_source_id = ds_result.data[0]['id']
    
    # Check if fields already exist
    existing = supabase.table('amc_schema_fields').select('id').eq('data_source_id', data_source_id).limit(1).execute()
    if existing.data:
        print(f"  ℹ️  Fields already exist for '{schema_id}', skipping")
        return True
    
    # Insert fields
    inserted = 0
    for idx, field in enumerate(fields[:20]):  # Limit to first 20 fields for now
        try:
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
            inserted += 1
        except Exception as e:
            print(f"    Error inserting field {field.get('name')}: {e}")
    
    print(f"  ✅ Inserted {inserted} fields for '{schema_id}'")
    return True

def main():
    """Main function"""
    
    print("\n=== Populating Basic AMC Data Source Fields ===\n")
    
    # Simple mappings for the fields we know exist
    field_mappings = {
        # DSP Clicks
        'dsp_clicks': dsp_clicks_fields,
        'dsp_clicks_for_audiences': dsp_clicks_fields,
        
        # DSP Views
        'dsp_views': dsp_views_fields,
        
        # Conversions
        'conversions': conversions_fields,
        'conversions_for_advertisers': conversions_fields,
        'conversions_for_audiences': conversions_fields,
        'conversions_for_optimization': conversions_fields,
        'conversions_for_path_to_conversion': conversions_fields,
        'conversions_all': conversions_fields,
        
        # Retail
        'retail_purchases': retail_purchases_fields,
        'retail_purchases_aggregated': retail_purchases_fields,
        
        # Vehicle
        'your_garage': your_garage_fields,
        'your_garage_audiences': your_garage_fields,
        'experian_vehicle': experian_vehicle_fields,
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