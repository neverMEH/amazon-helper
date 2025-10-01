# Database Schema - Instance Parameter Mapping

## Overview

This feature requires two new tables to store instance-level ASIN and campaign associations. The existing `instance_brands` table will be reused for brand associations.

## Schema Changes

### 1. Reuse Existing Table: `instance_brands`

**Status**: Already exists (see `database/supabase/migrations/02_instance_brands.sql`)

**Purpose**: Store brand associations for each instance

**Schema**:
```sql
CREATE TABLE instance_brands (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    brand_tag TEXT NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(instance_id, brand_tag)
);
```

**No Changes Required**: This table already supports our use case.

### 2. New Table: `instance_brand_asins`

**Purpose**: Store which ASINs are included for each brand-instance combination

**Rationale**:
- Allows brand-level ASIN filtering (user selects brand, sees ASINs, unchecks unwanted ones)
- Stores only included ASINs (exclusion approach: all ASINs under a brand are included by default)
- Junction table pattern: instance + brand + ASIN

**Schema**:
```sql
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

-- RLS policies
ALTER TABLE instance_brand_asins ENABLE ROW LEVEL SECURITY;

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

-- Updated_at trigger
CREATE TRIGGER update_instance_brand_asins_updated_at
    BEFORE UPDATE ON instance_brand_asins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Table comment
COMMENT ON TABLE instance_brand_asins IS 'Stores included ASINs for each brand-instance combination';
COMMENT ON COLUMN instance_brand_asins.brand_tag IS 'Brand identifier from product_asins.brand or brand_configurations.brand_tag';
COMMENT ON COLUMN instance_brand_asins.asin IS 'ASIN from product_asins table';
```

### 3. New Table: `instance_brand_campaigns`

**Purpose**: Store which campaigns are included for each brand-instance combination

**Rationale**:
- Allows brand-level campaign filtering (user selects brand, sees campaigns, unchecks unwanted ones)
- Stores only included campaigns (exclusion approach: all campaigns under a brand are included by default)
- Junction table pattern: instance + brand + campaign

**Schema**:
```sql
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

-- RLS policies
ALTER TABLE instance_brand_campaigns ENABLE ROW LEVEL SECURITY;

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

-- Updated_at trigger
CREATE TRIGGER update_instance_brand_campaigns_updated_at
    BEFORE UPDATE ON instance_brand_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Table comment
COMMENT ON TABLE instance_brand_campaigns IS 'Stores included campaigns for each brand-instance combination';
COMMENT ON COLUMN instance_brand_campaigns.brand_tag IS 'Brand identifier from campaign_mappings.brand_tag';
COMMENT ON COLUMN instance_brand_campaigns.campaign_id IS 'Campaign ID from campaign_mappings table';
```

### 4. Update Existing Table: `product_asins`

**Purpose**: Ensure brand field exists and is indexed for efficient filtering

**Current Schema** (from `scripts/migrations/001_create_asin_tables.sql`):
```sql
CREATE TABLE IF NOT EXISTS product_asins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin VARCHAR(20) NOT NULL,
    title TEXT,
    brand VARCHAR(255),  -- ✓ Already exists
    -- ... other fields
);

-- ✓ Index already exists
CREATE INDEX IF NOT EXISTS idx_asins_brand ON product_asins(brand) WHERE active = true;
```

**No Changes Required**: The `brand` column and index already exist.

### 5. Update Existing Table: `campaign_mappings`

**Purpose**: Ensure brand_tag field exists for brand-based filtering

**Current Schema** (from `database/supabase/schema/01_tables.sql`):
```sql
CREATE TABLE campaign_mappings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id BIGINT NOT NULL,
    campaign_name TEXT NOT NULL,
    brand_tag TEXT,  -- ✓ Already exists
    -- ... other fields
);
```

**Additional Index Needed**:
```sql
-- Add index for efficient brand-based filtering
CREATE INDEX IF NOT EXISTS idx_campaign_mappings_brand_tag
    ON campaign_mappings(brand_tag)
    WHERE brand_tag IS NOT NULL;
```

**Rationale**: Speeds up queries that filter campaigns by brand_tag.

## Migration Script

**File**: `database/supabase/migrations/04_instance_parameter_mapping.sql`

```sql
-- Migration: Instance Parameter Mapping Tables
-- Creates tables for storing instance-level ASIN and campaign associations

BEGIN;

-- 1. Create instance_brand_asins table
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

CREATE INDEX idx_instance_brand_asins_instance ON instance_brand_asins(instance_id);
CREATE INDEX idx_instance_brand_asins_brand ON instance_brand_asins(brand_tag);
CREATE INDEX idx_instance_brand_asins_asin ON instance_brand_asins(asin);
CREATE INDEX idx_instance_brand_asins_composite ON instance_brand_asins(instance_id, brand_tag);

ALTER TABLE instance_brand_asins ENABLE ROW LEVEL SECURITY;

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

CREATE TRIGGER update_instance_brand_asins_updated_at
    BEFORE UPDATE ON instance_brand_asins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instance_brand_asins IS 'Stores included ASINs for each brand-instance combination';

-- 2. Create instance_brand_campaigns table
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

CREATE INDEX idx_instance_brand_campaigns_instance ON instance_brand_campaigns(instance_id);
CREATE INDEX idx_instance_brand_campaigns_brand ON instance_brand_campaigns(brand_tag);
CREATE INDEX idx_instance_brand_campaigns_campaign ON instance_brand_campaigns(campaign_id);
CREATE INDEX idx_instance_brand_campaigns_composite ON instance_brand_campaigns(instance_id, brand_tag);

ALTER TABLE instance_brand_campaigns ENABLE ROW LEVEL SECURITY;

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

CREATE TRIGGER update_instance_brand_campaigns_updated_at
    BEFORE UPDATE ON instance_brand_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instance_brand_campaigns IS 'Stores included campaigns for each brand-instance combination';

-- 3. Add index for campaign_mappings.brand_tag (performance optimization)
CREATE INDEX IF NOT EXISTS idx_campaign_mappings_brand_tag
    ON campaign_mappings(brand_tag)
    WHERE brand_tag IS NOT NULL;

COMMIT;
```

## Data Relationships

### Entity Relationship Diagram

```
amc_instances (1) ──────< (M) instance_brands
                                      │
                                      │ brand_tag
                                      ├──────────────┐
                                      │              │
                                      ▼              ▼
amc_instances (1) ──< (M) instance_brand_asins    instance_brand_campaigns (M) >── (1) amc_instances
                            │                            │
                            │ asin                       │ campaign_id
                            ▼                            ▼
                      product_asins                 campaign_mappings
                      (brand field)                 (brand_tag field)
```

### Query Patterns

#### 1. Fetch Instance Mappings
```sql
-- Get all brands for an instance
SELECT brand_tag
FROM instance_brands
WHERE instance_id = $1;

-- Get all ASINs for an instance (grouped by brand)
SELECT iba.brand_tag, pa.asin, pa.title, pa.brand
FROM instance_brand_asins iba
JOIN product_asins pa ON iba.asin = pa.asin
WHERE iba.instance_id = $1
ORDER BY iba.brand_tag, pa.title;

-- Get all campaigns for an instance (grouped by brand)
SELECT ibc.brand_tag, cm.campaign_id, cm.campaign_name, cm.campaign_type
FROM instance_brand_campaigns ibc
JOIN campaign_mappings cm ON ibc.campaign_id = cm.campaign_id
WHERE ibc.instance_id = $1
ORDER BY ibc.brand_tag, cm.campaign_name;
```

#### 2. Fetch Available Items for Brand Selection
```sql
-- Get all ASINs for a specific brand
SELECT asin, title, brand
FROM product_asins
WHERE brand = $1 AND active = true
ORDER BY title;

-- Get all campaigns for a specific brand
SELECT campaign_id, campaign_name, campaign_type
FROM campaign_mappings
WHERE brand_tag = $1 AND user_id = $2
ORDER BY campaign_name;
```

#### 3. Save Instance Mappings (Transactional)
```sql
BEGIN;

-- Delete existing mappings
DELETE FROM instance_brands WHERE instance_id = $1;
DELETE FROM instance_brand_asins WHERE instance_id = $1;
DELETE FROM instance_brand_campaigns WHERE instance_id = $1;

-- Insert new brand associations
INSERT INTO instance_brands (instance_id, brand_tag, user_id)
VALUES
    ($1, 'brand1', $2),
    ($1, 'brand2', $2);

-- Insert new ASIN associations
INSERT INTO instance_brand_asins (instance_id, brand_tag, asin, user_id)
VALUES
    ($1, 'brand1', 'B001', $2),
    ($1, 'brand1', 'B002', $2),
    ($1, 'brand2', 'B003', $2);

-- Insert new campaign associations
INSERT INTO instance_brand_campaigns (instance_id, brand_tag, campaign_id, user_id)
VALUES
    ($1, 'brand1', 12345, $2),
    ($1, 'brand1', 67890, $2),
    ($1, 'brand2', 11111, $2);

COMMIT;
```

## Performance Considerations

### Index Strategy
- **Composite indexes**: `(instance_id, brand_tag)` for fast brand-level queries
- **Single-column indexes**: On foreign keys and frequently filtered columns
- **Partial indexes**: On `campaign_mappings.brand_tag` (WHERE NOT NULL) to save space

### Query Optimization
- Use JOINs instead of multiple SELECT queries
- Batch INSERTs for saving mappings (single transaction)
- Leverage RLS policies for security without application-level filtering

### Estimated Table Sizes
- **instance_brands**: ~50 rows per instance × 100 instances = 5,000 rows
- **instance_brand_asins**: ~100 ASINs per brand × 5 brands per instance × 100 instances = 50,000 rows
- **instance_brand_campaigns**: ~20 campaigns per brand × 5 brands per instance × 100 instances = 10,000 rows

**Total storage impact**: <5MB for typical deployment

## Rollback Plan

If migration fails or needs to be reverted:

```sql
BEGIN;

DROP TABLE IF EXISTS instance_brand_campaigns CASCADE;
DROP TABLE IF EXISTS instance_brand_asins CASCADE;
DROP INDEX IF EXISTS idx_campaign_mappings_brand_tag;

COMMIT;
```

**Note**: `instance_brands` table is not dropped as it was created in a previous migration and may have other dependencies.
