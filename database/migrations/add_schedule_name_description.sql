-- Migration: Add name and description fields to workflow_schedules table
-- Run this SQL in your Supabase SQL editor

-- Add name and description columns to workflow_schedules
ALTER TABLE workflow_schedules 
ADD COLUMN IF NOT EXISTS name TEXT,
ADD COLUMN IF NOT EXISTS description TEXT;

-- Update existing schedules to have a default name based on workflow name
UPDATE workflow_schedules ws
SET name = COALESCE(ws.name, w.name || ' Schedule')
FROM workflows w
WHERE ws.workflow_id = w.id
AND ws.name IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN workflow_schedules.name IS 'User-friendly name for the schedule';
COMMENT ON COLUMN workflow_schedules.description IS 'Optional description or notes about the schedule';