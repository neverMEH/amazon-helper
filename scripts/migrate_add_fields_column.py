#!/usr/bin/env python3
"""
Migration to add fields column to amc_data_sources table
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def main():
    """Add fields column via Supabase migration"""
    
    # Create client
    client = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    print("Checking if fields column exists...")
    
    # First, let's check current data
    result = client.table('amc_data_sources').select('*').limit(1).execute()
    
    if result.data and 'fields' in result.data[0]:
        print("Fields column already exists!")
        # Check if it's populated
        check_result = client.table('amc_data_sources').select('schema_id, fields').limit(5).execute()
        for item in check_result.data:
            fields = item.get('fields', [])
            field_count = len(fields) if isinstance(fields, list) else 0
            print(f"  {item['schema_id']}: {field_count} fields")
        return
    
    print("Fields column does not exist in the response.")
    print("This needs to be added via a Supabase migration.")
    
    # Let's create a SQL file for the migration
    migration_sql = """
-- Add fields column to amc_data_sources table
ALTER TABLE public.amc_data_sources 
ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN public.amc_data_sources.fields IS 'Array of field definitions for this data source schema';

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_amc_data_sources_fields ON public.amc_data_sources USING GIN (fields);
"""
    
    # Save migration file
    migration_file = '/root/amazon-helper/scripts/migration_add_fields_column.sql'
    with open(migration_file, 'w') as f:
        f.write(migration_sql)
    
    print(f"\nMigration SQL saved to: {migration_file}")
    print("\nTo apply this migration:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Run the migration SQL")
    print("\nOr use the Supabase CLI:")
    print("supabase migration new add_fields_column")
    print("# Copy the SQL to the migration file")
    print("supabase db push")

if __name__ == "__main__":
    main()