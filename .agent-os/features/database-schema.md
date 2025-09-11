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
    
    -- Report Dashboard Enhancements (2025-09-10)
    report_metadata JSONB, -- Cached KPI metadata and performance metrics
    last_report_generated_at TIMESTAMPTZ, -- Report freshness tracking
    
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
CREATE INDEX idx_report_data_collections_report_metadata ON report_data_collections USING GIN(report_metadata);
```

#### report_data_weeks
```sql
CREATE TABLE report_data_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    collection_id UUID NOT NULL REFERENCES report_data_collections(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    workflow_execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    amc_execution_id TEXT, -- AMC's actual execution ID for API calls
    
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
    
    -- Report Dashboard Enhancements (2025-09-10)
    summary_stats JSONB, -- Pre-calculated weekly statistics (totals, averages, min/max)
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_data_weeks_collection_id ON report_data_weeks(collection_id);
CREATE INDEX idx_data_weeks_execution_id ON report_data_weeks(execution_id);
CREATE INDEX idx_data_weeks_workflow_execution_id ON report_data_weeks(workflow_execution_id);
CREATE INDEX idx_data_weeks_status ON report_data_weeks(status);
CREATE INDEX idx_data_weeks_dates ON report_data_weeks(week_start_date, week_end_date);
CREATE INDEX idx_report_data_weeks_summary_stats ON report_data_weeks USING GIN(summary_stats);
CREATE INDEX idx_report_data_weeks_collection_date ON report_data_weeks(collection_id, week_start_date);
```

### Collection Report Dashboard (2025-09-10)

#### collection_report_configs
```sql
CREATE TABLE collection_report_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Foreign Keys
    collection_id UUID NOT NULL REFERENCES report_data_collections(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Configuration Data
    config_data JSONB NOT NULL DEFAULT '{}', -- Dashboard layout, filters, visualization settings
    
    -- Sharing and Access
    is_default BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT false,
    shared_with_users UUID[] DEFAULT '{}',
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_collection_report_configs_collection_user ON collection_report_configs(collection_id, user_id);
CREATE INDEX idx_collection_report_configs_user ON collection_report_configs(user_id);
CREATE INDEX idx_collection_report_configs_shared ON collection_report_configs(is_shared) WHERE is_shared = true;
CREATE INDEX idx_collection_report_configs_config_data ON collection_report_configs USING GIN(config_data);
```

#### collection_report_snapshots
```sql
CREATE TABLE collection_report_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    
    -- Foreign Keys
    collection_id UUID NOT NULL REFERENCES report_data_collections(id) ON DELETE CASCADE,
    config_id UUID REFERENCES collection_report_configs(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Snapshot Data
    snapshot_data JSONB NOT NULL, -- Computed metrics and visualization data
    metadata JSONB DEFAULT '{}', -- Report metadata (date range, parameters, etc.)
    
    -- Sharing Configuration
    is_public BOOLEAN DEFAULT false,
    access_token TEXT, -- For public sharing
    expires_at TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_collection_report_snapshots_collection ON collection_report_snapshots(collection_id);
CREATE INDEX idx_collection_report_snapshots_created_by ON collection_report_snapshots(created_by);
CREATE INDEX idx_collection_report_snapshots_config ON collection_report_snapshots(config_id);
CREATE INDEX idx_collection_report_snapshots_public ON collection_report_snapshots(is_public) WHERE is_public = true;
CREATE INDEX idx_collection_report_snapshots_token ON collection_report_snapshots(access_token) WHERE access_token IS NOT NULL;
CREATE INDEX idx_collection_report_snapshots_data ON collection_report_snapshots USING GIN(snapshot_data);
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

### Query Library System (Enhanced 2025-09-11)

#### query_templates (Enhanced)
```sql
CREATE TABLE query_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    
    -- Template Content
    sql_template TEXT NOT NULL,
    parameters JSONB DEFAULT '{}', -- Legacy parameter definitions
    parameters_schema JSONB DEFAULT '{}', -- JSON Schema for parameters
    
    -- Enhanced Features (Added 2025-09-11)
    report_config JSONB, -- Dashboard configuration for auto-generation
    version INTEGER DEFAULT 1, -- Template version number
    parent_template_id UUID REFERENCES query_templates(id), -- For forked templates
    execution_count INTEGER DEFAULT 0, -- Usage tracking
    
    -- Template Metadata
    tags TEXT[] DEFAULT '{}',
    difficulty_level TEXT, -- BEGINNER, INTERMEDIATE, ADVANCED
    estimated_runtime TEXT, -- Expected execution time
    
    -- Usage Tracking
    usage_count INTEGER DEFAULT 0, -- Legacy usage counter
    last_used_at TIMESTAMPTZ,
    
    -- Authoring
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_official BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT true,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enhanced Indexes (Updated 2025-09-11)
CREATE INDEX idx_query_templates_category ON query_templates(category);
CREATE INDEX idx_query_templates_tags ON query_templates USING GIN(tags);
CREATE INDEX idx_query_templates_usage ON query_templates(usage_count DESC);
CREATE INDEX idx_query_templates_public ON query_templates(is_public) WHERE is_public = true;
CREATE INDEX idx_query_templates_parent ON query_templates(parent_template_id);
CREATE INDEX idx_query_templates_execution_usage ON query_templates(execution_count DESC, created_at DESC);
```

#### query_template_parameters (New 2025-09-11)
```sql
CREATE TABLE query_template_parameters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    parameter_name TEXT NOT NULL,
    parameter_type TEXT NOT NULL CHECK (parameter_type IN (
        'asin_list', 'campaign_list', 'date_range', 'date_expression',
        'campaign_filter', 'threshold_numeric', 'percentage', 'enum_select',
        'string', 'number', 'boolean', 'string_list', 'mapped_from_node'
    )),
    
    -- Display Configuration
    display_name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER,
    group_name TEXT,
    
    -- Validation Rules
    required BOOLEAN DEFAULT true,
    default_value JSONB,
    validation_rules JSONB, -- JSON Schema validation rules
    
    -- UI Configuration
    ui_config JSONB, -- Component configuration and hints
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(template_id, parameter_name)
);

-- Indexes
CREATE INDEX idx_template_parameters_template ON query_template_parameters(template_id);
CREATE INDEX idx_template_parameters_order ON query_template_parameters(template_id, display_order);

-- Enable RLS
ALTER TABLE query_template_parameters ENABLE ROW LEVEL SECURITY;
```

#### query_template_reports (New 2025-09-11)
```sql
CREATE TABLE query_template_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    report_name TEXT NOT NULL,
    
    -- Dashboard Configuration
    dashboard_config JSONB NOT NULL, -- Widget layouts and types
    field_mappings JSONB NOT NULL,   -- Query field to widget mapping
    default_filters JSONB,           -- Default filter values
    widget_order JSONB,              -- Layout configuration
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_template_reports_template ON query_template_reports(template_id);

-- Enable RLS
ALTER TABLE query_template_reports ENABLE ROW LEVEL SECURITY;
```

#### query_template_instances (New 2025-09-11)
```sql
CREATE TABLE query_template_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES query_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Instance Configuration
    instance_name TEXT NOT NULL,
    saved_parameters JSONB NOT NULL, -- User-saved parameter values
    
    -- Usage Tracking
    is_favorite BOOLEAN DEFAULT false,
    last_executed_at TIMESTAMPTZ,
    execution_count INTEGER DEFAULT 0,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_template_instances_user ON query_template_instances(user_id, is_favorite DESC, last_executed_at DESC);
CREATE INDEX idx_template_instances_template ON query_template_instances(template_id);

-- Enable RLS
ALTER TABLE query_template_instances ENABLE ROW LEVEL SECURITY;
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

-- Collection Report Dashboard Functions (2025-09-10)

-- Function to calculate week-over-week changes
CREATE OR REPLACE FUNCTION calculate_week_over_week_change(
    current_week_data JSONB,
    previous_week_data JSONB,
    metric_name TEXT
) RETURNS JSONB AS $$
DECLARE
    current_value NUMERIC;
    previous_value NUMERIC;
    percentage_change NUMERIC;
    absolute_change NUMERIC;
    result JSONB;
BEGIN
    -- Extract metric values (handle null/missing values)
    current_value = COALESCE((current_week_data ->> metric_name)::NUMERIC, 0);
    previous_value = COALESCE((previous_week_data ->> metric_name)::NUMERIC, 0);
    
    -- Calculate absolute change
    absolute_change = current_value - previous_value;
    
    -- Calculate percentage change (handle division by zero)
    IF previous_value = 0 THEN
        IF current_value = 0 THEN
            percentage_change = 0;
        ELSE
            percentage_change = NULL; -- Infinite change from zero
        END IF;
    ELSE
        percentage_change = (absolute_change / previous_value) * 100;
    END IF;
    
    -- Return result as JSON
    result = jsonb_build_object(
        'metric', metric_name,
        'current_value', current_value,
        'previous_value', previous_value,
        'absolute_change', absolute_change,
        'percentage_change', percentage_change
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to aggregate collection weeks data
CREATE OR REPLACE FUNCTION aggregate_collection_weeks(
    collection_id_param UUID,
    start_date_param DATE,
    end_date_param DATE,
    aggregation_method TEXT DEFAULT 'sum' -- 'sum', 'avg', 'min', 'max'
) RETURNS JSONB AS $$
DECLARE
    week_data JSONB;
    aggregated_data JSONB;
    week_record RECORD;
BEGIN
    -- Initialize aggregated data object
    aggregated_data = '{}'::JSONB;
    
    -- Process each week in the date range
    FOR week_record IN 
        SELECT summary_stats 
        FROM report_data_weeks 
        WHERE collection_id = collection_id_param 
        AND week_start_date >= start_date_param 
        AND week_end_date <= end_date_param
        AND status = 'SUCCESS'
        AND summary_stats IS NOT NULL
    LOOP
        week_data = week_record.summary_stats;
        
        -- Aggregate based on method
        IF aggregation_method = 'sum' THEN
            aggregated_data = jsonb_concat_sum(aggregated_data, week_data);
        ELSIF aggregation_method = 'avg' THEN
            aggregated_data = jsonb_concat_avg(aggregated_data, week_data);
        ELSIF aggregation_method = 'min' THEN
            aggregated_data = jsonb_concat_min(aggregated_data, week_data);
        ELSIF aggregation_method = 'max' THEN
            aggregated_data = jsonb_concat_max(aggregated_data, week_data);
        END IF;
    END LOOP;
    
    RETURN aggregated_data;
END;
$$ LANGUAGE plpgsql;

-- Helper functions for JSONB aggregation
CREATE OR REPLACE FUNCTION jsonb_concat_sum(a JSONB, b JSONB) RETURNS JSONB AS $$
DECLARE
    key TEXT;
    result JSONB;
BEGIN
    result = a;
    FOR key IN SELECT jsonb_object_keys(b) LOOP
        IF jsonb_typeof(b -> key) = 'number' THEN
            result = result || jsonb_build_object(key, 
                COALESCE((result ->> key)::NUMERIC, 0) + (b ->> key)::NUMERIC
            );
        END IF;
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Collection Report Summary View
CREATE OR REPLACE VIEW collection_report_summary AS
SELECT 
    c.id as collection_id,
    c.name,
    c.status,
    c.start_date,
    c.end_date,
    c.total_weeks,
    c.completed_weeks,
    c.progress_percentage,
    c.report_metadata,
    c.last_report_generated_at,
    
    -- Week statistics
    COUNT(w.id) as actual_week_count,
    COUNT(CASE WHEN w.status = 'SUCCESS' THEN 1 END) as successful_weeks,
    COUNT(CASE WHEN w.status = 'FAILED' THEN 1 END) as failed_weeks,
    COUNT(CASE WHEN w.status = 'PENDING' THEN 1 END) as pending_weeks,
    
    -- Performance metrics
    AVG(w.execution_duration) as avg_execution_duration,
    SUM(w.result_rows) as total_result_rows,
    SUM(w.result_size_bytes) as total_result_size_bytes,
    
    -- Date ranges
    MIN(w.week_start_date) as earliest_week_start,
    MAX(w.week_end_date) as latest_week_end,
    
    c.created_at,
    c.updated_at
FROM report_data_collections c
LEFT JOIN report_data_weeks w ON w.collection_id = c.id
GROUP BY c.id, c.name, c.status, c.start_date, c.end_date, c.total_weeks, 
         c.completed_weeks, c.progress_percentage, c.report_metadata, 
         c.last_report_generated_at, c.created_at, c.updated_at;
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
ALTER TABLE report_data_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_report_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_report_snapshots ENABLE ROW LEVEL SECURITY;

-- Policies for data access
CREATE POLICY workflows_user_access ON workflows
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY executions_user_access ON workflow_executions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY instances_user_access ON amc_instances
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY collections_user_access ON report_data_collections
    FOR ALL USING (user_id = auth.uid());

-- Collection Report Dashboard RLS Policies (2025-09-10)
CREATE POLICY collection_report_configs_user_access ON collection_report_configs
    FOR ALL USING (
        user_id = auth.uid() 
        OR auth.uid() = ANY(shared_with_users)
    );

CREATE POLICY collection_report_snapshots_access ON collection_report_snapshots
    FOR ALL USING (
        created_by = auth.uid() 
        OR is_public = true
        OR EXISTS (
            SELECT 1 FROM collection_report_configs 
            WHERE id = collection_report_snapshots.config_id 
            AND (user_id = auth.uid() OR auth.uid() = ANY(shared_with_users))
        )
    );

-- Allow users to create their own snapshots
CREATE POLICY collection_report_snapshots_create ON collection_report_snapshots
    FOR INSERT WITH CHECK (created_by = auth.uid());
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