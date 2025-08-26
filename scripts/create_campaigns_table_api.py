#!/usr/bin/env python3
"""Create campaigns table using Supabase Database API"""

import sys
import os
import requests
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_table_via_api():
    """Create campaigns table using Supabase Database REST API"""
    
    # Construct the database API URL
    # Extract project ID from URL: https://loqaorroihxfkjvcrkdv.supabase.co
    project_id = settings.supabase_url.split('//')[1].split('.')[0]
    
    # Supabase Database API endpoint for executing SQL
    # This uses the postgres REST API
    api_url = f"{settings.supabase_url}/rest/v1/rpc/exec_sql"
    
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # The SQL to create campaigns table
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
    """
    
    # Unfortunately, Supabase REST API doesn't allow DDL statements
    # Let's try a different approach - using edge functions or database webhooks
    
    logger.info("Attempting to create campaigns table...")
    
    # Alternative: Try using PostgREST directly if available
    # This won't work for DDL but let's check table existence
    check_url = f"{settings.supabase_url}/rest/v1/campaigns"
    
    try:
        response = requests.get(check_url, headers={
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {settings.supabase_anon_key}"
        }, params={"limit": 1})
        
        if response.status_code == 200:
            logger.info("✅ campaigns table already exists!")
            return True
        elif response.status_code == 404 or "relation" in response.text:
            logger.info("Table doesn't exist yet")
            
            # Since we can't create tables via REST API, provide instructions
            logger.info("\n" + "="*60)
            logger.info("📋 CREATING TABLE MANUALLY IS REQUIRED")
            logger.info("="*60)
            logger.info("\n✨ EASY METHOD - Copy & Paste to Supabase Dashboard:")
            logger.info(f"\n1. Click here: https://{project_id}.supabase.co/project/{project_id}/sql/new")
            logger.info("2. Copy the SQL from: scripts/create_campaigns_table.sql")
            logger.info("3. Paste it and click 'Run'")
            logger.info("4. Then run: python scripts/import_campaigns.py")
            logger.info("\n" + "="*60)
            return False
            
    except Exception as e:
        logger.error(f"Error checking table: {e}")
        return False

if __name__ == "__main__":
    success = create_table_via_api()
    if success:
        logger.info("\n✅ Ready to import data!")
        logger.info("Run: python scripts/import_campaigns.py")
    else:
        logger.info("\n⏸️  After creating the table manually, run:")
        logger.info("python scripts/import_campaigns.py")