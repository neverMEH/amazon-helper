# Database Migration Required

## Workflow Versioning Migration

The workflow-centric execution system requires a database migration to enable version tracking.

### How to Apply the Migration

1. **Open Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to the SQL Editor section

2. **Create New Query**
   - Click "New Query"
   - Name it "Workflow Versioning Migration"

3. **Copy Migration SQL**
   - Copy the entire contents of: `database/supabase/migrations/10_workflow_versioning.sql`
   - Or use the SQL provided below

4. **Run the Migration**
   - Paste the SQL into the query editor
   - Click "Run" to execute

### What This Migration Does

- Creates `workflow_versions` table to track query iterations
- Adds version tracking columns to workflows table
- Links executions to specific workflow versions
- Creates automatic versioning triggers
- Sets up RLS policies for security

### Migration Status

The application will work without this migration, but version tracking features will not be available until it's applied.

### Full Migration SQL

```sql
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow_id ON workflow_versions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_created_at ON workflow_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_version ON workflow_executions(workflow_version_id);

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

-- Enable RLS
ALTER TABLE workflow_versions ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Users can view their workflow versions" ON workflow_versions
    FOR SELECT
    USING (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create versions for their workflows" ON workflow_versions
    FOR INSERT
    WITH CHECK (
        workflow_id IN (
            SELECT id FROM workflows WHERE user_id = auth.uid()
        )
    );
```

### After Migration

Once applied, the system will automatically:
- Track every query change as a new version
- Link each execution to the specific version that was run
- Provide complete iteration history for query development