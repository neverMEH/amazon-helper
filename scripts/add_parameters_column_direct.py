#!/usr/bin/env python3
"""Add missing parameters column to schedule_runs table using direct database connection."""

import os
import psycopg2
from urllib.parse import urlparse

def main():
    """Add parameters column to schedule_runs table."""
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Try to construct from Supabase URL
        supabase_url = os.environ.get('SUPABASE_URL')
        if supabase_url:
            # Extract project reference from Supabase URL
            parsed = urlparse(supabase_url)
            project_ref = parsed.hostname.split('.')[0]
            database_url = f"postgresql://postgres.{project_ref}:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    # Connect to database
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:] if parsed.path else 'postgres',
            user=parsed.username or 'postgres',
            password=parsed.password or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        )
        
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'schedule_runs' 
            AND column_name = 'parameters'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Parameters column already exists in schedule_runs table")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE schedule_runs 
                ADD COLUMN parameters jsonb
            """)
            
            # Add comment
            cursor.execute("""
                COMMENT ON COLUMN schedule_runs.parameters IS 
                'Execution parameters used for this run (date ranges, filters, etc.)'
            """)
            
            conn.commit()
            print("✅ Successfully added parameters column to schedule_runs table")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)