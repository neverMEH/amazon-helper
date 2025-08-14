#!/usr/bin/env python3
"""
Update NC Solutions (NCS) CPG Insights Stream data sources in AMC
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

# Define the NCS CPG Insights Stream data source
ncs_cpg_sources = [
    {
        "schema_id": "ncs_cpg_insights_stream",
        "name": "NCS CPG Insights Stream",
        "description": "Analytics table containing offline modeled CPG transactions at household level, representing 127MM+ US households. Derived from machine learning models using 2.7 trillion observed transaction records from 98MM+ households across 20+ major retailers and 56K+ locations. Enables holistic measurement of online media impact on offline purchases. Weekly data with Saturday week-ending dates.",
        "category": "Offline Sales",
        "table_type": "Analytics"
    }
    # Note: No audience table for NCS CPG Insights Stream
]

# Define the fields for NCS CPG Insights Stream table (13 fields)
ncs_cpg_fields = [
    {"name": "brand", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated brand name", "aggregation_threshold": "LOW"},
    {"name": "category", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated product category name", "aggregation_threshold": "LOW"},
    {"name": "department", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated department name", "aggregation_threshold": "LOW"},
    {"name": "household_purchase_id", "data_type": "STRING", "field_type": "Dimension", "description": "Unique ID for the household purchase event, can be used to count distinct household purchases", "aggregation_threshold": "VERY_HIGH"},
    {"name": "ncs_household_id", "data_type": "STRING", "field_type": "Dimension", "description": "NCS household ID", "aggregation_threshold": "VERY_HIGH"},
    {"name": "product_category", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated subscription resource object; associated with the department, super_category and category attributes", "aggregation_threshold": "LOW"},
    {"name": "purchase_dollar_amount", "data_type": "DECIMAL", "field_type": "Metric", "description": "US Dollar amount of products purchased", "aggregation_threshold": "LOW"},
    {"name": "purchase_quantity", "data_type": "INTEGER", "field_type": "Metric", "description": "Quantity of products purchased", "aggregation_threshold": "LOW"},
    {"name": "sub_brand", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated sub brand name", "aggregation_threshold": "LOW"},
    {"name": "super_category", "data_type": "STRING", "field_type": "Dimension", "description": "NCS syndicated super product category name", "aggregation_threshold": "LOW"},
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "User ID", "aggregation_threshold": "VERY_HIGH"},
    {"name": "user_id_type", "data_type": "STRING", "field_type": "Dimension", "description": "Type of user ID", "aggregation_threshold": "LOW"},
    {"name": "week_end_dt", "data_type": "DATE", "field_type": "Dimension", "description": "Week end date. Datestamp of last day included in the weekly transaction file. Always Saturday, representing Sunday-Saturday purchases", "aggregation_threshold": "LOW"}
]

def update_ncs_cpg():
    """Update NCS CPG Insights Stream data sources"""
    
    print("\n=== Updating NC Solutions (NCS) CPG Insights Stream Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in ncs_cpg_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'Offline-Sales',
                'CPG-Data',
                'US-Only',
                'Household-Level',
                'Machine-Learning-Modeled',
                'Weekly-Aggregation',
                'No-Audience-Table'
            ]
            
            # Add specific data scope tags
            tags.extend([
                '127MM-Households',
                '2.7T-Transactions',
                '20-Plus-Retailers',
                '56K-Locations',
                'Nielsen-Enhanced',
                'Saturday-Week-End'
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
            
            print(f"  Documented {len(ncs_cpg_fields)} fields")
            print(f"  💰 Marked as PAID FEATURE")
            print(f"  ⚠️  NO audience table available")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== NCS CPG Insights Stream Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Verify the update
    print("\n=== Verification ===")
    result = supabase.table('amc_data_sources').select('name, description, tags, is_paid_feature').eq('schema_id', 'ncs_cpg_insights_stream').execute()
    if result.data:
        print(f"\nncs_cpg_insights_stream:")
        print(f"  Name: {result.data[0]['name']}")
        print(f"  Description: {result.data[0]['description'][:100]}...")
        print(f"  Tags: {', '.join(result.data[0].get('tags', [])[:5])}...")
        print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
    
    print("\n💎 PAID FEATURE DETAILS:")
    print("   💰 Subscription Required: Yes (AMC Paid Features)")
    print("   🌎 Geographic Coverage: United States only")
    print("   🏪 Data Source: Nielsen Consumer Solutions (NCS)")
    print("   📊 Analytics Only: No audience table available")
    
    print("\n📈 DATA SCALE & COVERAGE:")
    print("   🏠 Household Coverage: 127MM+ US households (total population)")
    print("   📦 Transaction Records: 2.7 trillion observed transactions")
    print("   👥 Seed Dataset: 98MM+ US households")
    print("   🏬 Retail Partners: 20+ major national and regional CPG retailers")
    print("   📍 Store Locations: 56,000+ retail locations")
    print("   🤖 Methodology: Advanced machine learning models")
    print("   📊 Enhancement: Nielsen household-level data")
    
    print("\n📅 DATA FRESHNESS:")
    print("   📆 Update Frequency: Weekly")
    print("   🗓️ Week Definition: Sunday through Saturday")
    print("   📍 Week End Date: Always Saturday")
    print("   ⏱️ Reporting Lag: 7-day rolling window")
    
    print("\n🎯 KEY METRICS:")
    print("   • purchase_dollar_amount: Transaction value in USD")
    print("   • purchase_quantity: Units purchased")
    print("   • household_purchase_id: Unique purchase event")
    print("   • ncs_household_id: Household identifier")
    
    print("\n🏷️ PRODUCT HIERARCHY:")
    print("   1️⃣ Department: Highest level category")
    print("   2️⃣ Super Category: Major product grouping")
    print("   3️⃣ Category: Product category")
    print("   4️⃣ Brand: Manufacturer brand")
    print("   5️⃣ Sub Brand: Brand variant/line")
    
    print("\n📊 USE CASES:")
    print("   • Online-to-Offline (O2O) Attribution:")
    print("     - Measure digital media impact on in-store purchases")
    print("     - Connect Amazon Ads to offline retail sales")
    print("     - True ROAS including offline conversions")
    print("   • CPG Campaign Optimization:")
    print("     - Identify high-value household segments")
    print("     - Optimize media mix for offline impact")
    print("     - Cross-channel attribution analysis")
    print("   • Competitive Intelligence:")
    print("     - Category share analysis")
    print("     - Brand switching behavior")
    print("     - Market basket insights")
    print("   • Customer Journey Mapping:")
    print("     - Online browse to offline buy patterns")
    print("     - Multi-touchpoint attribution")
    print("     - Household purchase behavior analysis")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   ❌ NO audience table available (analytics only)")
    print("   ✅ Household-level granularity (not individual)")
    print("   ✅ Modeled data (not deterministic)")
    print("   ✅ Weekly aggregation (not daily)")
    print("   ✅ US market only")
    print("   ✅ CPG categories only")
    
    print("\n🔗 JOIN CONSIDERATIONS:")
    print("   • Join with AMC data using user_id")
    print("   • Match on week_end_dt for temporal alignment")
    print("   • Aggregate to weekly level before joining")
    print("   • Account for modeling confidence levels")
    
    print("\n🔍 AGGREGATION THRESHOLDS:")
    print("   • VERY_HIGH: user_id, ncs_household_id, household_purchase_id")
    print("   • LOW: All product hierarchy and metric fields")
    
    print(f"\n📋 Total Fields: {len(ncs_cpg_fields)}")
    
    print("\n💡 BEST PRACTICES:")
    print("   1. Use week_end_dt for consistent time alignment")
    print("   2. Count distinct household_purchase_id for unique purchases")
    print("   3. Aggregate metrics at household level first")
    print("   4. Consider modeling confidence in analysis")
    print("   5. Validate against known CPG benchmarks")

if __name__ == "__main__":
    update_ncs_cpg()