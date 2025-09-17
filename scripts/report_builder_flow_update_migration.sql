
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
    