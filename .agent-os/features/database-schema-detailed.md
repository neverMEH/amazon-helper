# Supabase Database Schema - Detailed Documentation

## Overview
RecomAMP uses Supabase (PostgreSQL) as its primary database with Row Level Security (RLS) enabled on all tables. This document provides comprehensive details about each table, its relationships, and usage patterns.

## Core User & Authentication Tables

### `public.users` (RLS: enabled)
**Purpose**: Stores user accounts and authentication tokens

```sql
CREATE TABLE public.users (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    amazon_customer_id text NULL UNIQUE,
    auth_tokens jsonb NULL,              -- Encrypted OAuth tokens
    preferences jsonb NULL DEFAULT '{}'::jsonb,
    is_active boolean NULL DEFAULT true,
    is_admin boolean NULL DEFAULT false,
    profile_ids jsonb NULL DEFAULT '[]'::jsonb,    -- Amazon profile IDs
    marketplace_ids jsonb NULL DEFAULT '[]'::jsonb, -- Marketplace access
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Key Fields**:
- `auth_tokens`: Stores encrypted OAuth tokens for Amazon API access
  ```json
  {
    "access_token": "encrypted_string",
    "refresh_token": "encrypted_string",
    "expires_at": "2025-01-01T00:00:00Z"
  }
  ```
- `is_admin`: Future multi-tenant role system
- `profile_ids`: List of Amazon advertising profile IDs user has access to
- `marketplace_ids`: Amazon marketplaces (US, UK, DE, etc.)

**Relationships**:
- One-to-Many with `amc_accounts`
- One-to-Many with `workflows`
- One-to-Many with `query_templates`

**Usage Example**:
```python
# Get user with decrypted tokens
user = db.table('users').select('*').eq('id', user_id).execute()
decrypted_token = token_service.decrypt_token(user.data[0]['auth_tokens']['access_token'])
```

## AMC Instance Management Tables

### `public.amc_accounts` (RLS: enabled)
**Purpose**: Amazon advertising accounts that own AMC instances

```sql
CREATE TABLE public.amc_accounts (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id text NOT NULL UNIQUE,     -- Amazon entity ID (advertiser ID)
    account_name text NOT NULL,
    marketplace_id text NOT NULL,        -- US, UK, DE, etc.
    region text NOT NULL,                -- na, eu, fe
    status text NULL DEFAULT 'active',
    metadata jsonb NULL DEFAULT '{}'::jsonb,
    user_id uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Critical Field**:
- `account_id`: This is the `entity_id` required for all AMC API calls
  ```python
  # IMPORTANT: Always join this table to get entity_id
  headers['Amazon-Advertising-API-AdvertiserId'] = account['account_id']
  ```

**Relationships**:
- Belongs to `users`
- One-to-Many with `amc_instances`

### `public.amc_instances` (RLS: enabled)
**Purpose**: Individual AMC instances configuration

```sql
CREATE TABLE public.amc_instances (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id text NOT NULL UNIQUE,    -- AMC instance ID (e.g., "amcibersblt")
    instance_name text NOT NULL,
    region text NOT NULL,
    endpoint_url text NULL,              -- AMC API endpoint
    account_id uuid NOT NULL REFERENCES amc_accounts(id),
    status text NULL DEFAULT 'active',
    capabilities jsonb NULL DEFAULT '{}'::jsonb,
    data_upload_account_id text NULL,    -- For custom data uploads
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Critical Fields**:
- `instance_id`: The actual AMC instance identifier (NOT the UUID `id`)
- `account_id`: Foreign key to `amc_accounts` (needed for entity_id)

**ID Resolution Pattern**:
```python
# Always join to get both IDs needed for API calls
instance = db.table('amc_instances')\
    .select('*, amc_accounts(*)')\
    .eq('instance_id', 'amcibersblt')\
    .execute()

amc_instance_id = instance['instance_id']  # For API URL
entity_id = instance['amc_accounts']['account_id']  # For API headers
```

**Relationships**:
- Belongs to `amc_accounts`
- One-to-Many with `workflows`
- One-to-Many with `instance_brands`

### `public.instance_brands` (RLS: enabled)
**Purpose**: Associate brands with AMC instances for filtering

```sql
CREATE TABLE public.instance_brands (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    instance_id uuid NOT NULL REFERENCES amc_instances(id),
    brand_tag text NOT NULL,
    user_id uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    UNIQUE(instance_id, brand_tag)  -- Prevent duplicate associations
);
```

**Usage**:
- Links instances to brands for campaign filtering
- Used by frontend to show/hide campaigns based on brand

**Query Pattern**:
```sql
-- Get all brands for an instance
SELECT DISTINCT brand_tag 
FROM instance_brands 
WHERE instance_id = $1
ORDER BY brand_tag;
```

## Brand & Configuration Tables

### `public.brand_configurations` (RLS: enabled)
**Purpose**: Brand-specific configurations and parameters

```sql
CREATE TABLE public.brand_configurations (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    brand_tag text NOT NULL UNIQUE,      -- Unique brand identifier
    brand_name text NOT NULL,            -- Display name
    description text NULL,
    yaml_parameters text NULL,           -- YAML config for workflows
    default_parameters jsonb NULL DEFAULT '{}'::jsonb,
    primary_asins jsonb NULL DEFAULT '[]'::jsonb,     -- Main products
    all_asins jsonb NULL DEFAULT '[]'::jsonb,         -- All products
    campaign_name_patterns jsonb NULL DEFAULT '[]'::jsonb,  -- Regex patterns
    owner_user_id uuid NOT NULL REFERENCES users(id),
    shared_with_users jsonb NULL DEFAULT '[]'::jsonb,  -- User IDs with access
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Key Fields**:
- `brand_tag`: Used throughout system as brand identifier
- `campaign_name_patterns`: Regex patterns to identify brand campaigns
  ```json
  [".*Brand1.*", ".*BRAND1.*", "^B1_.*"]
  ```
- `primary_asins`: Core products for focused analysis
- `shared_with_users`: Future multi-user brand access

## Workflow & Execution Tables

### `public.workflows` (RLS: enabled)
**Purpose**: SQL query definitions and configurations

```sql
CREATE TABLE public.workflows (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NULL,
    instance_id uuid NOT NULL REFERENCES amc_instances(id),
    sql_query text NOT NULL,
    parameters jsonb NULL DEFAULT '{}'::jsonb,
    user_id uuid NOT NULL REFERENCES users(id),
    status text NULL DEFAULT 'active',
    is_template boolean NULL DEFAULT false,
    tags jsonb NULL DEFAULT '[]'::jsonb,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    -- AMC sync fields
    amc_workflow_id text NULL,           -- ID in AMC system
    is_synced_to_amc boolean NULL DEFAULT false,
    amc_sync_status text NULL DEFAULT 'not_synced',
    last_synced_at timestamptz NULL,
    amc_synced_at timestamptz NULL,
    amc_last_updated_at timestamptz NULL
);
```

**Parameter Structure**:
```json
{
  "startDate": "@startDate",
  "endDate": "@endDate",
  "campaigns": ["camp1", "camp2"],
  "asins": ["B001", "B002"],
  "lookbackDays": 30
}
```

**Relationships**:
- Belongs to `amc_instances`
- Belongs to `users`
- One-to-Many with `workflow_executions`
- One-to-Many with `workflow_schedules`

### `public.workflow_executions` (RLS: enabled)
**Purpose**: Track individual query executions and results

```sql
CREATE TABLE public.workflow_executions (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    execution_id text NOT NULL UNIQUE,
    workflow_id uuid NOT NULL REFERENCES workflows(id),
    status text NOT NULL,                -- PENDING, RUNNING, SUCCEEDED, FAILED
    progress int4 NULL DEFAULT 0,
    execution_parameters jsonb NULL DEFAULT '{}'::jsonb,
    output_location text NULL,           -- S3 location
    row_count int4 NULL,
    size_bytes int8 NULL,
    error_message text NULL,
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    duration_seconds int4 NULL,
    triggered_by text NULL,              -- manual, schedule, api
    schedule_id uuid NULL REFERENCES workflow_schedules(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    -- Result storage
    result_columns jsonb NULL,           -- Column metadata
    result_rows jsonb NULL,              -- Actual data rows
    result_total_rows int4 NULL DEFAULT 0,
    result_sample_size int4 NULL DEFAULT 0,
    -- Performance metrics
    query_runtime_seconds numeric NULL,
    data_scanned_gb numeric NULL,
    cost_estimate_usd numeric NULL,
    -- AMC specific
    instance_id text NULL,               -- AMC instance ID (string)
    amc_execution_id text NULL,          -- AMC's execution ID
    execution_mode text NULL DEFAULT 'ad_hoc',  -- ad_hoc, scheduled, batch
    amc_workflow_id text NULL,
    -- Batch & composition support
    batch_execution_id uuid NULL REFERENCES batch_executions(id),
    target_instance_id uuid NULL,
    is_batch_member boolean NULL DEFAULT false,
    schedule_run_id uuid NULL,
    composition_id uuid NULL,
    composition_node_id varchar NULL,
    execution_order int4 NULL
);
```

**Status Flow**:
```
PENDING → RUNNING → SUCCEEDED/FAILED
         ↘ CANCELLED (user abort)
```

**Result Storage**:
```json
{
  "result_columns": [
    {"name": "campaign_id", "type": "string"},
    {"name": "impressions", "type": "integer"}
  ],
  "result_rows": [
    {"campaign_id": "ABC123", "impressions": 1000},
    {"campaign_id": "DEF456", "impressions": 2000}
  ]
}
```

### `public.workflow_schedules` (RLS: enabled)
**Purpose**: Automated execution scheduling

```sql
CREATE TABLE public.workflow_schedules (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id text NOT NULL UNIQUE,
    workflow_id uuid NOT NULL REFERENCES workflows(id),
    cron_expression text NOT NULL,       -- Standard cron format
    timezone text NOT NULL DEFAULT 'UTC',
    default_parameters jsonb NULL DEFAULT '{}'::jsonb,
    is_active boolean NULL DEFAULT true,
    last_run_at timestamptz NULL,
    next_run_at timestamptz NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    -- Schedule configuration
    schedule_type text NULL DEFAULT 'cron',  -- cron, interval
    interval_days int4 NULL,
    interval_config jsonb NULL,
    execution_history_limit int4 NULL DEFAULT 30,
    notification_config jsonb NULL,
    cost_limit numeric NULL,
    -- Failure handling
    auto_pause_on_failure boolean NULL DEFAULT false,
    failure_threshold int4 NULL DEFAULT 3,
    consecutive_failures int4 NULL DEFAULT 0,
    -- Metadata
    user_id uuid NULL REFERENCES users(id),
    name text NULL,
    description text NULL,
    lookback_days int4 NULL DEFAULT 1,   -- Dynamic date calculation
    composition_id uuid NULL
);
```

**Cron Examples**:
```
"0 2 * * *"     -- Daily at 2 AM
"0 2 * * 1"     -- Weekly on Monday at 2 AM
"0 2 1 * *"     -- Monthly on 1st at 2 AM
```

**Dynamic Parameters**:
```python
# Calculate dates based on lookback_days
today = datetime.now()
start_date = today - timedelta(days=schedule.lookback_days)
parameters['startDate'] = start_date.strftime('%Y-%m-%dT00:00:00')
parameters['endDate'] = today.strftime('%Y-%m-%dT23:59:59')
```

## Template & Query Library Tables

### `public.query_templates` (RLS: enabled)
**Purpose**: Pre-built query templates with parameterization

```sql
CREATE TABLE public.query_templates (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NULL,
    category text NOT NULL,              -- attribution, conversion, audience
    sql_template text NOT NULL,
    parameters_schema jsonb NOT NULL,    -- JSON Schema for parameters
    default_parameters jsonb NULL DEFAULT '{}'::jsonb,
    user_id uuid NOT NULL REFERENCES users(id),
    is_public boolean NULL DEFAULT false,
    tags jsonb NULL DEFAULT '[]'::jsonb,
    usage_count int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Parameter Schema Example**:
```json
{
  "type": "object",
  "properties": {
    "startDate": {
      "type": "string",
      "format": "date-time",
      "description": "Start date for analysis"
    },
    "campaigns": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Campaign IDs to analyze"
    }
  },
  "required": ["startDate", "endDate"]
}
```

## Batch Execution Tables

### `public.batch_executions` (RLS: enabled)
**Purpose**: Execute same query across multiple instances

```sql
CREATE TABLE public.batch_executions (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id text NOT NULL UNIQUE,
    workflow_id uuid NULL REFERENCES workflows(id),
    name text NULL,
    description text NULL,
    instance_ids jsonb NOT NULL,         -- Array of instance UUIDs
    base_parameters jsonb NULL DEFAULT '{}'::jsonb,
    instance_parameters jsonb NULL DEFAULT '{}'::jsonb,  -- Per-instance params
    status text NULL DEFAULT 'pending',
    total_instances int4 NOT NULL,
    completed_instances int4 NULL DEFAULT 0,
    failed_instances int4 NULL DEFAULT 0,
    user_id uuid NULL REFERENCES users(id),
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

**Instance Parameters Structure**:
```json
{
  "instance_uuid_1": {
    "campaigns": ["camp1", "camp2"],
    "brand": "Brand1"
  },
  "instance_uuid_2": {
    "campaigns": ["camp3", "camp4"],
    "brand": "Brand2"
  }
}
```

## AMC Schema Documentation Tables

### `public.amc_data_sources` (RLS: enabled)
**Purpose**: AMC table documentation and metadata

```sql
CREATE TABLE public.amc_data_sources (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    schema_id text NOT NULL UNIQUE,
    name text NOT NULL,
    category text NOT NULL,              -- Attribution, Traffic, Conversion
    description text NULL,
    data_sources jsonb NULL,             -- Related tables
    version text NULL DEFAULT '1.0.0',
    tags jsonb NULL DEFAULT '[]'::jsonb,
    is_paid_feature boolean NULL DEFAULT false,
    availability jsonb NULL,             -- Region/instance availability
    created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
    created_by uuid NULL REFERENCES users(id),
    search_vector tsvector NULL GENERATED,  -- Full-text search
    fields jsonb NULL DEFAULT '[]'::jsonb,
    field_count int4 NULL DEFAULT 0,
    example_count int4 NULL DEFAULT 0,
    complexity text NULL DEFAULT 'simple'  -- simple, moderate, complex
);
```

### `public.amc_schema_fields` (RLS: enabled)
**Purpose**: Field-level documentation for AMC tables

```sql
CREATE TABLE public.amc_schema_fields (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    data_source_id uuid NOT NULL REFERENCES amc_data_sources(id),
    field_name text NOT NULL,
    data_type text NOT NULL,             -- string, integer, float, timestamp
    dimension_or_metric text NOT NULL,   -- D (dimension) or M (metric)
    description text NULL,
    aggregation_threshold text NULL,     -- Min aggregation requirements
    field_category text NULL,
    examples jsonb NULL,
    field_order int4 NULL DEFAULT 0,
    is_nullable boolean NULL DEFAULT true,
    is_array boolean NULL DEFAULT false,
    created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
    search_vector tsvector NULL GENERATED
);
```

**Field Type Indicators**:
- **D (Dimension)**: Can be used in GROUP BY
- **M (Metric)**: Must be aggregated (SUM, COUNT, AVG)

### `public.amc_query_examples` (RLS: enabled)
**Purpose**: Example queries for each data source

```sql
CREATE TABLE public.amc_query_examples (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    data_source_id uuid NOT NULL REFERENCES amc_data_sources(id),
    title text NOT NULL,
    description text NULL,
    sql_query text NOT NULL,
    category text NULL,
    use_case text NULL,
    example_order int4 NULL DEFAULT 0,
    parameters jsonb NULL,
    expected_output text NULL,
    created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP,
    created_by uuid NULL REFERENCES users(id),
    search_vector tsvector NULL GENERATED
);
```

### `public.amc_schema_sections` (RLS: enabled)
**Purpose**: Documentation sections for data sources

```sql
CREATE TABLE public.amc_schema_sections (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    data_source_id uuid NOT NULL REFERENCES amc_data_sources(id),
    section_type text NOT NULL,          -- overview, usage, examples
    title text NULL,
    content_markdown text NOT NULL,      -- Markdown formatted content
    section_order int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `public.amc_schema_relationships` (RLS: enabled)
**Purpose**: Document relationships between AMC tables

```sql
CREATE TABLE public.amc_schema_relationships (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    source_schema_id uuid NOT NULL REFERENCES amc_data_sources(id),
    target_schema_id uuid NOT NULL REFERENCES amc_data_sources(id),
    relationship_type text NOT NULL,     -- one-to-many, many-to-many, etc.
    description text NULL,
    join_condition text NULL,            -- SQL join condition
    created_at timestamptz NULL DEFAULT CURRENT_TIMESTAMP
);
```

### `public.amc_field_relationships` (RLS: enabled)
**Purpose**: Field-level relationships between tables

```sql
CREATE TABLE public.amc_field_relationships (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    source_field_id uuid NOT NULL REFERENCES amc_schema_fields(id),
    target_field_id uuid NOT NULL REFERENCES amc_schema_fields(id),
    relationship_type text NOT NULL,     -- foreign_key, lookup, derived
    description text NULL
);
```

## Query Results Table

### `public.amc_query_results` (RLS: enabled)
**Purpose**: Cache query results for performance

```sql
CREATE TABLE public.amc_query_results (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    query_hash varchar NULL,             -- Hash of query for deduplication
    query_text text NULL,
    result_data jsonb NULL,              -- Cached results
    execution_timestamp timestamptz NULL,
    row_count int4 NULL,
    brand_tag text NULL,
    instance_id uuid NULL REFERENCES amc_instances(id),
    user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now()
);
```

## Row Level Security (RLS) Patterns

All tables have RLS enabled with policies like:

```sql
-- Users can only see their own data
CREATE POLICY users_own_data ON public.workflows
    FOR ALL USING (user_id = auth.uid());

-- Admins can see everything
CREATE POLICY admin_access ON public.workflows
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Shared access for brands
CREATE POLICY brand_shared_access ON public.brand_configurations
    FOR SELECT USING (
        owner_user_id = auth.uid() OR
        auth.uid() = ANY(shared_with_users)
    );
```

## Common Query Patterns

### Get Instance with Entity ID
```sql
SELECT 
    i.*,
    a.account_id as entity_id
FROM amc_instances i
JOIN amc_accounts a ON i.account_id = a.id
WHERE i.instance_id = $1;
```

### Get User's Workflows with Instance Details
```sql
SELECT 
    w.*,
    i.instance_name,
    i.instance_id as amc_instance_id
FROM workflows w
JOIN amc_instances i ON w.instance_id = i.id
WHERE w.user_id = $1
ORDER BY w.created_at DESC;
```

### Get Execution with Full Context
```sql
SELECT 
    e.*,
    w.name as workflow_name,
    w.sql_query,
    i.instance_name,
    s.name as schedule_name
FROM workflow_executions e
JOIN workflows w ON e.workflow_id = w.id
LEFT JOIN amc_instances i ON w.instance_id = i.id
LEFT JOIN workflow_schedules s ON e.schedule_id = s.id
WHERE e.execution_id = $1;
```

### Get Brands for Instance
```sql
SELECT ARRAY_AGG(brand_tag) as brands
FROM instance_brands
WHERE instance_id = $1
GROUP BY instance_id;
```

## Indexing Strategy

Key indexes for performance:

```sql
-- Execution status queries
CREATE INDEX idx_executions_status ON workflow_executions(status, updated_at);

-- Schedule next run queries
CREATE INDEX idx_schedules_next_run ON workflow_schedules(is_active, next_run_at);

-- User's workflows
CREATE INDEX idx_workflows_user ON workflows(user_id, created_at DESC);

-- Instance brand lookups
CREATE INDEX idx_instance_brands ON instance_brands(instance_id, brand_tag);

-- Full-text search
CREATE INDEX idx_data_sources_search ON amc_data_sources USING gin(search_vector);
```

## Migration Considerations

When adding new fields:
1. Always use NULL defaults for backwards compatibility
2. Add fields as nullable first, then migrate data
3. Use JSONB for flexible, evolving data structures
4. Keep audit fields (created_at, updated_at) on all tables

## Performance Tips

1. **Use JSONB indexing** for frequently queried JSON fields:
   ```sql
   CREATE INDEX idx_params ON workflows USING gin(parameters);
   ```

2. **Partition large tables** by date:
   ```sql
   CREATE TABLE workflow_executions_2025 PARTITION OF workflow_executions
   FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
   ```

3. **Use materialized views** for complex aggregations:
   ```sql
   CREATE MATERIALIZED VIEW execution_stats AS
   SELECT workflow_id, COUNT(*), AVG(duration_seconds)
   FROM workflow_executions
   GROUP BY workflow_id;
   ```

## Additional Schema Tables

### `public.schedule_runs` (RLS: enabled)
**Purpose**: Track individual schedule execution runs

```sql
CREATE TABLE public.schedule_runs (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id uuid NOT NULL REFERENCES workflow_schedules(id),
    run_number int4 NOT NULL,
    scheduled_at timestamptz NOT NULL,
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    status text NOT NULL,                -- pending, running, succeeded, failed
    execution_count int4 NULL DEFAULT 0,
    successful_count int4 NULL DEFAULT 0,
    failed_count int4 NULL DEFAULT 0,
    total_rows int4 NULL,
    total_cost numeric NULL,
    error_summary text NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    parameters jsonb NULL
);
```

## Build Guides System Tables

### `public.build_guides` (RLS: enabled)
**Purpose**: Step-by-step tutorials for AMC queries

```sql
CREATE TABLE public.build_guides (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id text NOT NULL UNIQUE,
    name text NOT NULL,
    category text NOT NULL,              -- getting-started, attribution, audience
    short_description text NULL,
    tags jsonb NULL DEFAULT '[]'::jsonb,
    icon text NULL,                      -- Icon identifier
    difficulty_level text NULL,          -- beginner, intermediate, advanced
    estimated_time_minutes int4 NULL,
    prerequisites jsonb NULL,            -- Required knowledge/setup
    is_published boolean NULL DEFAULT true,
    display_order int4 NULL DEFAULT 0,
    created_by uuid NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.build_guide_sections` (RLS: enabled)
**Purpose**: Content sections within guides

```sql
CREATE TABLE public.build_guide_sections (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id uuid NOT NULL REFERENCES build_guides(id),
    section_id text NOT NULL,
    title text NOT NULL,
    content_markdown text NOT NULL,      -- Markdown formatted content
    display_order int4 NOT NULL DEFAULT 0,
    is_collapsible boolean NULL DEFAULT false,
    default_expanded boolean NULL DEFAULT true,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.build_guide_queries` (RLS: enabled)
**Purpose**: SQL queries associated with guides

```sql
CREATE TABLE public.build_guide_queries (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id uuid NOT NULL REFERENCES build_guides(id),
    query_template_id uuid NULL REFERENCES query_templates(id),
    title text NOT NULL,
    description text NULL,
    sql_query text NOT NULL,
    parameters_schema jsonb NULL,
    default_parameters jsonb NULL,
    display_order int4 NULL DEFAULT 0,
    query_type text NULL,                -- analysis, export, aggregation
    expected_columns jsonb NULL,         -- Expected result structure
    interpretation_notes text NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.build_guide_examples` (RLS: enabled)
**Purpose**: Sample data and interpretations

```sql
CREATE TABLE public.build_guide_examples (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_query_id uuid NOT NULL REFERENCES build_guide_queries(id),
    example_name text NOT NULL,
    sample_data jsonb NOT NULL,          -- Example result data
    interpretation_markdown text NULL,    -- How to interpret results
    insights jsonb NULL,                 -- Key takeaways
    display_order int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.build_guide_metrics` (RLS: enabled)
**Purpose**: Metrics definitions for guides

```sql
CREATE TABLE public.build_guide_metrics (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    guide_id uuid NOT NULL REFERENCES build_guides(id),
    metric_name text NOT NULL,
    display_name text NOT NULL,
    definition text NOT NULL,            -- What this metric means
    metric_type text NOT NULL,           -- dimension, metric, calculated
    display_order int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT now()
);
```

### `public.user_guide_progress` (RLS: enabled)
**Purpose**: Track user progress through guides

```sql
CREATE TABLE public.user_guide_progress (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    guide_id uuid NOT NULL REFERENCES build_guides(id),
    status text NOT NULL,                -- not_started, in_progress, completed
    current_section text NULL,
    completed_sections jsonb NULL DEFAULT '[]'::jsonb,
    executed_queries jsonb NULL DEFAULT '[]'::jsonb,
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    last_accessed_at timestamptz NULL,
    progress_percentage int4 NULL DEFAULT 0,
    UNIQUE(user_id, guide_id)
);
```

### `public.user_guide_favorites` (RLS: enabled)
**Purpose**: User's favorite guides

```sql
CREATE TABLE public.user_guide_favorites (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    guide_id uuid NOT NULL REFERENCES build_guides(id),
    created_at timestamptz NULL DEFAULT now(),
    UNIQUE(user_id, guide_id)
);
```

## Campaign & Product Tables

### `public.campaigns` (RLS: enabled)
**Purpose**: Amazon advertising campaigns

```sql
CREATE TABLE public.campaigns (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id text NOT NULL UNIQUE,    -- Amazon campaign ID
    portfolio_id text NULL,              -- Portfolio ID if applicable
    type text NOT NULL,                  -- Sponsored Products, Brands, Display
    targeting_type text NULL,            -- keyword, product, auto
    bidding_strategy text NULL,          -- fixed, dynamic
    state text NOT NULL,                 -- enabled, paused, archived
    name text NOT NULL,
    brand text NULL,                     -- Associated brand
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.product_asins` (RLS: enabled)
**Purpose**: Product catalog with ASINs

```sql
CREATE TABLE public.product_asins (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    asin text NOT NULL UNIQUE,
    title text NULL,
    brand text NULL,
    marketplace text NOT NULL DEFAULT 'US',
    active boolean NULL DEFAULT true,
    description text NULL,
    department text NULL,
    manufacturer text NULL,
    product_group text NULL,
    product_type text NULL,
    color text NULL,
    size text NULL,
    model text NULL,
    item_length numeric NULL,
    item_height numeric NULL,
    item_width numeric NULL,
    item_weight numeric NULL,
    item_unit_dimension text NULL,       -- inches, cm
    item_unit_weight text NULL,          -- pounds, kg
    parent_asin text NULL,               -- For variations
    variant_type text NULL,              -- color, size, style
    last_known_price numeric NULL,
    monthly_estimated_sales numeric NULL,
    monthly_estimated_units int4 NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    last_imported_at timestamptz NULL
);
```

### `public.asin_import_logs` (RLS: enabled)
**Purpose**: Track ASIN bulk imports

```sql
CREATE TABLE public.asin_import_logs (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    file_name text NOT NULL,
    total_rows int4 NOT NULL,
    successful_imports int4 NULL DEFAULT 0,
    failed_imports int4 NULL DEFAULT 0,
    duplicate_skipped int4 NULL DEFAULT 0,
    import_status text NOT NULL,         -- pending, processing, completed, failed
    error_details jsonb NULL,
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    created_at timestamptz NULL DEFAULT now()
);
```

## Query Flow Template Tables - DEPRECATED (2025-09-11)

**DEPRECATED**: Flow template features were removed from the codebase on 2025-09-11. While these tables may still exist in some database instances, they are no longer used by the application. See `flow-template-removal.md` for details.

### `public.query_flow_templates` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Reusable query workflow templates~~ - Feature removed from application

```sql
CREATE TABLE public.query_flow_templates (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NULL,
    category text NOT NULL,
    sql_template text NOT NULL,
    is_active boolean NULL DEFAULT true,
    is_public boolean NULL DEFAULT false,
    version text NULL DEFAULT '1.0.0',
    created_by uuid NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    execution_count int4 NULL DEFAULT 0,
    avg_execution_time_ms int4 NULL,
    tags jsonb NULL DEFAULT '[]'::jsonb,
    metadata jsonb NULL DEFAULT '{}'::jsonb
);
```

### `public.template_parameters` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Parameter definitions for templates~~ - Feature removed from application

```sql
CREATE TABLE public.template_parameters (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    parameter_name text NOT NULL,
    display_name text NOT NULL,
    parameter_type text NOT NULL,        -- string, date, array, number
    required boolean NULL DEFAULT false,
    default_value jsonb NULL,
    validation_rules jsonb NULL,         -- Min/max, regex, etc.
    ui_component text NULL,              -- dropdown, datepicker, multiselect
    ui_config jsonb NULL,                -- Component configuration
    dependencies jsonb NULL,             -- Other parameters it depends on
    order_index int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.template_chart_configs` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Visualization configurations for templates~~ - Feature removed from application

```sql
CREATE TABLE public.template_chart_configs (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    chart_name text NOT NULL,
    chart_type text NOT NULL,            -- line, bar, pie, scatter, heatmap
    chart_config jsonb NOT NULL,         -- Chart.js configuration
    data_mapping jsonb NOT NULL,         -- Map result columns to chart
    is_default boolean NULL DEFAULT false,
    order_index int4 NULL DEFAULT 0,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.template_executions` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Track template usage~~ - Feature removed from application

```sql
CREATE TABLE public.template_executions (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    user_id uuid NOT NULL REFERENCES users(id),
    instance_id uuid NOT NULL REFERENCES amc_instances(id),
    parameters_used jsonb NOT NULL,
    workflow_id uuid NULL REFERENCES workflows(id),
    execution_id uuid NULL REFERENCES workflow_executions(id),
    status text NOT NULL,
    result_summary jsonb NULL,
    execution_time_ms int4 NULL,
    error_details text NULL,
    created_at timestamptz NULL DEFAULT now(),
    completed_at timestamptz NULL
);
```

### `public.user_template_favorites` (RLS: enabled) - DEPRECATED
**Purpose**: ~~User's favorite templates~~ - Feature removed from application

```sql
CREATE TABLE public.user_template_favorites (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    created_at timestamptz NULL DEFAULT now(),
    UNIQUE(user_id, template_id)
);
```

### `public.template_ratings` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Template ratings and reviews~~ - Feature removed from application

```sql
CREATE TABLE public.template_ratings (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    user_id uuid NOT NULL REFERENCES users(id),
    rating int4 NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review text NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    UNIQUE(template_id, user_id)
);
```

## Flow Composition Tables - DEPRECATED (2025-09-11)

**DEPRECATED**: Flow composition features were removed from the codebase on 2025-09-11.

### `public.template_flow_compositions` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Multi-step query workflows~~ - Feature removed from application

```sql
CREATE TABLE public.template_flow_compositions (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    composition_id text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NULL,
    canvas_state jsonb NOT NULL,         -- Visual flow representation
    global_parameters jsonb NULL,        -- Shared across all nodes
    tags jsonb NULL DEFAULT '[]'::jsonb,
    is_public boolean NULL DEFAULT false,
    is_active boolean NULL DEFAULT true,
    created_by uuid NULL REFERENCES users(id),
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    execution_count int4 NULL DEFAULT 0,
    last_executed_at timestamptz NULL
);
```

### `public.template_flow_nodes` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Individual nodes in a flow~~ - Feature removed from application

```sql
CREATE TABLE public.template_flow_nodes (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    composition_id uuid NOT NULL REFERENCES template_flow_compositions(id),
    node_id text NOT NULL,
    template_id uuid NOT NULL REFERENCES query_flow_templates(id),
    position jsonb NOT NULL,             -- x, y coordinates
    node_config jsonb NULL,              -- Node-specific settings
    parameter_overrides jsonb NULL,      -- Override template defaults
    parameter_mappings jsonb NULL,       -- Map outputs to inputs
    execution_order int4 NOT NULL,
    is_conditional boolean NULL DEFAULT false,
    condition_expression text NULL,      -- When to execute this node
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    UNIQUE(composition_id, node_id)
);
```

### `public.template_flow_connections` (RLS: enabled) - DEPRECATED
**Purpose**: ~~Connections between flow nodes~~ - Feature removed from application

```sql
CREATE TABLE public.template_flow_connections (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    composition_id uuid NOT NULL REFERENCES template_flow_compositions(id),
    connection_id text NOT NULL,
    source_node_id text NOT NULL,
    target_node_id text NOT NULL,
    field_mappings jsonb NULL,           -- Map source outputs to target inputs
    transformation_rules jsonb NULL,      -- Data transformation logic
    is_required boolean NULL DEFAULT true,
    created_at timestamptz NULL DEFAULT now(),
    UNIQUE(composition_id, connection_id)
);
```

## Dashboard & Reporting Tables

### `public.dashboards` (RLS: enabled)
**Purpose**: Custom dashboard configurations

```sql
CREATE TABLE public.dashboards (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    dashboard_id text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NULL,
    user_id uuid NOT NULL REFERENCES users(id),
    template_type text NULL,             -- performance, attribution, custom
    layout_config jsonb NOT NULL,        -- Grid layout configuration
    filter_config jsonb NULL,            -- Global filters
    is_public boolean NULL DEFAULT false,
    is_template boolean NULL DEFAULT false,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.dashboard_widgets` (RLS: enabled)
**Purpose**: Individual widgets on dashboards

```sql
CREATE TABLE public.dashboard_widgets (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    widget_id text NOT NULL UNIQUE,
    dashboard_id uuid NOT NULL REFERENCES dashboards(id),
    widget_type text NOT NULL,           -- chart, table, metric_card, text
    chart_type text NULL,                -- line, bar, pie, area, scatter
    title text NOT NULL,
    data_source jsonb NOT NULL,          -- Query or execution reference
    display_config jsonb NOT NULL,       -- Chart/widget configuration
    position_config jsonb NOT NULL,      -- Grid position and size
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.report_data_collections` (RLS: enabled)
**Purpose**: Historical data collection configurations

```sql
CREATE TABLE public.report_data_collections (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    collection_id text NOT NULL UNIQUE,
    workflow_id uuid NOT NULL REFERENCES workflows(id),
    instance_id uuid NOT NULL REFERENCES amc_instances(id),
    user_id uuid NOT NULL REFERENCES users(id),
    collection_type text NOT NULL,       -- weekly, daily, monthly
    target_weeks int4 NOT NULL,          -- Number of weeks to collect
    start_date date NOT NULL,
    end_date date NOT NULL,
    status text NOT NULL,                -- pending, running, paused, completed
    progress_percentage int4 NULL DEFAULT 0,
    weeks_completed int4 NULL DEFAULT 0,
    error_message text NULL,
    configuration jsonb NULL,            -- Collection settings
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.report_data_weeks` (RLS: enabled)
**Purpose**: Track individual week executions in collections

```sql
CREATE TABLE public.report_data_weeks (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    collection_id uuid NOT NULL REFERENCES report_data_collections(id),
    workflow_execution_id uuid NULL REFERENCES workflow_executions(id),
    week_start_date date NOT NULL,
    week_end_date date NOT NULL,
    status text NOT NULL,                -- pending, running, succeeded, failed
    execution_date timestamptz NULL,
    record_count int4 NULL,
    data_checksum text NULL,             -- For data integrity
    error_message text NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now(),
    started_at timestamptz NULL,
    completed_at timestamptz NULL,
    amc_execution_id text NULL,
    execution_id text NULL,              -- External execution ID
    execution_time_seconds int4 NULL,
    UNIQUE(collection_id, week_start_date)
);
```

### `public.report_data_aggregates` (RLS: enabled)
**Purpose**: Aggregated report data

```sql
CREATE TABLE public.report_data_aggregates (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    workflow_id uuid NOT NULL REFERENCES workflows(id),
    instance_id uuid NOT NULL REFERENCES amc_instances(id),
    date_start date NOT NULL,
    date_end date NOT NULL,
    aggregation_type text NOT NULL,      -- sum, avg, count, etc.
    metrics jsonb NOT NULL,              -- Aggregated metrics
    dimensions jsonb NULL,               -- Grouping dimensions
    data_checksum text NULL,
    created_at timestamptz NULL DEFAULT now(),
    updated_at timestamptz NULL DEFAULT now()
);
```

### `public.ai_insights` (RLS: enabled)
**Purpose**: AI-generated insights from data

```sql
CREATE TABLE public.ai_insights (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    insight_id text NOT NULL UNIQUE,
    user_id uuid NOT NULL REFERENCES users(id),
    dashboard_id uuid NULL REFERENCES dashboards(id),
    query_text text NOT NULL,            -- User's question
    response_text text NOT NULL,         -- AI's response
    data_context jsonb NOT NULL,         -- Data used for insight
    confidence_score numeric NULL,       -- 0-1 confidence score
    insight_type text NULL,              -- trend, anomaly, recommendation
    related_metrics jsonb NULL,          -- Metrics referenced
    created_at timestamptz NULL DEFAULT now()
);
```

### `public.dashboard_shares` (RLS: enabled)
**Purpose**: Dashboard sharing permissions

```sql
CREATE TABLE public.dashboard_shares (
    id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    dashboard_id uuid NOT NULL REFERENCES dashboards(id),
    shared_by uuid NOT NULL REFERENCES users(id),
    shared_with uuid NOT NULL REFERENCES users(id),
    permission_level text NOT NULL,      -- view, edit, admin
    expires_at timestamptz NULL,         -- Optional expiration
    created_at timestamptz NULL DEFAULT now(),
    UNIQUE(dashboard_id, shared_with)
);
```

## Complete Field Reference

Here's a complete listing of all fields for quick reference:

**users**: id, email, name, amazon_customer_id, auth_tokens, preferences, is_active, is_admin, profile_ids, marketplace_ids, created_at, updated_at

**amc_accounts**: id, account_id, account_name, marketplace_id, region, status, metadata, user_id, created_at, updated_at

**amc_instances**: id, instance_id, instance_name, region, endpoint_url, account_id, status, capabilities, data_upload_account_id, created_at, updated_at

**brand_configurations**: id, brand_tag, brand_name, description, yaml_parameters, default_parameters, primary_asins, all_asins, campaign_name_patterns, owner_user_id, shared_with_users, created_at, updated_at

**workflows**: id, workflow_id, name, description, instance_id, sql_query, parameters, user_id, status, is_template, tags, created_at, updated_at, amc_workflow_id, is_synced_to_amc, amc_sync_status, last_synced_at, amc_synced_at, amc_last_updated_at

**workflow_executions**: id, execution_id, workflow_id, status, progress, execution_parameters, output_location, row_count, size_bytes, error_message, started_at, completed_at, duration_seconds, triggered_by, schedule_id, created_at, updated_at, result_columns, result_rows, result_total_rows, result_sample_size, query_runtime_seconds, data_scanned_gb, cost_estimate_usd, instance_id, amc_execution_id, execution_mode, amc_workflow_id, batch_execution_id, target_instance_id, is_batch_member, schedule_run_id, composition_id, composition_node_id, execution_order

**workflow_schedules**: id, schedule_id, workflow_id, cron_expression, timezone, default_parameters, is_active, last_run_at, next_run_at, created_at, updated_at, schedule_type, interval_days, interval_config, execution_history_limit, notification_config, cost_limit, auto_pause_on_failure, failure_threshold, consecutive_failures, user_id, name, description, lookback_days, composition_id

**query_templates**: id, template_id, name, description, category, sql_template, parameters_schema, default_parameters, user_id, is_public, tags, usage_count, created_at, updated_at

**amc_query_results**: id, query_hash, query_text, result_data, execution_timestamp, row_count, brand_tag, instance_id, user_id, created_at

**instance_brands**: id, instance_id, brand_tag, user_id, created_at, updated_at

**batch_executions**: id, batch_id, workflow_id, name, description, instance_ids, base_parameters, instance_parameters, status, total_instances, completed_instances, failed_instances, user_id, started_at, completed_at, created_at, updated_at

**amc_data_sources**: id, schema_id, name, category, description, data_sources, version, tags, is_paid_feature, availability, created_at, updated_at, created_by, search_vector, fields, field_count, example_count, complexity

**amc_schema_fields**: id, data_source_id, field_name, data_type, dimension_or_metric, description, aggregation_threshold, field_category, examples, field_order, is_nullable, is_array, created_at, search_vector

**amc_query_examples**: id, data_source_id, title, description, sql_query, category, use_case, example_order, parameters, expected_output, created_at, created_by, search_vector

**amc_schema_sections**: id, data_source_id, section_type, title, content_markdown, section_order, created_at

**amc_schema_relationships**: id, source_schema_id, target_schema_id, relationship_type, description, join_condition, created_at

**amc_field_relationships**: id, source_field_id, target_field_id, relationship_type, description, created_at

**schedule_runs**: id, schedule_id, run_number, scheduled_at, started_at, completed_at, status, execution_count, successful_count, failed_count, total_rows, total_cost, error_summary, created_at, updated_at, parameters

**build_guides**: id, guide_id, name, category, short_description, tags, icon, difficulty_level, estimated_time_minutes, prerequisites, is_published, display_order, created_by, created_at, updated_at

**build_guide_sections**: id, guide_id, section_id, title, content_markdown, display_order, is_collapsible, default_expanded, created_at, updated_at

**build_guide_queries**: id, guide_id, query_template_id, title, description, sql_query, parameters_schema, default_parameters, display_order, query_type, expected_columns, interpretation_notes, created_at, updated_at

**build_guide_examples**: id, guide_query_id, example_name, sample_data, interpretation_markdown, insights, display_order, created_at, updated_at

**build_guide_metrics**: id, guide_id, metric_name, display_name, definition, metric_type, display_order, created_at

**user_guide_progress**: id, user_id, guide_id, status, current_section, completed_sections, executed_queries, started_at, completed_at, last_accessed_at, progress_percentage

**user_guide_favorites**: id, user_id, guide_id, created_at

**campaigns**: id, campaign_id, portfolio_id, type, targeting_type, bidding_strategy, state, name, brand, created_at, updated_at

**product_asins**: id, asin, title, brand, marketplace, active, description, department, manufacturer, product_group, product_type, color, size, model, item_length, item_height, item_width, item_weight, item_unit_dimension, item_unit_weight, parent_asin, variant_type, last_known_price, monthly_estimated_sales, monthly_estimated_units, created_at, updated_at, last_imported_at

**asin_import_logs**: id, user_id, file_name, total_rows, successful_imports, failed_imports, duplicate_skipped, import_status, error_details, started_at, completed_at, created_at

**query_flow_templates**: id, template_id, name, description, category, sql_template, is_active, is_public, version, created_by, created_at, updated_at, execution_count, avg_execution_time_ms, tags, metadata

**template_parameters**: id, template_id, parameter_name, display_name, parameter_type, required, default_value, validation_rules, ui_component, ui_config, dependencies, order_index, created_at, updated_at

**template_chart_configs**: id, template_id, chart_name, chart_type, chart_config, data_mapping, is_default, order_index, created_at, updated_at

**template_executions**: id, template_id, user_id, instance_id, parameters_used, workflow_id, execution_id, status, result_summary, execution_time_ms, error_details, created_at, completed_at

**user_template_favorites**: id, user_id, template_id, created_at

**template_ratings**: id, template_id, user_id, rating, review, created_at, updated_at

**template_flow_compositions**: id, composition_id, name, description, canvas_state, global_parameters, tags, is_public, is_active, created_by, created_at, updated_at, execution_count, last_executed_at

**template_flow_nodes**: id, composition_id, node_id, template_id, position, node_config, parameter_overrides, parameter_mappings, execution_order, is_conditional, condition_expression, created_at, updated_at

**template_flow_connections**: id, composition_id, connection_id, source_node_id, target_node_id, field_mappings, transformation_rules, is_required, created_at

**dashboards**: id, dashboard_id, name, description, user_id, template_type, layout_config, filter_config, is_public, is_template, created_at, updated_at

**dashboard_widgets**: id, widget_id, dashboard_id, widget_type, chart_type, title, data_source, display_config, position_config, created_at, updated_at

**report_data_collections**: id, collection_id, workflow_id, instance_id, user_id, collection_type, target_weeks, start_date, end_date, status, progress_percentage, weeks_completed, error_message, configuration, created_at, updated_at

**report_data_weeks**: id, collection_id, workflow_execution_id, week_start_date, week_end_date, status, execution_date, record_count, data_checksum, error_message, created_at, updated_at, started_at, completed_at, amc_execution_id, execution_id, execution_time_seconds

**report_data_aggregates**: id, workflow_id, instance_id, date_start, date_end, aggregation_type, metrics, dimensions, data_checksum, created_at, updated_at

**ai_insights**: id, insight_id, user_id, dashboard_id, query_text, response_text, data_context, confidence_score, insight_type, related_metrics, created_at

**dashboard_shares**: id, dashboard_id, shared_by, shared_with, permission_level, expires_at, created_at

## Security Considerations

1. **Encrypted fields**: auth_tokens are always encrypted with Fernet
2. **RLS policies**: Every table has user-based access control
3. **Audit trail**: created_at/updated_at track all changes
4. **Soft deletes**: Use status fields instead of DELETE operations
5. **JSONB validation**: Validate structure before storing