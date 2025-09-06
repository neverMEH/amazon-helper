-- Visual Query Flow Builder Database Migration
-- Creates tables for flow composition functionality
-- Migration: 002_create_flow_composition_tables.sql
-- Date: 2025-09-03

-- ================================================
-- FLOW COMPOSITION CORE TABLES
-- ================================================

-- Main composition table - stores flow metadata
CREATE TABLE IF NOT EXISTS template_flow_compositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id VARCHAR(100) UNIQUE NOT NULL, -- Human-readable ID (e.g., 'comp_campaign_analysis_v1')
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',
    canvas_state JSONB DEFAULT '{}', -- Visual state (viewport, zoom, etc.)
    config JSONB DEFAULT '{}', -- Execution config (mode, error handling, etc.)
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    parent_version_id UUID REFERENCES template_flow_compositions(id) ON DELETE SET NULL
);

-- Ensure all columns exist (in case table was created in previous partial migration)
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS canvas_state JSONB DEFAULT '{}';
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT false;
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE template_flow_compositions ADD COLUMN IF NOT EXISTS parent_version_id UUID REFERENCES template_flow_compositions(id) ON DELETE SET NULL;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_compositions_composition_id ON template_flow_compositions(composition_id);
CREATE INDEX IF NOT EXISTS idx_compositions_created_by ON template_flow_compositions(created_by);
CREATE INDEX IF NOT EXISTS idx_compositions_tags ON template_flow_compositions USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_compositions_active ON template_flow_compositions(is_active, is_public);
CREATE INDEX IF NOT EXISTS idx_compositions_updated_at ON template_flow_compositions(updated_at DESC);

-- Add constraint for composition_id format
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_composition_id_format') THEN
        ALTER TABLE template_flow_compositions ADD CONSTRAINT check_composition_id_format 
            CHECK (composition_id ~ '^comp_[a-z0-9_]+$');
    END IF;
END $$;

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_template_flow_compositions_updated_at ON template_flow_compositions;
CREATE TRIGGER update_template_flow_compositions_updated_at 
    BEFORE UPDATE ON template_flow_compositions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- FLOW NODES TABLE
-- ================================================

-- Node definitions within flow compositions
CREATE TABLE IF NOT EXISTS template_flow_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL, -- Unique within composition (e.g., 'node_1')
    template_id VARCHAR(100) NOT NULL, -- References query_flow_templates.template_id
    label VARCHAR(255),
    position JSONB DEFAULT '{"x": 0, "y": 0}', -- Canvas position
    config JSONB DEFAULT '{}', -- Node-specific configuration
    execution_order INTEGER, -- Topological sort order (calculated)
    status VARCHAR(50) DEFAULT 'ready', -- ready, running, completed, failed, skipped
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure node_id is unique within a composition
    UNIQUE(composition_id, node_id)
);

-- Ensure all columns exist (in case table was created in previous partial migration)
ALTER TABLE template_flow_nodes ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ready';
ALTER TABLE template_flow_nodes ADD COLUMN IF NOT EXISTS execution_order INTEGER;
ALTER TABLE template_flow_nodes ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}';
ALTER TABLE template_flow_nodes ADD COLUMN IF NOT EXISTS position JSONB DEFAULT '{"x": 0, "y": 0}';
ALTER TABLE template_flow_nodes ADD COLUMN IF NOT EXISTS label VARCHAR(255);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_flow_nodes_composition_id ON template_flow_nodes(composition_id);
CREATE INDEX IF NOT EXISTS idx_flow_nodes_template_id ON template_flow_nodes(template_id);
CREATE INDEX IF NOT EXISTS idx_flow_nodes_execution_order ON template_flow_nodes(composition_id, execution_order);
CREATE INDEX IF NOT EXISTS idx_flow_nodes_status ON template_flow_nodes(status) WHERE status != 'ready';

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_template_flow_nodes_updated_at ON template_flow_nodes;
CREATE TRIGGER update_template_flow_nodes_updated_at 
    BEFORE UPDATE ON template_flow_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- FLOW CONNECTIONS TABLE
-- ================================================

-- Connections between nodes (edges in the flow graph)
CREATE TABLE IF NOT EXISTS template_flow_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    connection_id VARCHAR(100) NOT NULL, -- Unique within composition
    source_node_id VARCHAR(100) NOT NULL, -- References template_flow_nodes.node_id
    source_handle VARCHAR(50) DEFAULT 'output', -- Handle identifier
    target_node_id VARCHAR(100) NOT NULL, -- References template_flow_nodes.node_id
    target_handle VARCHAR(50) DEFAULT 'input', -- Handle identifier
    mapping_config JSONB DEFAULT '{}', -- Field mappings and transformations
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraints for node references
    FOREIGN KEY (composition_id, source_node_id) REFERENCES template_flow_nodes(composition_id, node_id) ON DELETE CASCADE,
    FOREIGN KEY (composition_id, target_node_id) REFERENCES template_flow_nodes(composition_id, node_id) ON DELETE CASCADE,
    
    -- Ensure connection_id is unique within composition
    UNIQUE(composition_id, connection_id),
    
    -- Prevent self-connections
    CHECK (source_node_id != target_node_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_connections_composition ON template_flow_connections(composition_id);
CREATE INDEX IF NOT EXISTS idx_connections_source ON template_flow_connections(composition_id, source_node_id);
CREATE INDEX IF NOT EXISTS idx_connections_target ON template_flow_connections(composition_id, target_node_id);

-- ================================================
-- EXTEND EXISTING TABLES
-- ================================================

-- Add composition tracking to workflow_executions
-- These columns link individual workflow executions to their parent composition execution
ALTER TABLE workflow_executions 
    ADD COLUMN IF NOT EXISTS composition_execution_id UUID, -- Reference to master flow execution
    ADD COLUMN IF NOT EXISTS composition_node_id VARCHAR(100), -- Which node in the flow this represents
    ADD COLUMN IF NOT EXISTS composition_metadata JSONB DEFAULT '{}'; -- Additional composition context

-- Add index for composition executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_composition 
    ON workflow_executions(composition_execution_id)
    WHERE composition_execution_id IS NOT NULL;

-- Add composition scheduling support to workflow_schedules
ALTER TABLE workflow_schedules 
    ADD COLUMN IF NOT EXISTS composition_id UUID REFERENCES template_flow_compositions(id),
    ADD COLUMN IF NOT EXISTS composition_parameters JSONB DEFAULT '{}'; -- Flow-level parameters

-- Update constraint to allow either workflow OR composition scheduling
ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS check_schedule_type;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_schedule_type') THEN
        ALTER TABLE workflow_schedules ADD CONSTRAINT check_schedule_type CHECK (
            (workflow_id IS NOT NULL AND composition_id IS NULL) OR 
            (workflow_id IS NULL AND composition_id IS NOT NULL)
        );
    END IF;
END $$;

-- Add index for composition scheduling
CREATE INDEX IF NOT EXISTS idx_workflow_schedules_composition_id 
    ON workflow_schedules(composition_id)
    WHERE composition_id IS NOT NULL;

-- ================================================
-- USER FAVORITES FOR COMPOSITIONS
-- ================================================

-- Allow users to favorite flow compositions
CREATE TABLE IF NOT EXISTS user_composition_favorites (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (user_id, composition_id)
);

-- Add index for user favorites
CREATE INDEX IF NOT EXISTS idx_user_composition_favorites_user ON user_composition_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_composition_favorites_created ON user_composition_favorites(created_at DESC);

-- ================================================
-- COMPOSITION EXECUTION HISTORY
-- ================================================

-- Track composition execution history
CREATE TABLE IF NOT EXISTS template_flow_composition_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    execution_id VARCHAR(100) UNIQUE NOT NULL, -- Human-readable execution ID
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    execution_summary JSONB DEFAULT '{}', -- Summary of all node executions
    total_nodes INTEGER DEFAULT 0,
    completed_nodes INTEGER DEFAULT 0,
    failed_nodes INTEGER DEFAULT 0,
    parameters JSONB DEFAULT '{}', -- Input parameters
    result_summary JSONB DEFAULT '{}', -- Aggregated results
    
    -- Execution metrics
    total_runtime_seconds DECIMAL(10,2),
    total_cost_estimate DECIMAL(10,4),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for composition executions
CREATE INDEX IF NOT EXISTS idx_comp_executions_composition_id ON template_flow_composition_executions(composition_id);
CREATE INDEX IF NOT EXISTS idx_comp_executions_user_id ON template_flow_composition_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_comp_executions_status ON template_flow_composition_executions(status);
CREATE INDEX IF NOT EXISTS idx_comp_executions_started_at ON template_flow_composition_executions(started_at DESC);

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_composition_executions_updated_at ON template_flow_composition_executions;
CREATE TRIGGER update_composition_executions_updated_at 
    BEFORE UPDATE ON template_flow_composition_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ================================================

-- Enable RLS on new tables
ALTER TABLE template_flow_compositions ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_flow_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_flow_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_composition_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE template_flow_composition_executions ENABLE ROW LEVEL SECURITY;

-- Policies for template_flow_compositions
DROP POLICY IF EXISTS "Users can view their own compositions" ON template_flow_compositions;
CREATE POLICY "Users can view their own compositions" ON template_flow_compositions
    FOR SELECT USING (created_by = auth.uid() OR is_public = true);

DROP POLICY IF EXISTS "Users can create their own compositions" ON template_flow_compositions;
CREATE POLICY "Users can create their own compositions" ON template_flow_compositions
    FOR INSERT WITH CHECK (created_by = auth.uid());

DROP POLICY IF EXISTS "Users can update their own compositions" ON template_flow_compositions;
CREATE POLICY "Users can update their own compositions" ON template_flow_compositions
    FOR UPDATE USING (created_by = auth.uid()) WITH CHECK (created_by = auth.uid());

DROP POLICY IF EXISTS "Users can delete their own compositions" ON template_flow_compositions;
CREATE POLICY "Users can delete their own compositions" ON template_flow_compositions
    FOR DELETE USING (created_by = auth.uid());

-- Policies for template_flow_nodes (inherit from composition)
DROP POLICY IF EXISTS "Users can view nodes in accessible compositions" ON template_flow_nodes;
CREATE POLICY "Users can view nodes in accessible compositions" ON template_flow_nodes
    FOR SELECT USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions 
            WHERE created_by = auth.uid() OR is_public = true
        )
    );

DROP POLICY IF EXISTS "Users can manage nodes in their compositions" ON template_flow_nodes;
CREATE POLICY "Users can manage nodes in their compositions" ON template_flow_nodes
    FOR ALL USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions WHERE created_by = auth.uid()
        )
    );

-- Policies for template_flow_connections (inherit from composition)
DROP POLICY IF EXISTS "Users can view connections in accessible compositions" ON template_flow_connections;
CREATE POLICY "Users can view connections in accessible compositions" ON template_flow_connections
    FOR SELECT USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions 
            WHERE created_by = auth.uid() OR is_public = true
        )
    );

DROP POLICY IF EXISTS "Users can manage connections in their compositions" ON template_flow_connections;
CREATE POLICY "Users can manage connections in their compositions" ON template_flow_connections
    FOR ALL USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions WHERE created_by = auth.uid()
        )
    );

-- Policies for user_composition_favorites
DROP POLICY IF EXISTS "Users can manage their own favorites" ON user_composition_favorites;
CREATE POLICY "Users can manage their own favorites" ON user_composition_favorites
    FOR ALL USING (user_id = auth.uid());

-- Policies for template_flow_composition_executions
DROP POLICY IF EXISTS "Users can view their own executions" ON template_flow_composition_executions;
CREATE POLICY "Users can view their own executions" ON template_flow_composition_executions
    FOR SELECT USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can create their own executions" ON template_flow_composition_executions;
CREATE POLICY "Users can create their own executions" ON template_flow_composition_executions
    FOR INSERT WITH CHECK (user_id = auth.uid());

-- ================================================
-- SAMPLE DATA (Optional - for testing)
-- ================================================

-- Uncomment below to insert sample composition data
/*
INSERT INTO template_flow_compositions (composition_id, name, description, tags, config, is_public)
VALUES 
    ('comp_campaign_performance_flow', 
     'Campaign Performance Analysis Flow', 
     'Comprehensive campaign performance analysis with creative insights',
     ARRAY['campaign', 'performance', 'analysis'],
     '{"execution_mode": "sequential", "error_handling": "continue", "max_parallel": 3}',
     true);
*/

-- ================================================
-- MIGRATION METADATA
-- ================================================

-- Create migration history table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Record migration execution
INSERT INTO migration_history (migration_name, executed_at, status)
VALUES ('002_create_flow_composition_tables', NOW(), 'completed')
ON CONFLICT (migration_name) DO NOTHING;