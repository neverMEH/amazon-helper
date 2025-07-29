# Supabase Migration Guide for Amazon AMC Manager

## Overview
This guide provides step-by-step instructions for migrating your Amazon AMC Manager from PostgreSQL to Supabase.

## Prerequisites
- Active Supabase project
- Python 3.8+ with pip
- Access to Supabase dashboard

## Migration Steps

### 1. Environment Setup
Your `.env` file has been updated with the following Supabase credentials:
```env
SUPABASE_URL=https://loqaorroihxfkjvcrkdv.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2. Install Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create Database Schema
1. Log into your Supabase dashboard
2. Navigate to SQL Editor
3. Run the following SQL scripts in order:

#### a. Create Tables (supabase_schema.sql)
This creates all necessary tables including:
- `users` - User authentication and profiles
- `amc_accounts` - Amazon Advertising accounts
- `amc_instances` - AMC instance details
- `campaign_mappings` - Campaigns with ASINs and brands
- `brand_configurations` - Brand settings and ASIN associations
- `workflows` - AMC workflow definitions
- `workflow_executions` - Execution history
- `query_templates` - Reusable query templates

#### b. Set up Row Level Security (supabase_rls_policies_fixed.sql)
This ensures data isolation between users with policies for:
- User profile access
- Campaign and brand management
- Workflow execution tracking
- Admin access controls

**Note**: Use `supabase_rls_policies_fixed.sql` instead of the original file. The fixed version properly handles JSONB arrays using the `?` operator instead of trying to cast to text arrays.

#### c. Create Database Functions (supabase_functions.sql)
Utility functions for:
- `get_campaigns_by_asins()` - Find campaigns containing specific ASINs
- `analyze_brand_campaigns()` - Brand performance analytics
- `auto_tag_campaign()` - Automatic brand tagging
- `get_brand_asin_summary()` - ASIN aggregation by brand
- `validate_instance_access()` - Security validation
- `search_campaigns()` - Multi-field campaign search

### 4. Using Supabase in Your Code

#### Basic Usage Example:
```python
from amc_manager.core import CampaignMappingService

# Initialize service
campaign_service = CampaignMappingService()

# Get campaigns by brand
campaigns = await campaign_service.get_campaigns_by_brand(
    user_id="user-uuid",
    brand_tag="BRAND_A"
)

# Search campaigns by ASINs
campaigns_with_asins = await campaign_service.get_campaigns_by_asins(
    user_id="user-uuid",
    asins=["B08N5WRWNW", "B08N5WRWNX"]
)
```

#### Real-time Updates:
```python
from amc_manager.core import WorkflowService

workflow_service = WorkflowService()

def on_execution_update(payload):
    print(f"Execution updated: {payload}")

# Subscribe to workflow execution updates
workflow_service.subscribe_to_executions(
    workflow_id="workflow-uuid",
    callback=on_execution_update
)
```

### 5. Key Features Enabled by Supabase

#### Campaign Tracking with ASINs and Brands:
- Each campaign can have multiple ASINs associated
- Automatic brand tagging based on patterns
- ASIN-based campaign search and filtering

#### Multi-Account AMC Support:
- Track multiple Amazon Advertising accounts
- Manage multiple AMC instances per account
- Instance-level access validation

#### Enhanced Query Capabilities:
- Store custom parameters per campaign
- Brand-specific query templates
- ASIN-based query generation

### 6. API Endpoint Updates
Update your API endpoints to use Supabase services:

```python
from fastapi import Depends
from amc_manager.core import CampaignMappingService

@app.get("/api/campaigns")
async def get_campaigns(
    user_id: str = Depends(get_current_user),
    service: CampaignMappingService = Depends()
):
    return await service.get_campaigns_by_user(user_id)
```

### 7. Data Migration (if needed)
If you have existing data in PostgreSQL:

```python
# Example migration script
from sqlalchemy import create_engine
from amc_manager.core import SupabaseManager

# Connect to old database
old_db = create_engine(old_database_url)

# Get Supabase client
supabase = SupabaseManager.get_client()

# Migrate users
with old_db.connect() as conn:
    users = conn.execute("SELECT * FROM users").fetchall()
    for user in users:
        supabase.table('users').insert({
            'id': str(user.id),
            'email': user.email,
            'name': user.name,
            # ... map other fields
        }).execute()
```

### 8. Testing
Run the test script to verify your connection:
```bash
python test_supabase_simple.py
```

### 9. Update Alembic Configuration (Optional)
If you want to continue using Alembic for migrations:
```ini
sqlalchemy.url = postgresql://postgres.[project-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## Benefits of Supabase Integration

1. **Real-time Updates**: Subscribe to changes in workflow executions
2. **Built-in Auth**: Optionally use Supabase Auth for user management
3. **Auto-generated APIs**: REST APIs automatically created for your tables
4. **Row Level Security**: Fine-grained access control
5. **Storage**: Built-in file storage for query results
6. **Edge Functions**: Serverless functions for complex operations

## Troubleshooting

### Connection Issues
- Verify your Supabase project is active
- Check network connectivity
- Ensure credentials are correct in `.env`

### Table Not Found Errors
- Run all SQL scripts in the correct order
- Check the SQL Editor for any execution errors

### Permission Errors
- Verify RLS policies are correctly applied
- Use service role key for admin operations
- Check user authentication

## Next Steps

1. Integrate Supabase services into your API endpoints
2. Set up real-time subscriptions for live updates
3. Configure Supabase Storage for query results
4. Implement Edge Functions for complex AMC queries
5. Set up automated backups in Supabase dashboard

## Support
- Supabase Documentation: https://supabase.com/docs
- Amazon AMC Documentation: https://advertising.amazon.com/API/docs/amc