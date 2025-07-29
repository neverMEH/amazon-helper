# Amazon AMC Manager - Project Structure

## Directory Layout

```
amazon-helper/
├── amc_manager/                  # Main application package
│   ├── __init__.py
│   ├── api/                     # FastAPI endpoints
│   │   ├── auth.py
│   │   ├── campaigns.py
│   │   ├── instances.py
│   │   ├── queries.py
│   │   └── workflows.py
│   ├── config/                  # Configuration
│   │   ├── __init__.py
│   │   └── settings.py          # Environment settings with Supabase config
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── api_client.py        # Amazon API client
│   │   ├── auth.py              # Authentication manager
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── logger.py            # Logging configuration
│   │   └── supabase_client.py   # Supabase services (NEW)
│   ├── models/                  # Database models
│   │   ├── base.py
│   │   ├── campaign.py
│   │   ├── query_template.py
│   │   ├── user.py
│   │   └── workflow.py
│   └── services/                # Business logic
│       ├── data_service.py
│       ├── execution_service.py
│       ├── instance_service.py
│       ├── query_builder.py
│       └── workflow_service.py
│
├── database/                    # Database files (NEW STRUCTURE)
│   ├── README.md
│   └── supabase/
│       ├── schema/
│       │   ├── 01_tables.sql
│       │   └── 02_rls_policies.sql
│       ├── functions/
│       │   ├── 00_test_jsonb.sql
│       │   └── 01_utility_functions.sql
│       ├── migrations/          # Future migrations
│       └── setup_all.sql        # Complete setup script
│
├── docs/                        # Documentation
│   ├── API_SETUP_GUIDE.md
│   └── supabase/               # Supabase docs (NEW)
│       ├── README.md
│       ├── SUPABASE_MIGRATION_GUIDE.md
│       └── authentication_options.md
│
├── examples/                    # Example code (NEW)
│   └── example_api_migration.py
│
├── scripts/                     # Utility scripts
│   ├── setup_credentials.py
│   ├── test_api_connection.py
│   ├── test_api_simple.py
│   ├── exchange_token.py
│   └── amc_instances_working.py
│
├── tests/                       # Test files
│   ├── amc/                    # AMC API tests
│   │   ├── check_amc_instances.py
│   │   ├── get_amc_instances.py
│   │   ├── test_amc_access.py
│   │   └── ...
│   └── supabase/               # Supabase tests (NEW)
│       ├── README.md
│       ├── test_supabase_simple.py
│       ├── test_supabase_connection.py
│       └── test_supabase_integration.py
│
├── migrations/                  # Alembic migrations
│   ├── env.py
│   └── script.py.mako
│
├── .env                        # Environment variables (with Supabase)
├── .env.example               
├── requirements.txt            # Updated with Supabase dependencies
├── alembic.ini
├── main.py                     # Main FastAPI application
└── README.md                   # Project readme
```

## Key Changes for Supabase Integration

### 1. New Core Module
- `amc_manager/core/supabase_client.py` - Supabase service classes

### 2. Database Organization
- All SQL files moved to `database/supabase/`
- Organized by type: schema, functions, migrations
- Master setup script for easy deployment

### 3. Documentation Structure
- Supabase-specific docs in `docs/supabase/`
- Migration guide and authentication options
- API migration examples

### 4. Test Organization
- AMC tests in `tests/amc/`
- Supabase tests in `tests/supabase/`
- Clear separation of concerns

### 5. Examples Directory
- API migration examples
- Best practices for Supabase integration

## Quick Start

1. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**:
   - Go to Supabase SQL Editor
   - Run `database/supabase/setup_all.sql`

4. **Run tests**:
   ```bash
   python tests/supabase/test_supabase_connection.py
   ```

5. **Start development**:
   ```bash
   python main.py
   ```

## Next Steps

1. Update API endpoints to use Supabase services
2. Implement chosen authentication strategy
3. Set up real-time subscriptions
4. Configure Supabase Storage for results
5. Deploy to production