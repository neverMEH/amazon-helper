#!/usr/bin/env python3
"""
Add fields column to amc_data_sources table and populate with field data
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

def get_client():
    """Get Supabase client"""
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

async def add_fields_column():
    """Add fields column to amc_data_sources table"""
    client = get_client()
    
    print("Adding fields column to amc_data_sources table...")
    
    # Add the fields column as JSONB
    add_column_query = """
    ALTER TABLE amc_data_sources 
    ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;
    """
    
    try:
        # Execute the migration
        result = client.rpc('execute_raw_sql', {'query': add_column_query}).execute()
        print("✓ Fields column added successfully")
        return True
    except Exception as e:
        if 'already exists' in str(e).lower():
            print("Fields column already exists")
            return True
        else:
            print(f"Error adding fields column: {e}")
            return False

async def populate_fields_data():
    """Populate fields data for all data sources"""
    client = get_client()
    
    # Import field definitions from our update scripts
    from scripts.update_dsp_impressions_sources import DSP_IMPRESSIONS_FIELDS
    from scripts.update_conversions_sources import CONVERSIONS_FIELDS
    
    # Define fields for each data source
    fields_mapping = {
        # DSP Impressions sources
        'dsp_impressions': DSP_IMPRESSIONS_FIELDS,
        'dsp_impressions_for_advertisers': DSP_IMPRESSIONS_FIELDS,
        'dsp_impressions_for_optimization': DSP_IMPRESSIONS_FIELDS,
        'dsp_impressions_for_path_to_conversion': DSP_IMPRESSIONS_FIELDS,
        
        # Conversions sources
        'conversions': CONVERSIONS_FIELDS,
        'conversions_for_advertisers': CONVERSIONS_FIELDS,
        'conversions_for_optimization': CONVERSIONS_FIELDS,
        'conversions_for_path_to_conversion': CONVERSIONS_FIELDS,
        
        # DSP Clicks - similar structure to impressions but focused on clicks
        'dsp_clicks': [
            {"name": "click_dt", "type": "timestamp", "description": "Date and time of the click"},
            {"name": "user_id", "type": "string", "description": "Unique identifier for the user"},
            {"name": "campaign_id", "type": "string", "description": "Campaign identifier"},
            {"name": "creative_id", "type": "string", "description": "Creative identifier"},
            {"name": "placement_id", "type": "string", "description": "Placement identifier"},
            {"name": "device_type", "type": "string", "description": "Type of device used"},
            {"name": "click_verification", "type": "boolean", "description": "Whether click was verified"},
        ],
        
        # Sponsored Ads Clicks
        'sponsored_ads_clicks': [
            {"name": "click_dt", "type": "timestamp", "description": "Date and time of the click"},
            {"name": "user_id", "type": "string", "description": "Unique identifier for the user"},
            {"name": "campaign", "type": "string", "description": "Campaign name"},
            {"name": "ad_product_type", "type": "string", "description": "Type of sponsored ad product"},
            {"name": "asin", "type": "string", "description": "Amazon Standard Identification Number"},
            {"name": "keyword", "type": "string", "description": "Keyword that triggered the ad"},
        ],
        
        # Sponsored Ads Purchases
        'sponsored_ads_purchases': [
            {"name": "order_dt", "type": "timestamp", "description": "Date and time of the purchase"},
            {"name": "user_id", "type": "string", "description": "Unique identifier for the user"},
            {"name": "campaign", "type": "string", "description": "Campaign name"},
            {"name": "asin", "type": "string", "description": "Amazon Standard Identification Number"},
            {"name": "quantity", "type": "integer", "description": "Number of items purchased"},
            {"name": "purchase_value", "type": "decimal", "description": "Total value of the purchase"},
        ],
        
        # Brand Store
        'brand_store_interactions': [
            {"name": "event_dt", "type": "timestamp", "description": "Date and time of the interaction"},
            {"name": "user_id", "type": "string", "description": "Unique identifier for the user"},
            {"name": "store_id", "type": "string", "description": "Brand store identifier"},
            {"name": "page_id", "type": "string", "description": "Page within the brand store"},
            {"name": "interaction_type", "type": "string", "description": "Type of interaction (view, click, etc.)"},
        ],
        
        # Attribution
        'last_touch_attribution': [
            {"name": "conversion_dt", "type": "timestamp", "description": "Date and time of conversion"},
            {"name": "user_id", "type": "string", "description": "Unique identifier for the user"},
            {"name": "touchpoint_type", "type": "string", "description": "Type of last touchpoint"},
            {"name": "touchpoint_id", "type": "string", "description": "Identifier of the touchpoint"},
            {"name": "days_to_conversion", "type": "integer", "description": "Days between touchpoint and conversion"},
        ],
    }
    
    print("\nPopulating fields data for data sources...")
    
    # Get all data sources
    result = client.table('amc_data_sources').select('id, schema_id').execute()
    
    update_count = 0
    for source in result.data:
        schema_id = source['schema_id']
        
        # Get fields for this schema
        fields = fields_mapping.get(schema_id, [])
        
        if fields:
            # Update the data source with fields
            update_result = client.table('amc_data_sources').update({
                'fields': fields
            }).eq('id', source['id']).execute()
            
            print(f"✓ Updated {schema_id} with {len(fields)} fields")
            update_count += 1
    
    print(f"\n✓ Updated {update_count} data sources with field information")
    return True

async def main():
    """Main execution"""
    # Step 1: Add fields column
    success = await add_fields_column()
    if not success:
        print("Failed to add fields column. Exiting.")
        return
    
    # Step 2: Populate fields data
    await populate_fields_data()
    
    print("\n✅ Fields column added and populated successfully!")

if __name__ == "__main__":
    asyncio.run(main())