# Database Setup for Amazon AMC Manager

This directory contains all database-related files for the Supabase migration.

## Directory Structure

```
database/
├── supabase/
│   ├── schema/
│   │   ├── 01_tables.sql          # Core table definitions
│   │   └── 02_rls_policies.sql    # Row Level Security policies
│   ├── functions/
│   │   ├── 00_test_jsonb.sql      # JSONB operator tests
│   │   └── 01_utility_functions.sql # Database utility functions
│   └── migrations/                 # Future migration scripts
└── README.md
```

## Setup Instructions

### 1. Create Tables and Enable RLS

Run these scripts in order in your Supabase SQL Editor:

1. **01_tables.sql** - Creates all necessary tables:
   - `users` - User authentication and profiles
   - `amc_accounts` - Amazon Advertising accounts
   - `amc_instances` - AMC instance configurations
   - `campaign_mappings` - Campaigns with ASINs and brand associations
   - `brand_configurations` - Brand settings and ASIN mappings
   - `workflows` - AMC workflow definitions
   - `workflow_executions` - Execution history and status
   - `query_templates` - Reusable query templates
   - `amc_query_results` - Query result cache

2. **02_rls_policies.sql** - Sets up Row Level Security:
   - User-based access control
   - Brand sharing capabilities
   - Admin override policies
   - Multi-tenant data isolation

### 2. Create Database Functions

Run the function scripts:

1. **00_test_jsonb.sql** - Test JSONB operators (optional, for verification)
2. **01_utility_functions.sql** - Utility functions:
   - `get_campaigns_by_asins()` - Find campaigns containing specific ASINs
   - `analyze_brand_campaigns()` - Brand performance analytics
   - `auto_tag_campaign()` - Automatic brand tagging based on patterns
   - `get_brand_asin_summary()` - ASIN aggregation by brand
   - `validate_instance_access()` - Security validation for AMC instances
   - `get_workflow_execution_stats()` - Workflow performance metrics
   - `search_campaigns()` - Multi-field campaign search

## Key Features

### Campaign Tracking with ASINs
- Each campaign can have multiple ASINs stored as JSONB array
- Efficient ASIN-based search using GIN indexes
- Brand association for campaign grouping

### Multi-Account Support
- Track multiple Amazon Advertising accounts
- Multiple AMC instances per account
- Instance-level access validation

### Real-time Capabilities
- Tables are ready for Supabase real-time subscriptions
- Workflow execution status updates
- Campaign data changes

## Migration Notes

If migrating from existing PostgreSQL:
1. Export data from old tables
2. Transform to match new schema (especially JSONB fields)
3. Import using Supabase dashboard or API
4. Verify RLS policies are working correctly

## Performance Considerations

- JSONB columns have GIN indexes for fast searches
- Campaign name and type columns are indexed
- User-based queries are optimized with appropriate indexes
- Consider partitioning large tables by date in the future

## Security

- All tables have Row Level Security enabled
- Users can only access their own data
- Brand configurations support sharing between users
- Service role bypasses RLS for admin operations