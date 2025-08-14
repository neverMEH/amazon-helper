#!/usr/bin/env python3
"""
Update Conversions data sources in AMC
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

# Define the Conversions data sources
conversions_sources = [
    {
        "schema_id": "conversions",
        "name": "Conversions",
        "description": "Analytics table containing AMC conversion events. Includes ad-attributed conversions for ASINs tracked to Amazon DSP or sponsored ads campaigns and pixel conversions. Conversions are ad-attributed if a user was served a traffic event within the 28-day period prior to the conversion event.",
        "category": "Conversions",
        "table_type": "Analytics"
    },
    {
        "schema_id": "conversions_for_audiences",
        "name": "Conversions for Audiences",
        "description": "Audience table containing AMC conversion events. Includes ad-attributed conversions for ASINs tracked to Amazon DSP or sponsored ads campaigns and pixel conversions. Conversions are ad-attributed if a user was served a traffic event within the 28-day period prior to the conversion event.",
        "category": "Conversions",
        "table_type": "Audience"
    }
]

# Define the fields for Conversions tables
conversions_fields = [
    # Metrics
    {
        "name": "combined_sales",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "Sum of total_product_sales+off_Amazon_product_sales",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "conversions",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "The count of conversion events. This field always contains a value of 1, allowing you to calculate conversion totals for the records selected in your query. Conversion events can include on-Amazon activities like purchases and detail page views, as well as off-Amazon events measured through Events Manager. Possible values for this field are: '1' (the record represents a conversion event).",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "off_amazon_conversion_value",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "Non monetary \"value\" of conversion for non-purchase conversions",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "off_amazon_product_sales",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "\"Value\" of purchase conversions provided via Conversion Builder",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "total_product_sales",
        "data_type": "DECIMAL",
        "field_type": "Metric",
        "description": "Product sales (in local currency) for on-Amazon purchase events. Example value: '12.99'.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "total_units_sold",
        "data_type": "LONG",
        "field_type": "Metric",
        "description": "Units sold for on-Amazon purchase events. Example value: '3'.",
        "aggregation_threshold": "NONE"
    },
    
    # Dimensions
    {
        "name": "conversion_event_name",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "The advertiser's name of the conversion definition.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "conversion_event_source_name",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "The source of the advertiser-provided conversion data.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "conversion_id",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Unique identifier of the conversion event. In the conversions table, each row has a unique conversion_id value.",
        "aggregation_threshold": "VERY_HIGH"
    },
    {
        "name": "event_category",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "High-level category of the conversion event. For ASIN conversions, this categorizes whether the event was a purchase or website browsing interaction. Website events include activities like detail page views, add to wishlist actions, and first Subscribe and Save orders. For conversions measured through Events Manager, this field is always 'off-Amazon'. Possible values include: 'purchase', 'website', and 'off-Amazon'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_date_utc",
        "data_type": "DATE",
        "field_type": "Dimension",
        "description": "Date of the conversion event in Coordinated Universal Time (UTC) timezone. Example value: '2025-01-01'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_day_utc",
        "data_type": "INTEGER",
        "field_type": "Dimension",
        "description": "Day of month when the conversion event occurred in Coordinated Universal Time (UTC). Example value: '1'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_dt_hour_utc",
        "data_type": "TIMESTAMP",
        "field_type": "Dimension",
        "description": "Timestamp of the conversion event in Coordinated Universal Time (UTC) truncated to hour. Example value: '2025-01-01T00:00:00.000Z'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_dt_utc",
        "data_type": "TIMESTAMP",
        "field_type": "Dimension",
        "description": "Timestamp of the conversion event in Coordinated Universal Time (UTC). Example value: '2025-01-01T00:00:00.000Z'.",
        "aggregation_threshold": "MEDIUM"
    },
    {
        "name": "event_hour_utc",
        "data_type": "INTEGER",
        "field_type": "Dimension",
        "description": "Hour of the day (0-23) when the conversion event occurred in Coordinated Universal Time (UTC) timezone. Example value: '0'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_subtype",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Subtype of the conversion event. This field provides additional detail about the subtype of conversion event that occurred, such as whether it represents viewing a product's detail page on Amazon.com or completing a purchase on an advertiser's website. For on-Amazon conversion events, this field contains human-readable values, while off-Amazon events measured via Events Manager are represented by numeric values. Possible values include: 'detailPageView', 'shoppingCart', 'order', 'searchConversion', 'wishList', 'babyRegistry', 'weddingRegistry', 'customerReview' for on-Amazon events, and numeric values like '134', '140', '141' for off-Amazon events.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_type",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Type of conversion event. Conversion events in AMC can include both on-Amazon events (like purchases and detail page views) and off-Amazon events (like website visits and app installs measured through Events Manager). This field will always have a value of 'CONVERSION'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_type_class",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Classification of conversion events based on customer behavior. This field categorizes conversion events into consideration events (like detail page views) versus actual conversion events (like purchases). Possible values include: 'consideration', 'conversion', and NULL.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "event_type_description",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Human-readable description of the conversion event type. Conversion events can occur on Amazon (like product purchases or detail page views) or off Amazon (like brand site page views or in-store transactions measured via Events Manager). Example values: 'Product purchased', 'Add to Shopping Cart', 'Product detail page viewed'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "marketplace_id",
        "data_type": "INTEGER",
        "field_type": "Dimension",
        "description": "ID of the marketplace where the conversion event occurred. A marketplace represents a regional Amazon storefront where customers can make purchases (for example, Amazon.com, Amazon.co.uk).",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "marketplace_name",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Name of the marketplace where the conversion event occurred. A marketplace can be an online shopping site (like Amazon.com) or a physical retail location (like Amazon Fresh stores). This field helps distinguish between conversions that happen on different Amazon online marketplaces versus those that occur in Amazon's physical retail locations. Example values include: 'AMAZON.COM', 'AMAZON.CO.UK', 'WHOLE_FOODS_MARKET_US', and 'AMAZON_FRESH_STORES_US'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "new_to_brand",
        "data_type": "BOOLEAN",
        "field_type": "Dimension",
        "description": "Boolean value indicating whether the customer associated with a purchase event is new-to-brand. A customer is considered new-to-brand if they have not purchased from the brand in the previous 12 months. This field is only applicable for purchase events. Possible values for this field are: 'true', 'false'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "no_3p_trackers",
        "data_type": "BOOLEAN",
        "field_type": "Dimension",
        "description": "Boolean value indicating whether the event can be used for audience creation that is third-party tracking enabled (i.e. whether you can serve creative with third-party tracking when running media against the audience). Third-party tracking refers to measurement tags and pixels from external vendors that can be used to measure ad performance. Possible values for this field are: 'true', 'false'.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "purchase_currency",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "ISO currency code of the purchase. Currency codes follow the ISO 4217 standard for representing currencies (e.g., USD for US Dollar). Example value: 'USD'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "purchase_unit_price",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "The unit price of the product sold for on-Amazon purchase events, in local currency. This field represents the price per individual unit, not the total purchase price which may include multiple units. Example value: '29.99'.",
        "aggregation_threshold": "NONE"
    },
    {
        "name": "tracked_asin",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "The ASIN of the conversion event. An ASIN (Amazon Standard Identification Number) is a unique 10-character identifier assigned to products sold on Amazon. ASINs that appear in this field were either directly promoted by the campaign or are products from the same brand as the promoted ASINs. This field will only be for on-Amazon purchases (event_category = 'purchase'); for other conversion types, this field will be NULL. When this field is populated, tracked_item will have the same value. Example value: 'B01234ABCD'.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "tracked_item",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Identifier for the conversion event item. The value in this field depends on the subtype of the conversion event. For ASIN-related conversions on Amazon such as purchases, detail page views, add to cart events, this field will contain the ASIN of the product. For branded search conversions on Amazon, this field will contain the ad-attributed branded search keyword. For off-Amazon conversions, this field will contain the ID of the conversion definition. Note that when tracked_asin is populated, the same value will appear in tracked_item.",
        "aggregation_threshold": "LOW"
    },
    {
        "name": "user_id",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Pseudonymous identifier that connects user activity across different events. The field can contain ad user IDs (representing Amazon accounts), device IDs, or browser IDs. NULL values appear when Amazon Ads is unable to resolve an identifier for an event. The field has a VERY_HIGH aggregation threshold, meaning it cannot be included in final SELECT statements but can be used within Common Table Expressions (CTEs) for aggregation purposes like COUNT(DISTINCT user_id).",
        "aggregation_threshold": "VERY_HIGH"
    },
    {
        "name": "user_id_type",
        "data_type": "STRING",
        "field_type": "Dimension",
        "description": "Type of user ID value. AMC includes different types of user ID values, depending on whether the value represents a resolved Amazon account, a device, or a browser cookie. If Amazon Ads is unable to determine or provide an ID of any kind for a conversion event, the 'user_id' and 'user_id_type' values for that record will be NULL. Possible values include: 'adUserId', 'sisDeviceId', 'adBrowserId', and NULL.",
        "aggregation_threshold": "LOW"
    }
]

def update_conversions():
    """Update Conversions data sources"""
    
    print("\n=== Updating Conversions Data Sources ===\n")
    
    # Update/Insert data sources
    for source in conversions_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('amc_data_sources').update({
                    'name': source['name'],
                    'description': source['description'],
                    'category': source['category'],
                    'tags': [source.get('table_type'), '28-Day-Attribution'] if source.get('table_type') else ['28-Day-Attribution'],
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
                    'tags': [source.get('table_type'), '28-Day-Attribution'] if source.get('table_type') else ['28-Day-Attribution'],
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).execute()
                print(f"✅ Created data source: {source['schema_id']}")
                data_source_id = result.data[0]['id']
            
            print(f"  Documented {len(conversions_fields)} fields for {source['schema_id']}")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            continue
    
    print("\n=== Conversions Update Complete ===")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['conversions', 'conversions_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
    
    print("\n📊 Conversion Types Supported:")
    print("   ✅ On-Amazon conversions:")
    print("      - Product purchases")
    print("      - Detail page views")
    print("      - Add to cart")
    print("      - Wishlist/Registry adds")
    print("      - Customer reviews")
    print("   ✅ Off-Amazon conversions (via Events Manager):")
    print("      - Website visits")
    print("      - App installs")
    print("      - Custom conversion events")
    print("\n📈 Attribution: 28-day lookback window from traffic event to conversion")

if __name__ == "__main__":
    update_conversions()