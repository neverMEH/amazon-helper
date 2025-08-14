#!/usr/bin/env python3
"""
Update Experian Vehicle Purchases data sources in AMC
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

# Define the Experian Vehicle Purchases data source
experian_vehicle_sources = [
    {
        "schema_id": "experian_vehicle_purchases",
        "name": "Experian Vehicle Purchases",
        "description": "Analytics table containing vehicle purchase data from DMV partnership. Includes 12.5 months historical data with 2-month reporting lag. Current and prior month data always incomplete. For attribution and advertising insights only - not for aggregate market analysis. Vehicle purchases are not ad-attributed. Refreshed monthly.",
        "category": "Vehicle Purchases",
        "table_type": "Analytics"
    }
    # Note: No audience table for Experian Vehicle Purchases
]

# Define the fields for Experian Vehicle Purchases table (13 fields)
experian_vehicle_fields = [
    {"name": "new_or_used", "data_type": "STRING", "field_type": "Dimension", "description": "Indicates whether the vehicle was purchased new (N) or used (U)", "aggregation_threshold": "LOW"},
    {"name": "no_3p_trackers", "data_type": "BOOLEAN", "field_type": "Dimension", "description": "Is this item not allowed to use 3P tracking", "aggregation_threshold": "NONE"},
    {"name": "purchase_date", "data_type": "DATE", "field_type": "Dimension", "description": "Purchase Date of vehicle", "aggregation_threshold": "LOW"},
    {"name": "reported_dealership", "data_type": "STRING", "field_type": "Dimension", "description": "The name of the dealership which sold the vehicle, as reported by the DMV", "aggregation_threshold": "MEDIUM"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "Resolved User ID (or null)", "aggregation_threshold": "VERY_HIGH"},
    {"name": "user_id_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of user ID", "aggregation_threshold": "LOW"},
    {"name": "vehicle_class", "data_type": "STRING", "field_type": "Dimension", "description": "The vehicle class, e.g, Luxury", "aggregation_threshold": "LOW"},
    {"name": "vehicle_fuel_type", "data_type": "STRING", "field_type": "Dimension", "description": "The fuel type (i.e., gas, electric) of the purchased vehicle", "aggregation_threshold": "LOW"},
    {"name": "vehicle_make", "data_type": "STRING", "field_type": "Dimension", "description": "The make (brand) of the vehicle purchased", "aggregation_threshold": "LOW"},
    {"name": "vehicle_model", "data_type": "STRING", "field_type": "Dimension", "description": "The model name of the vehicle purchased", "aggregation_threshold": "MEDIUM"},
    {"name": "vehicle_model_year", "data_type": "INTEGER", "field_type": "Dimension", "description": "Model Year of vehicle purchased", "aggregation_threshold": "LOW"},
    {"name": "vehicle_registered_state", "data_type": "STRING", "field_type": "Dimension", "description": "The state where the purchased vehicle was registered", "aggregation_threshold": "LOW"},
    {"name": "vehicle_type", "data_type": "STRING", "field_type": "Dimension", "description": "The type/segment (i.e., SUV) of the purchased vehicle", "aggregation_threshold": "LOW"}
]

def update_experian_vehicle():
    """Update Experian Vehicle Purchases data sources"""
    
    print("\n=== Updating Experian Vehicle Purchases Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in experian_vehicle_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'DMV-Partnership',
                'Vehicle-Sales',
                'Offline-Conversions',
                '2-Month-Lag',
                'Monthly-Refresh',
                'No-Audience-Table',
                'Attribution-Only'
            ]
            
            # Add specific data characteristics tags
            tags.extend([
                '12.5-Months-History',
                'New-Used-Vehicles',
                'Dealership-Data',
                'State-Registration',
                'Not-Ad-Attributed',
                'AMC-Identity-Matched'
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
            
            print(f"  Documented {len(experian_vehicle_fields)} fields")
            print(f"  💰 Marked as PAID FEATURE")
            print(f"  ⚠️  NO audience table available")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Experian Vehicle Purchases Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Verify the update
    print("\n=== Verification ===")
    result = supabase.table('amc_data_sources').select('name, description, tags, is_paid_feature').eq('schema_id', 'experian_vehicle_purchases').execute()
    if result.data:
        print(f"\nexperian_vehicle_purchases:")
        print(f"  Name: {result.data[0]['name']}")
        print(f"  Description: {result.data[0]['description'][:100]}...")
        print(f"  Tags: {', '.join(result.data[0].get('tags', [])[:5])}...")
        print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
    
    print("\n💎 PAID FEATURE DETAILS:")
    print("   💰 Subscription Required: Yes (AMC Paid Features)")
    print("   🚗 Data Partner: Experian via DMV partnership")
    print("   📊 Analytics Only: No audience table available")
    print("   🎯 Purpose: Attribution and advertising insights only")
    
    print("\n⏱️ DATA TIMING & LAG:")
    print("   📅 Reporting Lag: 2 months")
    print("   🔄 Refresh Frequency: Monthly (end of month)")
    print("   ⚠️  Current Month: ALWAYS incomplete")
    print("   ⚠️  Prior Month: ALWAYS incomplete")
    print("   📊 Historical Data: 12.5 months")
    
    print("\n🔴 CRITICAL TIMING CALCULATION:")
    print("   For complete attribution results, wait:")
    print("   Campaign End Date + Attribution Window + 2 months")
    print("   ")
    print("   Example (60-day attribution):")
    print("   • Campaign ends: January 31")
    print("   • Attribution period: +60 days = March 31")
    print("   • Data completeness: April 1 or later")
    print("   • Reason: March data incomplete until April")
    
    print("\n🚗 VEHICLE ATTRIBUTES:")
    print("   • Make & Model: Brand and specific model")
    print("   • Model Year: Year of vehicle model")
    print("   • New vs Used: Purchase condition (N/U)")
    print("   • Vehicle Class: e.g., Luxury")
    print("   • Vehicle Type: Segment (SUV, Sedan, etc.)")
    print("   • Fuel Type: Gas, Electric, Hybrid, etc.")
    print("   • Dealership: Reporting dealer name")
    print("   • Registration State: Where vehicle registered")
    
    print("\n📈 USE CASES:")
    print("   ✅ SUPPORTED:")
    print("      • Campaign attribution analysis")
    print("      • DSP campaign effectiveness measurement")
    print("      • Customer journey to purchase")
    print("      • Media mix optimization")
    print("      • Audience segment performance")
    print("      • Cross-channel attribution")
    print("   ")
    print("   ❌ NOT SUPPORTED:")
    print("      • Total market vehicle sales")
    print("      • Market share analysis")
    print("      • Aggregate sales by model/type")
    print("      • Industry benchmarking")
    print("      • Non-matched purchase analysis")
    
    print("\n⚠️  IMPORTANT LIMITATIONS:")
    print("   1. Vehicle purchases are NOT ad-attributed")
    print("   2. Only includes AMC identity-matched purchases")
    print("   3. Cannot be used for market-level insights")
    print("   4. 2-month data lag affects real-time analysis")
    print("   5. No audience table for targeting")
    
    print("\n🔗 JOIN CONSIDERATIONS:")
    print("   • Join with DSP/SA tables using user_id")
    print("   • Account for 2-month reporting lag")
    print("   • Filter out incomplete months in analysis")
    print("   • Consider attribution window timing")
    
    print("\n📊 ATTRIBUTION BEST PRACTICES:")
    print("   1. Exclude current and prior month from analysis")
    print("   2. Allow sufficient time for data completeness")
    print("   3. Document attribution window in queries")
    print("   4. Validate dealership names for consistency")
    print("   5. Consider state-level privacy regulations")
    
    print("\n🔍 AGGREGATION THRESHOLDS:")
    print("   • VERY_HIGH: user_id")
    print("   • MEDIUM: reported_dealership, vehicle_model")
    print("   • LOW: Most vehicle attributes")
    print("   • NONE: no_3p_trackers")
    
    print("\n📋 KEY FIELDS:")
    print("   • user_id: AMC identity for joining")
    print("   • purchase_date: Transaction date")
    print("   • vehicle_make/model: Specific vehicle")
    print("   • new_or_used: N (new) or U (used)")
    print("   • reported_dealership: Selling dealer")
    print("   • vehicle_registered_state: Registration location")
    
    print(f"\n📋 Total Fields: {len(experian_vehicle_fields)}")
    
    print("\n💡 QUERY TIPS:")
    print("   -- Example: Campaign attribution with proper timing")
    print("   SELECT ")
    print("       campaign_id,")
    print("       COUNT(DISTINCT ev.user_id) as vehicle_purchasers")
    print("   FROM dsp_impressions di")
    print("   JOIN experian_vehicle_purchases ev")
    print("       ON di.user_id = ev.user_id")
    print("       AND ev.purchase_date BETWEEN di.event_date ")
    print("           AND di.event_date + INTERVAL '60 days'")
    print("   WHERE ")
    print("       -- Exclude incomplete months")
    print("       ev.purchase_date < DATE_TRUNC('month', CURRENT_DATE - INTERVAL '2 months')")
    print("   GROUP BY campaign_id")

if __name__ == "__main__":
    update_experian_vehicle()