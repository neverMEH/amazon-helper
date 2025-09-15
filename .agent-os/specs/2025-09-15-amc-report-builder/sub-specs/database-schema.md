# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-15-amc-report-builder/spec.md

## Schema Changes

### Extensions to Existing Tables

#### query_templates
```sql
-- Add report-specific columns to existing query_templates table
ALTER TABLE query_templates
  ADD COLUMN IF NOT EXISTS report_type TEXT,
  ADD COLUMN IF NOT EXISTS report_config JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS ui_schema JSONB DEFAULT '{}'::jsonb;

-- Add index for report type filtering
CREATE INDEX IF NOT EXISTS idx_query_templates_report_type
  ON query_templates(report_type)
  WHERE report_type IS NOT NULL;
```

**Rationale**: Extends existing templates with report metadata while maintaining backward compatibility. The `report_config` stores dashboard widget configurations, while `ui_schema` defines advanced form rendering rules.

### New Tables

#### report_definitions
```sql
CREATE TABLE IF NOT EXISTS report_definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  template_id UUID REFERENCES query_templates(id) ON DELETE RESTRICT,
  instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
  owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
  parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  frequency TEXT NOT NULL DEFAULT 'once' CHECK (frequency IN ('once', 'daily', 'weekly', 'monthly', 'quarterly')),
  timezone TEXT NOT NULL DEFAULT 'UTC',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  dashboard_id UUID REFERENCES dashboards(id) ON DELETE SET NULL,
  last_execution_id UUID,
  execution_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for query performance
CREATE INDEX idx_report_definitions_owner ON report_definitions(owner_id);
CREATE INDEX idx_report_definitions_instance ON report_definitions(instance_id);
CREATE INDEX idx_report_definitions_template ON report_definitions(template_id);
CREATE INDEX idx_report_definitions_active ON report_definitions(is_active) WHERE is_active = TRUE;
```

**Rationale**: Central entity for user-configured reports, linking templates to instances with saved parameters. The `report_id` provides a human-readable identifier.

#### report_executions
```sql
CREATE TABLE IF NOT EXISTS report_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id TEXT UNIQUE NOT NULL,
  report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
  template_id UUID REFERENCES query_templates(id) ON DELETE SET NULL,
  instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  triggered_by TEXT NOT NULL CHECK (triggered_by IN ('manual', 'schedule', 'backfill', 'api')),
  schedule_id UUID REFERENCES report_schedules(id) ON DELETE SET NULL,
  collection_id UUID REFERENCES report_data_collections(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
  amc_execution_id TEXT,
  output_location TEXT,
  row_count INTEGER,
  size_bytes BIGINT,
  error_message TEXT,
  parameters_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
  time_window_start TIMESTAMPTZ,
  time_window_end TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for query patterns
CREATE INDEX idx_report_executions_report ON report_executions(report_id);
CREATE INDEX idx_report_executions_status ON report_executions(status);
CREATE INDEX idx_report_executions_started ON report_executions(started_at DESC);
CREATE INDEX idx_report_executions_amc_id ON report_executions(amc_execution_id) WHERE amc_execution_id IS NOT NULL;
```

**Rationale**: Tracks individual execution instances with full audit trail. Supports multiple trigger types and maintains parameter snapshots for reproducibility.

#### report_schedules
```sql
CREATE TABLE IF NOT EXISTS report_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id TEXT UNIQUE NOT NULL,
  report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
  schedule_type TEXT NOT NULL CHECK (schedule_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'custom')),
  cron_expression TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'UTC',
  default_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_paused BOOLEAN NOT NULL DEFAULT FALSE,
  last_run_at TIMESTAMPTZ,
  last_run_status TEXT,
  next_run_at TIMESTAMPTZ,
  run_count INTEGER DEFAULT 0,
  failure_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(report_id, is_active) WHERE is_active = TRUE
);

-- Indexes for scheduler queries
CREATE INDEX idx_report_schedules_next_run ON report_schedules(next_run_at) WHERE is_active = TRUE AND is_paused = FALSE;
CREATE INDEX idx_report_schedules_report ON report_schedules(report_id);
```

**Rationale**: Manages recurring execution schedules with pause capability. Single active schedule per report prevents conflicts.

#### dashboard_favorites
```sql
CREATE TABLE IF NOT EXISTS dashboard_favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(dashboard_id, user_id)
);

-- Index for user queries
CREATE INDEX idx_dashboard_favorites_user ON dashboard_favorites(user_id);
```

**Rationale**: Enables per-user dashboard favoriting for quick access to frequently used reports.

### Modified Tables

#### report_data_collections
```sql
-- Extend for report-based collections
ALTER TABLE report_data_collections
  ADD COLUMN IF NOT EXISTS report_id UUID REFERENCES report_definitions(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS segment_type TEXT DEFAULT 'weekly' CHECK (segment_type IN ('daily', 'weekly', 'monthly', 'quarterly')),
  ADD COLUMN IF NOT EXISTS max_lookback_days INTEGER DEFAULT 365 CHECK (max_lookback_days <= 365);

-- Add index for report-based queries
CREATE INDEX IF NOT EXISTS idx_collections_report ON report_data_collections(report_id) WHERE report_id IS NOT NULL;
```

**Rationale**: Repurposes existing collection infrastructure for report backfills, maintaining compatibility while adding report-specific fields.

### Database Views

#### report_runs_overview
```sql
CREATE OR REPLACE VIEW report_runs_overview AS
SELECT
  rd.id AS report_uuid,
  rd.report_id,
  rd.name,
  rd.description,
  rd.instance_id,
  ai.instance_id AS amc_instance_id,
  ai.instance_name,
  rd.owner_id,
  u.email AS owner_email,
  qt.name AS template_name,
  qt.report_type,
  rd.is_active,
  rd.frequency,
  CASE
    WHEN rs.is_paused THEN 'paused'
    WHEN rd.is_active THEN 'active'
    ELSE 'inactive'
  END AS state,
  re.status AS latest_status,
  re.started_at AS last_run_at,
  re.completed_at AS last_completed_at,
  rs.next_run_at,
  rd.execution_count,
  rd.created_at,
  rd.updated_at,
  EXISTS(SELECT 1 FROM dashboard_favorites df WHERE df.dashboard_id = rd.dashboard_id AND df.user_id = rd.owner_id) AS is_favorite
FROM report_definitions rd
LEFT JOIN query_templates qt ON qt.id = rd.template_id
LEFT JOIN amc_instances ai ON ai.id = rd.instance_id
LEFT JOIN users u ON u.id = rd.owner_id
LEFT JOIN LATERAL (
  SELECT * FROM report_executions re2
  WHERE re2.report_id = rd.id
  ORDER BY re2.started_at DESC NULLS LAST
  LIMIT 1
) re ON TRUE
LEFT JOIN report_schedules rs ON rs.report_id = rd.id AND rs.is_active = TRUE
ORDER BY rd.created_at DESC;
```

**Rationale**: Provides unified view for dashboard table display with all necessary joins pre-computed for performance.

### Migration and Cleanup

#### Workflow Deprecation
```sql
-- Archive existing workflow data before removal
CREATE TABLE IF NOT EXISTS archived_workflows AS
SELECT * FROM workflows;

CREATE TABLE IF NOT EXISTS archived_workflow_executions AS
SELECT * FROM workflow_executions;

-- Add deprecation notice
COMMENT ON TABLE workflows IS 'DEPRECATED: Replaced by report_definitions. Archived data available in archived_workflows.';
COMMENT ON TABLE workflow_executions IS 'DEPRECATED: Replaced by report_executions. Archived data available in archived_workflow_executions.';
```

**Rationale**: Preserves existing data for historical reference while clearly marking tables as deprecated.

### Performance Optimizations

```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_report_exec_composite ON report_executions(report_id, status, started_at DESC);
CREATE INDEX idx_report_schedule_composite ON report_schedules(is_active, is_paused, next_run_at) WHERE is_active = TRUE;

-- Partial indexes for active records
CREATE INDEX idx_active_reports ON report_definitions(instance_id, is_active) WHERE is_active = TRUE;

-- Trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_report_definitions_updated_at BEFORE UPDATE ON report_definitions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_executions_updated_at BEFORE UPDATE ON report_executions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_report_schedules_updated_at BEFORE UPDATE ON report_schedules
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Rationale**: Optimizes common query patterns and ensures data consistency with automatic timestamp updates.