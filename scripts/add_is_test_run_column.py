#!/usr/bin/env python
"""
Add the is_test_run column to schedule_runs table.
"""

import os
import sys
from pathlib import Path
import psycopg2
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

def add_is_test_run_column():
    """Add is_test_run column to schedule_runs table."""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try to construct from Supabase URL
        supabase_url = os.getenv('SUPABASE_URL')
        if not supabase_url:
            print("Error: DATABASE_URL or SUPABASE_URL must be set")
            return False
        
        # Extract project ref from Supabase URL
        parsed = urlparse(supabase_url)
        project_ref = parsed.hostname.split('.')[0]
        
        # Construct database URL (standard Supabase pattern)
        database_url = f"postgresql://postgres.{project_ref}:Barney-$123@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'schedule_runs' 
            AND column_name = 'is_test_run'
        """)
        
        if cur.fetchone():
            print("Column 'is_test_run' already exists in schedule_runs table")
            conn.close()
            return True
        
        # Add the is_test_run column
        cur.execute("""
            ALTER TABLE schedule_runs 
            ADD COLUMN is_test_run BOOLEAN DEFAULT FALSE;
        """)
        
        print("Successfully added 'is_test_run' column to schedule_runs table")
        
        # Add an index on the column for better query performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_schedule_runs_is_test_run 
            ON schedule_runs(is_test_run);
        """)
        
        print("Successfully added index on 'is_test_run' column")
        
        # Commit changes
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error adding is_test_run column: {e}")
        return False

if __name__ == "__main__":
    success = add_is_test_run_column()
    if success:
        print("\n✅ Migration completed successfully")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)