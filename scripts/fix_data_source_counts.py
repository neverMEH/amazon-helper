#!/usr/bin/env python3
"""
Fix missing field_count and example_count values in amc_data_sources table
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_complexity_from_field_count(field_count: int) -> str:
    """Determine complexity based on field count"""
    if field_count <= 10:
        return 'simple'
    elif field_count <= 25:
        return 'medium'
    else:
        return 'complex'


async def fix_data_source_counts():
    """Fix missing field_count and example_count values"""
    
    print("Fetching all data sources...")
    
    # Get all data sources
    data_sources_result = supabase.table('amc_data_sources').select('*').execute()
    data_sources = data_sources_result.data
    
    print(f"Found {len(data_sources)} data sources")
    
    # Track statistics
    updated_count = 0
    missing_field_count = 0
    missing_example_count = 0
    
    for ds in data_sources:
        ds_id = ds['id']
        schema_id = ds['schema_id']
        name = ds['name']
        current_field_count = ds.get('field_count')
        current_example_count = ds.get('example_count')
        
        updates = {}
        
        # Check field count
        if current_field_count is None:
            missing_field_count += 1
            # Count fields for this data source
            fields_result = supabase.table('amc_schema_fields')\
                .select('id')\
                .eq('data_source_id', ds_id)\
                .execute()
            
            field_count = len(fields_result.data) if fields_result.data else 0
            updates['field_count'] = field_count
            
            # Update complexity based on field count
            updates['complexity'] = get_complexity_from_field_count(field_count)
            
            print(f"  {schema_id}: Setting field_count to {field_count}")
        
        # Check example count
        if current_example_count is None:
            missing_example_count += 1
            # Count examples for this data source
            examples_result = supabase.table('amc_query_examples')\
                .select('id')\
                .eq('data_source_id', ds_id)\
                .execute()
            
            example_count = len(examples_result.data) if examples_result.data else 0
            updates['example_count'] = example_count
            
            print(f"  {schema_id}: Setting example_count to {example_count}")
        
        # Update if needed
        if updates:
            try:
                update_result = supabase.table('amc_data_sources')\
                    .update(updates)\
                    .eq('id', ds_id)\
                    .execute()
                updated_count += 1
            except Exception as e:
                print(f"  Error updating {schema_id}: {e}")
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total data sources: {len(data_sources)}")
    print(f"Missing field_count: {missing_field_count}")
    print(f"Missing example_count: {missing_example_count}")
    print(f"Updated records: {updated_count}")
    
    # Verify the fix
    print("\nVerifying fix...")
    verify_result = supabase.table('amc_data_sources')\
        .select('schema_id, field_count, example_count')\
        .or_('field_count.is.null,example_count.is.null')\
        .execute()
    
    if verify_result.data:
        print(f"WARNING: Still have {len(verify_result.data)} data sources with null counts:")
        for ds in verify_result.data[:5]:
            print(f"  - {ds['schema_id']}: field_count={ds.get('field_count')}, example_count={ds.get('example_count')}")
    else:
        print("SUCCESS: All data sources now have field_count and example_count values!")


if __name__ == "__main__":
    asyncio.run(fix_data_source_counts())