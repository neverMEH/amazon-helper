#!/usr/bin/env python3
"""Replace campaign_mappings with campaigns table and import data from Campaigns.txt"""

import sys
import os
import csv
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_campaign_mappings():
    """Backup existing campaign_mappings data"""
    client = SupabaseManager.get_client(use_service_role=True)
    
    try:
        result = client.table('campaign_mappings').select('*').execute()
        backup_data = result.data
        
        # Save backup to JSON file
        backup_file = f'/root/amazon-helper/campaign_mappings_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        logger.info(f"✅ Backed up {len(backup_data)} records to {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Failed to backup campaign_mappings: {e}")
        return None

def main():
    """Main process to replace campaign_mappings with campaigns"""
    
    logger.info("="*60)
    logger.info("🔄 REPLACING campaign_mappings WITH campaigns TABLE")
    logger.info("="*60)
    
    # Step 1: Backup existing data
    logger.info("\n📌 Step 1: Backing up existing campaign_mappings...")
    backup_file = backup_campaign_mappings()
    
    if not backup_file:
        response = input("⚠️  Backup failed. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Aborting...")
            return False
    
    # Step 2: Show SQL to execute
    logger.info("\n📌 Step 2: Database changes needed...")
    logger.info("\nPlease execute the following SQL in Supabase Dashboard:")
    logger.info("https://loqaorroihxfkjvcrkdv.supabase.co/project/loqaorroihxfkjvcrkdv/sql/new")
    logger.info("\n" + "="*60)
    
    sql_script = """
-- Step 1: Drop the old campaign_mappings table
DROP TABLE IF EXISTS campaign_mappings CASCADE;

-- Step 2: Create the new campaigns table
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

-- Step 3: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_portfolio_id ON campaigns(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_brand ON campaigns(brand);
CREATE INDEX IF NOT EXISTS idx_campaigns_state ON campaigns(state);
CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(type);
CREATE INDEX IF NOT EXISTS idx_campaigns_targeting_type ON campaigns(targeting_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_bidding_strategy ON campaigns(bidding_strategy);

-- Step 4: Add RLS policies (optional, adjust as needed)
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "campaigns_all_policy" ON campaigns
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Step 5: Add comments
COMMENT ON TABLE campaigns IS 'Amazon advertising campaign data (replaced campaign_mappings)';
COMMENT ON COLUMN campaigns.campaign_id IS 'Amazon campaign ID';
COMMENT ON COLUMN campaigns.portfolio_id IS 'Portfolio ID the campaign belongs to';
COMMENT ON COLUMN campaigns.type IS 'Campaign type (sp, sb, sd)';
COMMENT ON COLUMN campaigns.targeting_type IS 'Targeting type (AUTO, MANUAL)';
COMMENT ON COLUMN campaigns.bidding_strategy IS 'Bidding strategy used';
COMMENT ON COLUMN campaigns.state IS 'Campaign state (ENABLED, PAUSED, ARCHIVED)';
COMMENT ON COLUMN campaigns.name IS 'Campaign name';
COMMENT ON COLUMN campaigns.brand IS 'Brand associated with the campaign';
"""
    
    print(sql_script)
    logger.info("="*60)
    
    logger.info("\n📋 INSTRUCTIONS:")
    logger.info("1. Copy the SQL above")
    logger.info("2. Go to Supabase SQL Editor")
    logger.info("3. Paste and click 'Run'")
    logger.info("4. Then run: python scripts/import_campaigns_after_drop.py")
    
    # Save the SQL to a file for convenience
    with open('/root/amazon-helper/scripts/replace_campaign_mappings.sql', 'w') as f:
        f.write(sql_script)
    logger.info(f"\n✅ SQL also saved to: /root/amazon-helper/scripts/replace_campaign_mappings.sql")
    
    if backup_file:
        logger.info(f"📦 Your backup is safe at: {backup_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)