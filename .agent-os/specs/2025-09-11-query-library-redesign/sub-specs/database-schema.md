# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-11-query-library-redesign/spec.md

> Created: 2025-09-11
> Version: 1.0.0

## Schema Changes

### Enhanced query_templates Table
```sql
ALTER TABLE public.query_templates
ADD COLUMN report_config JSONB,
ADD COLUMN version INTEGER DEFAULT 1,
ADD COLUMN parent_template_id UUID REFERENCES query_templates(id),
ADD COLUMN execution_count INTEGER DEFAULT 0;

CREATE INDEX idx_query_templates_parent ON query_templates(parent_template_id);
CREATE INDEX idx_query_templates_usage ON query_templates(execution_count DESC, created_at DESC);
```

### New query_template_parameters Table
```sql
CREATE TABLE public.query_template_parameters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
  parameter_name TEXT NOT NULL,
  parameter_type TEXT NOT NULL CHECK (parameter_type IN (
    'asin_list', 'campaign_list', 'date_range', 'date_expression',
    'campaign_filter', 'threshold_numeric', 'percentage', 'enum_select',
    'string', 'number', 'boolean'
  )),
  display_name TEXT NOT NULL,
  description TEXT,
  required BOOLEAN DEFAULT true,
  default_value JSONB,
  validation_rules JSONB,
  ui_config JSONB,
  display_order INTEGER,
  group_name TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(template_id, parameter_name)
);

CREATE INDEX idx_template_parameters_template ON query_template_parameters(template_id);
CREATE INDEX idx_template_parameters_order ON query_template_parameters(template_id, display_order);
```

### New query_template_reports Table
```sql
CREATE TABLE public.query_template_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
  report_name TEXT NOT NULL,
  dashboard_config JSONB NOT NULL,
  field_mappings JSONB NOT NULL,
  default_filters JSONB,
  widget_order JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_template_reports_template ON query_template_reports(template_id);
```

### New query_template_instances Table
```sql
CREATE TABLE public.query_template_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  instance_name TEXT NOT NULL,
  saved_parameters JSONB NOT NULL,
  is_favorite BOOLEAN DEFAULT false,
  last_executed_at TIMESTAMPTZ,
  execution_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_template_instances_user ON query_template_instances(user_id, is_favorite DESC, last_executed_at DESC);
CREATE INDEX idx_template_instances_template ON query_template_instances(template_id);
```

## Migrations

### Step 1: Backup Existing Data
```sql
CREATE TABLE query_templates_backup AS SELECT * FROM query_templates;
```

### Step 2: Apply Schema Changes
Execute all ALTER TABLE and CREATE TABLE statements above.

### Step 3: Migrate Existing Templates
```sql
-- Auto-detect and migrate parameters from existing templates
INSERT INTO query_template_parameters (template_id, parameter_name, parameter_type, display_name)
SELECT 
  id as template_id,
  param->>'name' as parameter_name,
  COALESCE(param->>'type', 'string') as parameter_type,
  param->>'name' as display_name
FROM query_templates,
LATERAL jsonb_array_elements(parameters_schema->'properties') as param
WHERE parameters_schema IS NOT NULL;
```

### Step 4: Enable Row Level Security
```sql
ALTER TABLE query_template_parameters ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_template_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_template_instances ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own template parameters"
ON query_template_parameters FOR SELECT
USING (template_id IN (SELECT id FROM query_templates WHERE user_id = auth.uid() OR is_public = true));

CREATE POLICY "Users can manage their own template parameters"
ON query_template_parameters FOR ALL
USING (template_id IN (SELECT id FROM query_templates WHERE user_id = auth.uid()));

-- Similar policies for other tables
```

## Rationale

- **Separate parameters table**: Allows flexible parameter management without modifying main template
- **JSONB for configurations**: Provides schema flexibility for UI configurations and validation rules
- **Cascading deletes**: Ensures data integrity when templates are deleted
- **Comprehensive indexes**: Optimizes common query patterns (by user, by usage, by template)
- **Row Level Security**: Maintains data isolation between users while allowing public template sharing