# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-03-visual-query-flow-builder/spec.md

## Integration Philosophy

The Visual Query Flow Builder extends existing RecomAMP architecture rather than creating parallel systems. It leverages proven tables and patterns while adding minimal new schema for flow composition capabilities.

## New Tables (3 Core Tables)

### template_flow_compositions
Lightweight table for visual flow compositions using existing templates

```sql
CREATE TABLE template_flow_compositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id VARCHAR(100) UNIQUE NOT NULL, -- Human-readable ID (e.g., 'comp_campaign_analysis_v1')
    name VARCHAR(255) NOT NULL,
    description TEXT,
    canvas_state JSONB NOT NULL, -- React Flow canvas state (viewport, zoom, nodes, edges)
    global_parameters JSONB, -- Flow-level parameter defaults
    tags TEXT[], -- Array of tags for categorization
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_compositions_composition_id ON template_flow_compositions(composition_id),
    INDEX idx_compositions_created_by ON template_flow_compositions(created_by),
    INDEX idx_compositions_tags ON template_flow_compositions USING GIN(tags),
    INDEX idx_compositions_active ON template_flow_compositions(is_active, is_public)
);

-- Check constraint for composition_id format
ALTER TABLE template_flow_compositions ADD CONSTRAINT check_composition_id_format 
    CHECK (composition_id ~ '^comp_[a-z0-9_]+$');
```

### template_flow_nodes
Node definitions within flow compositions (references existing templates)

```sql
CREATE TABLE template_flow_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL, -- Unique within composition (e.g., 'node_1')
    template_id VARCHAR(100) REFERENCES query_flow_templates(template_id), -- Existing template
    position JSONB NOT NULL, -- {x: number, y: number} for React Flow
    node_config JSONB NOT NULL DEFAULT '{}', -- Visual node configuration
    parameter_overrides JSONB, -- User-configured parameter values
    parameter_mappings JSONB, -- Field mappings from other nodes {"param_name": {"source_node": "node_1", "source_field": "campaign_id"}}
    execution_order INTEGER, -- Computed from dependency graph (null = parallel)
    is_conditional BOOLEAN DEFAULT false, -- Execute based on previous results
    condition_expression TEXT, -- Optional condition for execution
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Composite unique constraint
    UNIQUE(composition_id, node_id),
    
    -- Indexes
    INDEX idx_flow_nodes_composition_id ON template_flow_nodes(composition_id),
    INDEX idx_flow_nodes_template_id ON template_flow_nodes(template_id),
    INDEX idx_flow_nodes_execution_order ON template_flow_nodes(composition_id, execution_order)
);
```

### template_flow_connections
Connections between nodes for data flow and parameter mapping

```sql
CREATE TABLE template_flow_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    connection_id VARCHAR(100) NOT NULL, -- Unique within composition
    source_node_id VARCHAR(100) NOT NULL, -- References template_flow_nodes.node_id
    target_node_id VARCHAR(100) NOT NULL,
    field_mappings JSONB NOT NULL, -- {"target_param": "source_field", ...}
    transformation_rules JSONB, -- Optional data transformations
    is_required BOOLEAN DEFAULT true, -- Whether connection must succeed for flow to continue
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints using composite keys
    FOREIGN KEY (composition_id, source_node_id) REFERENCES template_flow_nodes(composition_id, node_id),
    FOREIGN KEY (composition_id, target_node_id) REFERENCES template_flow_nodes(composition_id, node_id),
    
    -- Unique constraint
    UNIQUE(composition_id, connection_id),
    
    -- Indexes
    INDEX idx_connections_composition ON template_flow_connections(composition_id),
    INDEX idx_connections_source ON template_flow_connections(composition_id, source_node_id),
    INDEX idx_connections_target ON template_flow_connections(composition_id, target_node_id)
);
```

## Extended Tables (Minimal Changes to Existing Schema)

### workflow_executions (extend existing table)
Add flow composition tracking to existing execution system

```sql
-- Add flow composition reference to existing workflow_executions
ALTER TABLE workflow_executions 
    ADD COLUMN composition_execution_id UUID, -- Reference to master flow execution
    ADD COLUMN composition_node_id VARCHAR(100), -- Which node in the flow this represents
    ADD COLUMN parameter_mappings JSONB; -- How parameters were mapped from previous nodes

-- Add index for flow executions
CREATE INDEX idx_workflow_executions_composition ON workflow_executions(composition_execution_id)
    WHERE composition_execution_id IS NOT NULL;
```

### workflow_schedules (extend existing table)
Enable scheduling of flow compositions using existing schedule system

```sql
-- Add composition scheduling to existing schedule table
ALTER TABLE workflow_schedules 
    ADD COLUMN composition_id UUID REFERENCES template_flow_compositions(id),
    ADD COLUMN composition_parameters JSONB; -- Flow-level parameters for scheduled execution

-- Update constraint to allow either workflow OR composition scheduling
ALTER TABLE workflow_schedules DROP CONSTRAINT IF EXISTS check_schedule_type;
ALTER TABLE workflow_schedules ADD CONSTRAINT check_schedule_type CHECK (
    (workflow_id IS NOT NULL AND composition_id IS NULL) OR 
    (workflow_id IS NULL AND composition_id IS NOT NULL)
);

-- Add index for composition scheduling
CREATE INDEX idx_workflow_schedules_composition_id ON workflow_schedules(composition_id)
    WHERE composition_id IS NOT NULL;
```

### user_template_favorites (extend existing table)
Allow favoriting flow compositions using existing favorites system

```sql
-- Add composition favorites to existing favorites table (assuming it exists)
-- If this table doesn't exist, create it following existing patterns
CREATE TABLE IF NOT EXISTS user_composition_favorites (
    user_id UUID REFERENCES users(id),
    composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (user_id, composition_id),
    INDEX idx_user_composition_favorites_user ON user_composition_favorites(user_id)
);
```

## Virtual Tables (No New Schema - Use Existing Data)

The following "tables" are actually views or service-layer constructs that reuse existing data:

### Flow Execution Status (uses existing workflow_executions)
- Master flow execution creates multiple workflow_executions
- Each node execution is a standard workflow_execution
- Flow status aggregated from individual executions
- Results stored using existing S3 and database patterns

### Flow Results (uses existing result storage)
- Node results stored in existing workflow_executions.result_s3_path
- Result schemas stored in existing workflow_executions.result_metadata  
- Combined flow results aggregated at service layer
- Existing result caching and pagination patterns apply

### Template Integration (uses existing query_flow_templates)
- All templates remain in existing query_flow_templates table
- Existing parameter schemas, chart configs, and ratings preserved
- Flow nodes reference existing templates by template_id
- No duplication of template definitions

## Integration Patterns

### Execution Flow Integration
1. **Flow Execution**: Creates master record (lightweight tracking)
2. **Node Execution**: Each node creates standard workflow_execution  
3. **Parameter Mapping**: Service layer maps results between executions
4. **Status Aggregation**: Flow status computed from node execution statuses
5. **Result Storage**: Uses existing S3 and caching infrastructure

### Parameter System Integration
- **Reuse Parameter Engine**: Existing parameter validation and substitution
- **Extend Parameter Types**: Add "mapped_from_node" parameter type
- **Leverage SQL Injection**: Existing handling for large campaign/ASIN lists
- **Template Compatibility**: All existing templates work in flows unchanged

### Background Services Integration
- **Execution Polling**: Existing status poller handles node executions
- **Token Refresh**: Existing token service handles AMC authentication
- **Scheduling**: Existing schedule executor extended for compositions
- **Error Handling**: Existing retry and error patterns apply

## Performance Optimizations

### Database Design
- **Minimal New Tables**: Only 3 new tables vs. original 6+ table design
- **Leverage Existing Indexes**: Reuse workflow_executions indexes for performance
- **JSONB for Flexibility**: Canvas state and mappings in JSONB for fast updates
- **Composite Keys**: Efficient foreign key relationships

### Query Patterns
- **Single Execution Queries**: Reuse existing execution detail queries  
- **Flow Status**: Aggregate from existing workflow_executions with simple JOINs
- **Parameter Resolution**: Extend existing parameter service patterns
- **Result Retrieval**: Use existing result pagination and caching

## Migration Strategy

### Phase 1: Create New Tables
```sql
-- Run all CREATE TABLE statements above
-- No impact on existing system - purely additive
```

### Phase 2: Extend Existing Tables
```sql  
-- Add new columns to workflow_executions and workflow_schedules
-- All columns nullable, no impact on existing data
```

### Phase 3: Create Integration Services
- FlowCompositionService extends existing patterns
- FlowExecutionService orchestrates existing workflow executions
- Parameter mapping service extends existing parameter engine

## Data Integrity and Constraints

### Referential Integrity
- All composition nodes must reference valid templates
- All connections must reference valid nodes within same composition
- Execution records maintain proper hierarchy (composition → workflow)

### Business Rules
- Compositions must form valid DAG (no cycles in connections)
- Parameter mappings must match source/target schemas  
- Flow execution creates individual workflow executions for each node
- Scheduled compositions follow existing schedule patterns

### Cleanup Patterns
- Cascade deletion handles composition cleanup
- Existing workflow execution cleanup patterns apply
- Flow results cleaned up through existing result management

## Modified Tables

### workflow_schedules (modification)
Add support for scheduling flows

```sql
-- Add new columns to existing workflow_schedules table
ALTER TABLE workflow_schedules 
    ADD COLUMN flow_id UUID REFERENCES query_flows(id),
    ADD COLUMN flow_parameters JSONB,
    ADD CONSTRAINT check_schedule_type CHECK (
        (workflow_id IS NOT NULL AND flow_id IS NULL) OR 
        (workflow_id IS NULL AND flow_id IS NOT NULL)
    );

-- Add index for flow scheduling
CREATE INDEX idx_workflow_schedules_flow_id ON workflow_schedules(flow_id);
```

### workflow_executions (modification)
Link to flow execution if applicable

```sql
-- Add reference to flow execution
ALTER TABLE workflow_executions 
    ADD COLUMN flow_execution_id UUID REFERENCES query_flow_executions(id),
    ADD COLUMN flow_node_id VARCHAR(100);

-- Add index
CREATE INDEX idx_workflow_executions_flow ON workflow_executions(flow_execution_id);
```

## Migration Strategy

1. **Phase 1**: Create new tables without affecting existing system
   - Run all CREATE TABLE statements
   - No impact on current Query Flow Templates

2. **Phase 2**: Modify existing tables
   - Add new columns to workflow_schedules
   - Add new columns to workflow_executions
   - Maintain backward compatibility

3. **Phase 3**: Data migration (if needed)
   - Optional: Convert existing template combinations to flows
   - Create migration script to import common patterns

## Performance Considerations

- **Indexes**: All foreign keys and commonly queried fields are indexed
- **JSONB**: Used for flexible schema evolution without migrations
- **Cascade Deletes**: Automatic cleanup of related records
- **Partitioning**: Consider partitioning query_flow_executions by created_at for large datasets

## Data Integrity Rules

- Flow must have at least one node to be executable
- Edges can only connect existing nodes within the same flow
- Node execution order must form a valid DAG (no cycles)
- Parameter mappings must match source output schema to target input types
- Flow versions are immutable once executed