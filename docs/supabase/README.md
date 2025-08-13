# Supabase Integration Documentation

This directory contains documentation for integrating Supabase with Amazon AMC Manager.

## Documentation Files

### SUPABASE_MIGRATION_GUIDE.md
Comprehensive guide for migrating from PostgreSQL to Supabase, including:
- Environment setup
- Database schema creation
- RLS policies configuration
- Code integration examples
- Migration strategies

### authentication_options.md
Detailed comparison of authentication strategies:
- Option 1: Keep existing Amazon OAuth + Custom JWT
- Option 2: Supabase Auth with Amazon OAuth provider
- Option 3: Hybrid approach (recommended)

## Quick Start

1. **Set up Supabase Project**
   - Create account at [supabase.com](https://supabase.com)
   - Create new project
   - Get credentials from project settings

2. **Configure Environment**
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-key
   ```

3. **Run Database Scripts**
   - Navigate to `database/supabase/`
   - Run scripts in Supabase SQL editor

4. **Update Code**
   - See `examples/example_api_migration.py`
   - Use Supabase services instead of SQLAlchemy

## Key Features Enabled

### Campaign Management
- Track campaigns with multiple ASINs
- Automatic brand tagging
- ASIN-based search and filtering

### Real-time Updates
- Live workflow execution status
- Campaign data changes
- Collaborative updates

### Enhanced Security
- Row Level Security (RLS)
- Multi-tenant data isolation
- Secure token storage

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FastAPI App    │────▶│ Supabase Client  │────▶│  Supabase DB    │
│                 │     │                  │     │                 │
│  - Auth         │     │  - Realtime      │     │  - PostgreSQL   │
│  - APIs         │     │  - Storage       │     │  - RLS          │
│  - Services     │     │  - Functions     │     │  - Functions    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Amazon AMC API  │
                        └──────────────────┘
```

## Support Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Amazon AMC Documentation](https://advertising.amazon.com/API/docs/amc)
- Project Issues: Create issue in repository