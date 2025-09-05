-- Migration to handle existing tables with different schemas
-- This handles the case where tables exist but with different structures

BEGIN;

-- =============================================
-- 1. Handle report_data_aggregates table
-- =============================================

-- The existing table has a different structure, so we'll rename it and create a new one
DO $$
BEGIN
    -- Check if the old structure exists (has data_date instead of date_start/date_end)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_aggregates' 
        AND column_name = 'data_date'
    ) THEN
        -- Rename the existing table to preserve any data
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'report_data_aggregates_old'
        ) THEN
            ALTER TABLE report_data_aggregates RENAME TO report_data_aggregates_old;
            RAISE NOTICE 'Renamed existing report_data_aggregates to report_data_aggregates_old';
        END IF;
    END IF;
END $$;

-- Now create the new table with the correct structure
CREATE TABLE IF NOT EXISTS report_data_aggregates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    aggregation_type VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL,
    dimensions JSONB DEFAULT '{}',
    data_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_aggregate UNIQUE(workflow_id, instance_id, date_start, date_end, aggregation_type)
);

-- =============================================
-- 2. Create all other tables if they don't exist
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
-- 3. Create indexes safely
-- =============================================

-- Create indexes only if they don't exist
CREATE INDEX IF NOT EXISTS idx_dashboards_user_id ON dashboards(user_id);
CREATE INDEX IF NOT EXISTS idx_dashboards_template_type ON dashboards(template_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_dashboard_id ON dashboard_widgets(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_collections_workflow_id ON report_data_collections(workflow_id);
CREATE INDEX IF NOT EXISTS idx_collections_instance_id ON report_data_collections(instance_id);
CREATE INDEX IF NOT EXISTS idx_collections_user_id ON report_data_collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_status ON report_data_collections(status);
CREATE INDEX IF NOT EXISTS idx_weeks_collection_id ON report_data_weeks(collection_id);
CREATE INDEX IF NOT EXISTS idx_weeks_status ON report_data_weeks(status);
CREATE INDEX IF NOT EXISTS idx_weeks_dates ON report_data_weeks(week_start_date, week_end_date);
CREATE INDEX IF NOT EXISTS idx_aggregates_workflow_instance ON report_data_aggregates(workflow_id, instance_id);
CREATE INDEX IF NOT EXISTS idx_aggregates_dates ON report_data_aggregates(date_start, date_end);
CREATE INDEX IF NOT EXISTS idx_insights_user_id ON ai_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_insights_dashboard_id ON ai_insights(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_shares_dashboard_id ON dashboard_shares(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_shares_shared_with ON dashboard_shares(shared_with);

-- =============================================
-- 4. Create or replace update triggers
-- =============================================

-- Drop and recreate triggers to avoid conflicts
DROP TRIGGER IF EXISTS update_dashboards_updated_at ON dashboards;
CREATE TRIGGER update_dashboards_updated_at
    BEFORE UPDATE ON dashboards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dashboard_widgets_updated_at ON dashboard_widgets;
CREATE TRIGGER update_dashboard_widgets_updated_at
    BEFORE UPDATE ON dashboard_widgets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_collections_updated_at ON report_data_collections;
CREATE TRIGGER update_report_data_collections_updated_at
    BEFORE UPDATE ON report_data_collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_weeks_updated_at ON report_data_weeks;
CREATE TRIGGER update_report_data_weeks_updated_at
    BEFORE UPDATE ON report_data_weeks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_aggregates_updated_at ON report_data_aggregates;
CREATE TRIGGER update_report_data_aggregates_updated_at
    BEFORE UPDATE ON report_data_aggregates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_insights_updated_at ON ai_insights;
CREATE TRIGGER update_ai_insights_updated_at
    BEFORE UPDATE ON ai_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- 5. Verify final state
-- =============================================

DO $$
DECLARE
    missing_tables TEXT := '';
BEGIN
    -- Check each required table
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboards') THEN
        missing_tables := missing_tables || 'dashboards, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboard_widgets') THEN
        missing_tables := missing_tables || 'dashboard_widgets, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_collections') THEN
        missing_tables := missing_tables || 'report_data_collections, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_weeks') THEN
        missing_tables := missing_tables || 'report_data_weeks, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'report_data_aggregates') THEN
        missing_tables := missing_tables || 'report_data_aggregates, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_insights') THEN
        missing_tables := missing_tables || 'ai_insights, ';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dashboard_shares') THEN
        missing_tables := missing_tables || 'dashboard_shares, ';
    END IF;
    
    IF missing_tables != '' THEN
        RAISE EXCEPTION 'Missing tables: %', missing_tables;
    ELSE
        RAISE NOTICE '✅ All reporting tables have been successfully created!';
    END IF;
END $$;

COMMIT;

-- =============================================
-- POST-MIGRATION VERIFICATION
-- =============================================
-- Run this query after the migration to verify everything is set up:

/*
SELECT 
    t.table_name,
    COUNT(c.column_name) as column_count,
    '✅ Created' as status
FROM information_schema.tables t
LEFT JOIN information_schema.columns c 
    ON t.table_name = c.table_name 
    AND t.table_schema = c.table_schema
WHERE t.table_schema = 'public'
AND t.table_name IN (
    'dashboards',
    'dashboard_widgets',
    'report_data_collections',
    'report_data_weeks',
    'report_data_aggregates',
    'ai_insights',
    'dashboard_shares'
)
GROUP BY t.table_name
ORDER BY t.table_name;
*/