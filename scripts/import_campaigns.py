#!/usr/bin/env python3

import sys
import os
import csv
import logging
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_create_table():
    """Check if campaigns table exists and create if needed."""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # First check if table exists by trying to query it
    try:
        result = client.table('campaigns').select('*').limit(1).execute()
        logger.info("campaigns table exists")
        
        # Get count of existing records
        count_result = client.table('campaigns').select('*', count='exact').execute()
        existing_count = count_result.count if hasattr(count_result, 'count') else 0
        logger.info(f"Existing records in campaigns table: {existing_count}")
        
        # Ask user if they want to clear existing data
        if existing_count > 0:
            response = input(f"Found {existing_count} existing records. Do you want to delete them first? (y/n): ")
            if response.lower() == 'y':
                client.table('campaigns').delete().neq('campaign_id', '0').execute()
                logger.info("Cleared existing campaign data")
        return True
    except Exception as e:
        logger.info(f"Table doesn't exist or error accessing it: {e}")
        
    # Create table if it doesn't exist
    try:
        # Use SQL to create the table
        create_table_sql = """
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
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create indexes for commonly queried fields
        CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id);
        CREATE INDEX IF NOT EXISTS idx_campaigns_portfolio_id ON campaigns(portfolio_id);
        CREATE INDEX IF NOT EXISTS idx_campaigns_brand ON campaigns(brand);
        CREATE INDEX IF NOT EXISTS idx_campaigns_state ON campaigns(state);
        CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(type);
        """
        
        # Note: Supabase client doesn't support direct SQL execution for DDL
        # We'll need to use the apply_migration approach
        logger.error("Cannot create table directly via client. Please create the campaigns table manually or use migrations.")
        return False
        
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False

def import_campaigns():
    """Import campaigns from TSV file into Supabase."""
    client = SupabaseManager.get_client(use_service_role=True)
    
    # Check/create table first
    if not check_and_create_table():
        # Try to proceed anyway - table might exist
        pass
    
    file_path = '/root/amazon-helper/Campaigns.txt'
    
    logger.info(f"Starting import from {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Use csv.DictReader with tab delimiter
            reader = csv.DictReader(file, delimiter='\t')
            
            campaigns = []
            batch_size = 500  # Insert in batches
            total_imported = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because line 1 is header
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
                        logger.warning(f"Skipping row {row_num}: No campaign_id")
                        continue
                    
                    campaigns.append(campaign)
                    
                    # Insert in batches
                    if len(campaigns) >= batch_size:
                        result = client.table('campaigns').insert(campaigns).execute()
                        total_imported += len(campaigns)
                        logger.info(f"Imported batch of {len(campaigns)} campaigns (total: {total_imported})")
                        campaigns = []
                        
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {e}")
                    logger.error(f"Row data: {row}")
                    continue
            
            # Insert remaining campaigns
            if campaigns:
                result = client.table('campaigns').insert(campaigns).execute()
                total_imported += len(campaigns)
                logger.info(f"Imported final batch of {len(campaigns)} campaigns")
            
            logger.info(f"✅ Import completed! Total campaigns imported: {total_imported}")
            
            # Verify import
            count_result = client.table('campaigns').select('*', count='exact').execute()
            db_count = count_result.count if hasattr(count_result, 'count') else 0
            logger.info(f"Total campaigns in database: {db_count}")
            
            # Get some sample data to verify
            sample = client.table('campaigns').select('*').limit(5).execute()
            logger.info(f"Sample of imported data:")
            for item in sample.data[:3]:
                logger.info(f"  - {item['name']} ({item['campaign_id']}) - Brand: {item['brand']}, State: {item['state']}")
            
    except Exception as e:
        logger.error(f"Error during import: {e}")
        raise

if __name__ == "__main__":
    try:
        import_campaigns()
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)