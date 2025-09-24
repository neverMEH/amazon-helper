-- Add Snowflake integration fields to workflow_executions table

-- Add Snowflake configuration fields
ALTER TABLE workflow_executions
ADD COLUMN IF NOT EXISTS snowflake_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS snowflake_table_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS snowflake_schema_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS snowflake_warehouse VARCHAR(255),
ADD COLUMN IF NOT EXISTS snowflake_status VARCHAR(50) DEFAULT 'pending', -- pending, uploading, completed, failed
ADD COLUMN IF NOT EXISTS snowflake_error_message TEXT,
ADD COLUMN IF NOT EXISTS snowflake_uploaded_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS snowflake_row_count INTEGER;

-- Add index for Snowflake queries
CREATE INDEX IF NOT EXISTS idx_workflow_executions_snowflake_enabled 
ON workflow_executions(snowflake_enabled);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_snowflake_status 
ON workflow_executions(snowflake_status);

-- Add Snowflake configuration table for user settings
CREATE TABLE IF NOT EXISTS snowflake_configurations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    account_identifier VARCHAR(255) NOT NULL,
    warehouse VARCHAR(255) NOT NULL,
    database VARCHAR(255) NOT NULL,
    schema VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    username VARCHAR(255),
    password_encrypted TEXT, -- Encrypted password
    private_key_encrypted TEXT, -- Encrypted private key for key-pair auth
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add RLS policies for Snowflake configurations
ALTER TABLE snowflake_configurations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own Snowflake configurations" ON snowflake_configurations
FOR ALL
USING (user_id = auth.uid());

-- Add index for user lookups
CREATE INDEX IF NOT EXISTS idx_snowflake_configurations_user_id 
ON snowflake_configurations(user_id);

CREATE INDEX IF NOT EXISTS idx_snowflake_configurations_active 
ON snowflake_configurations(is_active);
