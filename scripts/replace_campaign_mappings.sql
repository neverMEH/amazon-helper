
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
