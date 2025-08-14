#!/usr/bin/env python3
"""
Apply migration to add count columns to amc_data_sources table
This uses psycopg2 to connect directly to the database
"""

import os
import psycopg2
from psycopg2 import sql
from urllib.parse import urlparse
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    """Create direct database connection from Supabase URL"""
    # Get the database URL from environment
    db_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
    
    if not db_url:
        # Try to construct from Supabase URL
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            # Replace https with postgresql and adjust the URL
            db_url = supabase_url.replace('https://', 'postgresql://postgres:')
            db_url = db_url.replace('.supabase.co', '.supabase.co:5432/postgres')
            # Add password
            db_password = os.getenv('SUPABASE_DB_PASSWORD')
            if db_password:
                db_url = db_url.replace('postgres:', f'postgres:{db_password}@')
    
    if not db_url:
        raise ValueError("Cannot construct database URL. Please set DATABASE_URL or SUPABASE_DB_URL")
    
    return psycopg2.connect(db_url)

def apply_migration():
    """Apply the migration to add count columns"""
    
    migration_sql = """
    -- Add field_count column
    ALTER TABLE amc_data_sources 
    ADD COLUMN IF NOT EXISTS field_count INTEGER DEFAULT 0;

    -- Add example_count column
    ALTER TABLE amc_data_sources 
    ADD COLUMN IF NOT EXISTS example_count INTEGER DEFAULT 0;

    -- Add complexity column with check constraint
    ALTER TABLE amc_data_sources 
    ADD COLUMN IF NOT EXISTS complexity TEXT DEFAULT 'simple'
    CHECK (complexity IN ('simple', 'medium', 'complex'));

    -- Add indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_amc_data_sources_field_count ON amc_data_sources(field_count);
    CREATE INDEX IF NOT EXISTS idx_amc_data_sources_complexity ON amc_data_sources(complexity);

    -- Update existing rows with calculated counts
    UPDATE amc_data_sources ds
    SET 
        field_count = COALESCE((
            SELECT COUNT(*) 
            FROM amc_schema_fields f 
            WHERE f.data_source_id = ds.id
        ), 0),
        example_count = COALESCE((
            SELECT COUNT(*) 
            FROM amc_query_examples e 
            WHERE e.data_source_id = ds.id
        ), 0);

    -- Update complexity based on field count
    UPDATE amc_data_sources
    SET complexity = CASE
        WHEN field_count < 20 THEN 'simple'
        WHEN field_count < 50 THEN 'medium'
        ELSE 'complex'
    END;
    """
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        logger.info("Applying migration...")
        cur.execute(migration_sql)
        
        # Get row count
        cur.execute("SELECT COUNT(*) FROM amc_data_sources")
        count = cur.fetchone()[0]
        
        conn.commit()
        logger.info(f"Migration applied successfully! Updated {count} data sources.")
        
        # Verify the columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'amc_data_sources' 
            AND column_name IN ('field_count', 'example_count', 'complexity')
        """)
        
        columns = [row[0] for row in cur.fetchall()]
        logger.info(f"Verified columns exist: {columns}")
        
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error applying migration: {e}")
        logger.info("You may need to manually run the migration SQL in the Supabase dashboard.")
        logger.info("Check the file: migrations/add_data_source_counts.sql")
        return False

if __name__ == '__main__':
    if apply_migration():
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed. Please check the logs.")
        exit(1)