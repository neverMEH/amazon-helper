-- Migration to add instance_brands junction table for editable brand tags
-- This allows direct association of brands with AMC instances

-- Create instance_brands junction table
CREATE TABLE instance_brands (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    brand_tag TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(instance_id, brand_tag)
);

-- Create indexes for performance
CREATE INDEX idx_instance_brands_instance ON instance_brands(instance_id);
CREATE INDEX idx_instance_brands_brand ON instance_brands(brand_tag);
CREATE INDEX idx_instance_brands_user ON instance_brands(user_id);

-- Enable Row Level Security
ALTER TABLE instance_brands ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can only see and manage brands for instances they have access to
CREATE POLICY "Users can view instance brands"
    ON instance_brands FOR SELECT
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brands.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

CREATE POLICY "Users can insert instance brands"
    ON instance_brands FOR INSERT
    WITH CHECK (
        user_id = auth.uid()::uuid AND
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brands.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

CREATE POLICY "Users can delete instance brands"
    ON instance_brands FOR DELETE
    USING (
        user_id = auth.uid()::uuid OR
        EXISTS (
            SELECT 1 FROM amc_instances i
            JOIN amc_accounts a ON i.account_id = a.id
            WHERE i.id = instance_brands.instance_id
            AND a.user_id = auth.uid()::uuid
        )
    );

-- Add trigger for updated_at
CREATE TRIGGER update_instance_brands_updated_at 
    BEFORE UPDATE ON instance_brands
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to get all unique brands for a user
CREATE OR REPLACE FUNCTION get_available_brands(p_user_id UUID)
RETURNS TABLE(brand_tag TEXT, brand_name TEXT, source TEXT) AS $$
BEGIN
    RETURN QUERY
    -- Get brands from brand_configurations
    SELECT DISTINCT
        bc.brand_tag,
        bc.brand_name,
        'configuration'::TEXT as source
    FROM brand_configurations bc
    WHERE bc.owner_user_id = p_user_id
        OR p_user_id = ANY(bc.shared_with_users)
    
    UNION
    
    -- Get brands from campaign_mappings
    SELECT DISTINCT
        cm.brand_tag,
        cm.brand_tag as brand_name,  -- Use tag as name if no configuration exists
        'campaign'::TEXT as source
    FROM campaign_mappings cm
    WHERE cm.user_id = p_user_id
        AND cm.brand_tag IS NOT NULL
        AND cm.brand_tag != ''
    
    ORDER BY brand_tag;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to get campaigns filtered by instance brands
CREATE OR REPLACE FUNCTION get_instance_campaigns(p_instance_id UUID, p_user_id UUID)
RETURNS TABLE(
    campaign_id BIGINT,
    campaign_name TEXT,
    campaign_type TEXT,
    brand_tag TEXT,
    marketplace_id TEXT,
    profile_id TEXT,
    asins JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.campaign_id,
        cm.campaign_name,
        cm.campaign_type,
        cm.brand_tag,
        cm.marketplace_id,
        cm.profile_id,
        cm.asins,
        cm.created_at
    FROM campaign_mappings cm
    WHERE cm.user_id = p_user_id
        AND cm.brand_tag IN (
            SELECT ib.brand_tag
            FROM instance_brands ib
            WHERE ib.instance_id = p_instance_id
        )
    ORDER BY cm.campaign_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Migrate existing data: Create initial instance-brand associations based on current campaigns
-- This populates instance_brands with brands that are currently shown (aggregated from campaigns)
INSERT INTO instance_brands (instance_id, brand_tag, user_id)
SELECT DISTINCT
    i.id as instance_id,
    cm.brand_tag,
    cm.user_id
FROM amc_instances i
JOIN amc_accounts a ON i.account_id = a.id
JOIN campaign_mappings cm ON cm.user_id = a.user_id
WHERE cm.brand_tag IS NOT NULL 
    AND cm.brand_tag != ''
    AND NOT EXISTS (
        SELECT 1 FROM instance_brands ib 
        WHERE ib.instance_id = i.id 
        AND ib.brand_tag = cm.brand_tag
    );

-- Add comment to table
COMMENT ON TABLE instance_brands IS 'Junction table for many-to-many relationship between AMC instances and brands';
COMMENT ON COLUMN instance_brands.brand_tag IS 'Brand identifier matching brand_configurations.brand_tag or campaign_mappings.brand_tag';