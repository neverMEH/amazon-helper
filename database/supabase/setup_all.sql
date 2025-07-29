-- Master setup script for Amazon AMC Manager Supabase Database
-- Run this file in Supabase SQL Editor to set up everything at once

-- ============================================
-- STEP 1: Create Tables
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table with RLS
CREATE TABLE users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    amazon_customer_id TEXT UNIQUE,
    auth_tokens JSONB,
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    profile_ids JSONB DEFAULT '[]',
    marketplace_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AMC accounts table
CREATE TABLE amc_accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id TEXT UNIQUE NOT NULL,
    account_name TEXT NOT NULL,
    marketplace_id TEXT NOT NULL,
    region TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AMC instances tracking
CREATE TABLE amc_instances (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id TEXT UNIQUE NOT NULL,
    instance_name TEXT NOT NULL,
    region TEXT NOT NULL,
    endpoint_url TEXT,
    account_id UUID REFERENCES amc_accounts(id) ON DELETE CASCADE NOT NULL,
    status TEXT DEFAULT 'active',
    capabilities JSONB DEFAULT '{}',
    data_upload_account_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brand configurations with ASIN associations
CREATE TABLE brand_configurations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    brand_tag TEXT UNIQUE NOT NULL,
    brand_name TEXT NOT NULL,
    description TEXT,
    yaml_parameters TEXT,
    default_parameters JSONB DEFAULT '{}',
    primary_asins JSONB DEFAULT '[]',
    all_asins JSONB DEFAULT '[]',
    campaign_name_patterns JSONB DEFAULT '[]',
    owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    shared_with_users JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign mappings with brand and ASIN tracking
CREATE TABLE campaign_mappings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id BIGINT NOT NULL,
    campaign_name TEXT NOT NULL,
    original_name TEXT NOT NULL,
    campaign_type TEXT NOT NULL,
    marketplace_id TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    account_id UUID REFERENCES amc_accounts(id),
    brand_tag TEXT,
    brand_metadata JSONB DEFAULT '{}',
    asins JSONB DEFAULT '[]',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    first_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    name_history JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    custom_parameters JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(campaign_id, marketplace_id)
);

-- Workflows
CREATE TABLE workflows (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    instance_id UUID REFERENCES amc_instances(id) NOT NULL,
    sql_query TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    status TEXT DEFAULT 'active',
    is_template BOOLEAN DEFAULT false,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    execution_id TEXT UNIQUE NOT NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    execution_parameters JSONB DEFAULT '{}',
    output_location TEXT,
    row_count INTEGER,
    size_bytes BIGINT,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    triggered_by TEXT,
    schedule_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow schedules
CREATE TABLE workflow_schedules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id TEXT UNIQUE NOT NULL,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE NOT NULL,
    cron_expression TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC' NOT NULL,
    default_parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query templates
CREATE TABLE query_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    sql_template TEXT NOT NULL,
    parameters_schema JSONB NOT NULL,
    default_parameters JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    is_public BOOLEAN DEFAULT false,
    tags JSONB DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AMC query results cache
CREATE TABLE amc_query_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    query_hash VARCHAR(64),
    query_text TEXT,
    result_data JSONB,
    execution_timestamp TIMESTAMP WITH TIME ZONE,
    row_count INTEGER,
    brand_tag TEXT,
    instance_id UUID REFERENCES amc_instances(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_campaign_user_brand ON campaign_mappings(user_id, brand_tag);
CREATE INDEX idx_campaign_type ON campaign_mappings(campaign_type);
CREATE INDEX idx_campaign_name ON campaign_mappings(campaign_name);
CREATE INDEX idx_campaign_account ON campaign_mappings(account_id);
CREATE INDEX idx_campaign_asins ON campaign_mappings USING GIN (asins);
CREATE INDEX idx_brand_owner ON brand_configurations(owner_user_id);
CREATE INDEX idx_brand_asins ON brand_configurations USING GIN (all_asins);
CREATE INDEX idx_workflow_user_instance ON workflows(user_id, instance_id);
CREATE INDEX idx_workflow_status ON workflows(status);
CREATE INDEX idx_execution_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_execution_status ON workflow_executions(status);
CREATE INDEX idx_execution_started ON workflow_executions(started_at);
CREATE INDEX idx_schedule_workflow ON workflow_schedules(workflow_id);
CREATE INDEX idx_schedule_active ON workflow_schedules(is_active);
CREATE INDEX idx_instance_account ON amc_instances(account_id);
CREATE INDEX idx_account_user ON amc_accounts(user_id);
CREATE INDEX idx_query_hash ON amc_query_results(query_hash);
CREATE INDEX idx_query_timestamp ON amc_query_results(execution_timestamp);
CREATE INDEX idx_query_brand ON amc_query_results(brand_tag);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_amc_accounts_updated_at BEFORE UPDATE ON amc_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_amc_instances_updated_at BEFORE UPDATE ON amc_instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaign_mappings_updated_at BEFORE UPDATE ON campaign_mappings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_brand_configurations_updated_at BEFORE UPDATE ON brand_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_schedules_updated_at BEFORE UPDATE ON workflow_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_query_templates_updated_at BEFORE UPDATE ON query_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- STEP 2: Enable Row Level Security
-- ============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_query_results ENABLE ROW LEVEL SECURITY;

-- ============================================
-- STEP 3: Create RLS Policies
-- ============================================

-- Users policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Service role can manage all users" ON users
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- AMC Accounts policies
CREATE POLICY "Users can view own accounts" ON amc_accounts
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own accounts" ON amc_accounts
    FOR ALL USING (auth.uid() = user_id);

-- AMC Instances policies
CREATE POLICY "Users can view instances for their accounts" ON amc_instances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM amc_accounts 
            WHERE amc_accounts.id = amc_instances.account_id 
            AND amc_accounts.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can manage instances for their accounts" ON amc_instances
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM amc_accounts 
            WHERE amc_accounts.id = amc_instances.account_id 
            AND amc_accounts.user_id = auth.uid()
        )
    );

-- Campaign mappings policies
CREATE POLICY "Users can view own campaigns" ON campaign_mappings
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own campaigns" ON campaign_mappings
    FOR ALL USING (auth.uid() = user_id);

-- Brand configurations policies
CREATE POLICY "Users can view own or shared brands" ON brand_configurations
    FOR SELECT USING (
        auth.uid() = owner_user_id OR 
        shared_with_users::jsonb ? auth.uid()::text
    );
CREATE POLICY "Only owners can insert brands" ON brand_configurations
    FOR INSERT WITH CHECK (auth.uid() = owner_user_id);
CREATE POLICY "Only owners can update brands" ON brand_configurations
    FOR UPDATE USING (auth.uid() = owner_user_id);
CREATE POLICY "Only owners can delete brands" ON brand_configurations
    FOR DELETE USING (auth.uid() = owner_user_id);

-- Workflows policies
CREATE POLICY "Users can view own workflows" ON workflows
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own workflows" ON workflows
    FOR ALL USING (auth.uid() = user_id);

-- Workflow executions policies
CREATE POLICY "Users can view executions for their workflows" ON workflow_executions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_executions.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );
CREATE POLICY "Users can manage executions for their workflows" ON workflow_executions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_executions.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );

-- Other policies...
-- (Continue with remaining policies from 02_rls_policies.sql)

-- ============================================
-- STEP 4: Create Utility Functions
-- ============================================

-- Get campaigns by ASINs
CREATE OR REPLACE FUNCTION get_campaigns_by_asins(
    user_id_param UUID,
    asin_list TEXT[]
)
RETURNS TABLE (
    campaign_id BIGINT,
    campaign_name TEXT,
    brand_tag TEXT,
    matching_asins TEXT[],
    campaign_type TEXT,
    marketplace_id TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.campaign_id,
        cm.campaign_name,
        cm.brand_tag,
        ARRAY(
            SELECT jsonb_array_elements_text(cm.asins) 
            INTERSECT 
            SELECT unnest(asin_list)
        ) as matching_asins,
        cm.campaign_type,
        cm.marketplace_id
    FROM campaign_mappings cm
    WHERE cm.user_id = user_id_param
        AND cm.asins::jsonb ?| asin_list;
END;
$$;

-- (Continue with remaining functions from 01_utility_functions.sql)

-- ============================================
-- VERIFICATION
-- ============================================

-- Verify tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verify RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;