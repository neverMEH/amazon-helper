-- Migration: Instance Templates Table
-- Creates table for storing SQL templates scoped to specific AMC instances
-- This enables users to save and reuse queries specific to each instance

BEGIN;

-- ============================================================================
-- 1. Create instance_templates table
-- ============================================================================
-- Purpose: Store reusable SQL query templates for specific AMC instances
-- Pattern: User-scoped templates associated with instances for quick workflow creation

CREATE TABLE instance_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL CHECK (char_length(name) > 0 AND char_length(name) <= 255),
    description TEXT,
    sql_query TEXT NOT NULL CHECK (char_length(sql_query) > 0),
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    tags JSONB DEFAULT '[]',
    usage_count INTEGER DEFAULT 0 CHECK (usage_count >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 2. Performance Indexes
-- ============================================================================

-- Most common query: get all templates for a specific instance and user
CREATE INDEX idx_instance_templates_instance_user ON instance_templates(instance_id, user_id);

-- Get templates for specific instance (for admin/debugging)
CREATE INDEX idx_instance_templates_instance ON instance_templates(instance_id);

-- Get templates by user (for user's template list across instances)
CREATE INDEX idx_instance_templates_user ON instance_templates(user_id);

-- Lookup template by template_id (for GET/PUT/DELETE operations)
CREATE INDEX idx_instance_templates_template_id ON instance_templates(template_id);

-- ============================================================================
-- 3. Row Level Security (RLS)
-- ============================================================================

-- Enable Row Level Security
ALTER TABLE instance_templates ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only view their own templates
CREATE POLICY "Users can view own instance templates"
    ON instance_templates FOR SELECT
    USING (auth.uid()::uuid = user_id);

-- RLS Policy: Users can only insert templates with their own user_id
CREATE POLICY "Users can insert own instance templates"
    ON instance_templates FOR INSERT
    WITH CHECK (auth.uid()::uuid = user_id);

-- RLS Policy: Users can only update their own templates
CREATE POLICY "Users can update own instance templates"
    ON instance_templates FOR UPDATE
    USING (auth.uid()::uuid = user_id);

-- RLS Policy: Users can only delete their own templates
CREATE POLICY "Users can delete own instance templates"
    ON instance_templates FOR DELETE
    USING (auth.uid()::uuid = user_id);

-- ============================================================================
-- 4. Auto-update Trigger
-- ============================================================================

-- Auto-update trigger for updated_at column
CREATE TRIGGER update_instance_templates_updated_at
    BEFORE UPDATE ON instance_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. Table and Column Documentation
-- ============================================================================

COMMENT ON TABLE instance_templates IS 'Stores reusable SQL query templates scoped to specific AMC instances. Used for quick workflow creation without parameter management overhead.';
COMMENT ON COLUMN instance_templates.template_id IS 'Human-readable unique identifier with format tpl_inst_{random} for logging and debugging';
COMMENT ON COLUMN instance_templates.name IS 'Template name for easy identification (required, 1-255 characters)';
COMMENT ON COLUMN instance_templates.description IS 'Optional description explaining what the template does';
COMMENT ON COLUMN instance_templates.sql_query IS 'The actual SQL query text (required, non-empty)';
COMMENT ON COLUMN instance_templates.instance_id IS 'Foreign key to amc_instances - templates are scoped to specific instances';
COMMENT ON COLUMN instance_templates.user_id IS 'Owner of the template (templates are private to users)';
COMMENT ON COLUMN instance_templates.tags IS 'Optional array of tags for organization and filtering';
COMMENT ON COLUMN instance_templates.usage_count IS 'Number of times this template has been used to create workflows';

COMMIT;

-- ============================================================================
-- Rollback Instructions
-- ============================================================================
-- If migration needs to be reverted, run:
-- BEGIN;
-- DROP TABLE IF EXISTS instance_templates CASCADE;
-- COMMIT;
