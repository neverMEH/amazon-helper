#!/usr/bin/env python3
"""Import campaigns after dropping campaign_mappings"""

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

def check_table_ready():
    """Check if campaigns table exists and campaign_mappings is gone"""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Check campaign_mappings is gone
    try:
        client.table('campaign_mappings').select('*').limit(1).execute()
        logger.warning("⚠️  campaign_mappings table still exists! Please drop it first.")
        return False
    except Exception as e:
        if "does not exist" in str(e):
            logger.info("✅ campaign_mappings table successfully dropped")
        else:
            logger.warning(f"Unexpected error checking campaign_mappings: {e}")
    
    # Check campaigns table exists
    try:
        client.table('campaigns').select('*').limit(1).execute()
        logger.info("✅ campaigns table exists and is ready")
        return True
    except Exception as e:
        logger.error(f"❌ campaigns table does not exist: {e}")
        logger.info("\nPlease run the SQL from scripts/replace_campaign_mappings.sql first")
        return False

def parse_campaigns_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse the Campaigns.txt file"""
    campaigns = []
    skipped = 0
    
    logger.info(f"Parsing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        
        for row_num, row in enumerate(reader, start=2):
            try:
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
                logger.debug(f"Error parsing row {row_num}: {e}")
                skipped += 1
                continue
    
    logger.info(f"✅ Parsed {len(campaigns)} valid campaigns ({skipped} rows skipped)")
    return campaigns

def import_campaigns_batch(campaigns: List[Dict[str, Any]], batch_size: int = 500) -> int:
    """Import campaigns in batches"""
    client = SupabaseManager.get_client(use_service_role=True)
    total_imported = 0
    failed_count = 0
    
    total_batches = (len(campaigns) + batch_size - 1) // batch_size
    logger.info(f"Starting import of {len(campaigns)} campaigns in {total_batches} batches...")
    
    for i in range(0, len(campaigns), batch_size):
        batch = campaigns[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            result = client.table('campaigns').insert(batch).execute()
            total_imported += len(batch)
            
            # Progress indicator
            progress = (total_imported / len(campaigns)) * 100
            logger.info(f"Batch {batch_num}/{total_batches}: ✅ {len(batch)} campaigns imported ({progress:.1f}% complete)")
            
            # Small delay to avoid rate limits
            if batch_num < total_batches:
                time.sleep(0.05)
                
        except Exception as e:
            logger.error(f"❌ Batch {batch_num} failed: {str(e)[:100]}...")
            failed_count += len(batch)
            
            # Try individual inserts for failed batch
            recovered = 0
            for campaign in batch:
                try:
                    client.table('campaigns').insert(campaign).execute()
                    recovered += 1
                    total_imported += 1
                except Exception as ind_e:
                    if "duplicate" not in str(ind_e).lower():
                        logger.debug(f"Failed: {campaign['campaign_id']}")
            
            if recovered > 0:
                logger.info(f"  Recovered {recovered}/{len(batch)} campaigns from failed batch")
    
    return total_imported

def get_statistics():
    """Get statistics about imported campaigns"""
    client = SupabaseManager.get_client(use_service_role=True)
    
    try:
        # Total count
        count_result = client.table('campaigns').select('*', count='exact').execute()
        total = len(count_result.data) if count_result.data else 0
        
        # Get state distribution
        all_campaigns = client.table('campaigns').select('state, type, brand').execute()
        
        if all_campaigns.data:
            state_counts = {}
            type_counts = {}
            brand_counts = {}
            
            for item in all_campaigns.data:
                # State distribution
                state = item['state'] or 'UNKNOWN'
                state_counts[state] = state_counts.get(state, 0) + 1
                
                # Type distribution
                camp_type = item['type'] or 'UNKNOWN'
                type_counts[camp_type] = type_counts.get(camp_type, 0) + 1
                
                # Brand distribution
                brand = item['brand'] or 'UNKNOWN'
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            logger.info(f"\n📊 IMPORT STATISTICS")
            logger.info(f"{'='*40}")
            logger.info(f"Total Campaigns: {total:,}")
            
            logger.info(f"\n📈 Campaign States:")
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (count / total) * 100
                logger.info(f"  {state:15} {count:6,} ({percentage:5.1f}%)")
            
            logger.info(f"\n📈 Campaign Types:")
            for camp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                logger.info(f"  {camp_type:15} {count:6,} ({percentage:5.1f}%)")
            
            logger.info(f"\n📈 Top 10 Brands:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / total) * 100
                display_brand = brand[:30] + '...' if len(brand) > 30 else brand
                logger.info(f"  {display_brand:30} {count:6,} ({percentage:5.1f}%)")
        
        return total
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return 0

def main():
    """Main import process"""
    logger.info("="*60)
    logger.info("🚀 CAMPAIGNS IMPORT (AFTER DROPPING campaign_mappings)")
    logger.info("="*60)
    
    # Step 1: Check tables
    logger.info("\n📌 Step 1: Checking database state...")
    if not check_table_ready():
        logger.error("\n❌ Database is not ready. Please run the SQL first.")
        return False
    
    # Step 2: Parse file
    logger.info("\n📌 Step 2: Parsing Campaigns.txt...")
    file_path = '/root/amazon-helper/scripts/Campaigns.txt'
    
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return False
    
    campaigns = parse_campaigns_file(file_path)
    if not campaigns:
        logger.error("❌ No valid campaigns found")
        return False
    
    # Step 3: Import data
    logger.info(f"\n📌 Step 3: Importing {len(campaigns):,} campaigns...")
    imported = import_campaigns_batch(campaigns)
    
    # Step 4: Show statistics
    logger.info("\n📌 Step 4: Verifying import...")
    total_in_db = get_statistics()
    
    # Final summary
    logger.info("\n" + "="*60)
    if imported == len(campaigns):
        logger.info("🎉 IMPORT COMPLETED SUCCESSFULLY!")
        logger.info(f"✅ All {imported:,} campaigns imported")
    else:
        logger.info("⚠️  IMPORT COMPLETED WITH SOME ISSUES")
        logger.info(f"📊 Imported {imported:,} out of {len(campaigns):,} campaigns")
    
    logger.info(f"📊 Total in database: {total_in_db:,}")
    logger.info("="*60)
    
    return imported > 0

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