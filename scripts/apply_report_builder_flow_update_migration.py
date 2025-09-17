#!/usr/bin/env python3
"""
Apply Report Builder Flow Update database migration
Adds lookback configuration, enhanced scheduling, and audit tracking
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


def get_supabase_client() -> Client:
    """Create Supabase client with service role key"""
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not service_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    return create_client(url, service_key)


def execute_migration(client: Client) -> dict:
    """Execute the Report Builder Flow Update migration"""
    results = {
        'success': [],
        'errors': [],
        'warnings': []
    }

    migration_sql = """
    -- ============================================================
    -- REPORT BUILDER FLOW UPDATE - DATABASE MIGRATION
    -- ============================================================
    -- Adds lookback configuration, enhanced scheduling, and audit tracking
    -- for the improved 4-step Report Builder flow
    -- ============================================================

    BEGIN;

    -- 1. Update report_data_collections with lookback and segmentation config
    ALTER TABLE report_data_collections
    ADD COLUMN IF NOT EXISTS lookback_config JSONB DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS segmentation_config JSONB DEFAULT NULL;

    -- Example lookback_config:
    -- {
    --   "type": "relative" | "custom",
    --   "value": 7 | 14 | 30,  -- for relative
    --   "unit": "days" | "weeks" | "months",
    --   "startDate": "2025-01-01",  -- for custom
    --   "endDate": "2025-01-31"
    -- }

    -- Example segmentation_config:
    -- {
    --   "type": "daily" | "weekly" | "monthly",
    --   "parallel_limit": 10,
    --   "retry_failed": true
    -- }

    -- 2. Create backfill status enum if not exists
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'backfill_status_enum') THEN
            CREATE TYPE backfill_status_enum AS ENUM (
                'pending',
                'in_progress',
                'completed',
                'failed',
                'partial'
            );
        END IF;
    END $$;

    -- 3. Update workflow_schedules with backfill tracking
    ALTER TABLE workflow_schedules
    ADD COLUMN IF NOT EXISTS backfill_status backfill_status_enum DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS backfill_collection_id UUID REFERENCES report_data_collections(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS schedule_config JSONB DEFAULT NULL;

    -- Example schedule_config:
    -- {
    --   "frequency": "daily" | "weekly" | "monthly",
    --   "time": "09:00",
    --   "timezone": "America/New_York",
    --   "daysOfWeek": [1, 3, 5],  -- for weekly
    --   "dayOfMonth": 15  -- for monthly
    -- }

    -- 4. Create report_builder_audit table
    CREATE TABLE IF NOT EXISTS report_builder_audit (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
        step_completed TEXT NOT NULL CHECK (step_completed IN ('parameters', 'schedule', 'review', 'submit')),
        configuration JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT valid_step CHECK (step_completed IN ('parameters', 'schedule', 'review', 'submit'))
    );

    -- 5. Create performance indexes

    -- Optimize lookback queries with GIN index
    CREATE INDEX IF NOT EXISTS idx_collections_lookback
    ON report_data_collections USING GIN (lookback_config);

    -- Optimize segmentation queries
    CREATE INDEX IF NOT EXISTS idx_collections_segmentation
    ON report_data_collections USING GIN (segmentation_config);

    -- Optimize week-based queries for backfill
    CREATE INDEX IF NOT EXISTS idx_data_weeks_date_range
    ON report_data_weeks (week_start, week_end);

    -- Optimize schedule lookups with backfill
    CREATE INDEX IF NOT EXISTS idx_schedules_backfill
    ON workflow_schedules (backfill_status, backfill_collection_id)
    WHERE backfill_status IS NOT NULL;

    -- Composite index for efficient progress tracking
    CREATE INDEX IF NOT EXISTS idx_collection_progress
    ON report_data_weeks (collection_id, status, week_start);

    -- Index for user activity tracking
    CREATE INDEX IF NOT EXISTS idx_builder_audit_user
    ON report_builder_audit (user_id, created_at DESC);

    -- Index for workflow audit tracking
    CREATE INDEX IF NOT EXISTS idx_builder_audit_workflow
    ON report_builder_audit (workflow_id, created_at DESC);

    -- 6. Create helper functions for lookback calculations
    CREATE OR REPLACE FUNCTION calculate_lookback_dates(config JSONB)
    RETURNS TABLE (start_date DATE, end_date DATE) AS $$
    DECLARE
        lookback_type TEXT;
        lookback_value INTEGER;
        lookback_unit TEXT;
    BEGIN
        lookback_type := config->>'type';

        IF lookback_type = 'custom' THEN
            start_date := (config->>'startDate')::DATE;
            end_date := (config->>'endDate')::DATE;
        ELSIF lookback_type = 'relative' THEN
            lookback_value := (config->>'value')::INTEGER;
            lookback_unit := COALESCE(config->>'unit', 'days');

            end_date := CURRENT_DATE;

            CASE lookback_unit
                WHEN 'days' THEN
                    start_date := end_date - (lookback_value || ' days')::INTERVAL;
                WHEN 'weeks' THEN
                    start_date := end_date - (lookback_value || ' weeks')::INTERVAL;
                WHEN 'months' THEN
                    start_date := end_date - (lookback_value || ' months')::INTERVAL;
                ELSE
                    start_date := end_date - (lookback_value || ' days')::INTERVAL;
            END CASE;
        ELSE
            -- Default to last 7 days
            end_date := CURRENT_DATE;
            start_date := end_date - INTERVAL '7 days';
        END IF;

        RETURN QUERY SELECT start_date, end_date;
    END;
    $$ LANGUAGE plpgsql;

    -- 7. Create function to validate lookback within AMC limits
    CREATE OR REPLACE FUNCTION validate_lookback_limit(config JSONB)
    RETURNS BOOLEAN AS $$
    DECLARE
        start_date DATE;
        end_date DATE;
        days_diff INTEGER;
    BEGIN
        SELECT * INTO start_date, end_date FROM calculate_lookback_dates(config);
        days_diff := end_date - start_date;

        -- AMC has a 14-month (approximately 425 days) data retention limit
        RETURN days_diff <= 425;
    END;
    $$ LANGUAGE plpgsql;

    -- 8. Create function to calculate segmentation intervals
    CREATE OR REPLACE FUNCTION calculate_segmentation_intervals(
        start_date DATE,
        end_date DATE,
        segment_type TEXT
    )
    RETURNS TABLE (
        segment_start DATE,
        segment_end DATE,
        segment_number INTEGER
    ) AS $$
    DECLARE
        current_start DATE;
        current_end DATE;
        segment_num INTEGER := 1;
    BEGIN
        current_start := start_date;

        WHILE current_start <= end_date LOOP
            CASE segment_type
                WHEN 'daily' THEN
                    current_end := current_start;
                WHEN 'weekly' THEN
                    current_end := LEAST(current_start + INTERVAL '6 days', end_date);
                WHEN 'monthly' THEN
                    current_end := LEAST(
                        (current_start + INTERVAL '1 month' - INTERVAL '1 day')::DATE,
                        end_date
                    );
                ELSE
                    -- Default to weekly
                    current_end := LEAST(current_start + INTERVAL '6 days', end_date);
            END CASE;

            RETURN QUERY SELECT current_start, current_end, segment_num;

            segment_num := segment_num + 1;
            current_start := current_end + INTERVAL '1 day';
        END LOOP;
    END;
    $$ LANGUAGE plpgsql;

    -- 9. Create view for Report Builder audit trail
    CREATE OR REPLACE VIEW report_builder_activity AS
    SELECT
        rba.id,
        rba.user_id,
        u.email AS user_email,
        rba.workflow_id,
        w.name AS workflow_name,
        rba.step_completed,
        rba.configuration,
        rba.created_at,
        -- Extract specific configuration details
        CASE
            WHEN rba.step_completed = 'parameters' THEN
                rba.configuration->'lookback_config'
            ELSE NULL
        END AS lookback_config,
        CASE
            WHEN rba.step_completed = 'schedule' THEN
                rba.configuration->'schedule_type'
            ELSE NULL
        END AS schedule_type,
        CASE
            WHEN rba.step_completed = 'schedule' THEN
                rba.configuration->'backfill_config'
            ELSE NULL
        END AS backfill_config
    FROM report_builder_audit rba
    LEFT JOIN users u ON u.id = rba.user_id
    LEFT JOIN workflows w ON w.id = rba.workflow_id
    ORDER BY rba.created_at DESC;

    -- 10. Add comments for documentation
    COMMENT ON COLUMN report_data_collections.lookback_config IS
        'Configuration for date range selection: relative (e.g., last 7 days) or custom date range';

    COMMENT ON COLUMN report_data_collections.segmentation_config IS
        'Configuration for backfill segmentation: daily, weekly, or monthly processing chunks';

    COMMENT ON COLUMN workflow_schedules.backfill_status IS
        'Status of 365-day historical backfill operation';

    COMMENT ON COLUMN workflow_schedules.backfill_collection_id IS
        'Reference to the collection handling the backfill operation';

    COMMENT ON COLUMN workflow_schedules.schedule_config IS
        'Enhanced schedule configuration including timezone and frequency details';

    COMMENT ON TABLE report_builder_audit IS
        'Audit trail for Report Builder flow usage tracking user interactions through each step';

    COMMIT;

    -- ============================================================
    -- MIGRATION COMPLETE
    -- ============================================================
    """

    try:
        # Execute the migration using Supabase RPC or direct SQL
        print("Executing Report Builder Flow Update migration...")

        # Note: Supabase Python client doesn't directly support raw SQL execution
        # You would typically use the Supabase Dashboard SQL editor or psycopg2
        # For this implementation, we'll document the approach

        results['warnings'].append(
            "Migration SQL has been generated. Please execute it via:\n"
            "1. Supabase Dashboard SQL Editor, or\n"
            "2. Direct PostgreSQL connection using psycopg2"
        )

        # Save migration to file for manual execution
        migration_file = Path(__file__).parent / 'report_builder_flow_update_migration.sql'
        with open(migration_file, 'w') as f:
            f.write(migration_sql)

        results['success'].append(f"Migration SQL saved to {migration_file}")

        # Test that we can connect to Supabase
        test = client.table('users').select('id').limit(1).execute()
        results['success'].append("Successfully connected to Supabase")

    except Exception as e:
        results['errors'].append(f"Migration error: {str(e)}")

    return results


def verify_migration(client: Client) -> dict:
    """Verify that the migration was applied successfully"""
    verification_results = {
        'tables': [],
        'columns': [],
        'indexes': [],
        'functions': []
    }

    checks = [
        # Check for new columns
        {
            'type': 'column',
            'table': 'report_data_collections',
            'columns': ['lookback_config', 'segmentation_config']
        },
        {
            'type': 'column',
            'table': 'workflow_schedules',
            'columns': ['backfill_status', 'backfill_collection_id', 'schedule_config']
        },
        # Check for new table
        {
            'type': 'table',
            'table': 'report_builder_audit'
        }
    ]

    for check in checks:
        if check['type'] == 'table':
            try:
                result = client.table(check['table']).select('id').limit(1).execute()
                verification_results['tables'].append(f"✓ Table {check['table']} exists")
            except:
                verification_results['tables'].append(f"✗ Table {check['table']} not found")

        elif check['type'] == 'column':
            for col in check['columns']:
                try:
                    # Attempt to query the column
                    result = client.table(check['table']).select(col).limit(1).execute()
                    verification_results['columns'].append(f"✓ Column {check['table']}.{col} exists")
                except:
                    verification_results['columns'].append(f"✗ Column {check['table']}.{col} not found")

    return verification_results


def main():
    """Main execution function"""
    print("=" * 60)
    print("Report Builder Flow Update Migration")
    print("=" * 60)

    try:
        client = get_supabase_client()
        print("✓ Connected to Supabase")

        # Execute migration
        print("\nExecuting migration...")
        results = execute_migration(client)

        # Display results
        if results['success']:
            print("\n✓ Success:")
            for msg in results['success']:
                print(f"  - {msg}")

        if results['warnings']:
            print("\n⚠ Warnings:")
            for msg in results['warnings']:
                print(f"  - {msg}")

        if results['errors']:
            print("\n✗ Errors:")
            for msg in results['errors']:
                print(f"  - {msg}")

        # Verify migration (if manually applied)
        print("\n" + "=" * 60)
        print("Migration Verification")
        print("=" * 60)

        verification = verify_migration(client)

        for category, items in verification.items():
            if items:
                print(f"\n{category.title()}:")
                for item in items:
                    print(f"  {item}")

        print("\n" + "=" * 60)
        print("Migration process complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())