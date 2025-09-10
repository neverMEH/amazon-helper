# Database Schema Documentation

## Overview

RecomAMP uses Supabase (PostgreSQL) as its primary database, featuring a well-structured relational schema that supports user management, AMC integration, workflow execution, data collection, and reporting. The schema is designed for scalability, data integrity, and performance.

## Core Entity Relationships

### Primary Tables Hierarchy
```
users (root entity)
├── amc_instances (user's AMC configurations)
│   ├── workflows (queries and automation)
│   ├── campaigns (campaign data)
│   ├── asins (product tracking)
│   └── report_data_collections (historical data)
├── workflow_executions (execution history)
├── workflow_schedules (automation schedules)
└── build_guide_progress (user learning progress)
```

## Table Definitions

### Authentication and User Management

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    
    -- OAuth Integration
    amazon_user_id TEXT UNIQUE,
    encrypted_access_token TEXT,
    encrypted_refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    
    -- User Preferences
    timezone TEXT DEFAULT 'UTC',
    email_notifications BOOLEAN DEFAULT true,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_amazon_user_id ON users(amazon_user_id);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;
```

### AMC Instance Management

#### amc_accounts
```sql
CREATE TABLE amc_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id TEXT UNIQUE NOT NULL, -- This becomes entity_id for AMC API
    account_name TEXT NOT NULL,
    advertiser_id TEXT,
    profile_id TEXT,
    country_code TEXT DEFAULT 'US',
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_amc_accounts_account_id ON amc_accounts(account_id);
```

#### amc_instances
```sql
CREATE TABLE amc_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id TEXT NOT NULL, -- AMC string identifier (e.g., "amcibersblt")
    name TEXT NOT NULL,
    description TEXT,
    region TEXT DEFAULT 'us-east-1',
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES amc_accounts(id) ON DELETE CASCADE,
    
    -- Status and Health
    is_active BOOLEAN DEFAULT true,
    health_status TEXT DEFAULT 'UNKNOWN', -- HEALTHY, UNHEALTHY, ERROR
    health_error TEXT,
    last_health_check TIMESTAMPTZ,
    
    -- Sync Status
    campaigns_last_sync TIMESTAMPTZ,
    schema_last_sync TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_amc_instances_user_id ON amc_instances(user_id);
CREATE INDEX idx_amc_instances_active ON amc_instances(is_active) WHERE is_active = true;
CREATE UNIQUE INDEX idx_amc_instances_instance_id ON amc_instances(instance_id, user_id);
```

### Workflow System

#### workflows
```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    sql_query TEXT NOT NULL,
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    instance_id UUID NOT NULL REFERENCES amc_instances(id) ON DELETE CASCADE,
    template_id UUID REFERENCES query_templates(id) ON DELETE SET NULL,
    
    -- Configuration
    parameters JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_executed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_instance_id ON workflows(instance_id);
CREATE INDEX idx_workflows_last_executed ON workflows(last_executed_at);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);
```

#### workflow_executions
```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amc_execution_id TEXT, -- AMC's execution identifier
    
    -- Foreign Keys
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Execution Status
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, FAILED, CANCELLED, TIMEOUT
    parameters JSONB DEFAULT '{}',
    
    -- Results and Metrics
    result_data JSONB,
    result_rows INTEGER,
    result_size_bytes BIGINT,
    execution_duration INTEGER, -- seconds
    
    -- Error Handling
    error_message TEXT,
    error_type TEXT,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_user_id ON workflow_executions(user_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_created_at ON workflow_executions(created_at DESC);
CREATE INDEX idx_workflow_executions_amc_id ON workflow_executions(amc_execution_id) WHERE amc_execution_id IS NOT NULL;
```

### Scheduling System

#### workflow_schedules
```sql
CREATE TABLE workflow_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    cron_expression TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    
    -- Foreign Keys
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Schedule Status
    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMPTZ NOT NULL,
    parameters JSONB DEFAULT '{}',
    
    -- Tracking
    total_runs INTEGER DEFAULT 0,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    last_run_at TIMESTAMPTZ,
    last_run_status TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    paused_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_workflow_schedules_workflow_id ON workflow_schedules(workflow_id);
CREATE INDEX idx_workflow_schedules_user_id ON workflow_schedules(user_id);
CREATE INDEX idx_workflow_schedules_next_run ON workflow_schedules(is_active, next_run_at) WHERE is_active = true;
```

#### schedule_runs
```sql
CREATE TABLE schedule_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    schedule_id UUID NOT NULL REFERENCES workflow_schedules(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    
    -- Run Details
    status TEXT NOT NULL, -- SUCCESS, FAILED, SKIPPED
    error_message TEXT,
    duration_seconds INTEGER,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_schedule_runs_schedule_id ON schedule_runs(schedule_id);
CREATE INDEX idx_schedule_runs_created_at ON schedule_runs(created_at DESC);
```

### Data Collections (Reporting)

#### report_data_collections
```sql
CREATE TABLE report_data_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Foreign Keys
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    instance_id UUID NOT NULL REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Collection Configuration
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    parameters JSONB DEFAULT '{}',
    
    -- Status Tracking
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, PAUSED, COMPLETED, FAILED
    total_weeks INTEGER DEFAULT 0,
    completed_weeks INTEGER DEFAULT 0,
    failed_weeks INTEGER DEFAULT 0,
    
    -- Progress Metrics
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    estimated_completion TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_data_collections_workflow_id ON report_data_collections(workflow_id);
CREATE INDEX idx_data_collections_instance_id ON report_data_collections(instance_id);
CREATE INDEX idx_data_collections_user_id ON report_data_collections(user_id);
CREATE INDEX idx_data_collections_status ON report_data_collections(status);
```

#### report_data_weeks
```sql
CREATE TABLE report_data_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    collection_id UUID NOT NULL REFERENCES report_data_collections(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    
    -- Week Definition
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    week_number INTEGER, -- Week number within collection
    
    -- Status
    status TEXT DEFAULT 'PENDING', -- PENDING, RUNNING, SUCCESS, FAILED, SKIPPED
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metrics
    execution_duration INTEGER, -- seconds
    result_rows INTEGER,
    result_size_bytes BIGINT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_data_weeks_collection_id ON report_data_weeks(collection_id);
CREATE INDEX idx_data_weeks_execution_id ON report_data_weeks(execution_id);
CREATE INDEX idx_data_weeks_status ON report_data_weeks(status);
CREATE INDEX idx_data_weeks_dates ON report_data_weeks(week_start_date, week_end_date);
```

### Campaign and Product Management

#### campaigns
```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id TEXT NOT NULL, -- Amazon's campaign ID
    name TEXT NOT NULL,
    campaign_type TEXT NOT NULL, -- sponsoredProducts, sponsoredBrands, etc.
    state TEXT NOT NULL, -- ENABLED, PAUSED, ARCHIVED
    
    -- Foreign Keys
    instance_id UUID NOT NULL REFERENCES amc_instances(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Performance Metrics
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    sales DECIMAL(10,2) DEFAULT 0,
    acos DECIMAL(5,2), -- Advertising Cost of Sales
    roas DECIMAL(5,2), -- Return on Ad Spend
    
    -- Campaign Configuration
    start_date DATE,
    end_date DATE,
    budget DECIMAL(10,2),
    budget_type TEXT, -- DAILY, LIFETIME
    targeting_type TEXT,
    portfolio_id TEXT,
    
    -- Sync Status
    last_sync_at TIMESTAMPTZ,
    performance_updated_at TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_campaigns_campaign_id_instance ON campaigns(campaign_id, instance_id);
CREATE INDEX idx_campaigns_instance_id ON campaigns(instance_id);
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_state ON campaigns(state);
CREATE INDEX idx_campaigns_type ON campaigns(campaign_type);
```

#### asins
```sql
CREATE TABLE asins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin TEXT NOT NULL, -- Amazon Standard Identification Number
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Product Information
    title TEXT,
    brand TEXT,
    category TEXT,
    image_url TEXT,
    price DECIMAL(10,2),
    
    -- Performance Metrics
    sales_rank INTEGER, -- Best Sellers Rank
    review_count INTEGER,
    average_rating DECIMAL(2,1),
    
    -- User Organization
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    
    -- Product Status
    is_active BOOLEAN DEFAULT true,
    parent_asin TEXT, -- For product variations
    variation_theme TEXT, -- Color, Size, etc.
    
    -- Additional Details
    dimensions JSONB, -- Product dimensions
    weight DECIMAL(8,3), -- Product weight
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ
);

-- Indexes
CREATE UNIQUE INDEX idx_asins_asin_user ON asins(asin, user_id);
CREATE INDEX idx_asins_user_id ON asins(user_id);
CREATE INDEX idx_asins_brand ON asins(brand) WHERE brand IS NOT NULL;
CREATE INDEX idx_asins_category ON asins(category) WHERE category IS NOT NULL;
CREATE INDEX idx_asins_tags ON asins USING GIN(tags);
CREATE INDEX idx_asins_active ON asins(is_active) WHERE is_active = true;
```

#### asin_lists
```sql
CREATE TABLE asin_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- List Configuration
    category TEXT,
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    
    -- Cached Metrics
    asin_count INTEGER DEFAULT 0,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_asin_lists_user_id ON asin_lists(user_id);
CREATE INDEX idx_asin_lists_category ON asin_lists(category) WHERE category IS NOT NULL;
CREATE INDEX idx_asin_lists_public ON asin_lists(is_public) WHERE is_public = true;
```

#### asin_list_items
```sql
CREATE TABLE asin_list_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    list_id UUID NOT NULL REFERENCES asin_lists(id) ON DELETE CASCADE,
    asin_id UUID NOT NULL REFERENCES asins(id) ON DELETE CASCADE,
    
    -- List Position
    position INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    
    -- Audit Fields
    added_at TIMESTAMPTZ DEFAULT NOW(),
    added_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_asin_list_items_unique ON asin_list_items(list_id, asin_id);
CREATE INDEX idx_asin_list_items_list_id ON asin_list_items(list_id, position);
```

### AMC Schema and Templates

#### amc_data_sources
```sql
CREATE TABLE amc_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- impressions, clicks, conversions, etc.
    
    -- Source Configuration
    table_type TEXT, -- fact, dimension
    data_freshness TEXT, -- How fresh the data is
    grain TEXT, -- Data granularity
    
    -- Documentation
    documentation_url TEXT,
    example_queries TEXT[],
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    deprecated_at TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_amc_data_sources_name ON amc_data_sources(name);
CREATE INDEX idx_amc_data_sources_category ON amc_data_sources(category);
CREATE INDEX idx_amc_data_sources_active ON amc_data_sources(is_active) WHERE is_active = true;
```

#### amc_schema_fields
```sql
CREATE TABLE amc_schema_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    data_source_id UUID NOT NULL REFERENCES amc_data_sources(id) ON DELETE CASCADE,
    
    -- Field Definition
    field_name TEXT NOT NULL,
    data_type TEXT NOT NULL, -- STRING, INTEGER, DECIMAL, DATE, TIMESTAMP
    description TEXT,
    
    -- Field Properties
    is_nullable BOOLEAN DEFAULT true,
    is_primary_key BOOLEAN DEFAULT false,
    is_foreign_key BOOLEAN DEFAULT false,
    
    -- Field Constraints
    max_length INTEGER,
    valid_values TEXT[], -- For enum-like fields
    
    -- Documentation
    examples TEXT[],
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_amc_schema_fields_data_source ON amc_schema_fields(data_source_id);
CREATE INDEX idx_amc_schema_fields_name ON amc_schema_fields(field_name);
CREATE UNIQUE INDEX idx_amc_schema_fields_unique ON amc_schema_fields(data_source_id, field_name);
```

#### query_templates
```sql
CREATE TABLE query_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    
    -- Template Content
    sql_template TEXT NOT NULL,
    parameters JSONB DEFAULT '{}', -- Parameter definitions
    
    -- Template Metadata
    tags TEXT[] DEFAULT '{}',
    difficulty_level TEXT, -- BEGINNER, INTERMEDIATE, ADVANCED
    estimated_runtime TEXT, -- Expected execution time
    
    -- Usage Tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Authoring
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_official BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_query_templates_category ON query_templates(category);
CREATE INDEX idx_query_templates_tags ON query_templates USING GIN(tags);
CREATE INDEX idx_query_templates_usage ON query_templates(usage_count DESC);
CREATE INDEX idx_query_templates_public ON query_templates(is_public) WHERE is_public = true;
```

### Build Guides System

#### build_guides
```sql
CREATE TABLE build_guides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    
    -- Guide Configuration
    difficulty_level TEXT, -- BEGINNER, INTERMEDIATE, ADVANCED
    estimated_time INTEGER, -- Minutes to complete
    prerequisites TEXT[],
    
    -- Content Organization
    section_count INTEGER DEFAULT 0,
    query_count INTEGER DEFAULT 0,
    
    -- Tracking
    completion_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    
    -- Status
    is_published BOOLEAN DEFAULT true,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_build_guides_category ON build_guides(category);
CREATE INDEX idx_build_guides_difficulty ON build_guides(difficulty_level);
CREATE INDEX idx_build_guides_published ON build_guides(is_published) WHERE is_published = true;
```

#### user_guide_progress
```sql
CREATE TABLE user_guide_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    guide_id UUID NOT NULL REFERENCES build_guides(id) ON DELETE CASCADE,
    
    -- Progress Tracking
    current_section INTEGER DEFAULT 1,
    completed_sections INTEGER[] DEFAULT '{}',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Status
    status TEXT DEFAULT 'IN_PROGRESS', -- NOT_STARTED, IN_PROGRESS, COMPLETED
    
    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE UNIQUE INDEX idx_user_guide_progress_unique ON user_guide_progress(user_id, guide_id);
CREATE INDEX idx_user_guide_progress_user ON user_guide_progress(user_id);
CREATE INDEX idx_user_guide_progress_guide ON user_guide_progress(guide_id);
```

## Critical Database Functions

### Performance Indexes
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_workflow_executions_user_status ON workflow_executions(user_id, status);
CREATE INDEX idx_campaigns_instance_type ON campaigns(instance_id, campaign_type);
CREATE INDEX idx_data_weeks_collection_status ON report_data_weeks(collection_id, status);

-- Partial indexes for active records
CREATE INDEX idx_schedules_active_next_run ON workflow_schedules(next_run_at) 
WHERE is_active = true;

-- GIN indexes for JSONB columns
CREATE INDEX idx_workflows_parameters ON workflows USING GIN(parameters);
CREATE INDEX idx_executions_result_data ON workflow_executions USING GIN(result_data);
```

### Database Functions
```sql
-- Function to update workflow execution counts
CREATE OR REPLACE FUNCTION update_workflow_execution_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE workflows 
        SET last_executed_at = NEW.created_at
        WHERE id = NEW.workflow_id;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain execution counts
CREATE TRIGGER trigger_update_workflow_execution_count
    AFTER INSERT ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_execution_count();

-- Function to calculate collection progress
CREATE OR REPLACE FUNCTION calculate_collection_progress()
RETURNS TRIGGER AS $$
DECLARE
    total_weeks INTEGER;
    completed_weeks INTEGER;
    progress_pct DECIMAL(5,2);
BEGIN
    -- Count total and completed weeks
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as completed
    INTO total_weeks, completed_weeks
    FROM report_data_weeks
    WHERE collection_id = COALESCE(NEW.collection_id, OLD.collection_id);
    
    -- Calculate progress percentage
    progress_pct = CASE 
        WHEN total_weeks > 0 THEN (completed_weeks::DECIMAL / total_weeks * 100)
        ELSE 0 
    END;
    
    -- Update collection record
    UPDATE report_data_collections
    SET 
        total_weeks = total_weeks,
        completed_weeks = completed_weeks,
        progress_percentage = progress_pct,
        updated_at = NOW()
    WHERE id = COALESCE(NEW.collection_id, OLD.collection_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger for collection progress updates
CREATE TRIGGER trigger_calculate_collection_progress
    AFTER INSERT OR UPDATE OR DELETE ON report_data_weeks
    FOR EACH ROW
    EXECUTE FUNCTION calculate_collection_progress();
```

## Data Integrity Constraints

### Foreign Key Constraints
```sql
-- Ensure workflow executions belong to workflow owner
ALTER TABLE workflow_executions 
ADD CONSTRAINT fk_execution_user_workflow 
CHECK (
    user_id = (SELECT user_id FROM workflows WHERE id = workflow_id)
);

-- Ensure schedules belong to workflow owner  
ALTER TABLE workflow_schedules
ADD CONSTRAINT fk_schedule_user_workflow
CHECK (
    user_id = (SELECT user_id FROM workflows WHERE id = workflow_id)
);

-- Ensure collections belong to workflow owner
ALTER TABLE report_data_collections
ADD CONSTRAINT fk_collection_user_workflow
CHECK (
    user_id = (SELECT user_id FROM workflows WHERE id = workflow_id)
);
```

### Check Constraints
```sql
-- Validate execution status values
ALTER TABLE workflow_executions
ADD CONSTRAINT chk_execution_status
CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', 'TIMEOUT'));

-- Validate collection status values  
ALTER TABLE report_data_collections
ADD CONSTRAINT chk_collection_status
CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'FAILED'));

-- Validate progress percentage
ALTER TABLE report_data_collections
ADD CONSTRAINT chk_progress_percentage
CHECK (progress_percentage >= 0 AND progress_percentage <= 100);

-- Validate ASIN format
ALTER TABLE asins
ADD CONSTRAINT chk_asin_format
CHECK (asin ~ '^B[0-9A-Z]{9}$');
```

## Row Level Security (RLS)

### User Data Isolation
```sql
-- Enable RLS on user-specific tables
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE amc_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Policies for data access
CREATE POLICY workflows_user_access ON workflows
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY executions_user_access ON workflow_executions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY instances_user_access ON amc_instances
    FOR ALL USING (user_id = auth.uid());
```

## Performance Optimization

### Query Optimization Tips
1. **Always use indexes** on foreign key columns
2. **Avoid SELECT \*** in application queries  
3. **Use LIMIT** for paginated results
4. **Index JSONB columns** used in WHERE clauses
5. **Use partial indexes** for filtered queries

### Maintenance Queries
```sql
-- Analyze table statistics
ANALYZE workflows;
ANALYZE workflow_executions;

-- Find unused indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- Monitor slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;
```