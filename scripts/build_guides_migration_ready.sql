-- Build Guides Feature - Database Schema
-- This migration creates tables for the Build Guides feature that provides
-- step-by-step tactical guidance for various AMC query use cases

-- Main guides table
CREATE TABLE IF NOT EXISTS build_guides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id TEXT UNIQUE NOT NULL, -- e.g., "guide_creative_asin_impact"
    name TEXT NOT NULL, -- "Creative ASIN Impact Analysis"
    category TEXT NOT NULL, -- "ASIN Analysis", "Performance Deep Dive", etc.
    short_description TEXT, -- Brief summary for list view
    tags JSONB DEFAULT '[]', -- ["ASIN analysis", "Performance deep dive", "On-Amazon conversions"]
    icon TEXT, -- Icon identifier for UI (e.g., "Package", "TrendingUp")
    difficulty_level TEXT DEFAULT 'intermediate', -- "beginner", "intermediate", "advanced"
    estimated_time_minutes INTEGER DEFAULT 30, -- Estimated completion time
    prerequisites JSONB DEFAULT '[]', -- Required data/setup
    is_published BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Guide sections (Introduction, Data Query Instructions, etc.)
CREATE TABLE IF NOT EXISTS build_guide_sections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
    section_id TEXT NOT NULL, -- "introduction", "requirements", "data_query", etc.
    title TEXT NOT NULL,
    content_markdown TEXT, -- Rich markdown content
    display_order INTEGER NOT NULL,
    is_collapsible BOOLEAN DEFAULT true,
    default_expanded BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guide_id, section_id)
);

-- Guide queries (linked to query templates)
CREATE TABLE IF NOT EXISTS build_guide_queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
    query_template_id UUID REFERENCES query_templates(id),
    title TEXT NOT NULL, -- "Exploratory query for campaigns and creative ASINs"
    description TEXT,
    sql_query TEXT NOT NULL,
    parameters_schema JSONB DEFAULT '{}',
    default_parameters JSONB DEFAULT '{}',
    display_order INTEGER NOT NULL,
    query_type TEXT DEFAULT 'main_analysis', -- "exploratory", "main_analysis", "validation"
    expected_columns JSONB, -- Expected result structure for validation
    interpretation_notes TEXT, -- How to interpret the results
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example results for guides
CREATE TABLE IF NOT EXISTS build_guide_examples (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_query_id UUID REFERENCES build_guide_queries(id) ON DELETE CASCADE,
    example_name TEXT NOT NULL,
    sample_data JSONB NOT NULL, -- Sample result data
    interpretation_markdown TEXT, -- How to interpret these results
    insights JSONB DEFAULT '[]', -- Key insights from this example
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Metrics and dimensions definitions for guides
CREATE TABLE IF NOT EXISTS build_guide_metrics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    definition TEXT NOT NULL,
    metric_type TEXT DEFAULT 'metric', -- 'metric' or 'dimension'
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guide_id, metric_name)
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_guide_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'not_started', -- not_started, in_progress, completed
    current_section TEXT,
    completed_sections JSONB DEFAULT '[]',
    executed_queries JSONB DEFAULT '[]', -- Track which queries user has run
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress_percentage INTEGER DEFAULT 0,
    UNIQUE(user_id, guide_id)
);

-- User favorites for guides
CREATE TABLE IF NOT EXISTS user_guide_favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    guide_id UUID REFERENCES build_guides(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, guide_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_guides_published ON build_guides(is_published);
CREATE INDEX IF NOT EXISTS idx_guides_category ON build_guides(category);
CREATE INDEX IF NOT EXISTS idx_guides_display_order ON build_guides(display_order);
CREATE INDEX IF NOT EXISTS idx_guide_sections_guide ON build_guide_sections(guide_id);
CREATE INDEX IF NOT EXISTS idx_guide_sections_order ON build_guide_sections(guide_id, display_order);
CREATE INDEX IF NOT EXISTS idx_guide_queries_guide ON build_guide_queries(guide_id);
CREATE INDEX IF NOT EXISTS idx_guide_queries_order ON build_guide_queries(guide_id, display_order);
CREATE INDEX IF NOT EXISTS idx_guide_examples_query ON build_guide_examples(guide_query_id);
CREATE INDEX IF NOT EXISTS idx_guide_metrics_guide ON build_guide_metrics(guide_id);
CREATE INDEX IF NOT EXISTS idx_user_progress ON user_guide_progress(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_progress_guide ON user_guide_progress(guide_id, status);
CREATE INDEX IF NOT EXISTS idx_user_favorites ON user_guide_favorites(user_id);

-- Add updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_build_guides_updated_at BEFORE UPDATE ON build_guides
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_build_guide_sections_updated_at BEFORE UPDATE ON build_guide_sections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_build_guide_queries_updated_at BEFORE UPDATE ON build_guide_queries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_build_guide_examples_updated_at BEFORE UPDATE ON build_guide_examples
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE build_guides IS 'Main table for Build Guides feature - stores guide metadata and configuration';
COMMENT ON TABLE build_guide_sections IS 'Content sections for each guide with markdown support';
COMMENT ON TABLE build_guide_queries IS 'SQL queries associated with guides, can be executed directly';
COMMENT ON TABLE build_guide_examples IS 'Example results and interpretations for guide queries';
COMMENT ON TABLE build_guide_metrics IS 'Definitions of metrics and dimensions used in guide queries';
COMMENT ON TABLE user_guide_progress IS 'Tracks user progress through guides';
COMMENT ON TABLE user_guide_favorites IS 'User favorites for quick access to guides';