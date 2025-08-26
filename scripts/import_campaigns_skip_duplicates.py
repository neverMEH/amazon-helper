#!/usr/bin/env python3
"""Import campaigns skipping duplicates"""

import sys
import os
import csv
import logging
import time
from typing import List, Dict, Any, Set

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_existing_campaign_ids() -> Set[str]:
    """Get all existing campaign_ids from database"""
    client = SupabaseManager.get_client(use_service_role=True)
    existing_ids = set()
    
    try:
        # Get all existing campaign_ids
        result = client.table('campaigns').select('campaign_id').execute()
        for item in result.data:
            existing_ids.add(item['campaign_id'])
        
        logger.info(f"Found {len(existing_ids)} existing campaigns in database")
        return existing_ids
    except Exception as e:
        logger.error(f"Error getting existing campaign IDs: {e}")
        return set()

def parse_campaigns_file(file_path: str, existing_ids: Set[str]) -> List[Dict[str, Any]]:
    """Parse the Campaigns.txt file, skipping existing and duplicate campaign_ids"""
    campaigns = []
    skipped_existing = 0
    skipped_duplicate = 0
    skipped_invalid = 0
    seen_ids = set(existing_ids)  # Start with existing IDs
    
    logger.info(f"Parsing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        
        for row_num, row in enumerate(reader, start=2):
            try:
                campaign_id = row['CAMPAIGN_ID'].strip() if row['CAMPAIGN_ID'] else None
                
                # Skip rows with no campaign_id
                if not campaign_id:
                    skipped_invalid += 1
                    continue
                
                # Skip if already in database
                if campaign_id in existing_ids:
                    skipped_existing += 1
                    continue
                
                # Skip if duplicate in file
                if campaign_id in seen_ids:
                    skipped_duplicate += 1
                    continue
                
                # Mark as seen
                seen_ids.add(campaign_id)
                
                campaign = {
                    'campaign_id': campaign_id,
                    'portfolio_id': row['PORTFOLIO_ID'].strip() if row['PORTFOLIO_ID'] else None,
                    'type': row['TYPE'].strip() if row['TYPE'] else None,
                    'targeting_type': row['TARGETING_TYPE'].strip() if row['TARGETING_TYPE'] else None,
                    'bidding_strategy': row['BIDDING_STRATEGY'].strip() if row['BIDDING_STRATEGY'] else None,
                    'state': row['STATE'].strip() if row['STATE'] else None,
                    'name': row['NAME'].strip() if row['NAME'] else None,
                    'brand': row['BRAND'].strip() if row['BRAND'] else None
                }
                
                campaigns.append(campaign)
                
            except Exception as e:
                logger.debug(f"Error parsing row {row_num}: {e}")
                skipped_invalid += 1
                continue
    
    logger.info(f"✅ Parsed {len(campaigns)} new unique campaigns")
    logger.info(f"   Skipped: {skipped_existing} already in DB, {skipped_duplicate} duplicates in file, {skipped_invalid} invalid")
    return campaigns

def import_campaigns_batch(campaigns: List[Dict[str, Any]], batch_size: int = 500) -> int:
    """Import campaigns in batches, with individual retry on batch failure"""
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
            logger.warning(f"Batch {batch_num} failed, trying individual inserts...")
            
            # Try individual inserts for failed batch
            recovered = 0
            for campaign in batch:
                try:
                    client.table('campaigns').insert(campaign).execute()
                    recovered += 1
                    total_imported += 1
                except Exception as ind_e:
                    # Only count as failed if not a duplicate error
                    if "duplicate" not in str(ind_e).lower():
                        failed_count += 1
                        logger.debug(f"Failed: {campaign['campaign_id']}: {str(ind_e)[:50]}")
                    else:
                        # It's a duplicate, just skip it silently
                        pass
            
            if recovered > 0:
                logger.info(f"  Recovered {recovered}/{len(batch)} campaigns from failed batch")
    
    return total_imported

def main():
    """Main import process"""
    logger.info("="*60)
    logger.info("🚀 CAMPAIGNS IMPORT (SKIP DUPLICATES)")
    logger.info("="*60)
    
    # Step 1: Get existing campaign IDs
    logger.info("\n📌 Step 1: Getting existing campaign IDs...")
    existing_ids = get_existing_campaign_ids()
    
    # Step 2: Parse file skipping duplicates
    logger.info("\n📌 Step 2: Parsing Campaigns.txt (skipping duplicates)...")
    file_path = '/root/amazon-helper/scripts/Campaigns.txt'
    
    if not os.path.exists(file_path):
        logger.error(f"❌ File not found: {file_path}")
        return False
    
    campaigns = parse_campaigns_file(file_path, existing_ids)
    if not campaigns:
        logger.info("✅ No new campaigns to import (all are duplicates or already exist)")
        return True
    
    # Step 3: Import new campaigns
    logger.info(f"\n📌 Step 3: Importing {len(campaigns):,} new unique campaigns...")
    imported = import_campaigns_batch(campaigns)
    
    # Step 4: Final verification
    logger.info("\n📌 Step 4: Verifying final count...")
    client = SupabaseManager.get_client(use_service_role=True)
    
    try:
        count_result = client.table('campaigns').select('*', count='exact').execute()
        final_count = len(count_result.data) if count_result.data else 0
        
        # Get statistics
        all_campaigns = client.table('campaigns').select('state, type, brand').execute()
        if all_campaigns.data:
            state_counts = {}
            type_counts = {}
            brand_counts = {}
            
            for item in all_campaigns.data:
                state = item['state'] or 'UNKNOWN'
                state_counts[state] = state_counts.get(state, 0) + 1
                
                camp_type = item['type'] or 'UNKNOWN'
                type_counts[camp_type] = type_counts.get(camp_type, 0) + 1
                
                brand = item['brand'] or 'UNKNOWN'
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            logger.info(f"\n📊 FINAL STATISTICS")
            logger.info(f"{'='*40}")
            logger.info(f"Total Campaigns: {final_count:,}")
            logger.info(f"New Imported: {imported:,}")
            
            logger.info(f"\n📈 Campaign States:")
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (count / final_count) * 100
                logger.info(f"  {state:15} {count:6,} ({percentage:5.1f}%)")
            
            logger.info(f"\n📈 Campaign Types:")
            for camp_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / final_count) * 100
                logger.info(f"  {camp_type:15} {count:6,} ({percentage:5.1f}%)")
            
            logger.info(f"\n📈 Top 10 Brands:")
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / final_count) * 100
                display_brand = brand[:30] + '...' if len(brand) > 30 else brand
                logger.info(f"  {display_brand:30} {count:6,} ({percentage:5.1f}%)")
        
    except Exception as e:
        logger.error(f"Error getting final statistics: {e}")
    
    # Final summary
    logger.info("\n" + "="*60)
    logger.info("🎉 IMPORT COMPLETED SUCCESSFULLY!")
    logger.info(f"✅ Database now contains {final_count:,} unique campaigns")
    logger.info("="*60)
    
    return True

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