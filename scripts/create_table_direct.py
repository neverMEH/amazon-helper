#!/usr/bin/env python3
"""Create campaigns table using direct database connection"""

import sys
import os
import logging
import psycopg2
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_campaigns_table_direct():
    """Create campaigns table using direct PostgreSQL connection"""
    
    # Extract project ID from Supabase URL
    project_id = settings.supabase_url.split('//')[1].split('.')[0]
    
    # Construct PostgreSQL connection string
    # Supabase database URL format: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
    db_url = f"postgresql://postgres.{project_id}:{settings.supabase_service_role_key}@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    logger.info("Attempting to create campaigns table via direct connection...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Create the table
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
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        logger.info("✅ campaigns table created successfully!")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'campaigns'
        """)
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            logger.info("✅ Verified: campaigns table exists in the database!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except ImportError:
        logger.error("psycopg2 is not installed. Installing...")
        os.system("pip install psycopg2-binary")
        logger.info("Please run this script again after installation.")
        return False
        
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        
        # Provide manual instructions as fallback
        logger.info("\n" + "="*60)
        logger.info("📋 MANUAL TABLE CREATION REQUIRED")
        logger.info("="*60)
        logger.info(f"\n1. Go to Supabase SQL Editor:")
        logger.info(f"   https://{project_id}.supabase.co/project/{project_id}/sql/new")
        logger.info("\n2. Copy and run this SQL:")
        
        with open('scripts/create_campaigns_table.sql', 'r') as f:
            logger.info("\n" + f.read())
        
        logger.info("\n3. After creating the table, run:")
        logger.info("   python scripts/import_campaigns.py")
        logger.info("="*60)
        
        return False

if __name__ == "__main__":
    success = create_campaigns_table_direct()
    if success:
        logger.info("\n✅ Table created! Now importing data...")
        # Automatically run import
        os.system("python scripts/import_campaigns.py")