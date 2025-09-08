# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**RecomAMP** - Amazon Marketing Cloud (AMC) platform for managing AMC instances, building SQL queries, executing workflows, and analyzing campaign data across multiple Amazon advertiser accounts.

## Tech Stack

### Backend
- **Framework**: FastAPI with Python 3.11
- **Database**: Supabase (PostgreSQL)
- **Authentication**: OAuth 2.0 with Amazon, JWT tokens
- **Encryption**: Fernet for token storage
- **HTTP Client**: httpx with tenacity for retries
- **Task Scheduling**: croniter
- **Background Services**: Token refresh, execution polling, schedule executor, collection executor

### Frontend
- **Framework**: React 19.1.0 with TypeScript 5.8
- **Routing**: React Router v7
- **State Management**: TanStack Query v5
- **UI**: Tailwind CSS with forms/typography plugins
- **Code Editor**: Monaco Editor for SQL
- **Charts**: Chart.js with react-chartjs-2
- **Build Tool**: Vite

## Development Commands

### Quick Start
```bash
# Start all services with one command
./start_services.sh

# This launches:
# ✓ Backend API: http://localhost:8001
# ✓ Frontend UI: http://localhost:5173
# ✓ API Documentation: http://localhost:8001/docs
```

### Backend Commands
```bash
# Run backend
python main_supabase.py

# Run tests
pytest tests/ -v
pytest tests/test_api_auth.py -v  # Specific test
pytest --cov=amc_manager tests/    # With coverage

# Check connections
python scripts/check_supabase_connection.py
```

### Frontend Commands
```bash
cd frontend

# Development
npm install
npm run dev

# Linting
npm run lint

# Type checking (no npm script, use directly)
npx tsc --noEmit
npx tsc --noEmit --watch  # Watch mode

# Build
npm run build

# Testing
npm test                     # Unit tests with Vitest
npm run test:ui             # Vitest UI
npm run test:coverage       # Coverage report
npx playwright test         # E2E tests
npx playwright test --ui    # Interactive E2E
```

## ⚡ Critical Gotchas

1. **AMC ID Duality**: Always use `instance_id` for AMC API calls, not the internal `id` UUID
2. **Entity ID Required**: AMC API calls require `entity_id` from `amc_accounts.account_id` (joined via `amc_instances.account_id` FK)
3. **Date Format**: AMC requires dates without timezone: `2025-07-15T00:00:00` (no 'Z')
4. **Token Refresh**: Use `refresh_access_token()` not `refresh_token()` in TokenService
5. **Async/Await**: Always await async methods, but Supabase client is synchronous (no await)
6. **Type Imports**: Use `import type` for TypeScript type-only imports (verbatimModuleSyntax)
7. **Monaco Editor**: Must use pixel heights (e.g., `height="400px"`), not percentages
8. **FastAPI Routes**: Collections need trailing slash for POST/PUT (e.g., `/workflows/` not `/workflows`)
9. **Schedule Deduplication**: Schedules check for recent runs within 5 minutes to prevent duplicates
10. **Python Command**: Use `python` not `python3` in scripts

## Project Structure

```
amazon-helper-2/
├── amc_manager/               # Backend Python package
│   ├── api/                  # API endpoints
│   │   ├── supabase/        # Supabase-specific endpoints
│   │   └── routes/          # Additional route modules
│   ├── core/                # Core utilities
│   ├── services/            # Business logic layer
│   ├── models/              # Database models
│   └── schemas/             # Pydantic schemas
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Route pages
│   │   ├── services/       # API service layer
│   │   └── types/          # TypeScript types
│   └── dist/               # Production build
├── scripts/                 # Utility and migration scripts
├── tests/                   # Test suites
│   ├── amc/                # AMC integration tests
│   ├── supabase/           # Database tests
│   └── flow_composition/   # Flow composition tests (future feature)
├── .agent-os/              # Agent OS configuration
│   ├── instructions/       # Execution instructions
│   └── standards/          # Code standards
├── .cursor/rules/          # Cursor IDE rules
├── main_supabase.py        # FastAPI application entry
└── start_services.sh       # Local development launcher
```

## Key Database Tables

```sql
-- Core tables
users                      -- User accounts with encrypted OAuth tokens
amc_instances             -- AMC instance configurations
amc_accounts              -- AMC account details (contains entity_id)
workflows                 -- SQL query workflows
workflow_executions       -- Execution history with results
workflow_schedules        -- Automated execution schedules
schedule_runs             -- Schedule execution history

-- Supporting tables
amc_data_sources         -- AMC schema documentation
amc_schema_fields        -- Field metadata
query_templates          -- Pre-built query library
query_flow_templates     -- Flow template definitions
campaigns                -- Campaign data
instance_brands          -- Brand-instance associations
asins                    -- ASIN management

-- Build Guides (Added 2025-08-21)
build_guides             -- Guide metadata and configuration
build_guide_sections     -- Guide content sections
build_guide_queries      -- Associated SQL queries
build_guide_examples     -- Example results
build_guide_metrics      -- Metric/dimension definitions
user_guide_progress      -- User progress tracking
user_guide_favorites     -- User favorites

-- Reports & Analytics (Phase 3-4)
report_data_collections  -- Historical data collection configs
report_data_weeks       -- Week-by-week execution tracking
dashboards              -- Dashboard configurations
dashboard_widgets       -- Widget definitions
dashboard_shares        -- Sharing permissions
```

## Critical Architecture Patterns

### Backend Service Layer Pattern
```python
# ALL services inherit from DatabaseService
from amc_manager.services.database_service import DatabaseService

class MyService(DatabaseService):
    def __init__(self):
        super().__init__()
    
    @with_connection_retry
    async def my_method(self):
        # Database operations auto-retry on disconnect
        pass
```

### AMC Instance ID Resolution
```python
# CRITICAL: Always join amc_accounts when fetching instances
instance = db.table('amc_instances')\
    .select('*, amc_accounts(*)')\  # ← REQUIRED for entity_id
    .eq('instance_id', instance_id)\
    .execute()

entity_id = instance['amc_accounts']['account_id']  # This is the AMC entity ID
```

### Token Management
```python
# Always use retry client for AMC operations
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry

result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,  # Use AMC instance ID, not UUID!
    user_id=user_id,
    entity_id=entity_id,
)
```

### Frontend API Service Pattern
```typescript
// Service pattern with consistent error handling
const service = {
  list: () => api.get('/workflows'),
  get: (id) => api.get(`/workflows/${id}`),
  create: (data) => api.post('/workflows/', data),  // Trailing slash!
  update: (id, data) => api.put(`/workflows/${id}`, data),
  delete: (id) => api.delete(`/workflows/${id}`)
};
```

### React Query Pattern
```typescript
// Consistent query key structure for caching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes
      gcTime: 10 * 60 * 1000,        // 10 minutes (not cacheTime!)
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
  },
});

// Query keys must be consistent
['workflows', workflowId]  // ✓ Good
['workflow', id]           // ✗ Bad - different structure
```

## Background Services

1. **Token Refresh Service** (every 10 minutes): Refreshes OAuth tokens before expiry
2. **Execution Status Poller** (every 15 seconds): Updates status of pending AMC executions
3. **Schedule Executor Service** (every 60 seconds): Executes scheduled workflows
4. **Collection Executor Service**: Manages historical data collection for reports

## Common Issues & Solutions

### "Failed to decrypt token"
User must re-authenticate - FERNET_KEY may have changed

### 403 Forbidden on AMC API
- Use `instance_id` not internal UUID
- Ensure entity_id in headers from `amc_accounts.account_id`

### Empty AMC Query Results
- Check date format (no 'Z' suffix)
- Account for 14-day data lag

### Schedule Execution Failures
- Check entity_id is properly joined from amc_accounts
- Verify user has valid tokens
- Check timezone calculations
- Handle null last_run_at properly

### TypeScript Build Errors
```typescript
// Fix type-only imports
import type { Workflow } from '../types';  // ✓ Correct
import { Workflow } from '../types';       // ✗ Error with verbatimModuleSyntax
```

### Monaco Editor Height Issues
```tsx
// Must use pixel heights
<SQLEditor height="400px" />     // ✓ Works
<SQLEditor height="100%" />      // ✗ Often fails in flex containers
```

### FastAPI Route Issues
```python
# Collections need trailing slash
api.post('/workflows/', data)    # ✓ Returns 201
api.post('/workflows', data)      # ✗ Returns 405
```

## Environment Variables

```bash
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx
FERNET_KEY=xxx  # Auto-generated if missing, keep consistent!
JWT_SECRET_KEY=xxx

# Optional
AMC_USE_REAL_API=true  # "false" for mock responses
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8001
FRONTEND_URL=http://localhost:5173
```

## API Endpoints

### Core Endpoints
```http
# Authentication
POST   /api/auth/login
POST   /api/auth/amazon/callback
GET    /api/auth/me

# Workflows (note trailing slash!)
GET    /api/workflows/
POST   /api/workflows/
GET    /api/workflows/{id}
PUT    /api/workflows/{id}
POST   /api/workflows/{id}/execute

# Schedules
GET    /api/schedules/
POST   /api/schedules/
GET    /api/schedules/{id}
POST   /api/schedules/{id}/pause
POST   /api/schedules/{id}/resume
GET    /api/schedules/{id}/history

# AMC Instances
GET    /api/instances/
POST   /api/instances/
GET    /api/instances/{id}

# Campaigns & ASINs
GET    /api/campaigns/
POST   /api/campaigns/import/{instance_id}
GET    /api/asins/
POST   /api/asins/
DELETE /api/asins/{id}

# Data Sources
GET    /api/data-sources/
GET    /api/data-sources/{id}

# Build Guides
GET    /api/build-guides/
GET    /api/build-guides/{guide_id}
POST   /api/build-guides/{guide_id}/start
PUT    /api/build-guides/{guide_id}/progress
POST   /api/build-guides/{guide_id}/favorite

# Query Templates
GET    /api/query-templates/
GET    /api/query-templates/{id}

# Query Flow Templates
GET    /api/query-flow-templates/
POST   /api/query-flow-templates/
GET    /api/query-flow-templates/{id}
PUT    /api/query-flow-templates/{id}
DELETE /api/query-flow-templates/{id}

# Data Collections (Phase 3)
GET    /api/data-collections/
POST   /api/data-collections/
GET    /api/data-collections/{id}
POST   /api/data-collections/{id}/pause
POST   /api/data-collections/{id}/resume
POST   /api/data-collections/{id}/retry-failed
DELETE /api/data-collections/{id}

# Dashboards (Phase 4)
GET    /api/dashboards/
POST   /api/dashboards/
GET    /api/dashboards/{dashboard_id}
PUT    /api/dashboards/{dashboard_id}
DELETE /api/dashboards/{dashboard_id}
POST   /api/dashboards/{dashboard_id}/share
GET    /api/dashboards/{dashboard_id}/shares
DELETE /api/dashboards/{dashboard_id}/shares/{user_id}

# Dashboard Widgets
GET    /api/dashboards/{dashboard_id}/widgets/
POST   /api/dashboards/{dashboard_id}/widgets/
PUT    /api/dashboards/{dashboard_id}/widgets/{widget_id}
DELETE /api/dashboards/{dashboard_id}/widgets/{widget_id}
POST   /api/dashboards/{dashboard_id}/widgets/{widget_id}/data
PUT    /api/dashboards/{dashboard_id}/widgets/reorder
```

## Testing

### Backend Testing
```bash
# Run all tests
pytest tests/ -v

# Specific test file
pytest tests/test_api_auth.py -v

# With coverage
pytest --cov=amc_manager tests/

# Flow composition tests (future feature)
pytest tests/flow_composition/ -v
```

### Frontend Testing
```bash
# Unit tests with Vitest
npm test
npm run test:ui      # Interactive UI
npm run test:coverage

# E2E with Playwright
npx playwright test
npx playwright test --ui  # Interactive mode
npx playwright test test-name.spec.ts  # Specific test
```

## Build Guides Feature

Build Guides provide step-by-step tactical guidance for AMC query use cases:
- Structured markdown content sections
- Pre-built SQL queries with parameters
- Example results with interpretation
- Progress tracking and favorites

### Key Components
- **Backend**: `build_guide_service.py`, `/api/build-guides/` endpoints
- **Frontend**: `BuildGuides.tsx`, `BuildGuideDetail.tsx`
- **Database**: 7 tables for guides, sections, queries, examples, metrics

### Markdown Rendering
Uses react-markdown with remark-gfm for tables, code blocks, and formatting.

## Reports & Analytics Platform

### Phase 3: Historical Data Collection (Complete)
- 52-week backfill capability
- Week-by-week AMC workflow execution
- Real-time progress tracking
- Parallel processing (5 collections, 10 weeks concurrent)
- Automatic retry on failures

### Phase 4: Dashboard Visualization (Complete)
- 10 widget types (line, bar, pie, area, scatter, table, metric_card, text, heatmap, funnel)
- Dashboard sharing with permissions
- Chart.js integration for visualizations
- Widget configuration system with layout detection

## Agent OS Integration

The repository includes Agent OS configuration for AI-assisted development:
- `.agent-os/` directory contains instructions and standards
- `.cursor/rules/` contains MDC rules for Cursor IDE integration
- Follows structured task execution patterns with pre/post-flight checks

## Recent Critical Fixes

- **2025-08-29**: SQL preview fixes for campaign/ASIN parameters
- **2025-08-28**: Parameter injection improvements for AMC limits
- **2025-08-27**: ASIN management system implementation
- **Schedule Execution**: Fixed entity_id resolution and null handling
- **Token Refresh**: Changed to use `refresh_access_token()` method
- **Monaco Editor**: Fixed height issues in modals using pixel values
- **Data Collections**: Fixed date serialization and ID field management

## Debugging Commands

```bash
# Check API routes
curl http://localhost:8001/api/debug/routes

# Test Supabase connection
python scripts/check_supabase_connection.py

# Monitor server logs
tail -f server.log

# Check running executions
python scripts/find_running_executions.py

# Validate schedules
python scripts/validate_schedules.py
```

## Database Migrations

```bash
# Apply migrations
python scripts/apply_performance_indexes.py
python scripts/apply_schedule_migrations.py
python scripts/apply_build_guides_migration.py
python scripts/apply_campaign_optimizations.py
python scripts/apply_instance_brands_migration.py

# Import schemas
python scripts/import_amc_schemas.py

# Seed data
python scripts/seed_creative_asin_guide.py
```

## Deployment

```bash
# Docker
docker build -t recomamp .
docker run -p 8001:8001 --env-file .env recomamp

# Railway
./prepare_railway.sh
# Configure environment variables in Railway dashboard
```

## Architecture Decisions

- **Supabase**: Built-in auth, RLS, real-time subscriptions, managed PostgreSQL
- **FastAPI**: Native async/await, automatic OpenAPI docs, type validation
- **Monaco Editor**: Full SQL syntax highlighting, same as VS Code
- **TanStack Query**: Powerful caching, optimistic updates, background refetching
- **Vite**: Fast HMR, optimized builds, TypeScript support out of the box