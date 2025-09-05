-- Safe Migration: Create Reporting Platform Tables
-- Description: Safely adds tables for dashboards, data collection, aggregation, and AI insights
-- Created: 2025-09-05
-- Version: 1.1.0 (Safe version with existence checks)

BEGIN;

-- =============================================
-- 1. CREATE TABLES (IF NOT EXISTS)
-- =============================================

-- Dashboard configurations and metadata
CREATE TABLE IF NOT EXISTS dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(100),
    layout_config JSONB NOT NULL DEFAULT '{}',
    filter_config JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual dashboard widgets
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    widget_id VARCHAR(255) NOT NULL,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(100) NOT NULL,
    chart_type VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    data_source JSONB NOT NULL,
    display_config JSONB DEFAULT '{}',
    position_config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_dashboard_widget UNIQUE(dashboard_id, widget_id)
);

-- Historical data collection for reports
CREATE TABLE IF NOT EXISTS report_data_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id VARCHAR(255) NOT NULL UNIQUE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    collection_type VARCHAR(50) NOT NULL DEFAULT 'backfill',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    target_weeks INTEGER NOT NULL DEFAULT 52,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    weeks_completed INTEGER DEFAULT 0,
    progress_percentage INTEGER DEFAULT 0,
    configuration JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual week execution tracking
CREATE TABLE IF NOT EXISTS report_data_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES report_data_collections(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    amc_execution_id VARCHAR(255),
    data_checksum VARCHAR(64),
    record_count INTEGER,
    execution_time_seconds INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_collection_week UNIQUE(collection_id, week_start_date)
);

-- Pre-computed aggregates for performance
CREATE TABLE IF NOT EXISTS report_data_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    aggregation_type VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL,
    dimensions JSONB DEFAULT '{}',
    data_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_aggregate UNIQUE(workflow_id, instance_id, date_range_start, date_range_end, aggregation_type)
);

-- AI-powered insights storage
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    data_context JSONB NOT NULL,
    ai_model VARCHAR(100),
    confidence_score DECIMAL(3,2),
    is_starred BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dashboard sharing and permissions
CREATE TABLE IF NOT EXISTS dashboard_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    shared_by UUID REFERENCES users(id) ON DELETE CASCADE,
    shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(50) NOT NULL DEFAULT 'view',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_dashboard_share UNIQUE(dashboard_id, shared_with)
);

-- =============================================
-- 2. CREATE INDEXES (IF NOT EXISTS)
-- =============================================

-- Function to create index if it doesn't exist
CREATE OR REPLACE FUNCTION create_index_if_not_exists(
    index_name text,
    table_name text,
    column_list text
) RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = index_name
    ) THEN
        EXECUTE format('CREATE INDEX %I ON %I (%s)', 
            index_name, 
            table_name, 
            column_list
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create indexes using the function
SELECT create_index_if_not_exists('idx_dashboards_user_id', 'dashboards', 'user_id');
SELECT create_index_if_not_exists('idx_dashboards_template_type', 'dashboards', 'template_type');
SELECT create_index_if_not_exists('idx_dashboard_widgets_dashboard_id', 'dashboard_widgets', 'dashboard_id');
SELECT create_index_if_not_exists('idx_collections_workflow_id', 'report_data_collections', 'workflow_id');
SELECT create_index_if_not_exists('idx_collections_instance_id', 'report_data_collections', 'instance_id');
SELECT create_index_if_not_exists('idx_collections_user_id', 'report_data_collections', 'user_id');
SELECT create_index_if_not_exists('idx_collections_status', 'report_data_collections', 'status');
SELECT create_index_if_not_exists('idx_weeks_collection_id', 'report_data_weeks', 'collection_id');
SELECT create_index_if_not_exists('idx_weeks_status', 'report_data_weeks', 'status');
SELECT create_index_if_not_exists('idx_weeks_dates', 'report_data_weeks', 'week_start_date, week_end_date');
SELECT create_index_if_not_exists('idx_aggregates_workflow_instance', 'report_data_aggregates', 'workflow_id, instance_id');
SELECT create_index_if_not_exists('idx_aggregates_dates', 'report_data_aggregates', 'date_range_start, date_range_end');
SELECT create_index_if_not_exists('idx_insights_user_id', 'ai_insights', 'user_id');
SELECT create_index_if_not_exists('idx_insights_dashboard_id', 'ai_insights', 'dashboard_id');
SELECT create_index_if_not_exists('idx_shares_dashboard_id', 'dashboard_shares', 'dashboard_id');
SELECT create_index_if_not_exists('idx_shares_shared_with', 'dashboard_shares', 'shared_with');

-- Drop the helper function
DROP FUNCTION IF EXISTS create_index_if_not_exists(text, text, text);

-- =============================================
-- 3. CREATE TRIGGERS (SAFELY)
-- =============================================

-- Function to safely create or replace triggers
CREATE OR REPLACE FUNCTION create_update_trigger_if_not_exists(
    table_name text
) RETURNS void AS $$
DECLARE
    trigger_name text;
BEGIN
    trigger_name := 'update_' || table_name || '_updated_at';
    
    -- Drop existing trigger if it exists
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', trigger_name, table_name);
    
    -- Create the trigger
    EXECUTE format('
        CREATE TRIGGER %I
        BEFORE UPDATE ON %I
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column()',
        trigger_name, table_name
    );
END;
$$ LANGUAGE plpgsql;

-- Create triggers for all tables
SELECT create_update_trigger_if_not_exists('dashboards');
SELECT create_update_trigger_if_not_exists('dashboard_widgets');
SELECT create_update_trigger_if_not_exists('report_data_collections');
SELECT create_update_trigger_if_not_exists('report_data_weeks');
SELECT create_update_trigger_if_not_exists('report_data_aggregates');
SELECT create_update_trigger_if_not_exists('ai_insights');

-- Drop the helper function
DROP FUNCTION IF EXISTS create_update_trigger_if_not_exists(text);

-- =============================================
-- 4. VERIFY TABLES EXIST
-- =============================================

DO $$
BEGIN
    -- Check if all required tables exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboards') THEN
        RAISE EXCEPTION 'Table dashboards was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboard_widgets') THEN
        RAISE EXCEPTION 'Table dashboard_widgets was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_collections') THEN
        RAISE EXCEPTION 'Table report_data_collections was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_weeks') THEN
        RAISE EXCEPTION 'Table report_data_weeks was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_aggregates') THEN
        RAISE EXCEPTION 'Table report_data_aggregates was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_insights') THEN
        RAISE EXCEPTION 'Table ai_insights was not created';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboard_shares') THEN
        RAISE EXCEPTION 'Table dashboard_shares was not created';
    END IF;
    
    RAISE NOTICE 'All reporting tables have been created or already exist';
END $$;

COMMIT;

-- =============================================
-- VERIFICATION QUERY
-- =============================================
-- Run this separately to verify all tables were created:

/*
SELECT 
    table_name,
    CASE 
        WHEN table_name IS NOT NULL THEN '✅ Created'
        ELSE '❌ Missing'
    END as status
FROM (
    VALUES 
        ('dashboards'),
        ('dashboard_widgets'),
        ('report_data_collections'),
        ('report_data_weeks'),
        ('report_data_aggregates'),
        ('ai_insights'),
        ('dashboard_shares')
) AS required(table_name)
LEFT JOIN information_schema.tables ist 
    ON ist.table_name = required.table_name
    AND ist.table_schema = 'public'
ORDER BY required.table_name;
*/