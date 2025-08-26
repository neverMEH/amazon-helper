#!/usr/bin/env python3
"""Apply campaigns table migration to Supabase using raw SQL"""

import sys
import os
import logging
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_campaigns_migration():
    """Apply the campaigns table migration"""
    
    # Get Supabase client
    client = SupabaseManager.get_client(use_service_role=True)
    
    # The SQL to create campaigns table
    migration_sql = """
    -- Create campaigns table for storing Amazon advertising campaign data
    CREATE TABLE IF NOT EXISTS campaigns (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        campaign_id TEXT NOT NULL,
        portfolio_id TEXT,
        type TEXT,
        targeting_type TEXT,
        bidding_strategy TEXT,
        state TEXT,
        name TEXT,
        brand TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(campaign_id)
    );
    
    -- Create indexes for commonly queried fields
    CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id);
    CREATE INDEX IF NOT EXISTS idx_campaigns_portfolio_id ON campaigns(portfolio_id);
    CREATE INDEX IF NOT EXISTS idx_campaigns_brand ON campaigns(brand);
    CREATE INDEX IF NOT EXISTS idx_campaigns_state ON campaigns(state);
    CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(type);
    CREATE INDEX IF NOT EXISTS idx_campaigns_targeting_type ON campaigns(targeting_type);
    CREATE INDEX IF NOT EXISTS idx_campaigns_bidding_strategy ON campaigns(bidding_strategy);
    
    -- Add RLS policies (Row Level Security)
    ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
    
    -- Policy to allow read access to all authenticated users
    CREATE POLICY "campaigns_read_policy" ON campaigns
        FOR SELECT
        USING (true);
    
    -- Policy to allow insert for service role
    CREATE POLICY "campaigns_insert_policy" ON campaigns
        FOR INSERT
        WITH CHECK (true);
    
    -- Policy to allow update for service role
    CREATE POLICY "campaigns_update_policy" ON campaigns
        FOR UPDATE
        USING (true)
        WITH CHECK (true);
    
    -- Policy to allow delete for service role
    CREATE POLICY "campaigns_delete_policy" ON campaigns
        FOR DELETE
        USING (true);
    
    -- Add comment to table
    COMMENT ON TABLE campaigns IS 'Stores Amazon advertising campaign data';
    """
    
    # Unfortunately, Supabase Python client doesn't support DDL execution directly
    # Try alternative approach - directly use postgrest if available
    try:
        # Check if campaigns table already exists
        result = client.table('campaigns').select('*').limit(1).execute()
        logger.info("✅ campaigns table already exists!")
        return True
    except Exception as e:
        logger.info(f"Table doesn't exist yet: {e}")
        
        # We need to create it manually through Supabase Dashboard
        logger.info("\n" + "="*60)
        logger.info("⚠️  MANUAL STEP REQUIRED")
        logger.info("="*60)
        logger.info("\nThe campaigns table needs to be created manually.")
        logger.info("\nOption 1: Use Supabase Dashboard")
        logger.info("1. Go to: https://loqaorroihxfkjvcrkdv.supabase.co")
        logger.info("2. Navigate to SQL Editor")
        logger.info("3. Copy the SQL from scripts/create_campaigns_table.sql")
        logger.info("4. Paste and click 'Run'")
        logger.info("\nOption 2: Use Supabase CLI (if installed)")
        logger.info("supabase db execute -f scripts/create_campaigns_table.sql")
        logger.info("\n" + "="*60)
        
        # Save the SQL to a file for convenience
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_campaigns_table.sql')
        if not os.path.exists(sql_file_path):
            with open(sql_file_path, 'w') as f:
                f.write(migration_sql)
            logger.info(f"\n✅ SQL saved to: {sql_file_path}")
        
        return False

if __name__ == "__main__":
    success = apply_campaigns_migration()
    if not success:
        logger.info("\n⏸️  Please create the table manually, then run:")
        logger.info("python scripts/import_campaigns.py")
        sys.exit(1)
    else:
        logger.info("\n✅ Table is ready! You can now run:")
        logger.info("python scripts/import_campaigns.py")