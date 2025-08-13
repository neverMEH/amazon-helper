-- Migration: Create AMC Data Sources Schema Tables
-- Purpose: Store comprehensive AMC schema documentation, field definitions, and query examples
-- Date: 2025-08-13

-- ============================================
-- Table: amc_data_sources
-- ============================================
CREATE TABLE IF NOT EXISTS amc_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id TEXT UNIQUE NOT NULL, -- e.g., 'attributed-events-conversion-time'
    name TEXT NOT NULL, -- Display name
    category TEXT NOT NULL, -- 'DSP Tables', 'Attribution Tables', 'Insights Tables', etc.
    description TEXT,
    data_sources JSONB, -- Array of actual table names in AMC
    version TEXT DEFAULT '1.0.0',
    tags JSONB DEFAULT '[]'::JSONB, -- ['attribution', 'conversion', 'dsp', etc.]
    is_paid_feature BOOLEAN DEFAULT FALSE,
    availability JSONB, -- Geographic coverage, requirements
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(category, '')), 'C')
    ) STORED
);

-- ============================================
-- Table: amc_schema_fields
-- ============================================
CREATE TABLE IF NOT EXISTS amc_schema_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    data_type TEXT NOT NULL, -- STRING, LONG, DECIMAL, BOOLEAN, ARRAY, etc.
    dimension_or_metric TEXT NOT NULL, -- 'Dimension' or 'Metric'
    description TEXT,
    aggregation_threshold TEXT, -- NONE, LOW, MEDIUM, HIGH, VERY_HIGH, INTERNAL
    field_category TEXT, -- Optional grouping within schema
    examples JSONB, -- Array of example values
    field_order INTEGER DEFAULT 0,
    is_nullable BOOLEAN DEFAULT TRUE,
    is_array BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique field names per data source
    UNIQUE(data_source_id, field_name),
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(field_name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B')
    ) STORED
);

-- ============================================
-- Table: amc_query_examples
-- ============================================
CREATE TABLE IF NOT EXISTS amc_query_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    sql_query TEXT NOT NULL,
    category TEXT, -- 'Basic', 'Advanced', 'Performance', 'Attribution', etc.
    use_case TEXT, -- Business use case description
    example_order INTEGER DEFAULT 0,
    parameters JSONB, -- Any parameters used in the query
    expected_output TEXT, -- Description of expected results
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(use_case, '')), 'C')
    ) STORED
);

-- ============================================
-- Table: amc_schema_sections
-- ============================================
CREATE TABLE IF NOT EXISTS amc_schema_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL, -- 'overview', 'concepts', 'best_practices', 'usage_guidelines', etc.
    title TEXT,
    content_markdown TEXT NOT NULL, -- Full markdown content
    section_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique section types per data source
    UNIQUE(data_source_id, section_type)
);

-- ============================================
-- Table: amc_schema_relationships
-- ============================================
CREATE TABLE IF NOT EXISTS amc_schema_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_schema_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    target_schema_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'variant', 'joins_with', 'extends', 'requires', etc.
    description TEXT,
    join_condition TEXT, -- SQL join condition if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate relationships
    UNIQUE(source_schema_id, target_schema_id, relationship_type)
);

-- ============================================
-- Table: amc_field_relationships
-- ============================================
CREATE TABLE IF NOT EXISTS amc_field_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_field_id UUID NOT NULL REFERENCES amc_schema_fields(id) ON DELETE CASCADE,
    target_field_id UUID NOT NULL REFERENCES amc_schema_fields(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'foreign_key', 'derived_from', 'aggregates_to', etc.
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate relationships
    UNIQUE(source_field_id, target_field_id, relationship_type)
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX idx_amc_data_sources_category ON amc_data_sources(category);
CREATE INDEX idx_amc_data_sources_schema_id ON amc_data_sources(schema_id);
CREATE INDEX idx_amc_data_sources_search ON amc_data_sources USING GIN(search_vector);
CREATE INDEX idx_amc_data_sources_tags ON amc_data_sources USING GIN(tags);

CREATE INDEX idx_amc_schema_fields_data_source ON amc_schema_fields(data_source_id);
CREATE INDEX idx_amc_schema_fields_type ON amc_schema_fields(dimension_or_metric);
CREATE INDEX idx_amc_schema_fields_threshold ON amc_schema_fields(aggregation_threshold);
CREATE INDEX idx_amc_schema_fields_search ON amc_schema_fields USING GIN(search_vector);

CREATE INDEX idx_amc_query_examples_data_source ON amc_query_examples(data_source_id);
CREATE INDEX idx_amc_query_examples_category ON amc_query_examples(category);
CREATE INDEX idx_amc_query_examples_search ON amc_query_examples USING GIN(search_vector);

CREATE INDEX idx_amc_schema_sections_data_source ON amc_schema_sections(data_source_id);
CREATE INDEX idx_amc_schema_sections_type ON amc_schema_sections(section_type);

CREATE INDEX idx_amc_relationships_source ON amc_schema_relationships(source_schema_id);
CREATE INDEX idx_amc_relationships_target ON amc_schema_relationships(target_schema_id);

-- ============================================
-- RLS Policies
-- ============================================
ALTER TABLE amc_data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_schema_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_query_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_schema_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_schema_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_field_relationships ENABLE ROW LEVEL SECURITY;

-- Everyone can read data sources and schemas
CREATE POLICY "Data sources are viewable by all users" ON amc_data_sources
    FOR SELECT USING (true);

CREATE POLICY "Schema fields are viewable by all users" ON amc_schema_fields
    FOR SELECT USING (true);

CREATE POLICY "Query examples are viewable by all users" ON amc_query_examples
    FOR SELECT USING (true);

CREATE POLICY "Schema sections are viewable by all users" ON amc_schema_sections
    FOR SELECT USING (true);

CREATE POLICY "Schema relationships are viewable by all users" ON amc_schema_relationships
    FOR SELECT USING (true);

CREATE POLICY "Field relationships are viewable by all users" ON amc_field_relationships
    FOR SELECT USING (true);

-- Only admins can insert/update/delete (add admin check as needed)
-- For now, we'll use service role for management

-- ============================================
-- Functions for Search
-- ============================================
CREATE OR REPLACE FUNCTION search_amc_schemas(search_query TEXT)
RETURNS TABLE (
    schema_id TEXT,
    name TEXT,
    category TEXT,
    description TEXT,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ds.schema_id,
        ds.name,
        ds.category,
        ds.description,
        ts_rank(ds.search_vector, plainto_tsquery('english', search_query)) +
        ts_rank(COALESCE(
            (SELECT AVG(ts_rank(f.search_vector, plainto_tsquery('english', search_query)))
             FROM amc_schema_fields f 
             WHERE f.data_source_id = ds.id), 0
        ), plainto_tsquery('english', search_query)) as rank
    FROM amc_data_sources ds
    WHERE ds.search_vector @@ plainto_tsquery('english', search_query)
       OR EXISTS (
           SELECT 1 FROM amc_schema_fields f 
           WHERE f.data_source_id = ds.id 
           AND f.search_vector @@ plainto_tsquery('english', search_query)
       )
    ORDER BY rank DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Function to get schema with all details
-- ============================================
CREATE OR REPLACE FUNCTION get_amc_schema_details(p_schema_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'schema', row_to_json(ds),
        'fields', (
            SELECT json_agg(row_to_json(f) ORDER BY f.field_order, f.field_name)
            FROM amc_schema_fields f
            WHERE f.data_source_id = ds.id
        ),
        'examples', (
            SELECT json_agg(row_to_json(e) ORDER BY e.example_order, e.title)
            FROM amc_query_examples e
            WHERE e.data_source_id = ds.id
        ),
        'sections', (
            SELECT json_agg(row_to_json(s) ORDER BY s.section_order)
            FROM amc_schema_sections s
            WHERE s.data_source_id = ds.id
        ),
        'relationships', (
            SELECT json_agg(json_build_object(
                'type', r.relationship_type,
                'target_schema', t.schema_id,
                'target_name', t.name,
                'description', r.description
            ))
            FROM amc_schema_relationships r
            JOIN amc_data_sources t ON t.id = r.target_schema_id
            WHERE r.source_schema_id = ds.id
        )
    ) INTO result
    FROM amc_data_sources ds
    WHERE ds.schema_id = p_schema_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Comments for Documentation
-- ============================================
COMMENT ON TABLE amc_data_sources IS 'Master table for AMC data source schemas';
COMMENT ON TABLE amc_schema_fields IS 'Field definitions for each AMC data source';
COMMENT ON TABLE amc_query_examples IS 'Example queries for each data source';
COMMENT ON TABLE amc_schema_sections IS 'Documentation sections for each data source';
COMMENT ON TABLE amc_schema_relationships IS 'Relationships between different data sources';
COMMENT ON TABLE amc_field_relationships IS 'Relationships between fields across data sources';