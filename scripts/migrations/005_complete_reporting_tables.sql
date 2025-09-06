-- Complete Reporting Tables Setup - Final Migration
-- This ensures all tables exist with the correct structure
-- Safe to run multiple times

BEGIN;

-- =============================================
-- 1. DASHBOARDS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id VARCHAR(255) NOT NULL,
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

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'dashboards_dashboard_id_key'
    ) THEN
        ALTER TABLE dashboards ADD CONSTRAINT dashboards_dashboard_id_key UNIQUE(dashboard_id);
    END IF;
END $$;

-- =============================================
-- 2. DASHBOARD WIDGETS TABLE
-- =============================================
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_dashboard_widget'
    ) THEN
        ALTER TABLE dashboard_widgets ADD CONSTRAINT unique_dashboard_widget UNIQUE(dashboard_id, widget_id);
    END IF;
END $$;

-- =============================================
-- 3. REPORT DATA COLLECTIONS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS report_data_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id VARCHAR(255) NOT NULL,
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

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'report_data_collections_collection_id_key'
    ) THEN
        ALTER TABLE report_data_collections ADD CONSTRAINT report_data_collections_collection_id_key UNIQUE(collection_id);
    END IF;
END $$;

-- =============================================
-- 4. REPORT DATA WEEKS TABLE
-- =============================================
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_collection_week'
    ) THEN
        ALTER TABLE report_data_weeks ADD CONSTRAINT unique_collection_week UNIQUE(collection_id, week_start_date);
    END IF;
END $$;

-- =============================================
-- 5. REPORT DATA AGGREGATES TABLE (NEW STRUCTURE)
-- =============================================

-- Handle existing table with different structure
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_aggregates' 
        AND column_name = 'data_date'
    ) THEN
        -- Old structure exists, rename it
        ALTER TABLE report_data_aggregates RENAME TO report_data_aggregates_old;
        RAISE NOTICE 'Renamed old report_data_aggregates table';
    END IF;
END $$;

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'unique_aggregate'
    ) THEN
        ALTER TABLE report_data_aggregates 
        ADD CONSTRAINT unique_aggregate UNIQUE(workflow_id, instance_id, date_start, date_end, aggregation_type);
    END IF;
END $$;

-- =============================================
-- 6. AI INSIGHTS TABLE
-- =============================================
CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id VARCHAR(255) NOT NULL,
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

-- Add unique constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'ai_insights_insight_id_key'
    ) THEN
        ALTER TABLE ai_insights ADD CONSTRAINT ai_insights_insight_id_key UNIQUE(insight_id);
    END IF;
END $$;

-- =============================================
-- 7. DASHBOARD SHARES TABLE (FIXED)
-- =============================================

-- Drop the old table if it exists with wrong structure
DROP TABLE IF EXISTS dashboard_shares CASCADE;

-- Create with correct structure
CREATE TABLE dashboard_shares (
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
-- 8. CREATE ALL INDEXES
-- =============================================
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
-- 9. CREATE UPDATE TRIGGERS
-- =============================================

-- Ensure the update function exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers (drop first to avoid conflicts)
DROP TRIGGER IF EXISTS update_dashboards_updated_at ON dashboards;
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dashboard_widgets_updated_at ON dashboard_widgets;
CREATE TRIGGER update_dashboard_widgets_updated_at BEFORE UPDATE ON dashboard_widgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_collections_updated_at ON report_data_collections;
CREATE TRIGGER update_report_data_collections_updated_at BEFORE UPDATE ON report_data_collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_weeks_updated_at ON report_data_weeks;
CREATE TRIGGER update_report_data_weeks_updated_at BEFORE UPDATE ON report_data_weeks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_report_data_aggregates_updated_at ON report_data_aggregates;
CREATE TRIGGER update_report_data_aggregates_updated_at BEFORE UPDATE ON report_data_aggregates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_insights_updated_at ON ai_insights;
CREATE TRIGGER update_ai_insights_updated_at BEFORE UPDATE ON ai_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- 10. FINAL VERIFICATION
-- =============================================
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'dashboards',
        'dashboard_widgets',
        'report_data_collections',
        'report_data_weeks',
        'report_data_aggregates',
        'ai_insights',
        'dashboard_shares'
    );
    
    IF table_count = 7 THEN
        RAISE NOTICE '✅ SUCCESS: All 7 reporting tables have been created!';
        RAISE NOTICE 'The Data Collections feature is now ready to use.';
    ELSE
        RAISE EXCEPTION 'ERROR: Only % of 7 tables were created', table_count;
    END IF;
END $$;

COMMIT;

-- =============================================
-- VERIFICATION QUERY
-- =============================================
-- Run this to verify the setup:
/*
SELECT 
    table_name as "Table",
    COUNT(column_name) as "Columns",
    '✅' as "Status"
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN (
    'dashboards',
    'dashboard_widgets',
    'report_data_collections',
    'report_data_weeks',
    'report_data_aggregates',
    'ai_insights',
    'dashboard_shares'
)
GROUP BY table_name
ORDER BY table_name;
*/