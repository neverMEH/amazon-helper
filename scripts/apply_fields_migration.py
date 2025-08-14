#!/usr/bin/env python3
"""
Apply migration to add fields column via psycopg2
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get direct database connection from Supabase URL"""
    supabase_url = os.getenv('SUPABASE_URL')
    
    # Parse the URL to get the project ref
    parsed = urlparse(supabase_url)
    project_ref = parsed.hostname.split('.')[0]
    
    # Construct database URL
    # Supabase DB URLs follow pattern: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    
    if not db_password:
        # Try to use service role key as password (common pattern)
        db_password = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    db_url = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print(f"Connecting to database...")
    return psycopg2.connect(db_url)

def apply_migration():
    """Apply the fields column migration"""
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("Adding fields column to amc_data_sources table...")
        
        # Add the fields column
        cur.execute("""
            ALTER TABLE public.amc_data_sources 
            ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;
        """)
        
        # Add comment
        cur.execute("""
            COMMENT ON COLUMN public.amc_data_sources.fields IS 
            'Array of field definitions for this data source schema';
        """)
        
        # Create index
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_amc_data_sources_fields 
            ON public.amc_data_sources USING GIN (fields);
        """)
        
        conn.commit()
        print("✓ Migration applied successfully!")
        
        # Verify the column was added
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'amc_data_sources' 
            AND column_name = 'fields';
        """)
        
        result = cur.fetchone()
        if result:
            print(f"✓ Verified: Column '{result[0]}' of type '{result[1]}' exists")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error applying migration: {e}")
        if 'already exists' in str(e).lower():
            print("Fields column already exists")
            return True
        return False

if __name__ == "__main__":
    apply_migration()