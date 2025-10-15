# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-10-15-instance-templates/spec.md

> Created: 2025-10-15
> Version: 1.0.0

## Schema Changes

### New Table: instance_templates

```sql
CREATE TABLE instance_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    sql_query TEXT NOT NULL,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    tags JSONB DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instance_templates_instance ON instance_templates(instance_id);
CREATE INDEX idx_instance_templates_user ON instance_templates(user_id);
CREATE INDEX idx_instance_templates_template_id ON instance_templates(template_id);
CREATE INDEX idx_instance_templates_instance_user ON instance_templates(instance_id, user_id);

-- Updated_at trigger
CREATE TRIGGER update_instance_templates_updated_at
    BEFORE UPDATE ON instance_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security
ALTER TABLE instance_templates ENABLE ROW LEVEL SECURITY;

-- Users can only see their own templates
CREATE POLICY instance_templates_select_own ON instance_templates
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own templates
CREATE POLICY instance_templates_insert_own ON instance_templates
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own templates
CREATE POLICY instance_templates_update_own ON instance_templates
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can only delete their own templates
CREATE POLICY instance_templates_delete_own ON instance_templates
    FOR DELETE USING (auth.uid() = user_id);
```

## Rationale

### Table Structure

**id (UUID)**: Primary key using Supabase's gen_random_uuid() for internal references and foreign keys.

**template_id (TEXT)**: Human-readable unique identifier with format `tpl_inst_{random}` to distinguish instance templates from global query templates in logs and debugging.

**name (TEXT, NOT NULL)**: Required template name for easy identification in lists and searches.

**description (TEXT, nullable)**: Optional description to provide context about what the template does.

**sql_query (TEXT, NOT NULL)**: The actual SQL query text. This is the core content of the template. Unlike query_templates, no parameter_schema or default_parameters fields are needed since this is simplified storage.

**instance_id (UUID, FK to amc_instances)**: Associates each template with a specific AMC instance. CASCADE delete ensures templates are automatically removed when an instance is deleted.

**user_id (UUID, FK to users)**: Owner of the template. CASCADE delete ensures templates are removed when user is deleted. Used for access control.

**tags (JSONB, default [])**: Optional array of tags for future organization/filtering capabilities. Stored as JSONB for PostgreSQL native JSON operations.

**usage_count (INTEGER, default 0)**: Track how many times the template has been used to create workflows. Helps identify popular templates.

**created_at/updated_at**: Standard timestamp fields for auditing and sorting. Updated_at automatically maintained by trigger.

### Indexes

**idx_instance_templates_instance**: Optimizes queries filtering by instance_id (primary use case: "show all templates for this instance").

**idx_instance_templates_user**: Optimizes queries filtering by user_id (access control checks).

**idx_instance_templates_template_id**: Optimizes single template lookups by template_id (GET operations).

**idx_instance_templates_instance_user**: Composite index for common query pattern: "show user's templates for specific instance" (most common query pattern).

### Row Level Security (RLS)

Templates are private to their owner. RLS policies ensure:
- Users can only SELECT their own templates
- Users can only INSERT templates with their own user_id
- Users can only UPDATE their own templates
- Users can only DELETE their own templates

This prevents users from accessing, modifying, or deleting other users' templates, even if they know the template_id.

### Data Integrity

**Foreign Key Constraints**:
- `instance_id` references `amc_instances(id)`: Ensures templates can only be created for valid instances. CASCADE delete removes templates if instance is deleted.
- `user_id` references `users(id)`: Ensures templates have valid owners. CASCADE delete removes templates if user is deleted.

**NOT NULL Constraints**:
- `name`: Every template must have a name
- `sql_query`: Every template must have SQL content
- `instance_id`: Every template must belong to an instance
- `user_id`: Every template must have an owner

**UNIQUE Constraint**:
- `template_id`: Ensures no duplicate template identifiers

## Migrations

### Migration Script: `apply_instance_templates_migration.py`

```python
"""
Migration script to create instance_templates table.
Run: python scripts/apply_instance_templates_migration.py
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

    supabase: Client = create_client(supabase_url, supabase_key)

    print("Creating instance_templates table...")

    migration_sql = """
    -- Create instance_templates table
    CREATE TABLE IF NOT EXISTS instance_templates (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        template_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        sql_query TEXT NOT NULL,
        instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
        tags JSONB DEFAULT '[]',
        usage_count INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_instance_templates_instance ON instance_templates(instance_id);
    CREATE INDEX IF NOT EXISTS idx_instance_templates_user ON instance_templates(user_id);
    CREATE INDEX IF NOT EXISTS idx_instance_templates_template_id ON instance_templates(template_id);
    CREATE INDEX IF NOT EXISTS idx_instance_templates_instance_user ON instance_templates(instance_id, user_id);

    -- Create updated_at trigger
    CREATE TRIGGER update_instance_templates_updated_at
        BEFORE UPDATE ON instance_templates
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Enable RLS
    ALTER TABLE instance_templates ENABLE ROW LEVEL SECURITY;

    -- Create RLS policies
    DROP POLICY IF EXISTS instance_templates_select_own ON instance_templates;
    CREATE POLICY instance_templates_select_own ON instance_templates
        FOR SELECT USING (auth.uid() = user_id);

    DROP POLICY IF EXISTS instance_templates_insert_own ON instance_templates;
    CREATE POLICY instance_templates_insert_own ON instance_templates
        FOR INSERT WITH CHECK (auth.uid() = user_id);

    DROP POLICY IF EXISTS instance_templates_update_own ON instance_templates;
    CREATE POLICY instance_templates_update_own ON instance_templates
        FOR UPDATE USING (auth.uid() = user_id);

    DROP POLICY IF EXISTS instance_templates_delete_own ON instance_templates;
    CREATE POLICY instance_templates_delete_own ON instance_templates
        FOR DELETE USING (auth.uid() = user_id);
    """

    # Execute migration (Note: Supabase Python client doesn't support raw SQL execution)
    # This SQL should be run via Supabase SQL Editor or psql
    print("\nMigration SQL generated. Please run the following SQL in Supabase SQL Editor:")
    print("=" * 80)
    print(migration_sql)
    print("=" * 80)
    print("\nOr save to file and run via psql:")
    print("python scripts/apply_instance_templates_migration.py > migration.sql")
    print("psql <connection_string> < migration.sql")

    return migration_sql

if __name__ == "__main__":
    apply_migration()
```

### Rollback Script: `rollback_instance_templates_migration.py`

```python
"""
Rollback script to remove instance_templates table.
Run: python scripts/rollback_instance_templates_migration.py
"""

def rollback_migration():
    rollback_sql = """
    -- Drop RLS policies
    DROP POLICY IF EXISTS instance_templates_select_own ON instance_templates;
    DROP POLICY IF EXISTS instance_templates_insert_own ON instance_templates;
    DROP POLICY IF EXISTS instance_templates_update_own ON instance_templates;
    DROP POLICY IF EXISTS instance_templates_delete_own ON instance_templates;

    -- Drop indexes
    DROP INDEX IF EXISTS idx_instance_templates_instance;
    DROP INDEX IF EXISTS idx_instance_templates_user;
    DROP INDEX IF EXISTS idx_instance_templates_template_id;
    DROP INDEX IF EXISTS idx_instance_templates_instance_user;

    -- Drop trigger
    DROP TRIGGER IF EXISTS update_instance_templates_updated_at ON instance_templates;

    -- Drop table (CASCADE to remove any dependencies)
    DROP TABLE IF EXISTS instance_templates CASCADE;
    """

    print("Rollback SQL generated. Please run the following SQL in Supabase SQL Editor:")
    print("=" * 80)
    print(rollback_sql)
    print("=" * 80)

    return rollback_sql

if __name__ == "__main__":
    rollback_migration()
```

## Testing Queries

### Verify Table Creation
```sql
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'instance_templates'
ORDER BY ordinal_position;
```

### Verify Indexes
```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'instance_templates';
```

### Verify RLS Policies
```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'instance_templates';
```

### Test Data Insertion
```sql
-- Insert test template (replace with actual user_id and instance_id)
INSERT INTO instance_templates (
    template_id,
    name,
    description,
    sql_query,
    instance_id,
    user_id,
    tags
) VALUES (
    'tpl_inst_test123',
    'Test Template',
    'A test instance template',
    'SELECT * FROM campaigns LIMIT 10',
    'your-instance-uuid-here',
    'your-user-uuid-here',
    '["test", "sample"]'::jsonb
);

-- Verify insertion
SELECT * FROM instance_templates WHERE template_id = 'tpl_inst_test123';
```

### Test RLS Policies
```sql
-- Test as authenticated user (run in Supabase with auth context)
SELECT * FROM instance_templates; -- Should only return templates owned by current user

-- Test update own template
UPDATE instance_templates
SET usage_count = usage_count + 1
WHERE template_id = 'tpl_inst_test123'; -- Should succeed if owner

-- Test delete own template
DELETE FROM instance_templates WHERE template_id = 'tpl_inst_test123'; -- Should succeed if owner
```
