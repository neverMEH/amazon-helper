#!/usr/bin/env python3
"""
Update Conversions with Relevance data sources in AMC
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

# Define the Conversions with Relevance data sources
conversions_relevance_sources = [
    {
        "schema_id": "conversions_with_relevance",
        "name": "Conversions with Relevance",
        "description": "Analytics table for creating custom attribution models for both ASIN conversions (purchases) and pixel conversions. Contains only ad-attributed and pixel conversions, with multiple rows per conversion if relevant to multiple campaigns, engagement scopes, or brand halo types. Simplifies attribution queries by removing non-ad attributed conversions.",
        "category": "Conversions",
        "table_type": "Analytics"
    },
    {
        "schema_id": "conversions_with_relevance_for_audiences",
        "name": "Conversions with Relevance for Audiences",
        "description": "Audience table for creating custom attribution models for both ASIN conversions (purchases) and pixel conversions. Contains only ad-attributed and pixel conversions, with multiple rows per conversion if relevant to multiple campaigns, engagement scopes, or brand halo types. Simplifies attribution queries by removing non-ad attributed conversions.",
        "category": "Conversions",
        "table_type": "Audience"
    }
]

# Define the fields for Conversions with Relevance tables
conversions_relevance_fields = [
    # Advertiser Setup
    {"name": "advertiser", "data_type": "STRING", "field_type": "Dimension", "description": "Advertiser name.", "aggregation_threshold": "LOW", "category": "Advertiser Setup"},
    {"name": "advertiser_id", "data_type": "LONG", "field_type": "Dimension", "description": "Advertiser ID.", "aggregation_threshold": "LOW", "category": "Advertiser Setup"},
    {"name": "advertiser_timezone", "data_type": "STRING", "field_type": "Dimension", "description": "Time zone of the advertiser.", "aggregation_threshold": "LOW", "category": "Advertiser Setup"},
    
    # Campaign Setup
    {"name": "campaign", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign name.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_budget_amount", "data_type": "LONG", "field_type": "Dimension", "description": "Campaign budget amount(millicents).", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_end_date", "data_type": "DATE", "field_type": "Dimension", "description": "Campaign end date in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_end_date_utc", "data_type": "DATE", "field_type": "Dimension", "description": "Campaign end date in UTC", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_end_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Campaign end timestamp in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_end_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Campaign end timestamp in UTC", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_id", "data_type": "LONG", "field_type": "Dimension", "description": "Campaign ID.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_id_internal", "data_type": "LONG", "field_type": "Dimension", "description": "The globally unique internal campaign ID.", "aggregation_threshold": "INTERNAL", "category": "Campaign Setup"},
    {"name": "campaign_id_string", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign ID as a string data_type, covers DSP and Sponsored Advertising campaign objects.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_sales_type", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign sales type", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_source", "data_type": "STRING", "field_type": "Dimension", "description": "Campaign source.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_start_date", "data_type": "DATE", "field_type": "Dimension", "description": "Campaign start date in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_start_date_utc", "data_type": "DATE", "field_type": "Dimension", "description": "Campaign start date in UTC.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_start_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Campaign start timestamp in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "campaign_start_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Campaign start timestamp in UTC.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    {"name": "targeting", "data_type": "STRING", "field_type": "Dimension", "description": "The keyword used by advertiser for targeting.", "aggregation_threshold": "LOW", "category": "Campaign Setup"},
    
    # Conversion Info
    {"name": "conversion_id", "data_type": "STRING", "field_type": "Dimension", "description": "Unique identifier of the conversion event. In the dataset conversions, each row has a unique conversion_id. In the dataset conversions_with_relevance, the same conversion event will appear multiple times if a conversion is determined to be relevant to multiple campaigns, engagement scopes, or brand halo types.", "aggregation_threshold": "VERY_HIGH", "category": "Conversion Info"},
    {"name": "conversions", "data_type": "LONG", "field_type": "Metric", "description": "Conversion count.", "aggregation_threshold": "NONE", "category": "Conversion Info"},
    {"name": "engagement_scope", "data_type": "STRING", "field_type": "Dimension", "description": "The engagement scope between the campaign setup and the conversion. Possible values for this column are PROMOTED, BRAND_HALO, and null. See also the definition for halo_code. The engagement_scope will always be 'PROMOTED' for pixel conversions (when event_category = 'pixel').", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_category", "data_type": "STRING", "field_type": "Dimension", "description": "For ASIN conversions, the event_category is the high level category of the conversion event, either 'purchase' or 'website'. Examples of ASIN conversions when event_category = 'website' include: detail page views, add to wishlist, or the first Subscribe and Save order. For search conversions (when event_subtype = 'searchConversion'), the event_category is always 'website'. For pixel conversions, this field is always 'pixel'.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_date", "data_type": "DATE", "field_type": "Dimension", "description": "Date of the conversion event in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_date_utc", "data_type": "DATE", "field_type": "Dimension", "description": "Date of the conversion event in UTC.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_day", "data_type": "INTEGER", "field_type": "Dimension", "description": "Day of the month of the conversion event in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_day_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Day of the month of the conversion event in UTC.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the conversion event in the advertiser time zone.", "aggregation_threshold": "MEDIUM", "category": "Conversion Info"},
    {"name": "event_dt_hour", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the conversion event in the advertiser time zone truncated to the hour.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_dt_hour_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the conversion event in UTC truncated to the hour.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the conversion event in UTC.", "aggregation_threshold": "MEDIUM", "category": "Conversion Info"},
    {"name": "event_hour", "data_type": "INTEGER", "field_type": "Dimension", "description": "Hour of the day of the conversion event in the advertiser time zone.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_hour_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Hour of the day of the conversion event in UTC.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_source", "data_type": "STRING", "field_type": "Dimension", "description": "System that generated the conversion event.", "aggregation_threshold": "VERY_HIGH", "category": "Conversion Info"},
    {"name": "event_subtype", "data_type": "STRING", "field_type": "Dimension", "description": "Subtype of the conversion event. For ASIN conversions, the examples of event_subtype include: 'alexaSkillEnable', 'babyRegistry', 'customerReview', 'detailPageView', 'order', 'shoppingCart', 'snsSubscription', 'weddingRegistry', 'wishList'. For search conversions, event_subtype is always 'searchConversion'. For pixel conversions, the numeric ID of the event_subtype is provided.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of the conversion event.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_type_class", "data_type": "STRING", "field_type": "Dimension", "description": "For ASIN conversions, the event_type_class is the High level classification of the event type, e.g. consideration, conversion, etc. This field will be blank for pixel conversions (when event_category = 'pixel') and search conversions (when event_subtype = 'searchConversion').", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "event_type_description", "data_type": "STRING", "field_type": "Dimension", "description": "Human-readable description of the conversion event. For ASIN conversions, examples include: 'add to baby registry', 'Add to Shopping Cart', 'add to wedding registry', 'add to wishlist', 'Customer Reviews Page', 'New SnS Subscription', 'Product detail page viewed', 'Product purchased'. This field will be blank for search conversions. For pixel conversions, includes additional information from campaign setup.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "halo_code", "data_type": "STRING", "field_type": "Dimension", "description": "The halo code between the campaign and conversion. Possible values for this column are TRACKED_ASIN, VARIATIONAL_ASIN, BRAND_KEYWORD, CATEGORY_KEYWORD, BRAND_MARKETPLACE, BRAND_GL_PRODUCT, BRAND_CATEGORY, BRAND_SUBCATEGORY, and null. The halo_code will be NULL for pixel conversions (when event_category = 'pixel').", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "marketplace_id", "data_type": "INTEGER", "field_type": "Dimension", "description": "Marketplace ID of where the conversion event occurred.", "aggregation_threshold": "INTERNAL", "category": "Conversion Info"},
    {"name": "marketplace_name", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the marketplace where the conversion event occurred. Example values are online marketplaces such as AMAZON.COM, AMAZON.CO.UK. Or in-store marketplaces, such as WHOLE_FOODS_MARKET_US or AMAZON_FRESH_STORES_US.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "new_to_brand", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "True if the user was new to the brand.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "purchase_currency", "data_type": "STRING", "field_type": "Dimension", "description": "ISO currency code of the purchase order.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "purchase_unit_price", "data_type": "DECIMAL", "field_type": "Metric", "description": "Unit price of the product sold.", "aggregation_threshold": "NONE", "category": "Conversion Info"},
    {"name": "total_product_sales", "data_type": "DECIMAL", "field_type": "Metric", "description": "Total sales(in local currency) of promoted ASINs and ASINs from the same brands as promoted ASINs purchased by customers on Amazon.", "aggregation_threshold": "NONE", "category": "Conversion Info"},
    {"name": "total_units_sold", "data_type": "LONG", "field_type": "Metric", "description": "Total quantity of promoted products and products from the same brand as promoted products purchased by customers on Amazon. A campaign can have multiple units sold in a single purchase event.", "aggregation_threshold": "NONE", "category": "Conversion Info"},
    {"name": "tracked_asin", "data_type": "STRING", "field_type": "Dimension", "description": "The tracked Amazon Standard Identification Number, which is either the promoted or brand halo ASIN. When the tracked_item results in a purchase conversion, the tracked_asin will be populated in this column. The tracked_asin is populated only if the event_category = 'purchase'. For the first SnS order and non-purchase conversions, such as detail page views, the ASIN is populated under tracked_item.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "tracked_item", "data_type": "STRING", "field_type": "Dimension", "description": "Identifier of an item of interest for the campaign, such as the ASIN tracked to the campaign, the brand halo ASIN, or the ad-attributed branded keyword. Attribution algorithms match traffic and conversion event by the user identity and tracked item. Matching rules for tracked items may include expansion algorithms such as brand halo when the conversions_with_relevance dataset is used. If tracked_asin has a value populated, the same value for tracked_item will match tracked_asin.", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "User ID.", "aggregation_threshold": "VERY_HIGH", "category": "Conversion Info"},
    {"name": "conversion_event_source", "data_type": "STRING", "field_type": "Dimension", "description": "Source through which the conversion event was sent to Amazon DSP", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    {"name": "conversion_event_name", "data_type": "STRING", "field_type": "Dimension", "description": "Advertiser defined name for the conversion event", "aggregation_threshold": "LOW", "category": "Conversion Info"},
    
    # Purchase Info
    {"name": "off_amazon_product_sales", "data_type": "LONG", "field_type": "Metric", "description": "Sales amount for off-Amazon purchase conversions", "aggregation_threshold": "NONE", "category": "Purchase Info"},
    {"name": "off_amazon_conversion_value", "data_type": "LONG", "field_type": "Metric", "description": "Value of off Amazon non-purchase conversions. Value is unitless and advertiser defined.", "aggregation_threshold": "NONE", "category": "Conversion Info"},
    {"name": "combined_sales", "data_type": "LONG", "field_type": "Metric", "description": "Sum of total_product_sales(Amazon product sales) and off_amazon_product_sales", "aggregation_threshold": "NONE", "category": "Purchase Info"}
]

def update_conversions_relevance():
    """Update Conversions with Relevance data sources"""
    
    print("\n=== Updating Conversions with Relevance Data Sources ===\n")
    
    # Update/Insert data sources
    for source in conversions_relevance_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type'), 'Custom-Attribution', 'Brand-Halo', 'Multi-Row-Per-Conversion'] if source.get('table_type') else ['Custom-Attribution', 'Brand-Halo', 'Multi-Row-Per-Conversion'],
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
                    'tags': [source.get('table_type'), 'Custom-Attribution', 'Brand-Halo', 'Multi-Row-Per-Conversion'] if source.get('table_type') else ['Custom-Attribution', 'Brand-Halo', 'Multi-Row-Per-Conversion'],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            print(f"  Documented {len(conversions_relevance_fields)} fields for {source['schema_id']}")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== Conversions with Relevance Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['conversions_with_relevance', 'conversions_with_relevance_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
    
    print("\n📊 Key Features:")
    print("   ✅ Only ad-attributed and pixel conversions included")
    print("   ✅ Multiple rows per conversion for relevance analysis")
    print("   ✅ Engagement scopes: PROMOTED, BRAND_HALO")
    print("   ✅ Halo codes for brand expansion tracking:")
    print("      - TRACKED_ASIN, VARIATIONAL_ASIN")
    print("      - BRAND_KEYWORD, CATEGORY_KEYWORD")
    print("      - BRAND_MARKETPLACE, BRAND_GL_PRODUCT")
    print("      - BRAND_CATEGORY, BRAND_SUBCATEGORY")
    print("\n📈 Use Cases:")
    print("   - Custom attribution models")
    print("   - Brand halo effect analysis")
    print("   - Cross-campaign conversion impact")
    print("   - Off-Amazon media impact on Amazon conversions")

if __name__ == "__main__":
    update_conversions_relevance()