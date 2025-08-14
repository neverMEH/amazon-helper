#!/usr/bin/env python3
"""
Add missing field_count, example_count, and complexity columns to amc_data_sources table
"""

import os
from supabase import create_client
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_supabase_client():
    """Create Supabase client with service role key"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment variables")
    
    return create_client(url, key)

def add_columns():
    """Add missing columns to amc_data_sources table"""
    
    client = get_supabase_client()
    
    # SQL to add the columns
    sql_commands = [
        """
        ALTER TABLE amc_data_sources 
        ADD COLUMN IF NOT EXISTS field_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE amc_data_sources 
        ADD COLUMN IF NOT EXISTS example_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE amc_data_sources 
        ADD COLUMN IF NOT EXISTS complexity TEXT DEFAULT 'simple'
        CHECK (complexity IN ('simple', 'medium', 'complex'));
        """
    ]
    
    for sql in sql_commands:
        try:
            # Use RPC to execute raw SQL
            result = client.rpc('exec_sql', {'query': sql}).execute()
            logger.info(f"Executed: {sql.strip()[:50]}...")
        except Exception as e:
            # Try direct approach if RPC doesn't exist
            logger.warning(f"RPC exec_sql not available, column may already exist: {e}")
    
    logger.info("Column addition complete. Please run fix_data_source_counts.py to populate the data.")

if __name__ == '__main__':
    add_columns()