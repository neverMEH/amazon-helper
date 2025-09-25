# Report Builder Dashboards Migration (010)

## Overview
This migration creates the database schema for the Report Builder Dashboards feature, which enables queries from the query library to generate interactive visual reports with charts, graphs, and AI-powered insights.

## Migration File
- **SQL File**: `010_create_report_builder_dashboard_tables.sql`
- **Python Execution Script**: `../execute_report_builder_dashboards_migration.py`

## What This Migration Does

### 1. Creates New Tables
- **report_configurations**: Stores dashboard configuration for workflows/templates
- **dashboard_views**: Individual dashboard components and visualizations
- **dashboard_insights**: AI-generated insights for dashboard data
- **report_exports**: Tracks exported reports (PDF, CSV, etc.)

### 2. Adds Columns to Existing Tables
- **workflows**: Adds `report_enabled` and `report_config_id` columns
- **query_templates**: Adds `default_dashboard_type` column

### 3. Creates Indexes
- Performance indexes on all foreign keys
- Composite indexes for common query patterns
- Filtered indexes for boolean flags

### 4. Sets Up Row Level Security
- Enables RLS on all new tables
- Creates policies for user access control
- Ensures users can only access their own data

## How to Run the Migration

### Option 1: Via Supabase Dashboard (Recommended)
1. Open your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy the entire contents of `010_create_report_builder_dashboard_tables.sql`
4. Paste into the SQL Editor
5. Click "Run" to execute the migration

### Option 2: Via Python Script (Requires psycopg2)
```bash
# Install psycopg2 if not already installed
pip install psycopg2-binary

# Set environment variables
export SUPABASE_DB_PASSWORD="your_database_password"
export SUPABASE_URL="your_supabase_url"

# Run the migration
python scripts/execute_report_builder_dashboards_migration.py
```

### Option 3: Via Direct PostgreSQL Connection
```bash
# If you have PostgreSQL client installed
psql "your_connection_string" < scripts/migrations/010_create_report_builder_dashboard_tables.sql
```

## Verification

After running the migration, verify it was successful by checking:

1. **Tables Created**:
   - report_configurations
   - dashboard_views
   - dashboard_insights
   - report_exports

2. **Columns Added**:
   - workflows.report_enabled
   - workflows.report_config_id
   - query_templates.default_dashboard_type

3. **Run Tests**:
```bash
pytest tests/supabase/test_report_builder_dashboard_schema.py -v
```

## Rollback

If you need to rollback this migration:

```sql
-- Drop new tables (CASCADE will remove dependent objects)
DROP TABLE IF EXISTS report_exports CASCADE;
DROP TABLE IF EXISTS dashboard_insights CASCADE;
DROP TABLE IF EXISTS dashboard_views CASCADE;
DROP TABLE IF EXISTS report_configurations CASCADE;

-- Remove columns from existing tables
ALTER TABLE workflows
DROP COLUMN IF EXISTS report_enabled,
DROP COLUMN IF EXISTS report_config_id;

ALTER TABLE query_templates
DROP COLUMN IF EXISTS default_dashboard_type;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
```

## Dependencies
- Requires existing tables: workflows, query_templates, users
- Requires UUID extension (should already be enabled)
- Requires auth.uid() function for RLS

## Related Documentation
- Feature Spec: `.agent-os/specs/2025-09-23-report-builder-dashboards/spec.md`
- Tasks: `.agent-os/specs/2025-09-23-report-builder-dashboards/tasks.md`
- Technical Spec: `.agent-os/specs/2025-09-23-report-builder-dashboards/sub-specs/technical-spec.md`