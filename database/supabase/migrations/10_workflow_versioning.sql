-- Workflow Versioning System
-- Tracks every iteration of a workflow query for development history

-- Create workflow versions table
CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE NOT NULL,
    version_number INTEGER NOT NULL,
    sql_query TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    change_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Ensure unique version numbers per workflow
    UNIQUE(workflow_id, version_number)
);

-- Add version tracking to workflow executions
ALTER TABLE workflow_executions 
ADD COLUMN IF NOT EXISTS workflow_version_id UUID REFERENCES workflow_versions(id) ON DELETE SET NULL;

-- Add current version tracking to workflows
ALTER TABLE workflows
ADD COLUMN IF NOT EXISTS current_version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS total_versions INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS last_executed_version INTEGER;

-- Create index for faster version lookups
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id 
ON workflow_versions(workflow_id);

CREATE INDEX IF NOT EXISTS idx_workflow_versions_created_at 
ON workflow_versions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_version 
ON workflow_executions(workflow_version_id);

-- Function to automatically create version on workflow update
CREATE OR REPLACE FUNCTION create_workflow_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create version if SQL query changed
    IF OLD.sql_query IS DISTINCT FROM NEW.sql_query THEN
        -- Increment version counters
        NEW.total_versions = COALESCE(OLD.total_versions, 0) + 1;
        NEW.current_version = NEW.total_versions;
        
        -- Insert new version record
        INSERT INTO workflow_versions (
            workflow_id,
            version_number,
            sql_query,
            parameters,
            created_by,
            change_description
        ) VALUES (
            NEW.id,
            NEW.total_versions,
            NEW.sql_query,
            NEW.parameters,
            NEW.user_id,
            'Query updated via workflow edit'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic versioning
CREATE TRIGGER workflow_version_trigger
BEFORE UPDATE ON workflows
FOR EACH ROW
EXECUTE FUNCTION create_workflow_version();

-- Create initial versions for existing workflows
INSERT INTO workflow_versions (workflow_id, version_number, sql_query, parameters, created_by, change_description)
SELECT 
    id as workflow_id,
    1 as version_number,
    sql_query,
    parameters,
    user_id as created_by,
    'Initial version' as change_description
FROM workflows
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_versions WHERE workflow_versions.workflow_id = workflows.id
);

-- RLS policies for workflow versions
ALTER TABLE workflow_versions ENABLE ROW LEVEL SECURITY;

-- Users can view versions of their own workflows
CREATE POLICY "Users can view their workflow versions" ON workflow_versions
    FOR SELECT
    USING (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );

-- Users can create versions for their own workflows
CREATE POLICY "Users can create versions for their workflows" ON workflow_versions
    FOR INSERT
    WITH CHECK (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );

-- Add helpful view for latest version of each workflow
CREATE OR REPLACE VIEW workflow_latest_versions AS
SELECT DISTINCT ON (workflow_id)
    wv.*,
    w.name as workflow_name,
    w.user_id as workflow_owner
FROM workflow_versions wv
JOIN workflows w ON w.id = wv.workflow_id
ORDER BY workflow_id, version_number DESC;

-- Add view for execution history with version info
CREATE OR REPLACE VIEW workflow_execution_history AS
SELECT 
    we.*,
    w.name as workflow_name,
    w.sql_query as current_query,
    wv.version_number,
    wv.sql_query as executed_query,
    wv.parameters as version_parameters
FROM workflow_executions we
LEFT JOIN workflows w ON w.id = we.workflow_id
LEFT JOIN workflow_versions wv ON wv.id = we.workflow_version_id
ORDER BY we.started_at DESC;