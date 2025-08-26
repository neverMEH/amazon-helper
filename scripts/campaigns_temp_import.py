#!/usr/bin/env python3
"""Import campaigns using a temporary approach"""

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

def create_temp_table_and_import():
    """Create a temporary table with JSON data and import campaigns"""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # First, let's check if we can create a simple table
    try:
        # Check if campaigns_temp exists
        result = client.table('campaigns_temp').select('*').limit(1).execute()
        logger.info("campaigns_temp table exists")
    except Exception as e:
        logger.info(f"campaigns_temp doesn't exist: {e}")
        
        # Try to insert dummy data to trigger auto-creation (won't work for DDL but worth trying)
        try:
            dummy = {'data': {}}
            client.table('campaigns_temp').insert(dummy).execute()
            logger.info("Created campaigns_temp table")
            # Delete the dummy
            client.table('campaigns_temp').delete().eq('data', {}).execute()
        except Exception as create_e:
            logger.error(f"Cannot create table programmatically: {create_e}")
            
            # Provide manual SQL
            logger.info("\n" + "="*60)
            logger.info("📋 PLEASE CREATE THE TABLE MANUALLY")
            logger.info("="*60)
            logger.info("\n1. Go to Supabase SQL Editor:")
            logger.info("   https://loqaorroihxfkjvcrkdv.supabase.co/project/loqaorroihxfkjvcrkdv/sql/new")
            logger.info("\n2. Run this SQL:")
            print("""
CREATE TABLE campaigns_temp (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Or the full campaigns table:
CREATE TABLE campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id TEXT NOT NULL UNIQUE,
    portfolio_id TEXT,
    type TEXT,
    targeting_type TEXT,
    bidding_strategy TEXT,
    state TEXT,
    name TEXT,
    brand TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaigns_campaign_id ON campaigns(campaign_id);
CREATE INDEX idx_campaigns_brand ON campaigns(brand);
CREATE INDEX idx_campaigns_state ON campaigns(state);
            """)
            logger.info("\n3. After creating the table, run this script again")
            return False
    
    # If we get here, try importing to campaigns_temp
    file_path = '/root/amazon-helper/Campaigns.txt'
    logger.info(f"Importing from {file_path} to campaigns_temp...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            
            batch = []
            batch_size = 100
            total = 0
            
            for row in reader:
                # Wrap each row in a JSON structure
                record = {
                    'data': {
                        'campaign_id': row['CAMPAIGN_ID'].strip() if row['CAMPAIGN_ID'] else None,
                        'portfolio_id': row['PORTFOLIO_ID'].strip() if row['PORTFOLIO_ID'] else None,
                        'type': row['TYPE'].strip() if row['TYPE'] else None,
                        'targeting_type': row['TARGETING_TYPE'].strip() if row['TARGETING_TYPE'] else None,
                        'bidding_strategy': row['BIDDING_STRATEGY'].strip() if row['BIDDING_STRATEGY'] else None,
                        'state': row['STATE'].strip() if row['STATE'] else None,
                        'name': row['NAME'].strip() if row['NAME'] else None,
                        'brand': row['BRAND'].strip() if row['BRAND'] else None
                    }
                }
                
                if record['data']['campaign_id']:
                    batch.append(record)
                
                if len(batch) >= batch_size:
                    client.table('campaigns_temp').insert(batch).execute()
                    total += len(batch)
                    logger.info(f"Imported {total} campaigns...")
                    batch = []
            
            # Insert remaining
            if batch:
                client.table('campaigns_temp').insert(batch).execute()
                total += len(batch)
            
            logger.info(f"✅ Imported {total} campaigns to campaigns_temp")
            
            # Now provide SQL to move data to proper table
            logger.info("\n" + "="*60)
            logger.info("📋 NEXT STEP: Move data to campaigns table")
            logger.info("="*60)
            logger.info("\nRun this SQL in Supabase SQL Editor:")
            print("""
-- First create the campaigns table if it doesn't exist
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id TEXT NOT NULL UNIQUE,
    portfolio_id TEXT,
    type TEXT,
    targeting_type TEXT,
    bidding_strategy TEXT,
    state TEXT,
    name TEXT,
    brand TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Then migrate data from campaigns_temp
INSERT INTO campaigns (campaign_id, portfolio_id, type, targeting_type, bidding_strategy, state, name, brand)
SELECT 
    data->>'campaign_id',
    data->>'portfolio_id',
    data->>'type',
    data->>'targeting_type',
    data->>'bidding_strategy',
    data->>'state',
    data->>'name',
    data->>'brand'
FROM campaigns_temp
WHERE data->>'campaign_id' IS NOT NULL
ON CONFLICT (campaign_id) DO NOTHING;

-- Verify the import
SELECT COUNT(*) as total_campaigns FROM campaigns;

-- Optional: Drop the temp table
-- DROP TABLE campaigns_temp;
            """)
            
            return True
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    success = create_temp_table_and_import()
    sys.exit(0 if success else 1)