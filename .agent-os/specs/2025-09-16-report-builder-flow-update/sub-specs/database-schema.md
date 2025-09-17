# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-16-report-builder-flow-update/spec.md

> Created: 2025-09-16
> Version: 1.0.0

## Schema Changes

### Modifications to Existing Tables

#### report_data_collections
```sql
-- Add lookback configuration column
ALTER TABLE report_data_collections
ADD COLUMN lookback_config JSONB DEFAULT NULL;

-- Example lookback_config structure:
-- {
--   "type": "relative" | "custom",
--   "value": 7 | 14 | 30,  -- for relative
--   "unit": "days" | "weeks" | "months",
--   "startDate": "2025-01-01",  -- for custom
--   "endDate": "2025-01-31"
-- }

-- Add backfill segmentation configuration
ALTER TABLE report_data_collections
ADD COLUMN segmentation_config JSONB DEFAULT NULL;

-- Example segmentation_config:
-- {
--   "type": "daily" | "weekly" | "monthly",
--   "parallel_limit": 10,
--   "retry_failed": true
-- }
```

#### workflow_schedules
```sql
-- Add backfill status tracking
ALTER TABLE workflow_schedules
ADD COLUMN backfill_status TEXT DEFAULT NULL,
ADD COLUMN backfill_collection_id UUID REFERENCES report_data_collections(id) ON DELETE SET NULL,
ADD COLUMN schedule_config JSONB DEFAULT NULL;

-- Create enum for backfill status
CREATE TYPE backfill_status_enum AS ENUM (
  'pending',
  'in_progress',
  'completed',
  'failed',
  'partial'
);

ALTER TABLE workflow_schedules
ALTER COLUMN backfill_status TYPE backfill_status_enum USING backfill_status::backfill_status_enum;

-- Example schedule_config:
-- {
--   "frequency": "daily" | "weekly" | "monthly",
--   "time": "09:00",
--   "timezone": "America/New_York",
--   "daysOfWeek": [1, 3, 5],  -- for weekly
--   "dayOfMonth": 15  -- for monthly
-- }
```

### New Indexes

```sql
-- Optimize lookback queries
CREATE INDEX idx_collections_lookback ON report_data_collections
USING GIN (lookback_config);

-- Optimize week-based queries for backfill
CREATE INDEX idx_data_weeks_date_range ON report_data_weeks (week_start, week_end);

-- Optimize schedule lookups with backfill
CREATE INDEX idx_schedules_backfill ON workflow_schedules (backfill_status, backfill_collection_id)
WHERE backfill_status IS NOT NULL;

-- Composite index for efficient progress tracking
CREATE INDEX idx_collection_progress ON report_data_weeks (collection_id, status, week_start);
```

### New Audit Table

```sql
-- Track report builder flow usage
CREATE TABLE report_builder_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
  step_completed TEXT NOT NULL,  -- 'parameters', 'schedule', 'review', 'submit'
  configuration JSONB NOT NULL,  -- Full configuration at each step
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for user activity tracking
CREATE INDEX idx_builder_audit_user ON report_builder_audit (user_id, created_at DESC);
```

## Migration Script

```sql
-- Full migration to apply all changes
BEGIN;

-- 1. Update report_data_collections
ALTER TABLE report_data_collections
ADD COLUMN IF NOT EXISTS lookback_config JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS segmentation_config JSONB DEFAULT NULL;

-- 2. Create backfill status enum
DO $$ BEGIN
  CREATE TYPE backfill_status_enum AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'partial');
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

-- 3. Update workflow_schedules
ALTER TABLE workflow_schedules
ADD COLUMN IF NOT EXISTS backfill_status backfill_status_enum DEFAULT NULL,
ADD COLUMN IF NOT EXISTS backfill_collection_id UUID REFERENCES report_data_collections(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS schedule_config JSONB DEFAULT NULL;

-- 4. Create indexes
CREATE INDEX IF NOT EXISTS idx_collections_lookback ON report_data_collections USING GIN (lookback_config);
CREATE INDEX IF NOT EXISTS idx_data_weeks_date_range ON report_data_weeks (week_start, week_end);
CREATE INDEX IF NOT EXISTS idx_schedules_backfill ON workflow_schedules (backfill_status, backfill_collection_id)
WHERE backfill_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_collection_progress ON report_data_weeks (collection_id, status, week_start);

-- 5. Create audit table
CREATE TABLE IF NOT EXISTS report_builder_audit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
  step_completed TEXT NOT NULL,
  configuration JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_builder_audit_user ON report_builder_audit (user_id, created_at DESC);

COMMIT;
```

## Rationale

### Lookback Configuration Storage
Using JSONB for `lookback_config` provides flexibility for both relative and custom date ranges without requiring multiple columns. This allows future extensions like "last quarter" or "year-to-date" without schema changes.

### Segmentation for Backfill
The `segmentation_config` JSONB field enables dynamic configuration of how historical data is processed, allowing users to balance between processing speed (smaller segments) and API efficiency (larger segments).

### Backfill Status Tracking
Linking schedules to collections via `backfill_collection_id` maintains referential integrity while allowing schedules to exist independently. The enum type ensures data consistency for status tracking.

### Performance Considerations
- GIN index on JSONB columns enables efficient querying of configuration options
- Date range indexes optimize temporal queries during backfill operations
- Composite indexes reduce query time for progress tracking across hundreds of weekly segments
- Partial index on backfill status avoids indexing NULL values for non-backfill schedules

### Data Integrity
- Foreign key constraints ensure collections and schedules remain linked
- ON DELETE behaviors preserve audit trail while cleaning up orphaned references
- JSONB validation happens at application layer to maintain schema flexibility