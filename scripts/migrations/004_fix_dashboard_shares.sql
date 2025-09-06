-- Fix dashboard_shares table structure
-- This handles cases where the table exists but with different column names

BEGIN;

-- First check what columns exist in dashboard_shares
DO $$
BEGIN
    -- If the table exists but doesn't have shared_with column, we may need to add it or rename
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'dashboard_shares'
    ) THEN
        -- Check if shared_with column exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'dashboard_shares' 
            AND column_name = 'shared_with'
        ) THEN
            -- Check if there's a similar column with different name (like shared_with_user_id)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dashboard_shares' 
                AND column_name = 'shared_with_user_id'
            ) THEN
                -- Rename the column
                ALTER TABLE dashboard_shares RENAME COLUMN shared_with_user_id TO shared_with;
                RAISE NOTICE 'Renamed shared_with_user_id to shared_with';
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dashboard_shares' 
                AND column_name = 'user_id'
            ) THEN
                -- Rename user_id to shared_with
                ALTER TABLE dashboard_shares RENAME COLUMN user_id TO shared_with;
                RAISE NOTICE 'Renamed user_id to shared_with';
            ELSE
                -- Add the column if it doesn't exist in any form
                ALTER TABLE dashboard_shares ADD COLUMN shared_with UUID REFERENCES users(id) ON DELETE CASCADE;
                RAISE NOTICE 'Added shared_with column';
            END IF;
        END IF;
        
        -- Also ensure shared_by column exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'dashboard_shares' 
            AND column_name = 'shared_by'
        ) THEN
            -- Check for alternative names
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dashboard_shares' 
                AND column_name = 'shared_by_user_id'
            ) THEN
                ALTER TABLE dashboard_shares RENAME COLUMN shared_by_user_id TO shared_by;
                RAISE NOTICE 'Renamed shared_by_user_id to shared_by';
            ELSIF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dashboard_shares' 
                AND column_name = 'owner_id'
            ) THEN
                ALTER TABLE dashboard_shares RENAME COLUMN owner_id TO shared_by;
                RAISE NOTICE 'Renamed owner_id to shared_by';
            ELSE
                ALTER TABLE dashboard_shares ADD COLUMN shared_by UUID REFERENCES users(id) ON DELETE CASCADE;
                RAISE NOTICE 'Added shared_by column';
            END IF;
        END IF;
        
        -- Drop and recreate the unique constraint with correct column names
        ALTER TABLE dashboard_shares DROP CONSTRAINT IF EXISTS unique_dashboard_share;
        ALTER TABLE dashboard_shares ADD CONSTRAINT unique_dashboard_share UNIQUE(dashboard_id, shared_with);
        
    ELSE
        -- Create the table if it doesn't exist
        CREATE TABLE dashboard_shares (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
            shared_by UUID REFERENCES users(id) ON DELETE CASCADE,
            shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
            permission_level VARCHAR(50) NOT NULL DEFAULT 'view',
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_dashboard_share UNIQUE(dashboard_id, shared_with)
        );
        RAISE NOTICE 'Created dashboard_shares table';
    END IF;
END $$;

-- Now create the index safely
CREATE INDEX IF NOT EXISTS idx_shares_dashboard_id ON dashboard_shares(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_shares_shared_with ON dashboard_shares(shared_with);
CREATE INDEX IF NOT EXISTS idx_shares_shared_by ON dashboard_shares(shared_by);

-- Verify the final structure
DO $$
DECLARE
    col_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'dashboard_shares'
    AND column_name IN ('dashboard_id', 'shared_by', 'shared_with', 'permission_level');
    
    IF col_count < 4 THEN
        RAISE EXCEPTION 'dashboard_shares table is missing required columns';
    ELSE
        RAISE NOTICE '✅ dashboard_shares table structure is correct';
    END IF;
END $$;

COMMIT;

-- Verification query to run after migration
/*
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'dashboard_shares'
ORDER BY ordinal_position;
*/