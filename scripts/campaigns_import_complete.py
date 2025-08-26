#!/usr/bin/env python3
"""Complete campaigns import script with table creation SQL and data import"""

import sys
import os
import csv
import logging
import time
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SQL for creating the campaigns table
CREATE_TABLE_SQL = """
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
"""

def check_table_exists() -> bool:
    """Check if campaigns table exists in Supabase"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        result = client.table('campaigns').select('*').limit(1).execute()
        return True
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            return False
        logger.error(f"Error checking table: {e}")
        return False

def get_existing_count() -> int:
    """Get count of existing records in campaigns table"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        result = client.table('campaigns').select('*', count='exact').execute()
        return len(result.data) if result.data else 0
    except Exception:
        return 0

def parse_campaigns_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse the Campaigns.txt file and return list of campaign dictionaries"""
    campaigns = []
    skipped = 0
    
    logger.info(f"Parsing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Clean and prepare the data
                campaign = {
                    'campaign_id': row['CAMPAIGN_ID'].strip() if row['CAMPAIGN_ID'] else None,
                    'portfolio_id': row['PORTFOLIO_ID'].strip() if row['PORTFOLIO_ID'] else None,
                    'type': row['TYPE'].strip() if row['TYPE'] else None,
                    'targeting_type': row['TARGETING_TYPE'].strip() if row['TARGETING_TYPE'] else None,
                    'bidding_strategy': row['BIDDING_STRATEGY'].strip() if row['BIDDING_STRATEGY'] else None,
                    'state': row['STATE'].strip() if row['STATE'] else None,
                    'name': row['NAME'].strip() if row['NAME'] else None,
                    'brand': row['BRAND'].strip() if row['BRAND'] else None
                }
                
                # Skip rows with no campaign_id
                if not campaign['campaign_id']:
                    skipped += 1
                    continue
                
                campaigns.append(campaign)
                
            except Exception as e:
                logger.warning(f"Error parsing row {row_num}: {e}")
                skipped += 1
                continue
    
    logger.info(f"✅ Parsed {len(campaigns)} campaigns ({skipped} rows skipped)")
    return campaigns

def import_campaigns_batch(campaigns: List[Dict[str, Any]], batch_size: int = 500) -> int:
    """Import campaigns in batches to Supabase"""
    client = SupabaseManager.get_client(use_service_role=True)
    total_imported = 0
    failed_batches = 0
    
    logger.info(f"Starting import of {len(campaigns)} campaigns in batches of {batch_size}")
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(campaigns) + batch_size - 1) // batch_size
        
        try:
            result = client.table('campaigns').insert(batch).execute()
            total_imported += len(batch)
            logger.info(f"✅ Batch {batch_num}/{total_batches}: Imported {len(batch)} campaigns (Total: {total_imported}/{len(campaigns)})")
            
            # Small delay to avoid rate limits
            if batch_num < total_batches:
                time.sleep(0.1)
                
        except Exception as e:
            failed_batches += 1
            logger.error(f"❌ Batch {batch_num}/{total_batches} failed: {e}")
            
            # Try to import individually for this batch
            individual_success = 0
            for campaign in batch:
                try:
                    client.table('campaigns').insert(campaign).execute()
                    individual_success += 1
                    total_imported += 1
                except Exception as ind_e:
                    logger.debug(f"Failed to import campaign {campaign['campaign_id']}: {ind_e}")
            
            if individual_success > 0:
                logger.info(f"  Recovered {individual_success}/{len(batch)} campaigns from failed batch")
    
    return total_imported

def verify_import(expected_count: int) -> bool:
    """Verify that the import was successful"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Get total count
        count_result = client.table('campaigns').select('*', count='exact').execute()
        actual_count = len(count_result.data) if count_result.data else 0
        
        logger.info(f"\n📊 Import Verification:")
        logger.info(f"  Expected: {expected_count} campaigns")
        logger.info(f"  Actual: {actual_count} campaigns")
        
        # Get sample data
        sample_result = client.table('campaigns').select('*').limit(5).execute()
        if sample_result.data:
            logger.info(f"\n📋 Sample of imported campaigns:")
            for campaign in sample_result.data[:3]:
                logger.info(f"  • {campaign['name'][:50]}... ({campaign['campaign_id']})")
                logger.info(f"    Brand: {campaign['brand']}, State: {campaign['state']}, Type: {campaign['type']}")
        
        # Get statistics
        stats_result = client.table('campaigns').select('state').execute()
        if stats_result.data:
            state_counts = {}
            for item in stats_result.data:
                state = item['state'] or 'UNKNOWN'
                state_counts[state] = state_counts.get(state, 0) + 1
            
            logger.info(f"\n📈 Campaign State Distribution:")
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {state}: {count} campaigns")
        
        return actual_count == expected_count
        
    except Exception as e:
        logger.error(f"Error verifying import: {e}")
        return False

def main():
    """Main function to orchestrate the import process"""
    logger.info("="*60)
    logger.info("🚀 CAMPAIGNS IMPORT TOOL")
    logger.info("="*60)
    
    # Step 1: Check if table exists
    logger.info("\n📌 Step 1: Checking campaigns table...")
    if not check_table_exists():
        logger.warning("❌ campaigns table does not exist!")
        logger.info("\n" + "="*60)
        logger.info("📋 MANUAL SETUP REQUIRED")
        logger.info("="*60)
        logger.info("\n1. Go to Supabase SQL Editor:")
        logger.info("   https://loqaorroihxfkjvcrkdv.supabase.co/project/loqaorroihxfkjvcrkdv/sql/new")
        logger.info("\n2. Copy and paste this SQL:")
        logger.info("-"*60)
        print(CREATE_TABLE_SQL)
        logger.info("-"*60)
        logger.info("\n3. Click 'Run' to create the table")
        logger.info("\n4. Run this script again: python scripts/campaigns_import_complete.py")
        logger.info("="*60)
        return False
    
    logger.info("✅ campaigns table exists!")
    
    # Check existing data
    existing_count = get_existing_count()
    if existing_count > 0:
        logger.info(f"⚠️  Found {existing_count} existing records in campaigns table")
        response = input("Do you want to delete existing records before import? (y/n): ")
        if response.lower() == 'y':
            try:
                client = SupabaseManager.get_client(use_service_role=True)
                client.table('campaigns').delete().neq('campaign_id', '').execute()
                logger.info("✅ Cleared existing campaign data")
            except Exception as e:
                logger.error(f"Error clearing data: {e}")
                return False
    
    # Step 2: Parse the file
    logger.info("\n📌 Step 2: Parsing Campaigns.txt file...")
    file_path = '/root/amazon-helper/Campaigns.txt'
    
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return False
    
    campaigns = parse_campaigns_file(file_path)
    if not campaigns:
        logger.error("❌ No valid campaigns found in file")
        return False
    
    # Step 3: Import the data
    logger.info(f"\n📌 Step 3: Importing {len(campaigns)} campaigns to Supabase...")
    imported_count = import_campaigns_batch(campaigns)
    
    # Step 4: Verify the import
    logger.info("\n📌 Step 4: Verifying import...")
    success = verify_import(len(campaigns))
    
    # Final summary
    logger.info("\n" + "="*60)
    if success:
        logger.info("🎉 IMPORT COMPLETED SUCCESSFULLY!")
        logger.info(f"✅ Imported {imported_count} campaigns")
    else:
        logger.info("⚠️  IMPORT COMPLETED WITH WARNINGS")
        logger.info(f"📊 Imported {imported_count}/{len(campaigns)} campaigns")
    logger.info("="*60)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏸️  Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        sys.exit(1)