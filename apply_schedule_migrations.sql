-- Schedule Enhancement Migrations
-- Run this SQL directly in Supabase SQL Editor

-- 1. Add new columns to workflow_schedules
ALTER TABLE workflow_schedules 
ADD COLUMN IF NOT EXISTS schedule_type TEXT DEFAULT 'cron',
ADD COLUMN IF NOT EXISTS interval_days INTEGER,
ADD COLUMN IF NOT EXISTS interval_config JSONB,
ADD COLUMN IF NOT EXISTS execution_history_limit INTEGER DEFAULT 30,
ADD COLUMN IF NOT EXISTS notification_config JSONB,
ADD COLUMN IF NOT EXISTS cost_limit DECIMAL(10, 2),
ADD COLUMN IF NOT EXISTS auto_pause_on_failure BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS failure_threshold INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- 2. Add indexes for workflow_schedules
CREATE INDEX IF NOT EXISTS idx_workflow_schedules_user_id ON workflow_schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_schedules_next_run ON workflow_schedules(next_run_at) WHERE is_active = true;

-- 3. Create schedule_runs table
CREATE TABLE IF NOT EXISTS schedule_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id UUID REFERENCES workflow_schedules(id) ON DELETE CASCADE,
    run_number INTEGER NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'pending',
    execution_count INTEGER DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    total_rows BIGINT DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0,
    error_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_schedule_run UNIQUE(schedule_id, run_number),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- 4. Add indexes for schedule_runs
CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_id ON schedule_runs(schedule_id);
CREATE INDEX IF NOT EXISTS idx_schedule_runs_status ON schedule_runs(status);
CREATE INDEX IF NOT EXISTS idx_schedule_runs_scheduled_at ON schedule_runs(scheduled_at DESC);

-- 5. Add schedule_run_id to workflow_executions
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS schedule_run_id UUID REFERENCES schedule_runs(id) ON DELETE SET NULL;

-- 6. Add index for workflow_executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_schedule_run_id ON workflow_executions(schedule_run_id);

-- 7. Create schedule_metrics view
CREATE OR REPLACE VIEW schedule_metrics AS
SELECT 
    ws.id as schedule_id,
    ws.schedule_id as schedule_identifier,
    ws.cron_expression,
    ws.timezone,
    ws.is_active,
    ws.last_run_at,
    ws.next_run_at,
    w.name as workflow_name,
    w.workflow_id,
    COUNT(DISTINCT sr.id) as total_runs,
    COUNT(DISTINCT sr.id) FILTER (WHERE sr.status = 'completed') as successful_runs,
    COUNT(DISTINCT sr.id) FILTER (WHERE sr.status = 'failed') as failed_runs,
    AVG(EXTRACT(EPOCH FROM (sr.completed_at - sr.started_at))) FILTER (WHERE sr.status = 'completed') as avg_runtime_seconds,
    SUM(sr.total_rows) as total_rows_processed,
    SUM(sr.total_cost) as total_cost,
    MAX(sr.scheduled_at) as last_scheduled_at,
    MIN(sr.scheduled_at) as first_scheduled_at
FROM workflow_schedules ws
LEFT JOIN workflows w ON ws.workflow_id = w.id
LEFT JOIN schedule_runs sr ON ws.id = sr.schedule_id
GROUP BY ws.id, ws.schedule_id, ws.cron_expression, ws.timezone, ws.is_active, 
         ws.last_run_at, ws.next_run_at, w.name, w.workflow_id;

-- 8. Enable RLS on schedule_runs
ALTER TABLE schedule_runs ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS policies for schedule_runs
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own schedule runs" ON schedule_runs;
DROP POLICY IF EXISTS "Users can create their own schedule runs" ON schedule_runs;
DROP POLICY IF EXISTS "Users can update their own schedule runs" ON schedule_runs;

-- Create new policies
CREATE POLICY "Users can view their own schedule runs" ON schedule_runs
    FOR SELECT USING (
        schedule_id IN (
            SELECT id FROM workflow_schedules WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create their own schedule runs" ON schedule_runs
    FOR INSERT WITH CHECK (
        schedule_id IN (
            SELECT id FROM workflow_schedules WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own schedule runs" ON schedule_runs
    FOR UPDATE USING (
        schedule_id IN (
            SELECT id FROM workflow_schedules WHERE user_id = auth.uid()
        )
    );

-- 10. Grant permissions
GRANT ALL ON schedule_runs TO authenticated;
GRANT ALL ON schedule_metrics TO authenticated;

-- Verify the migration
SELECT 
    'Migration completed successfully!' as message,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'workflow_schedules' AND column_name = 'schedule_type') as schedule_type_exists,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'schedule_runs') as schedule_runs_exists,
    (SELECT COUNT(*) FROM information_schema.views WHERE table_name = 'schedule_metrics') as schedule_metrics_exists;