-- Flow Composition Tables Migration
-- Creates minimal new tables for Visual Query Flow Builder
-- Integrates with existing RecomAMP schema patterns

-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: template_flow_compositions
-- Stores flow composition definitions (lightweight, references existing templates)
CREATE TABLE IF NOT EXISTS template_flow_compositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    composition_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    canvas_state JSONB NOT NULL DEFAULT '{"viewport":{"x":0,"y":0,"zoom":1},"nodes":[],"edges":[]}',
    global_parameters JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE
);

-- Add check constraint for composition_id format (must start with 'comp_')
ALTER TABLE template_flow_compositions ADD CONSTRAINT check_composition_id_format 
    CHECK (composition_id ~ '^comp_[a-z0-9_]+$');

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_compositions_composition_id ON template_flow_compositions(composition_id);
CREATE INDEX IF NOT EXISTS idx_compositions_created_by ON template_flow_compositions(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_compositions_tags ON template_flow_compositions USING GIN(tags) WHERE array_length(tags, 1) > 0;
CREATE INDEX IF NOT EXISTS idx_compositions_active_public ON template_flow_compositions(is_active, is_public);
CREATE INDEX IF NOT EXISTS idx_compositions_updated_at ON template_flow_compositions(updated_at DESC);

-- Add RLS policy following existing patterns
ALTER TABLE template_flow_compositions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see public compositions or their own compositions
CREATE POLICY "Users can view accessible compositions" ON template_flow_compositions
    FOR SELECT USING (
        is_public = true OR 
        created_by = auth.uid()
    );

-- Policy: Users can only create compositions for themselves
CREATE POLICY "Users can create their own compositions" ON template_flow_compositions
    FOR INSERT WITH CHECK (created_by = auth.uid());

-- Policy: Users can only update their own compositions
CREATE POLICY "Users can update their own compositions" ON template_flow_compositions
    FOR UPDATE USING (created_by = auth.uid());

-- Policy: Users can only delete their own compositions
CREATE POLICY "Users can delete their own compositions" ON template_flow_compositions
    FOR DELETE USING (created_by = auth.uid());

-- Table 2: template_flow_nodes
-- Stores individual nodes within flow compositions (references existing templates)
CREATE TABLE IF NOT EXISTS template_flow_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    template_id VARCHAR(100) REFERENCES query_flow_templates(template_id) ON DELETE RESTRICT,
    position JSONB NOT NULL DEFAULT '{"x":0,"y":0}',
    node_config JSONB NOT NULL DEFAULT '{}',
    parameter_overrides JSONB DEFAULT '{}',
    parameter_mappings JSONB DEFAULT '{}',
    execution_order INTEGER,
    is_conditional BOOLEAN DEFAULT false,
    condition_expression TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure node_id is unique within each composition
    UNIQUE(composition_id, node_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_flow_nodes_composition_id ON template_flow_nodes(composition_id);
CREATE INDEX IF NOT EXISTS idx_flow_nodes_template_id ON template_flow_nodes(template_id);
CREATE INDEX IF NOT EXISTS idx_flow_nodes_execution_order ON template_flow_nodes(composition_id, execution_order) WHERE execution_order IS NOT NULL;

-- Add RLS policy following existing patterns (inherit from parent composition)
ALTER TABLE template_flow_nodes ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access nodes if they can access the parent composition
CREATE POLICY "Users can access nodes via composition access" ON template_flow_nodes
    FOR ALL USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions 
            WHERE is_public = true OR created_by = auth.uid()
        )
    );

-- Table 3: template_flow_connections
-- Stores connections between nodes for data flow and parameter mapping
CREATE TABLE IF NOT EXISTS template_flow_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    connection_id VARCHAR(100) NOT NULL,
    source_node_id VARCHAR(100) NOT NULL,
    target_node_id VARCHAR(100) NOT NULL,
    field_mappings JSONB NOT NULL DEFAULT '{}',
    transformation_rules JSONB DEFAULT '{}',
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure connection_id is unique within each composition
    UNIQUE(composition_id, connection_id),
    
    -- Foreign key constraints to ensure nodes exist
    FOREIGN KEY (composition_id, source_node_id) REFERENCES template_flow_nodes(composition_id, node_id) ON DELETE CASCADE,
    FOREIGN KEY (composition_id, target_node_id) REFERENCES template_flow_nodes(composition_id, node_id) ON DELETE CASCADE
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_connections_composition ON template_flow_connections(composition_id);
CREATE INDEX IF NOT EXISTS idx_connections_source ON template_flow_connections(composition_id, source_node_id);
CREATE INDEX IF NOT EXISTS idx_connections_target ON template_flow_connections(composition_id, target_node_id);

-- Add RLS policy following existing patterns (inherit from parent composition)
ALTER TABLE template_flow_connections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can access connections if they can access the parent composition
CREATE POLICY "Users can access connections via composition access" ON template_flow_connections
    FOR ALL USING (
        composition_id IN (
            SELECT id FROM template_flow_compositions 
            WHERE is_public = true OR created_by = auth.uid()
        )
    );

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers for compositions and nodes
DROP TRIGGER IF EXISTS update_template_flow_compositions_updated_at ON template_flow_compositions;
CREATE TRIGGER update_template_flow_compositions_updated_at
    BEFORE UPDATE ON template_flow_compositions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_template_flow_nodes_updated_at ON template_flow_nodes;
CREATE TRIGGER update_template_flow_nodes_updated_at
    BEFORE UPDATE ON template_flow_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE template_flow_compositions IS 'Flow compositions that connect multiple query flow templates';
COMMENT ON TABLE template_flow_nodes IS 'Individual template nodes within flow compositions';
COMMENT ON TABLE template_flow_connections IS 'Connections between nodes defining parameter mappings and data flow';

COMMENT ON COLUMN template_flow_compositions.composition_id IS 'Human-readable composition identifier (comp_*)';
COMMENT ON COLUMN template_flow_compositions.canvas_state IS 'React Flow canvas state (viewport, nodes, edges)';
COMMENT ON COLUMN template_flow_compositions.global_parameters IS 'Flow-level parameter defaults';

COMMENT ON COLUMN template_flow_nodes.node_id IS 'Unique node identifier within composition';
COMMENT ON COLUMN template_flow_nodes.template_id IS 'Reference to existing query flow template';
COMMENT ON COLUMN template_flow_nodes.position IS 'Node position on canvas {x, y}';
COMMENT ON COLUMN template_flow_nodes.parameter_overrides IS 'User-configured parameter values for this node';
COMMENT ON COLUMN template_flow_nodes.parameter_mappings IS 'Parameter mappings from other nodes';

COMMENT ON COLUMN template_flow_connections.field_mappings IS 'Mapping of source fields to target parameters';
COMMENT ON COLUMN template_flow_connections.transformation_rules IS 'Optional data transformations';

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'Flow composition tables created successfully!';
    RAISE NOTICE 'Tables: template_flow_compositions, template_flow_nodes, template_flow_connections';
    RAISE NOTICE 'RLS policies enabled following existing RecomAMP patterns';
    RAISE NOTICE 'Indexes created for optimal query performance';
END $$;