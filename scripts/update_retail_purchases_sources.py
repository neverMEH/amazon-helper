#!/usr/bin/env python3
"""
Update Amazon Retail Purchases (ARP) data sources in AMC
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

# Define the Amazon Retail Purchases data sources
retail_purchases_sources = [
    {
        "schema_id": "amazon_retail_purchases",
        "name": "Amazon Retail Purchases",
        "description": "Analytics table containing long-term (up to 60 months) customer purchase behavior data. Covers entire purchase activity in Amazon store regardless of advertising. Available as AMC Paid Feature in US, CA, JP, AU, UK, FR, DE, IT, ES marketplaces. Includes 60-day free trial. Sourced from retail data pipeline matching Vendor/Seller Central reports.",
        "category": "Retail Purchases",
        "table_type": "Analytics"
    },
    {
        "schema_id": "amazon_retail_purchases_for_audiences",
        "name": "Amazon Retail Purchases for Audiences",
        "description": "Audience table containing long-term (up to 60 months) customer purchase behavior data. Covers entire purchase activity in Amazon store regardless of advertising. Available as AMC Paid Feature. Note: UK and EU data excluded from audience creation.",
        "category": "Retail Purchases",
        "table_type": "Audience"
    }
]

# Define the fields for Amazon Retail Purchases tables (27 fields)
retail_purchases_fields = [
    {"name": "asin", "data_type": "STRING", "field_type": "Dimension", "description": "Amazon Standard Identification Number. The item associated with the retail event.", "aggregation_threshold": "LOW"},
    {"name": "asin_brand", "data_type": "STRING", "field_type": "Dimension", "description": "ASIN item merchant brand name.", "aggregation_threshold": "LOW"},
    {"name": "asin_name", "data_type": "STRING", "field_type": "Dimension", "description": "ASIN item name.", "aggregation_threshold": "LOW"},
    {"name": "asin_parent", "data_type": "STRING", "field_type": "Dimension", "description": "The parent ASIN of this ASIN for the retail event.", "aggregation_threshold": "LOW"},
    {"name": "currency_code", "data_type": "STRING", "field_type": "Dimension", "description": "ISO currency code of the retail event.", "aggregation_threshold": "LOW"},
    {"name": "event_id", "data_type": "STRING", "field_type": "Dimension", "description": "Unique identifier of the retail event record. Each row has unique event_id with many-to-one relationship with purchase_id.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "is_business_flag", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Indicates whether the retail event is associated with Amazon Business program.", "aggregation_threshold": "LOW"},
    {"name": "is_gift_flag", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Indicates whether the retail event is associated with send an order as a gift.", "aggregation_threshold": "LOW"},
    {"name": "marketplace_id", "data_type": "INTEGER", "field_type": "Dimension", "description": "Marketplace ID of where the retail event occurred.", "aggregation_threshold": "INTERNAL"},
    {"name": "marketplace_name", "data_type": "STRING", "field_type": "Dimension", "description": "Name of the marketplace where the retail event occurred. Example: AMAZON.COM, AMAZON.CO.UK.", "aggregation_threshold": "LOW"},
    {"name": "no_3p_trackers", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Is this item not allowed to use 3P tracking.", "aggregation_threshold": "NONE"},
    {"name": "origin_session_id", "data_type": "STRING", "field_type": "Dimension", "description": "Describes the session when the retail item was added to cart.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "purchase_date_utc", "data_type": "DATE", "field_type": "Dimension", "description": "Date of the retail event in UTC.", "aggregation_threshold": "LOW"},
    {"name": "purchase_day_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Day of the month of the retail event in UTC.", "aggregation_threshold": "LOW"},
    {"name": "purchase_dt_hour_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the retail event in UTC truncated to the hour.", "aggregation_threshold": "LOW"},
    {"name": "purchase_dt_utc", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp of the retail event in UTC.", "aggregation_threshold": "MEDIUM"},
    {"name": "purchase_hour_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Hour of the day of the retail event in UTC.", "aggregation_threshold": "LOW"},
    {"name": "purchase_id", "data_type": "STRING", "field_type": "Dimension", "description": "Unique identifier of the retail purchase record. Has one-to-many relationship with event_id.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "purchase_month_utc", "data_type": "INTEGER", "field_type": "Dimension", "description": "Month of the conversion event in UTC.", "aggregation_threshold": "LOW"},
    {"name": "purchase_order_method", "data_type": "STRING", "field_type": "Dimension", "description": "How the shopper purchased the item. S = Shopping Cart, B = Buy Now, 1 = 1-Click Buy.", "aggregation_threshold": "LOW"},
    {"name": "purchase_order_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of retail order. Values include Prime and NON-PRIME.", "aggregation_threshold": "LOW"},
    {"name": "purchase_program_name", "data_type": "STRING", "field_type": "Dimension", "description": "Indicates the purchase program associated with the retail event.", "aggregation_threshold": "LOW"},
    {"name": "purchase_session_id", "data_type": "STRING", "field_type": "Dimension", "description": "Describes the session when the retail item was purchased.", "aggregation_threshold": "VERY_HIGH"},
    {"name": "purchase_units_sold", "data_type": "LONG", "field_type": "Metric", "description": "Total quantity of retail items associated with the retail event. A record can have multiple units sold of a single retail item.", "aggregation_threshold": "NONE"},
    {"name": "unit_price", "data_type": "DECIMAL", "field_type": "Metric", "description": "Per unit price of the product sold.", "aggregation_threshold": "NONE"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "User ID associated with the retail event (the user ID of the shopper that purchased the item).", "aggregation_threshold": "VERY_HIGH"},
    {"name": "user_id_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of user ID. The only value for this data set is adUserId.", "aggregation_threshold": "LOW"}
]

def update_retail_purchases():
    """Update Amazon Retail Purchases data sources"""
    
    print("\n=== Updating Amazon Retail Purchases (ARP) Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in retail_purchases_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'Long-Term-Data',
                '60-Months-History',
                'Retail-Pipeline',
                'Non-Advertising',
                'Free-Trial-Available'
            ]
            
            # Add marketplace restrictions for audience table
            if 'for_audiences' in source['schema_id']:
                tags.append('EU-UK-Excluded-Audiences')
            
            # Add data scope tags
            tags.extend([
                'Vendor-Central-Match',
                'Seller-Central-Match',
                'Prime-Orders',
                'Business-Orders',
                'Gift-Orders'
            ])
            
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
            
            print(f"  Documented {len(retail_purchases_fields)} fields")
            print(f"  💰 Marked as PAID FEATURE with 60-day free trial")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Amazon Retail Purchases Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['amazon_retail_purchases', 'amazon_retail_purchases_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags, is_paid_feature').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {', '.join(result.data[0].get('tags', [])[:5])}...")
            print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
    
    print("\n💎 PAID FEATURE DETAILS:")
    print("   💰 Subscription Required: Yes (after 60-day free trial)")
    print("   🆓 Free Trial: 60 days")
    print("   🌎 Available Marketplaces: US, CA, JP, AU, UK, FR, DE, IT, ES")
    print("   ⚠️  Audience Restriction: UK and EU data excluded from audience creation")
    
    print("\n📊 KEY DIFFERENTIATORS vs Conversions Datasets:")
    print("   ┌─────────────────────┬────────────────────────┬────────────────────────┐")
    print("   │ Aspect              │ ARP                    │ CONV                   │")
    print("   ├─────────────────────┼────────────────────────┼────────────────────────┤")
    print("   │ Historical Data     │ 60 months (5 years)    │ 13 months              │")
    print("   │ Conversion Types    │ Amazon purchases only  │ Various (purchase,     │")
    print("   │                     │                        │ consideration, pixel)  │")
    print("   │ Event Scope         │ ALL Amazon purchases   │ Ad-exposed only        │")
    print("   │ Data Source         │ Retail pipeline        │ Advertising pipeline   │")
    print("   │ Reporting Match     │ Vendor/Seller Central  │ Ads Console            │")
    print("   └─────────────────────┴────────────────────────┴────────────────────────┘")
    
    print("\n⚠️  CRITICAL BEST PRACTICES:")
    print("   ❌ NEVER join ARP directly with other AMC datasets without time filters")
    print("   ✅ ALWAYS account for 60-month vs 13-month data window differences")
    print("   ✅ VERIFY Vendor/Seller Central account associations in Ads Console")
    print("   ✅ CHECK Reports > Retail Analytics (Vendor) or Business Reports (Seller)")
    
    print("\n📈 Use Cases:")
    print("   • Long-term customer lifetime value (CLV) analysis")
    print("   • Historical purchase pattern identification")
    print("   • Customer segmentation based on purchase history")
    print("   • Brand loyalty and repeat purchase analysis")
    print("   • Market basket analysis across extended periods")
    print("   • Seasonal trend analysis (multi-year)")
    print("   • Customer journey mapping (5-year view)")
    print("   • Product adoption and lifecycle analysis")
    
    print("\n🎯 Key Fields:")
    print("   • purchase_id: Unique purchase transaction")
    print("   • event_id: Individual line items (many-to-one with purchase_id)")
    print("   • user_id: Shopper identifier (adUserId type)")
    print("   • asin/asin_parent: Product hierarchy")
    print("   • purchase_order_type: Prime vs Non-Prime")
    print("   • purchase_order_method: S (Cart), B (Buy Now), 1 (1-Click)")
    print("   • is_business_flag: Amazon Business purchases")
    print("   • is_gift_flag: Gift orders")
    
    print("\n📅 Date Fields:")
    print("   • purchase_dt_utc: Full timestamp")
    print("   • purchase_dt_hour_utc: Hourly aggregation")
    print("   • purchase_date_utc: Daily aggregation")
    print("   • purchase_month_utc: Monthly aggregation")
    
    print("\n🔍 Session Tracking:")
    print("   • origin_session_id: Add to cart session")
    print("   • purchase_session_id: Purchase completion session")
    print("   • Enables cart abandonment analysis")
    
    print(f"\n📋 Total Fields: {len(retail_purchases_fields)}")

if __name__ == "__main__":
    update_retail_purchases()