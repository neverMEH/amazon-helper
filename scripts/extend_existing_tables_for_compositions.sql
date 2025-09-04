-- Extend Existing Tables for Flow Composition Support
-- Adds minimal columns to existing tables to support composition execution
-- Maintains backward compatibility with existing workflows

-- Add composition columns to workflow_executions table
-- This allows tracking which executions are part of a flow composition
ALTER TABLE workflow_executions 
ADD COLUMN IF NOT EXISTS composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS composition_node_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS execution_order INTEGER;

-- Add composition columns to workflow_schedules table  
-- This allows scheduling entire flow compositions
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS composition_id UUID REFERENCES template_flow_compositions(id) ON DELETE SET NULL;

-- Create indexes for composition queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_composition_id 
ON workflow_executions(composition_id) WHERE composition_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_executions_composition_node 
ON workflow_executions(composition_id, composition_node_id) 
WHERE composition_id IS NOT NULL AND composition_node_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_order
ON workflow_executions(composition_id, execution_order)
WHERE composition_id IS NOT NULL AND execution_order IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_schedules_composition_id
ON workflow_schedules(composition_id) WHERE composition_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN workflow_executions.composition_id IS 'References flow composition this execution belongs to (NULL for standalone executions)';
COMMENT ON COLUMN workflow_executions.composition_node_id IS 'Node ID within the composition (matches template_flow_nodes.node_id)';
COMMENT ON COLUMN workflow_executions.execution_order IS 'Execution order within composition for dependency tracking';

COMMENT ON COLUMN workflow_schedules.composition_id IS 'References flow composition to schedule (NULL for standalone workflow schedules)';

-- Create view for composition execution status aggregation
CREATE OR REPLACE VIEW composition_execution_summary AS
SELECT 
    c.id as composition_id,
    c.composition_id as composition_identifier,
    c.name as composition_name,
    COUNT(we.id) as total_executions,
    COUNT(CASE WHEN we.status = 'completed' THEN 1 END) as completed_executions,
    COUNT(CASE WHEN we.status = 'failed' THEN 1 END) as failed_executions,
    COUNT(CASE WHEN we.status = 'running' THEN 1 END) as running_executions,
    COUNT(CASE WHEN we.status = 'pending' THEN 1 END) as pending_executions,
    MIN(we.created_at) as first_execution_start,
    MAX(we.updated_at) as last_execution_update,
    CASE 
        WHEN COUNT(CASE WHEN we.status IN ('running', 'pending') THEN 1 END) > 0 THEN 'running'
        WHEN COUNT(CASE WHEN we.status = 'failed' THEN 1 END) > 0 THEN 'failed'
        WHEN COUNT(CASE WHEN we.status = 'completed' THEN 1 END) = COUNT(we.id) AND COUNT(we.id) > 0 THEN 'completed'
        WHEN COUNT(we.id) = 0 THEN 'not_started'
        ELSE 'partial'
    END as overall_status
FROM template_flow_compositions c
LEFT JOIN workflow_executions we ON we.composition_id = c.id
GROUP BY c.id, c.composition_id, c.name;

-- Add RLS policy for composition execution view
ALTER VIEW composition_execution_summary SET (security_barrier = true);

-- Create function to get composition execution details
CREATE OR REPLACE FUNCTION get_composition_execution_details(comp_id UUID)
RETURNS TABLE (
    node_id VARCHAR(100),
    template_id VARCHAR(100),
    workflow_execution_id UUID,
    status VARCHAR(50),
    execution_order INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    result_row_count INTEGER,
    result_s3_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        we.composition_node_id,
        w.workflow_id,
        we.id,
        we.status,
        we.execution_order,
        we.created_at,
        we.updated_at,
        we.error_message,
        we.result_row_count,
        we.result_s3_path
    FROM workflow_executions we
    JOIN workflows w ON w.id = we.workflow_id
    WHERE we.composition_id = comp_id
    ORDER BY we.execution_order NULLS LAST, we.created_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on function
GRANT EXECUTE ON FUNCTION get_composition_execution_details(UUID) TO authenticated;

-- Add check constraints to ensure data integrity
ALTER TABLE workflow_executions 
ADD CONSTRAINT check_composition_node_consistency 
CHECK (
    (composition_id IS NULL AND composition_node_id IS NULL) OR
    (composition_id IS NOT NULL AND composition_node_id IS NOT NULL)
);

ALTER TABLE workflow_executions
ADD CONSTRAINT check_execution_order_with_composition
CHECK (
    (composition_id IS NULL AND execution_order IS NULL) OR
    (composition_id IS NOT NULL)
);

-- Print completion message
DO $$
BEGIN
    RAISE NOTICE 'Existing tables extended for composition support!';
    RAISE NOTICE 'Added columns: workflow_executions.composition_id, composition_node_id, execution_order';
    RAISE NOTICE 'Added columns: workflow_schedules.composition_id';
    RAISE NOTICE 'Created composition_execution_summary view and helper function';
    RAISE NOTICE 'All changes maintain backward compatibility with existing workflows';
END $$;