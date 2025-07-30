-- Performance optimization indexes for AMC application
-- These indexes will significantly improve query performance

-- Index on amc_instances for faster lookups by instance_id
CREATE INDEX IF NOT EXISTS idx_amc_instances_instance_id 
ON amc_instances(instance_id);

-- Index on amc_instances for faster account_id lookups
CREATE INDEX IF NOT EXISTS idx_amc_instances_account_id 
ON amc_instances(account_id);

-- Index on amc_instances for status filtering
CREATE INDEX IF NOT EXISTS idx_amc_instances_status 
ON amc_instances(status);

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_amc_instances_account_status 
ON amc_instances(account_id, status);

-- Index on workflows for instance lookups
CREATE INDEX IF NOT EXISTS idx_workflows_instance_id 
ON workflows(instance_id);

-- Index on workflows for status filtering
CREATE INDEX IF NOT EXISTS idx_workflows_status 
ON workflows(status);

-- Composite index for workflow stats calculation
CREATE INDEX IF NOT EXISTS idx_workflows_instance_status 
ON workflows(instance_id, status);

-- Index on instance_brands for faster lookups
CREATE INDEX IF NOT EXISTS idx_instance_brands_instance_id 
ON instance_brands(instance_id);

-- Index on campaign_mappings for user lookups
CREATE INDEX IF NOT EXISTS idx_campaign_mappings_user_id 
ON campaign_mappings(user_id);

-- Index on campaign_mappings for brand filtering
CREATE INDEX IF NOT EXISTS idx_campaign_mappings_brand_tag 
ON campaign_mappings(brand_tag);

-- Analyze tables to update statistics
ANALYZE amc_instances;
ANALYZE workflows;
ANALYZE instance_brands;
ANALYZE campaign_mappings;
ANALYZE amc_accounts;