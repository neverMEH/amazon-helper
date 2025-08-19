"""
Database migration to add schedule enhancements
Run this script to add the new scheduling tables and columns
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from amc_manager.core.supabase_client import get_supabase_client
from amc_manager.core.logger_simple import get_logger

logger = get_logger(__name__)


async def apply_schedule_enhancements():
    """Apply database schema enhancements for scheduling"""
    
    db = get_supabase_client()
    
    try:
        logger.info("Starting schedule enhancement migration...")
        
        # SQL to add new columns to workflow_schedules table
        alter_workflow_schedules_sql = """
        -- Add new columns to workflow_schedules if they don't exist
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
        
        -- Add index for user_id if not exists
        CREATE INDEX IF NOT EXISTS idx_workflow_schedules_user_id ON workflow_schedules(user_id);
        CREATE INDEX IF NOT EXISTS idx_workflow_schedules_next_run ON workflow_schedules(next_run_at) WHERE is_active = true;
        """
        
        # SQL to create schedule_runs table
        create_schedule_runs_sql = """
        -- Create schedule_runs table for tracking execution groups
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
        
        -- Add indexes for schedule_runs
        CREATE INDEX IF NOT EXISTS idx_schedule_runs_schedule_id ON schedule_runs(schedule_id);
        CREATE INDEX IF NOT EXISTS idx_schedule_runs_status ON schedule_runs(status);
        CREATE INDEX IF NOT EXISTS idx_schedule_runs_scheduled_at ON schedule_runs(scheduled_at DESC);
        """
        
        # SQL to add schedule_run_id to workflow_executions
        alter_workflow_executions_sql = """
        -- Add schedule_run_id to workflow_executions for linking
        ALTER TABLE workflow_executions
        ADD COLUMN IF NOT EXISTS schedule_run_id UUID REFERENCES schedule_runs(id) ON DELETE SET NULL;
        
        -- Add index for efficient queries
        CREATE INDEX IF NOT EXISTS idx_workflow_executions_schedule_run_id ON workflow_executions(schedule_run_id);
        """
        
        # SQL to create schedule_metrics view for analytics
        create_schedule_metrics_view_sql = """
        -- Create or replace view for schedule metrics
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
        """
        
        # Execute migrations
        logger.info("Applying workflow_schedules table enhancements...")
        await db.rpc('exec_sql', {'sql': alter_workflow_schedules_sql}).execute()
        
        logger.info("Creating schedule_runs table...")
        await db.rpc('exec_sql', {'sql': create_schedule_runs_sql}).execute()
        
        logger.info("Adding schedule_run_id to workflow_executions...")
        await db.rpc('exec_sql', {'sql': alter_workflow_executions_sql}).execute()
        
        logger.info("Creating schedule_metrics view...")
        await db.rpc('exec_sql', {'sql': create_schedule_metrics_view_sql}).execute()
        
        # Enable RLS on new table
        enable_rls_sql = """
        -- Enable RLS on schedule_runs
        ALTER TABLE schedule_runs ENABLE ROW LEVEL SECURITY;
        
        -- Create RLS policies for schedule_runs
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
        """
        
        logger.info("Enabling RLS on schedule_runs table...")
        await db.rpc('exec_sql', {'sql': enable_rls_sql}).execute()
        
        logger.info("✅ Schedule enhancement migration completed successfully!")
        
        # Verify the changes
        logger.info("Verifying migration...")
        
        # Check if new columns exist
        check_columns_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_schedules' 
        AND column_name IN ('schedule_type', 'interval_days', 'user_id')
        """
        
        result = await db.rpc('exec_sql', {'sql': check_columns_sql}).execute()
        
        if result.data:
            logger.info(f"✅ New columns added successfully: {result.data}")
        
        # Check if schedule_runs table exists
        check_table_sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'schedule_runs'
        )
        """
        
        result = await db.rpc('exec_sql', {'sql': check_table_sql}).execute()
        
        if result.data and result.data[0].get('exists'):
            logger.info("✅ schedule_runs table created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        
        # Attempt rollback
        logger.info("Attempting to rollback changes...")
        rollback_sql = """
        -- Remove added columns (if you want to rollback)
        -- ALTER TABLE workflow_schedules 
        -- DROP COLUMN IF EXISTS schedule_type,
        -- DROP COLUMN IF EXISTS interval_days,
        -- DROP COLUMN IF EXISTS interval_config,
        -- DROP COLUMN IF EXISTS execution_history_limit,
        -- DROP COLUMN IF EXISTS notification_config,
        -- DROP COLUMN IF EXISTS cost_limit,
        -- DROP COLUMN IF EXISTS auto_pause_on_failure,
        -- DROP COLUMN IF EXISTS failure_threshold,
        -- DROP COLUMN IF EXISTS consecutive_failures;
        
        -- DROP TABLE IF EXISTS schedule_runs CASCADE;
        -- DROP VIEW IF EXISTS schedule_metrics;
        
        -- Note: Uncomment above lines only if you need to rollback
        SELECT 'Rollback SQL ready but not executed - uncomment lines in rollback_sql to execute';
        """
        
        logger.error("Rollback SQL prepared but not executed. Review and run manually if needed.")
        return False


async def main():
    """Main function"""
    success = await apply_schedule_enhancements()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the new scheduling features")
        print("2. Update the API endpoints to use the new schema")
        print("3. Build the frontend components")
    else:
        print("\n❌ Migration failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())