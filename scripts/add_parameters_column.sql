-- Add missing parameters column to schedule_runs table
-- Run this in the Supabase SQL editor

-- Check if column exists and add it if not
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'schedule_runs' 
        AND column_name = 'parameters'
    ) THEN
        ALTER TABLE public.schedule_runs 
        ADD COLUMN parameters jsonb;
        
        COMMENT ON COLUMN public.schedule_runs.parameters IS 
        'Execution parameters used for this run (date ranges, filters, etc.)';
        
        RAISE NOTICE 'Parameters column added successfully';
    ELSE
        RAISE NOTICE 'Parameters column already exists';
    END IF;
END $$;