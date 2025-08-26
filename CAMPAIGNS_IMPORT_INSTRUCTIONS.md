# Campaigns Import Instructions

## Step 1: Create the Campaigns Table

Go to Supabase SQL Editor:
https://loqaorroihxfkjvcrkdv.supabase.co/project/loqaorroihxfkjvcrkdv/sql/new

Copy and paste this SQL, then click "Run":

```sql
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

-- Add RLS policies (Row Level Security) - Optional
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Policy to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "campaigns_all_policy" ON campaigns
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Add comments
COMMENT ON TABLE campaigns IS 'Stores Amazon advertising campaign data imported from Campaigns.txt';
```

## Step 2: Run the Import Script

After creating the table, run:

```bash
python scripts/campaigns_import_complete.py
```

This will:
1. Parse all 26,661 campaigns from Campaigns.txt
2. Import them in batches of 500
3. Verify the import was successful
4. Show statistics about the imported data

## File Information

- **Source File**: `/root/amazon-helper/Campaigns.txt`
- **Size**: 2.9MB
- **Rows**: 26,661 (including header)
- **Format**: Tab-separated values (TSV)
- **Columns**:
  - CAMPAIGN_ID
  - PORTFOLIO_ID
  - TYPE (sp, sb, sd)
  - TARGETING_TYPE (AUTO, MANUAL)
  - BIDDING_STRATEGY
  - STATE (ENABLED, PAUSED, ARCHIVED)
  - NAME
  - BRAND

## Verification

After import, you can verify the data with these SQL queries:

```sql
-- Total count
SELECT COUNT(*) FROM campaigns;

-- Distribution by state
SELECT state, COUNT(*) as count 
FROM campaigns 
GROUP BY state 
ORDER BY count DESC;

-- Distribution by brand
SELECT brand, COUNT(*) as count 
FROM campaigns 
GROUP BY brand 
ORDER BY count DESC 
LIMIT 10;

-- Sample data
SELECT * FROM campaigns LIMIT 10;
```

## Troubleshooting

If the import fails:

1. **Table doesn't exist**: Make sure you ran the CREATE TABLE SQL in Step 1
2. **Permission errors**: Make sure you're using the service role key in .env
3. **Duplicate key errors**: The campaign_id has a UNIQUE constraint - run the delete query first if re-importing
4. **Connection errors**: Check your Supabase URL and keys in .env file

To delete all data and re-import:
```sql
DELETE FROM campaigns;
```

## Success Criteria

The import is successful when:
- ✅ All 26,661 rows (minus header) are imported
- ✅ No duplicate campaign_ids exist
- ✅ All columns are properly populated
- ✅ Indexes are created for fast queries