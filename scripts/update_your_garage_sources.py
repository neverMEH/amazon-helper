#!/usr/bin/env python3
"""
Update Amazon Your Garage data sources in AMC
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

# Define the Amazon Your Garage data sources
your_garage_sources = [
    {
        "schema_id": "your_garage",
        "name": "Amazon Your Garage",
        "description": "Analytics table containing user-to-vehicle association records. Available as an AMC Paid Feature for North America marketplaces. Contains vehicle attributes including make, model, year, and body style. Refreshes daily as DIMENSION dataset type.",
        "category": "Vehicle Data",
        "table_type": "Analytics"
    },
    {
        "schema_id": "your_garage_for_audiences",
        "name": "Amazon Your Garage for Audiences",
        "description": "Audience table containing user-to-vehicle association records. Available as an AMC Paid Feature for North America marketplaces. Contains vehicle attributes for audience creation and targeting.",
        "category": "Vehicle Data",
        "table_type": "Audience"
    }
]

# Define the fields for Your Garage tables (17 fields)
your_garage_fields = [
    {"name": "user_id", "data_type": "STRING", "field_type": "Dimension", "description": "AMC user ID", "aggregation_threshold": "VERY_HIGH"},
    {"name": "vehicle_body_doors", "data_type": "INTEGER", "field_type": "Dimension", "description": "Number of doors on the vehicle", "aggregation_threshold": "LOW"},
    {"name": "vehicle_body_style", "data_type": "STRING", "field_type": "Dimension", "description": "Body style of the vehicle (e.g., Sedan, SUV, Truck)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_cylinders", "data_type": "INTEGER", "field_type": "Dimension", "description": "Number of cylinders in the vehicle engine", "aggregation_threshold": "LOW"},
    {"name": "vehicle_drive", "data_type": "STRING", "field_type": "Dimension", "description": "Drive type of the vehicle (e.g., FWD, RWD, AWD, 4WD)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_engine_name", "data_type": "STRING", "field_type": "Dimension", "description": "Name/description of the vehicle engine", "aggregation_threshold": "LOW"},
    {"name": "vehicle_engine_size", "data_type": "DECIMAL", "field_type": "Dimension", "description": "Engine displacement size in liters", "aggregation_threshold": "LOW"},
    {"name": "vehicle_fuel", "data_type": "STRING", "field_type": "Dimension", "description": "Fuel type of the vehicle (e.g., Gasoline, Diesel, Electric, Hybrid)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_make", "data_type": "STRING", "field_type": "Dimension", "description": "Manufacturer/brand of the vehicle (e.g., Toyota, Ford, Tesla)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_model", "data_type": "STRING", "field_type": "Dimension", "description": "Model name of the vehicle (e.g., Camry, F-150, Model 3)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_submodel", "data_type": "STRING", "field_type": "Dimension", "description": "Submodel or trim level of the vehicle", "aggregation_threshold": "LOW"},
    {"name": "vehicle_transmission", "data_type": "STRING", "field_type": "Dimension", "description": "Transmission type (e.g., Automatic, Manual, CVT)", "aggregation_threshold": "LOW"},
    {"name": "vehicle_transmission_speeds", "data_type": "INTEGER", "field_type": "Dimension", "description": "Number of transmission speeds/gears", "aggregation_threshold": "LOW"},
    {"name": "vehicle_trim", "data_type": "STRING", "field_type": "Dimension", "description": "Trim level of the vehicle", "aggregation_threshold": "LOW"},
    {"name": "vehicle_year", "data_type": "INTEGER", "field_type": "Dimension", "description": "Model year of the vehicle", "aggregation_threshold": "LOW"},
    {"name": "updated_date", "data_type": "DATE", "field_type": "Dimension", "description": "Date when the record was last updated", "aggregation_threshold": "LOW"},
    {"name": "update_dt", "data_type": "TIMESTAMP", "field_type": "Dimension", "description": "Timestamp when the record was last updated", "aggregation_threshold": "MEDIUM"}
]

def update_your_garage():
    """Update Amazon Your Garage data sources"""
    
    print("\n=== Updating Amazon Your Garage Data Sources ===\n")
    
    success_count = 0
    error_count = 0
    
    # Update/Insert data sources
    for source in your_garage_sources:
        try:
            # Check if data source exists
            existing = supabase.table('amc_data_sources').select('*').eq('schema_id', source['schema_id']).execute()
            
            tags = [
                source.get('table_type'),
                'Paid-Feature',
                'North-America-Only',
                'Vehicle-Data',
                'DIMENSION-Dataset',
                'Daily-Refresh',
                'Automotive'
            ]
            
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
            
            print(f"  Documented {len(your_garage_fields)} fields")
            print(f"  💰 Marked as PAID FEATURE")
            
        except Exception as e:
            print(f"❌ Error updating {source['schema_id']}: {str(e)}")
            error_count += 1
            continue
    
    print(f"\n=== Amazon Your Garage Update Complete ===")
    print(f"   ✅ Success: {success_count} data sources")
    if error_count > 0:
        print(f"   ❌ Errors: {error_count} data sources")
    
    # Verify the update
    print("\n=== Verification ===")
    for schema_id in ['your_garage', 'your_garage_for_audiences']:
        result = supabase.table('amc_data_sources').select('name, description, tags, is_paid_feature').eq('schema_id', schema_id).execute()
        if result.data:
            print(f"\n{schema_id}:")
            print(f"  Name: {result.data[0]['name']}")
            print(f"  Description: {result.data[0]['description'][:100]}...")
            print(f"  Tags: {result.data[0].get('tags', [])}")
            print(f"  Paid Feature: {result.data[0].get('is_paid_feature', False)}")
    
    print("\n💎 PAID FEATURE DETAILS:")
    print("   🌎 Geographic Availability: North America marketplaces only")
    print("   💰 Requires: AMC Paid Feature enrollment")
    print("   📅 Refresh: Daily updates")
    print("   📊 Type: DIMENSION dataset")
    
    print("\n🚗 Vehicle Attributes:")
    print("   • Make & Model: Brand and model identification")
    print("   • Year: Model year for version tracking")
    print("   • Body Style: Sedan, SUV, Truck, etc.")
    print("   • Engine: Size, cylinders, fuel type")
    print("   • Transmission: Type and speeds")
    print("   • Drive: FWD, RWD, AWD, 4WD")
    print("   • Trim/Submodel: Specific configurations")
    
    print("\n📈 Use Cases:")
    print("   • Automotive aftermarket targeting")
    print("   • Parts & accessories recommendations")
    print("   • Service & maintenance campaigns")
    print("   • Insurance & warranty offerings")
    print("   • Vehicle-specific content personalization")
    print("   • Competitive conquest campaigns")
    print("   • Model year upgrade targeting")
    
    print("\n🎯 Key Fields:")
    print("   • user_id: AMC user identifier (VERY_HIGH threshold)")
    print("   • vehicle_make: Manufacturer/brand")
    print("   • vehicle_model: Specific model name")
    print("   • vehicle_year: Model year")
    print("   • vehicle_body_style: Vehicle type")
    print("   • vehicle_fuel: Energy source")
    print("   • updated_date: Last update timestamp")
    
    print("\n⚠️  Important Notes:")
    print("   - Only available in North America")
    print("   - Requires paid feature subscription")
    print("   - User-vehicle associations from Amazon Your Garage")
    print("   - Daily refresh for current vehicle ownership")
    print("   - Join with other tables using user_id")
    
    # Print field summary
    print("\n📋 Field Categories:")
    print("   • Identification: user_id")
    print("   • Basic Info: make, model, year, submodel, trim")
    print("   • Body: style, doors")
    print("   • Engine: size, cylinders, name, fuel")
    print("   • Drivetrain: drive, transmission, speeds")
    print("   • Metadata: updated_date, update_dt")
    print(f"   • Total Fields: {len(your_garage_fields)}")

if __name__ == "__main__":
    update_your_garage()