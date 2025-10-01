-- Migration: Instance Parameter Mapping Tables
-- Creates tables for storing instance-level ASIN and campaign associations
-- This enables brand-based hierarchical parameter management at the instance level

BEGIN;

-- ============================================================================
-- 1. Create instance_brand_asins table
-- ============================================================================
-- Purpose: Store which ASINs are included for each brand-instance combination
-- Pattern: Junction table linking instances → brands → ASINs

CREATE TABLE instance_brand_asins (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    brand_tag TEXT NOT NULL,
    asin TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_instance_brand_asin UNIQUE(instance_id, brand_tag, asin)
);

-- Performance indexes
CREATE INDEX idx_instance_brand_asins_instance ON instance_brand_asins(instance_id);
CREATE INDEX idx_instance_brand_asins_brand ON instance_brand_asins(brand_tag);
CREATE INDEX idx_instance_brand_asins_asin ON instance_brand_asins(asin);
CREATE INDEX idx_instance_brand_asins_composite ON instance_brand_asins(instance_id, brand_tag);

-- Enable Row Level Security
ALTER TABLE instance_brand_asins ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view ASINs for instances they have access to
CREATE POLICY "Users can view instance brand ASINs"
    ON instance_brand_asins FOR SELECT
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_asins.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- RLS Policy: Users can insert ASINs for their own instances
CREATE POLICY "Users can insert instance brand ASINs"
    ON instance_brand_asins FOR INSERT
    WITH CHECK (
        user_id = auth.uid()::uuid AND
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_asins.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- RLS Policy: Users can delete ASINs from their own instances
CREATE POLICY "Users can delete instance brand ASINs"
    ON instance_brand_asins FOR DELETE
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_asins.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- Auto-update trigger for updated_at column
CREATE TRIGGER update_instance_brand_asins_updated_at
    BEFORE UPDATE ON instance_brand_asins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Table documentation
COMMENT ON TABLE instance_brand_asins IS 'Stores included ASINs for each brand-instance combination. Used for auto-populating query parameters.';
COMMENT ON COLUMN instance_brand_asins.brand_tag IS 'Brand identifier from product_asins.brand or brand_configurations.brand_tag';
COMMENT ON COLUMN instance_brand_asins.asin IS 'ASIN from product_asins table';

-- ============================================================================
-- 2. Create instance_brand_campaigns table
-- ============================================================================
-- Purpose: Store which campaigns are included for each brand-instance combination
-- Pattern: Junction table linking instances → brands → campaigns

CREATE TABLE instance_brand_campaigns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    brand_tag TEXT NOT NULL,
    campaign_id BIGINT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_instance_brand_campaign UNIQUE(instance_id, brand_tag, campaign_id)
);

-- Performance indexes
CREATE INDEX idx_instance_brand_campaigns_instance ON instance_brand_campaigns(instance_id);
CREATE INDEX idx_instance_brand_campaigns_brand ON instance_brand_campaigns(brand_tag);
CREATE INDEX idx_instance_brand_campaigns_campaign ON instance_brand_campaigns(campaign_id);
CREATE INDEX idx_instance_brand_campaigns_composite ON instance_brand_campaigns(instance_id, brand_tag);

-- Enable Row Level Security
ALTER TABLE instance_brand_campaigns ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view campaigns for instances they have access to
CREATE POLICY "Users can view instance brand campaigns"
    ON instance_brand_campaigns FOR SELECT
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_campaigns.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- RLS Policy: Users can insert campaigns for their own instances
CREATE POLICY "Users can insert instance brand campaigns"
    ON instance_brand_campaigns FOR INSERT
    WITH CHECK (
        user_id = auth.uid()::uuid AND
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_campaigns.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- RLS Policy: Users can delete campaigns from their own instances
CREATE POLICY "Users can delete instance brand campaigns"
    ON instance_brand_campaigns FOR DELETE
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brand_campaigns.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- Auto-update trigger for updated_at column
CREATE TRIGGER update_instance_brand_campaigns_updated_at
    BEFORE UPDATE ON instance_brand_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Table documentation
COMMENT ON TABLE instance_brand_campaigns IS 'Stores included campaigns for each brand-instance combination. Used for auto-populating query parameters.';
COMMENT ON COLUMN instance_brand_campaigns.brand_tag IS 'Brand identifier from campaign_mappings.brand_tag';
COMMENT ON COLUMN instance_brand_campaigns.campaign_id IS 'Campaign ID from campaign_mappings table';

-- ============================================================================
-- 3. Add index for campaign_mappings.brand_tag (performance optimization)
-- ============================================================================
-- Purpose: Speed up queries that filter campaigns by brand_tag
-- Only index non-null values to save space

CREATE INDEX IF NOT EXISTS idx_campaign_mappings_brand_tag
    ON campaign_mappings(brand_tag)
    WHERE brand_tag IS NOT NULL;

COMMIT;

-- ============================================================================
-- Rollback Instructions
-- ============================================================================
-- If migration needs to be reverted, run:
-- BEGIN;
-- DROP TABLE IF EXISTS instance_brand_campaigns CASCADE;
-- DROP TABLE IF EXISTS instance_brand_asins CASCADE;
-- DROP INDEX IF EXISTS idx_campaign_mappings_brand_tag;
-- COMMIT;
