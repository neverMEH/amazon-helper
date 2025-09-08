# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-09-08-fix-workflow-execution-tracking/spec.md

> Created: 2025-09-08
> Version: 1.0.0

## Schema Changes

### Current Schema State

The `report_data_weeks` table already contains an `execution_id` column, but it is not being populated during data collection operations.

**Existing Table Structure**:
```sql
CREATE TABLE report_data_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    execution_id UUID,  -- ← This column exists but is not populated
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_message TEXT,
    
    CONSTRAINT fk_collection_id 
        FOREIGN KEY (collection_id) 
        REFERENCES report_data_collections(id) 
        ON DELETE CASCADE
);
```

### Schema Validation Requirements

#### Column Specifications
- **execution_id**: UUID type, nullable, should reference workflow_executions.id
- **Data Type**: UUID to match workflow_executions primary key
- **Nullability**: Must allow NULL for backward compatibility
- **Foreign Key**: Should reference workflow_executions table if referential integrity is desired

#### Foreign Key Relationship Analysis
```sql
-- Check if foreign key constraint should be added
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_name = 'report_data_weeks'
AND kcu.column_name = 'execution_id';
```

### Schema Verification Script

```sql
-- Verify execution_id column exists with correct properties
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public'
    AND table_name = 'report_data_weeks' 
    AND column_name = 'execution_id';

-- Expected result:
-- column_name: execution_id
-- data_type: uuid
-- is_nullable: YES
-- column_default: NULL
```

### Index Considerations

#### Current Indexes
Review existing indexes on report_data_weeks table:
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'report_data_weeks'
ORDER BY indexname;
```

#### Recommended Indexes
Consider adding index on execution_id for lookup performance:
```sql
-- Optional: Add index if execution_id lookups become frequent
CREATE INDEX CONCURRENTLY idx_report_data_weeks_execution_id 
ON report_data_weeks (execution_id) 
WHERE execution_id IS NOT NULL;

-- Composite index for collection + execution lookups  
CREATE INDEX CONCURRENTLY idx_report_data_weeks_collection_execution
ON report_data_weeks (collection_id, execution_id)
WHERE execution_id IS NOT NULL;
```

## Migrations

### Migration Script Template

Since the column already exists, no DDL migration is required. However, a verification script should be run:

```sql
-- migration_verify_execution_id_tracking.sql
-- Verification script for execution_id column readiness

BEGIN;

-- 1. Verify column exists with correct type
DO $$
DECLARE
    col_exists BOOLEAN;
    col_type TEXT;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'report_data_weeks' 
        AND column_name = 'execution_id'
    ) INTO col_exists;
    
    IF NOT col_exists THEN
        RAISE EXCEPTION 'execution_id column does not exist in report_data_weeks table';
    END IF;
    
    SELECT data_type INTO col_type
    FROM information_schema.columns 
    WHERE table_name = 'report_data_weeks' 
    AND column_name = 'execution_id';
    
    IF col_type != 'uuid' THEN
        RAISE EXCEPTION 'execution_id column type is %, expected uuid', col_type;
    END IF;
    
    RAISE NOTICE 'execution_id column verification passed';
END $$;

-- 2. Verify workflow_executions table exists (for potential FK)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'workflow_executions'
    ) THEN
        RAISE WARNING 'workflow_executions table does not exist - FK constraint not possible';
    ELSE
        RAISE NOTICE 'workflow_executions table exists - FK relationship possible';
    END IF;
END $$;

-- 3. Check current execution_id population
SELECT 
    COUNT(*) as total_weeks,
    COUNT(execution_id) as weeks_with_execution_id,
    ROUND(COUNT(execution_id)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as population_percentage
FROM report_data_weeks;

-- 4. Sample current data state
SELECT 
    collection_id,
    status,
    execution_id,
    created_at
FROM report_data_weeks 
ORDER BY created_at DESC 
LIMIT 5;

COMMIT;
```

### Data Quality Checks

#### Pre-Implementation Checks
```sql
-- Check current execution_id population
SELECT 
    'Current State' as check_type,
    COUNT(*) as total_records,
    COUNT(execution_id) as populated_execution_ids,
    COUNT(*) - COUNT(execution_id) as null_execution_ids
FROM report_data_weeks;

-- Check data types consistency  
SELECT DISTINCT 
    pg_typeof(execution_id) as execution_id_type
FROM report_data_weeks 
WHERE execution_id IS NOT NULL;
```

#### Post-Implementation Validation
```sql
-- Check new execution_id population after implementation
SELECT 
    DATE(created_at) as creation_date,
    COUNT(*) as total_records,
    COUNT(execution_id) as with_execution_id,
    ROUND(COUNT(execution_id)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as population_rate
FROM report_data_weeks 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY creation_date DESC;

-- Validate execution_ids exist in workflow_executions
SELECT 
    rdw.id,
    rdw.execution_id,
    we.id as execution_exists
FROM report_data_weeks rdw
LEFT JOIN workflow_executions we ON we.id = rdw.execution_id
WHERE rdw.execution_id IS NOT NULL
AND rdw.created_at >= CURRENT_DATE - INTERVAL '1 day'
LIMIT 10;
```

### Rollback Considerations

#### Rollback Strategy
Since no schema changes are required, rollback primarily involves:
1. Reverting application code changes
2. No database schema rollback needed
3. execution_id data can remain in place (no harm)

#### Data Cleanup (if needed)
```sql
-- Optional: Clear execution_id values if rollback required
UPDATE report_data_weeks 
SET execution_id = NULL,
    updated_at = NOW()
WHERE execution_id IS NOT NULL
AND created_at >= '2025-09-08'::DATE;  -- Only clear recent tracking
```

### Performance Impact Analysis

#### Query Performance Impact
```sql
-- Test query performance with execution_id joins
EXPLAIN ANALYZE
SELECT 
    rdw.collection_id,
    rdw.week_start_date,
    rdw.status,
    we.status as execution_status,
    we.created_at as execution_started
FROM report_data_weeks rdw
LEFT JOIN workflow_executions we ON we.id = rdw.execution_id
WHERE rdw.collection_id = 'sample-uuid'
ORDER BY rdw.week_start_date;
```

#### Storage Impact
- execution_id column: UUID type (16 bytes per row)
- Minimal storage impact for existing tables
- No significant impact on backup/restore operations