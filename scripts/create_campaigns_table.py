#!/usr/bin/env python3
"""Create campaigns table in Supabase"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from amc_manager.core.supabase_client import SupabaseManager

# Get Supabase client
client = SupabaseManager.get_client(use_service_role=True)

def create_campaigns_table():
    """Create campaigns table using Supabase SQL"""
    # client is already defined globally
    
    # Check if table exists
    try:
        result = client.table('campaigns').select('*').limit(1).execute()
        print("✓ campaigns table already exists")
        
        # Get count
        count_result = client.table('campaigns').select('*', count='exact').execute()
        count = len(count_result.data) if count_result.data else 0
        print(f"  Current record count: {count}")
        return True
    except Exception as e:
        print(f"campaigns table doesn't exist yet: {e}")
        print("Creating campaigns table...")
        
        # Unfortunately, Supabase Python client doesn't support DDL directly
        # We need to use the SQL editor in Supabase dashboard or use migrations
        print("\n⚠️ Please create the campaigns table using Supabase Dashboard SQL Editor:")
        print("\nCopy and paste the following SQL:")
        print("-" * 60)
        
        sql = """
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
        print(sql)
        print("-" * 60)
        print("\nRun this SQL in Supabase Dashboard:")
        print(f"1. Go to: https://loqaorroihxfkjvcrkdv.supabase.co")
        print("2. Navigate to SQL Editor")
        print("3. Paste the SQL above and click 'Run'")
        print("4. Then run this import script again")
        
        return False

if __name__ == "__main__":
    create_campaigns_table()