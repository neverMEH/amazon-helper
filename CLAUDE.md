# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the RecomAMP codebase. Follow these patterns and conventions to ensure consistent, high-quality code.

## ⚡ Most Important Things to Remember

1. **AMC ID Duality**: Always use `instance_id` for AMC API calls, not the internal `id` UUID
2. **Date Format**: AMC requires dates without timezone: `2025-07-15T00:00:00` (no 'Z')
3. **Token Refresh**: Use `amc_api_client_with_retry` for automatic token handling
4. **Async/Await**: Always await async methods, but Supabase client is synchronous (no await)
5. **Type Imports**: Use `import type` for TypeScript type-only imports
6. **Monaco Editor**: Must use pixel heights, not percentages
7. **FastAPI Routes**: Collections need trailing slash for POST/PUT
8. **Environment**: Use `python` not `python3` in scripts

## Project Overview

**RecomAMP** - A full-stack Amazon Marketing Cloud (AMC) platform for:
- Managing multiple AMC instances across different advertiser accounts
- Building and testing SQL queries with a visual editor and schema explorer
- Executing workflows with parameter substitution and result visualization
- Scheduling automated recurring executions with smart date handling
- Building a reusable query library with templates and examples
- Tracking execution history with comprehensive error reporting

## Tech Stack

### Backend
- **FastAPI** (0.109.0): Async web framework with automatic OpenAPI docs
- **Supabase**: PostgreSQL database with built-in auth & realtime
- **Python 3.11**: With full async/await support
- **Fernet**: Symmetric encryption for OAuth tokens
- **httpx/tenacity**: HTTP client with retry logic
- **croniter**: CRON expression parsing for scheduling

### Frontend  
- **React 19.1.0**: With new JSX transform
- **TypeScript 5.8**: With verbatimModuleSyntax enabled
- **TanStack Query v5**: Server state management
- **React Router v7**: Client-side routing
- **Monaco Editor**: SQL editing with syntax highlighting
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Build tool and dev server

## 🚀 Quick Start Guide

### One-Command Launch
```bash
# Start everything with one command
./start_services.sh

# This launches:
# ✓ Backend API: http://localhost:8001
# ✓ Frontend UI: http://localhost:5173
# ✓ API Documentation: http://localhost:8001/docs
# ✓ Background services (token refresh, execution polling, scheduling)
```

### First-Time Setup
```bash
# 1. Clone and setup environment
cp .env.example .env
# Edit .env with your Supabase and Amazon credentials

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Initialize database
python scripts/check_supabase_connection.py
python scripts/import_amc_schemas.py
python scripts/apply_performance_indexes.py

# 4. Launch application
./start_services.sh
```

## Development Commands

### Environment Setup
```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Required variables:
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx  
SUPABASE_SERVICE_ROLE_KEY=xxx
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx
FERNET_KEY=xxx  # Auto-generated if missing, keep consistent!
```

### Backend Commands
```bash
# Run backend server (note: system uses 'python' not 'python3' in scripts)
python main_supabase.py                      # Port 8001
uvicorn main_supabase:app --reload --port 8001  # With auto-reload

# Testing
pytest tests/                                # All tests
pytest tests/test_api_auth.py::test_login_success  # Specific test
pytest tests/integration/                    # Integration tests only
pytest tests/supabase/                       # Supabase tests only  
pytest tests/amc/                            # AMC API tests (requires credentials)
pytest -v --tb=short                        # Verbose with short traceback

# Code quality
black amc_manager/                           # Format
flake8 amc_manager/                          # Lint
mypy amc_manager/                            # Type check

# Database operations
python scripts/check_supabase_connection.py  # Check connection
python scripts/import_amc_schemas.py         # Import AMC schema documentation
python scripts/apply_performance_indexes.py  # Apply indexes
python scripts/create_cja_workflow.py        # Create CJA workflow
python scripts/populate_all_fields.py        # Populate field metadata
python scripts/add_execution_results_fields.py # Add results fields to executions

# Token management
python test_token_refresh.py                 # Test automatic token refresh
python scripts/validate_tokens.py            # Validate encrypted tokens
python scripts/fix_token_encryption.py       # Fix token encryption issues

# Scheduling operations
python scripts/apply_schedule_migrations.py  # Apply scheduling schema
python scripts/test_schedule_executor.py     # Test schedule execution
python scripts/validate_schedules.py         # Validate active schedules
```

### Frontend Commands
```bash
cd frontend
npm install                                  # Install dependencies
npm run dev                                  # Dev server on port 5173
npm run build                                # Production build
npm run lint                                 # ESLint
npm run preview                              # Preview production build
npm run typecheck                           # TypeScript type checking
npx tsc --noEmit --watch                    # Type checking in watch mode

# E2E testing with Playwright
npx playwright test                         # Run all tests
npx playwright test --ui                    # Interactive mode
npx playwright test test-name.spec.ts       # Specific test file
npx playwright test --debug                 # Debug mode with inspector
```

## Project Structure

```
amazon-helper/
├── amc_manager/                # Backend Python package
│   ├── api/                   # API endpoints
│   │   └── supabase/         # Supabase-specific endpoints
│   ├── core/                  # Core utilities
│   │   ├── config.py         # Settings management
│   │   ├── supabase_client.py # DB connection singleton
│   │   └── logger_simple.py  # Logging configuration
│   └── services/              # Business logic layer
│       ├── db_service.py     # Base class with reconnection
│       ├── amc_api_client*.py # AMC API integration
│       ├── token_service.py  # OAuth token management
│       ├── enhanced_schedule_service.py # Schedule management
│       ├── schedule_executor_service.py # Schedule execution
│       └── schedule_history_service.py  # History tracking
├── frontend/                   # React application
│   ├── src/
│   │   ├── pages/            # Route components
│   │   ├── components/       # Reusable UI components
│   │   ├── services/         # API client layer
│   │   └── types/            # TypeScript definitions
│   └── dist/                  # Production build output
├── scripts/                    # Utility and migration scripts
├── tests/                      # Test suites
│   ├── amc/                  # AMC API tests
│   ├── integration/          # Integration tests
│   └── supabase/             # Database tests
├── amc_dataset/               # AMC schema documentation (markdown)
├── main_supabase.py           # FastAPI application entry
├── Dockerfile                 # Single container for full stack
└── start_services.sh          # Local development launcher
```

## High-Level Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                      │
│  • TanStack Query for server state                           │
│  • React Router v7 for routing                               │
│  • Monaco Editor for SQL editing                             │
│  • Tailwind CSS for styling                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ /api proxy (dev) or /api (prod)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                          │
│  • Service layer pattern                                      │
│  • Async/await throughout                                     │
│  • Background services (token refresh, polling, scheduling)   │
│  • Token encryption with Fernet                               │
│  • CRON-based workflow scheduling                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴────────────┬─────────────────┐
           ▼                        ▼                 ▼
    ┌──────────────┐     ┌──────────────┐    ┌──────────────┐
    │   Supabase   │     │   AMC API    │    │ Amazon OAuth │
    │  PostgreSQL  │     │              │    │              │
    └──────────────┘     └──────────────┘    └──────────────┘
```

### Backend Service Architecture

All services inherit from `DatabaseService` (aliased as `SupabaseService`) with automatic 30-minute reconnection:

```python
amc_manager/services/
├── db_service.py              # Base class with reconnection logic
│   └── DatabaseService        # Auto-reconnects every 30 min
│       └── @with_connection_retry  # Decorator for retry on disconnect
├── amc_api_client.py          # Direct AMC API integration  
├── amc_api_client_with_retry.py # Enhanced with auto token refresh
│   └── AMCAPIClientWithRetry # Wraps AMCAPIClient with 401 retry
├── token_service.py           # Fernet encryption for OAuth tokens
│   ├── encrypt_token()        # Symmetric encryption with Fernet
│   ├── decrypt_token()        # Safe decryption with error handling
│   └── get_valid_token()      # Auto-refresh if expired
├── token_refresh_service.py   # Background token refresh (10-min intervals)
│   └── TokenRefreshService   # Singleton with asyncio tasks
├── execution_status_poller.py # Background polling (15-second intervals)
│   └── ExecutionStatusPoller # Polls pending executions
├── data_source_service.py     # AMC schema documentation
├── workflow_service.py        # Query workflow management
├── instance_service.py        # AMC instance CRUD
├── amc_execution_service.py   # Execution lifecycle management
├── enhanced_schedule_service.py # Schedule CRUD with presets
│   ├── create_schedule()      # Create with interval presets
│   ├── update_schedule()      # Update configuration
│   ├── get_schedule_with_relations() # Include workflow data
│   └── validate_cron_expression() # CRON validation
├── schedule_executor_service.py # Background execution (1-min intervals)
│   └── ScheduleExecutorService # Singleton with asyncio tasks
│       ├── check_due_schedules() # Find schedules ready to run
│       ├── execute_schedule()    # Run workflow with parameters
│       └── update_next_run()    # Calculate next execution time
└── schedule_history_service.py # Execution history tracking
    ├── record_execution()     # Log each run
    ├── get_execution_history() # Retrieve history
    └── calculate_metrics()    # Success rate, costs, etc.
```

### Frontend Component Architecture

```
src/
├── pages/                      # Route components
│   ├── QueryBuilder.tsx        # 3-step wizard with test execution
│   ├── DataSources.tsx         # List view with side panel preview
│   ├── DataSourceDetail.tsx    # Enhanced with TOC, field explorer
│   ├── MyQueries.tsx          # Workflows with advanced filtering/sorting
│   ├── InstanceDetail.tsx     # Instance management with tabs
│   └── ScheduleManager.tsx    # Schedule dashboard with grid/list views
├── components/
│   ├── query-builder/          # Wizard steps
│   │   ├── QueryEditorStep.tsx       # SQL editor + schema explorer
│   │   ├── QueryConfigurationStep.tsx # Instance & parameters
│   │   └── QueryReviewStep.tsx       # Final review & cost (full width)
│   ├── data-sources/           # Data source UI components
│   ├── workflows/              # Workflow management
│   │   ├── WorkflowFilters.tsx       # Advanced filter sidebar
│   │   ├── WorkflowSortDropdown.tsx  # Sort options dropdown
│   │   ├── ActiveFilterBadges.tsx    # Filter status display
│   │   └── ExecutionModal.tsx        # Execution tracking modal
│   ├── executions/             # Execution viewing
│   │   ├── AMCExecutionDetail.tsx    # Primary execution viewer
│   │   └── ExecutionResults.tsx      # Results table/chart view
│   ├── schedules/              # Scheduling components
│   │   ├── ScheduleWizard.tsx        # 4-step creation wizard
│   │   ├── ScheduleDetailModal.tsx   # View/edit with 3 tabs
│   │   ├── ScheduleHistory.tsx       # Execution history overlay
│   │   ├── IntervalSelector.tsx      # Preset interval picker
│   │   └── CronExpressionBuilder.tsx # Custom CRON builder
│   └── common/                 # Shared components
│       ├── SQLEditor.tsx             # Monaco Editor wrapper
│       └── LoadingSpinner.tsx        # Loading states
└── services/
    ├── api.ts                  # Axios instance with interceptors
    │   ├── Request interceptor       # Adds Bearer token
    │   └── Response interceptor      # Handles 401s
    ├── workflowService.ts      # Workflow CRUD operations
    ├── instanceService.ts      # AMC instance management
    ├── dataSourceService.ts    # Schema documentation
    ├── amcExecutionService.ts  # Execution lifecycle
    └── scheduleService.ts      # Schedule management API
```

## Routing Structure

```typescript
// Main routes (defined in App.tsx)
/login                              // Public: Authentication
/dashboard                          // Protected: Overview
/instances                          // Instance list
/instances/:instanceId              // Instance detail with tabs
  ?tab=overview                     // Default tab
  ?tab=workflows                    // Associated workflows
  ?tab=campaigns                    // Campaign management
/workflows/:workflowId             // Workflow detail view
/query-builder/new                 // Create new query
/query-builder/edit/:workflowId    // Edit existing query
/query-builder/copy/:workflowId    // Duplicate query
/query-library                     // Template library
/my-queries                        // User's workflows
/executions                        // All executions
/data-sources                      // Schema browser
/data-sources/:schemaId            // Schema detail
/schedules                         // Schedule management dashboard
/schedules/new                     // Create schedule wizard
/schedules/:scheduleId             // Schedule detail modal
/profile                           // User settings
```

## 📐 Code Patterns & Best Practices

### Backend Patterns

#### Service Layer Pattern
```python
# ALL services inherit from DatabaseService for auto-reconnection
class MyService(DatabaseService):
    def __init__(self):
        super().__init__()
        # Service-specific initialization
    
    @with_connection_retry
    async def my_method(self):
        # Database operations auto-retry on disconnect
        pass
```

#### Error Handling
```python
# AMC API errors need special parsing
try:
    result = await amc_api_client.execute_query(...)
except Exception as e:
    error_detail = e.response.json() if hasattr(e, 'response') else {}
    # Check 'details' field for AMC-specific errors
    if 'details' in error_detail:
        line = error_detail['details'].get('line')
        column = error_detail['details'].get('column')
        message = error_detail['details'].get('message')
```

#### Token Management
```python
# Always use the retry client for AMC operations
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry

# This automatically handles:
# - Token refresh on 401
# - Retry with new token
# - User ID lookup for token refresh
result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,  # Use AMC instance ID, not UUID!
    user_id=user_id,
    entity_id=entity_id,
)
```

### Frontend Patterns

#### Component Structure
```tsx
// Use explicit type imports (verbatimModuleSyntax)
import type { FC, ReactNode } from 'react';
import type { Workflow } from '../types';

// Export interfaces for cross-component use
export interface MyComponentProps {
  workflow: Workflow;
  onUpdate: (workflow: Workflow) => void;
}

// Functional component with proper typing
export const MyComponent: FC<MyComponentProps> = ({ workflow, onUpdate }) => {
  // Component logic
};
```

#### React Query Patterns
```tsx
// Consistent query key structure
const { data, isLoading } = useQuery({
  queryKey: ['workflows', { instanceId, status, tags }],
  queryFn: () => workflowService.getWorkflows({ instanceId, status, tags }),
  staleTime: 5 * 60 * 1000, // 5 minutes
  enabled: !!instanceId, // Conditional fetching
});

// Optimistic updates
const mutation = useMutation({
  mutationFn: workflowService.updateWorkflow,
  onMutate: async (newData) => {
    // Cancel queries and update cache optimistically
    await queryClient.cancelQueries(['workflows']);
    const previous = queryClient.getQueryData(['workflows']);
    queryClient.setQueryData(['workflows'], old => ({
      ...old,
      data: old.data.map(w => w.id === newData.id ? newData : w)
    }));
    return { previous };
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['workflows'], context.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries(['workflows']);
  },
});
```

#### Modal Stacking
```tsx
// Proper z-index hierarchy for modals
<MainModal className="z-50">
  {showNested && (
    <NestedModal className="z-60" />
  )}
  {showError && (
    <ErrorModal className="z-70" />
  )}
</MainModal>
```

## 🚨 Critical Implementation Patterns

These patterns MUST be followed to avoid common errors and ensure the application works correctly.

### AMC ID Field Duality
```typescript
// Two ID systems must be carefully managed:
instanceId  // AMC's actual instance ID (use for API calls)
id         // Internal UUID (use for database relationships)

// CORRECT: Use instanceId for AMC API
await amcApiClient.executeQuery(instanceId, query)

// WRONG: Internal UUID causes 403 errors
await amcApiClient.executeQuery(instance.id, query)  // ✗
```

### Date Handling for AMC
```python
# AMC requires specific date format WITHOUT timezone
'2025-07-15T00:00:00'    # ✓ Correct
'2025-07-15T00:00:00Z'   # ✗ Causes empty results

# Account for 14-day data lag
end_date = datetime.utcnow() - timedelta(days=14)
start_date = end_date - timedelta(days=7)
```

### API Authentication Headers
```python
# Entity ID MUST be in headers, not query params
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-AdvertiserId': entity_id  # Critical!
}
```

### Token Auto-Refresh Pattern
```python
# Backend: Use amc_api_client_with_retry for automatic token refresh
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry

# Will automatically retry with refreshed token on 401
result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,
    user_id=user_id,  # Required for token refresh
    entity_id=entity_id,
)
```

### Async/Await Patterns
```python
# ALWAYS await async methods in async contexts
result = await async_method()  # ✓ Correct
result = async_method()  # ✗ Returns coroutine, not result

# Common error in execution_status_poller.py:
status = await amc_execution_service.poll_and_update_execution(...)  # ✓
status = amc_execution_service.poll_and_update_execution(...)  # ✗ Missing await
```

### FastAPI Router Registration
```python
# In endpoint file - NO prefix
router = APIRouter(tags=["Data Sources"])

# In main_supabase.py - ADD full prefix
app.include_router(data_sources_router, prefix="/api/data-sources")
```

### Frontend Type-Only Imports (verbatimModuleSyntax)
```typescript
// TypeScript requires explicit type imports
import type { QueryTemplate } from '../types/queryTemplate';  // ✓
import { QueryTemplate } from '../types/queryTemplate';       // ✗ Error

// When exporting interfaces for other components
export interface FilterGroup { ... }  // Must export for cross-component use
```

### React Query Key Consistency
```typescript
// Keys must be consistent for caching
['dataSource', schemaId]        // ✓ Consistent
['data-source', id]             // ✗ Different structure breaks cache

// Query with dependencies
queryKey: ['dataSources', { search, category, tags }]
```

### SessionStorage for Component Communication
```typescript
// DataSourceDetail passes example to QueryBuilder
sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
  sql_query: example.sql_query,
  name: example.name,
  parameters: example.parameters || {}
}));

// QueryBuilder loads and immediately clears
const draft = sessionStorage.getItem('queryBuilderDraft');
if (draft) {
  setQueryState(JSON.parse(draft));
  sessionStorage.removeItem('queryBuilderDraft');  // Prevent stale data
}
```

## 📊 Database Schema

Complete Supabase schema with relationships and key fields. All tables have Row Level Security (RLS) enabled.

```sql
users
├── id (uuid, PK)
├── email (unique)
├── name
├── auth_tokens (jsonb)            -- Fernet encrypted OAuth tokens
│   ├── access_token               -- Encrypted, expires in 1 hour
│   ├── refresh_token              -- Encrypted, long-lived
│   └── expires_at                 -- Token expiration timestamp
├── is_active (boolean)
└── created_at

amc_instances
├── id (uuid, PK)                 -- Internal ID for DB relations
├── instance_id (text, unique)     -- AMC's actual ID (use for API calls!)
├── name
├── entity_id                      -- Required for API headers
├── brands (text[])                -- Brand associations for filtering
├── region                         -- AMC region
├── status                         -- active/inactive
├── user_id (FK → users)
└── created_at

workflows
├── id (uuid, PK)
├── workflow_id (text)             -- Format: wf_XXXXXXXX (auto-generated)
├── name
├── description
├── sql_query (text)               -- AMC SQL query
├── parameters (jsonb)             -- Dynamic parameters
│   ├── startDate                  -- ISO format without Z
│   └── endDate                    -- ISO format without Z
├── amc_workflow_id                -- AMC API workflow ID
├── is_synced_to_amc (boolean)     -- Sync status
├── tags (text[])                  -- Workflow tags for filtering
├── status                         -- active/draft/archived
├── last_executed_at               -- For sorting
├── execution_count (integer)      -- Track usage
├── user_id (FK → users)
├── created_at
└── updated_at

workflow_executions
├── id (uuid, PK)
├── workflow_id (FK → workflows)
├── instance_id (text)             -- AMC instance ID (not UUID!)
├── amc_execution_id               -- From AMC API
├── amc_workflow_id                -- AMC workflow ID used
├── status                         -- PENDING/RUNNING/SUCCEEDED/FAILED
├── query_text (text)              -- Actual SQL executed
├── parameters (jsonb)             -- Parameters used
├── results (jsonb)                -- Query results when successful
├── error_details (jsonb)          -- Structured error information
│   ├── message                    -- Error message
│   ├── details                    -- AMC-specific details
│   └── line/column                -- SQL error location
├── started_at
├── completed_at
└── created_at

amc_data_sources                  -- Schema documentation
├── id (uuid, PK)
├── schema_id (text, unique)       -- Hyphenated ID (e.g., 'dsp-impressions')
├── name                           -- Display name
├── amc_name                       -- Actual AMC table name (e.g., 'dsp_impressions')
├── data_sources (jsonb)           -- Array of actual AMC table names
├── description (text)
├── tags (jsonb)                   -- Array of tag strings
├── category                       -- Attribution/Conversion/etc
├── example_queries (jsonb)        -- SQL examples
├── field_count (integer)          -- Number of fields
├── dimension_count (integer)      -- Number of dimensions
├── metric_count (integer)         -- Number of metrics
└── fields (relation → amc_schema_fields)

amc_schema_fields
├── id (uuid, PK)
├── data_source_id (FK → amc_data_sources)
├── field_name                     -- Column name in AMC
├── display_name                   -- User-friendly name
├── data_type                      -- SQL data type
├── description
├── is_dimension (boolean)         -- True for dimensions (D)
├── is_metric (boolean)            -- True for metrics (M)
├── examples (jsonb)               -- Sample values
└── notes (text)

query_templates                   -- Pre-built query library
├── id (uuid, PK)
├── name
├── description
├── sql_template (text)            -- Template with {{parameters}}
├── parameters (jsonb)             -- Parameter definitions
├── category                       -- Query category
├── tags (text[])
├── is_public (boolean)
└── created_at

workflow_schedules                -- Automated execution schedules
├── id (uuid, PK)
├── workflow_id (uuid, FK → workflows)
├── name                           -- Schedule display name
├── description                    -- Optional description
├── interval_preset                -- daily/weekly/monthly/etc
├── cron_expression                -- CRON format schedule
├── timezone                       -- IANA timezone (e.g., 'America/New_York')
├── is_active (boolean)            -- Enable/disable schedule
├── default_parameters (jsonb)     -- Override workflow parameters
│   ├── startDate                  -- Dynamic or fixed date
│   ├── endDate                    -- Dynamic or fixed date
│   └── [custom params]            -- Any workflow-specific params
├── notification_settings (jsonb)  -- Email notification config
│   ├── on_success (boolean)       -- Notify on successful run
│   ├── on_failure (boolean)       -- Notify on failed run
│   └── recipients (text[])        -- Email addresses
├── max_retries (integer)          -- Retry count on failure
├── retry_delay_minutes (integer)  -- Wait between retries
├── pause_on_failure (boolean)     -- Auto-pause after failures
├── failure_threshold (integer)    -- Consecutive failures to pause
├── cost_limit (decimal)           -- Maximum cost per execution
├── last_run (timestamp)           -- Last execution time
├── next_run (timestamp)           -- Next scheduled execution
├── execution_count (integer)      -- Total runs
├── success_count (integer)        -- Successful runs
├── failure_count (integer)        -- Failed runs
├── consecutive_failures (integer) -- Current failure streak
├── user_id (FK → users)
├── created_at
└── updated_at

schedule_runs                     -- Schedule execution history
├── id (uuid, PK)
├── schedule_id (FK → workflow_schedules)
├── workflow_execution_id (FK → workflow_executions)
├── triggered_at (timestamp)       -- When schedule triggered
├── started_at (timestamp)         -- Actual execution start
├── completed_at (timestamp)       -- Execution completion
├── status                         -- PENDING/RUNNING/SUCCESS/FAILED/SKIPPED
├── error_message (text)           -- Error details if failed
├── parameters_used (jsonb)        -- Actual parameters at runtime
├── cost (decimal)                 -- Execution cost
├── retry_count (integer)          -- Number of retries attempted
└── created_at
```

## Environment Variables

Required for operation:
```bash
# Supabase (Required)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# Amazon Advertising API (Required)
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx
AMAZON_REDIRECT_URI=http://localhost:8001/api/auth/amazon/callback
AMC_USE_REAL_API=true              # Set to "false" for mock responses

# Security (Required)
FERNET_KEY=xxx                      # Auto-generated if missing, keep consistent!
JWT_SECRET_KEY=xxx                  # For JWT tokens

# Application Settings (Optional)
ENVIRONMENT=development             # development/production
DEBUG=true                          # Enable debug logging
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8001

# Rate Limiting (Optional)
SLOWAPI_LIMIT=100                   # Requests per minute

# Frontend URL (Optional, for CORS)
FRONTEND_URL=http://localhost:5173
```

## ⚠️ Common Pitfalls & Solutions

These are the most frequent issues encountered and their solutions.

### FastAPI Trailing Slashes
```python
# POST/PUT to collections requires trailing slash
api.post('/workflows/', data)      # ✓ Returns 201
api.post('/workflows', data)        # ✗ Returns 405
```

### Async/Await in FastAPI
```python
# DON'T use asyncio.run() in async context
async def api_endpoint():
    await service_method()          # ✓ Correct
    asyncio.run(service_method())   # ✗ Event loop error

# Always await async methods
result = await async_method()      # ✓ Correct
result = async_method()            # ✗ Returns coroutine object
```

### React Fragment Syntax
```tsx
// Multiple elements need wrapper
return (
  <>
    <div>First</div>
    <div>Second</div>
  </>
);
```

### Modal Z-Index Layering
```tsx
// Main modal
<div className="z-50">...</div>

// Nested modal must be higher
<NestedModal className="z-60" />

// Error detail modal highest
<ErrorDetailsModal className="z-70" />
```

### Monaco Editor Height Issues
```tsx
// CRITICAL: Monaco Editor requires explicit pixel heights
<SQLEditor height="400px" />     // ✓ Works
<SQLEditor height="100%" />      // ✗ Often fails in flex containers

// For modals with Monaco Editor:
<div className="flex flex-col max-h-[90vh]">
  <header className="flex-shrink-0">...</header>
  <div className="flex-1 min-h-0 overflow-hidden">
    <SQLEditor height="400px" />  // Must be pixels!
  </div>
  <footer className="flex-shrink-0">...</footer>
</div>
```

### JSON Field Parsing in Supabase
```python
# Supabase may return JSON fields as strings
if isinstance(schema.get('data_sources'), str):
    schema['data_sources'] = json.loads(schema['data_sources'])
if isinstance(schema.get('tags'), str):
    schema['tags'] = json.loads(schema['tags'])
```

### Field Examples Array Handling
```typescript
// amc_schema_fields.examples may be null, array of strings, or array of objects
// Always check type before using array methods:
{field.examples && Array.isArray(field.examples) && field.examples.length > 0 && (
  field.examples
    .slice(0, 2)
    .map(ex => typeof ex === 'string' ? ex : JSON.stringify(ex))
    .join(', ')
)}
```

### Python Command Variations
```bash
# Scripts use 'python' not 'python3'
# start_services.sh uses: python main_supabase.py
# If python3 is required on your system, create an alias:
alias python=python3
```

## Background Services

The application runs three critical background services:

### 1. Token Refresh Service
- **Frequency**: Every 10 minutes
- **Purpose**: Refreshes Amazon OAuth tokens before expiry
- **Buffer**: 15 minutes before token expiration  
- **Auto-start**: Launches on application startup
- **Implementation**: `token_refresh_service.py`
- **Features**:
  - Tracks all users with valid tokens
  - Refreshes tokens 15 minutes before expiry
  - Updates encrypted tokens in database
  - Handles refresh failures gracefully

### 2. Execution Status Poller
- **Frequency**: Every 15 seconds
- **Purpose**: Updates status of pending AMC executions
- **Implementation**: `execution_status_poller.py`
- **Common Issue**: Missing await on async methods
- **Features**:
  - Polls only PENDING/RUNNING executions
  - Fetches results when execution completes
  - Updates error details on failure
  - Auto-cleanup: Removes completed executions from polling
  - Handles AMC API rate limits

### 3. Schedule Executor Service
- **Frequency**: Every 60 seconds
- **Purpose**: Executes scheduled workflows at their due times
- **Implementation**: `schedule_executor_service.py`
- **Auto-start**: Launches on application startup
- **Features**:
  - Checks all active schedules for due execution
  - Ensures valid OAuth tokens before execution
  - Handles timezone conversions for global schedules
  - Applies default parameters with date calculations
  - Records execution history for tracking
  - Auto-pauses schedules after consecutive failures
  - Updates next run time after each execution
  - Supports retry logic with configurable delays
  - Cost tracking and limit enforcement

## AMC Data Sources

AMC schemas are imported from markdown files in `amc_dataset/` directory:
- Run `python scripts/import_amc_schemas.py` to import/update schemas
- Run `python scripts/populate_all_fields.py` to populate field metadata
- Schemas are stored with proper AMC table names (e.g., `dsp_impressions`)
- Each schema includes:
  - Fields with dimension/metric indicators
  - SQL query examples
  - Data type information
  - Sample values
  - Relationships to other tables

### Schema Categories
- **Attribution**: Attribution models and paths
- **Conversion**: Conversion events and metrics
- **DSP**: Display advertising data
- **Sponsored Ads**: Search and product ads
- **Audience**: Segment and audience data
- **Retail**: Purchase and cart data

## Deployment

### Docker Build
```bash
docker build -t recomamp .
docker run -p 8001:8001 --env-file .env recomamp
```

### Railway Deployment
```bash
# Prepare for deployment
./prepare_railway.sh

# Railway configuration files:
# - railway.json: Service configuration
# - nixpacks.toml: Build settings
# - Procfile: Process definition
```

- Uses single Dockerfile for both frontend and backend
- Frontend built during Docker image creation
- Single container serves both:
  - Frontend static files from `/frontend/dist`
  - Backend API on same port
- Environment variables set in Railway dashboard
- Auto-deploys on GitHub push

## 🧪 Testing Strategy

### Backend Testing

#### Unit Tests
```bash
# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_token_service.py -v

# Run specific test
pytest tests/test_api_auth.py::test_login_success -v

# With coverage report
pytest --cov=amc_manager --cov-report=html tests/
# Open htmlcov/index.html to view coverage
```

#### Integration Tests
```bash
# Database integration tests (requires Supabase)
pytest tests/integration/ --tb=short

# AMC API integration tests (requires credentials)
AMC_USE_REAL_API=true pytest tests/amc/

# Test with real token refresh
python test_token_refresh.py
```

#### Testing Patterns
```python
# Use pytest fixtures for setup
@pytest.fixture
async def mock_instance():
    return {
        "id": str(uuid4()),
        "instance_id": "test_instance_123",
        "entity_id": "ENTITY123",
        "name": "Test Instance"
    }

# Mock external services
@patch('amc_manager.services.amc_api_client.AMCAPIClient.execute_query')
async def test_execution(mock_execute):
    mock_execute.return_value = {"executionId": "exec123"}
    # Test logic here

# Test async functions properly
@pytest.mark.asyncio
async def test_async_function():
    result = await async_service_method()
    assert result is not None
```

### Frontend Testing

#### Type Checking
```bash
# Check all TypeScript types
npm run typecheck

# Watch mode for development
npx tsc --noEmit --watch

# Fix type-only import issues
# Search for: import { SomeType }
# Replace with: import type { SomeType }
```

#### E2E Testing with Playwright
```bash
# Install Playwright browsers
npx playwright install

# Run all E2E tests
npx playwright test

# Interactive mode with browser
npx playwright test --ui

# Debug specific test
npx playwright test test-name.spec.ts --debug

# Generate test code by recording
npx playwright codegen http://localhost:5173
```

#### Component Testing Patterns
```tsx
// Mock API responses
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/workflows', (req, res, ctx) => {
    return res(ctx.json({ data: mockWorkflows }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Test React Query hooks
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const wrapper = ({ children }) => (
  <QueryClientProvider client={new QueryClient()}>
    {children}
  </QueryClientProvider>
);

test('loads workflows', async () => {
  const { result } = renderHook(() => useWorkflows(), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data).toHaveLength(2);
});
```

### Testing Checklist

Before committing code, ensure:
- [ ] All unit tests pass: `pytest tests/`
- [ ] Type checking passes: `npm run typecheck`
- [ ] Linting passes: `npm run lint`
- [ ] No console errors in browser
- [ ] API endpoints return expected status codes
- [ ] Error states are handled gracefully
- [ ] Loading states display correctly
- [ ] Modal z-indexes stack properly
- [ ] Schedule executions trigger on time

## Performance Optimizations

### Backend
- **Connection Pooling**: Supabase client reused via singleton
- **Async Throughout**: All I/O operations are async
- **Background Tasks**: Token refresh and polling run independently
- **Rate Limiting**: Prevents API abuse (configurable)
- **Gzip Compression**: Enabled for responses > 1KB

### Frontend
- **Code Splitting**: Monaco Editor lazy loaded
- **React Query Caching**: 5-minute staleTime reduces API calls
- **Virtual Scrolling**: React Window for large tables
- **Debounced Search**: 300ms delay on search inputs
- **Memoization**: React.memo for expensive components
- **Optimistic Updates**: Immediate UI feedback

## Known Issues & Workarounds

### Token Encryption
- If seeing "Failed to decrypt token" errors, the FERNET_KEY may have changed
- Tokens are automatically cleared and users must re-authenticate
- Prevention: Keep FERNET_KEY consistent across deployments

### AMC API Errors
- 400 errors with "unable to compile workflow" need special parsing
- Error details are in the `details` field, not `message`
- Table not found errors include line/column information

### Workflow Not Found
- AMC workflows may be deleted externally
- System auto-creates workflows on first execution if missing
- Falls back to ad-hoc execution if creation fails

### TypeScript Unused Imports
- When removing UI elements, also remove related props and imports
- Common issue: onPreview, onViewDetails props after removing action buttons
- Solution: Remove from both component interface and usage

### Supabase Connection Timeouts
- Connection auto-refreshes every 30 minutes
- "Server disconnected" errors are automatically retried
- Keep SUPABASE_SERVICE_ROLE_KEY consistent across deploys

### Scheduling-Specific Patterns
```python
# Workflow ID conversion for schedules
# Database expects UUID, API accepts string
workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id

# DateTime must be ISO strings for JSON
schedule['next_run'] = schedule['next_run'].isoformat()
schedule['last_run'] = schedule['last_run'].isoformat() if schedule['last_run'] else None

# Supabase client is synchronous
result = self.client.table('workflow_schedules').select().execute()  # No await!
# NOT: result = await self.client.table(...).execute()  # Error!
```

### Schedule History Modal Pattern
```tsx
// ScheduleHistory must be rendered as overlay, not embedded
// CORRECT: Separate modal with own z-index
{showHistory && (
  <ScheduleHistory
    scheduleId={schedule.id}
    onClose={() => setShowHistory(false)}
  />
)}

// WRONG: Embedded in parent modal
<div className="modal-content">
  <ScheduleHistory />  // Won't display properly
</div>
```

### AMC API Rate Limits
- AMC API has undocumented rate limits
- Implement exponential backoff on 429 errors
- Use batch operations where possible

### Execution Polling Coroutine Error
- Error: `'coroutine' object has no attribute 'get'`
- Cause: Missing `await` in execution_status_poller.py
- Fix: Always await async methods in async contexts

### Schedule Service UUID Errors
- Error: `Invalid input syntax for type uuid`
- Cause: Passing string workflow_id instead of UUID
- Fix: Convert workflow_id to UUID before database operations
```python
workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
```

### Schedule DateTime Serialization
- Error: `Object of type datetime is not JSON serializable`
- Cause: Returning Python datetime objects in API responses
- Fix: Convert all datetime fields to ISO strings
```python
schedule['next_run'] = schedule['next_run'].isoformat()
```

### Supabase Async/Await Confusion
- Error: `'coroutine' object has no attribute 'data'`
- Cause: Using await with Supabase synchronous client
- Fix: Supabase Python client is synchronous, don't use await
```python
# CORRECT
result = self.client.table('schedules').select().execute()
# WRONG
result = await self.client.table('schedules').select().execute()
```

## 🔧 Troubleshooting Guide

### Quick Fixes for Common Issues

#### "Failed to decrypt token" Error
```bash
# User tokens corrupted due to FERNET_KEY change
# Solution: User must re-authenticate
curl -X POST http://localhost:8001/api/auth/logout
# Then login again via UI
```

#### "Server disconnected" Error
```python
# Supabase connection timeout (happens after 30 minutes)
# Solution: Automatic retry is built-in via @with_connection_retry decorator
# If persists, restart backend:
pkill -f "python main_supabase.py"
./start_services.sh
```

#### Empty AMC Query Results
```python
# Check date format - AMC requires no timezone
'2025-07-15T00:00:00'    # ✓ Correct
'2025-07-15T00:00:00Z'   # ✗ Wrong - 'Z' causes empty results

# Check for 14-day data lag
from datetime import datetime, timedelta
end_date = datetime.utcnow() - timedelta(days=14)  # Account for lag
```

#### 403 Forbidden on AMC API
```python
# Using wrong instance ID
instance.instance_id  # ✓ Use AMC's actual ID
instance.id          # ✗ Internal UUID causes 403

# Missing entity_id in headers
headers['Amazon-Advertising-API-AdvertiserId'] = entity_id  # Required!
```

#### TypeScript Build Errors
```bash
# Type-only imports not marked correctly
import type { Workflow } from '../types';  # ✓ Correct
import { Workflow } from '../types';       # ✗ Error with verbatimModuleSyntax

# Fix all at once:
npm run typecheck
# Then fix reported errors
```

#### Schedule Not Executing
```sql
-- Check schedule status
SELECT id, name, is_active, next_run, last_run, consecutive_failures
FROM workflow_schedules
WHERE next_run < NOW() AND is_active = true;

-- Check user has valid tokens
SELECT u.email, u.auth_tokens->>'expires_at' as token_expires
FROM users u
JOIN workflow_schedules ws ON ws.user_id = u.id
WHERE ws.id = 'schedule-id-here';
```

## 🔍 Debugging Guide

### Common Error Patterns

When you encounter these errors, here's what to check:
```python
# 403 Forbidden on AMC API
# Check: Using instance_id not internal UUID
# Check: entity_id in request headers
# Check: Token has required scopes

# Empty AMC results
# Check: Date format (no 'Z' suffix)
# Check: 14-day data lag accounted for
# Check: Table names use underscores not hyphens

# Token decryption failures
# Check: FERNET_KEY hasn't changed
# Solution: User must re-authenticate

# Coroutine errors in logs
# Check: Missing await on async method calls
# Fix: Add await to all async method calls

# Schedule not executing
# Check: Schedule is active (is_active = true)
# Check: Next run time is in the past
# Check: User has valid OAuth tokens
# Check: Timezone calculations are correct

# Schedule history not showing
# Check: ScheduleHistory rendered as overlay, not embedded
# Check: Proper z-index for modal stacking
# Check: schedule_runs table has entries
```

### Useful Debug Commands
```bash
# Check API routes
curl http://localhost:8001/api/debug/routes

# Test Supabase connection
python scripts/check_supabase_connection.py

# Validate token encryption
python scripts/validate_tokens.py

# Check running executions
python scripts/find_running_executions.py

# Check due schedules
python scripts/check_due_schedules.py

# Test schedule execution
python scripts/test_schedule_executor.py

# Monitor server logs
tail -f server.log
```

## 🏗️ Architecture Decisions

Key technology choices and their rationale:

### Why Supabase?
- Built-in auth and RLS (Row Level Security)
- Real-time subscriptions (future feature)
- Automatic API generation
- Managed PostgreSQL with backups

### Why FastAPI?
- Native async/await support
- Automatic OpenAPI documentation
- Type hints for validation
- High performance with Uvicorn

### Why Monaco Editor?
- Full SQL syntax highlighting
- IntelliSense support (future)
- Same editor as VS Code
- Extensive customization options

### Why TanStack Query?
- Powerful caching strategies
- Optimistic updates
- Background refetching
- DevTools for debugging

## ✅ Working Features

Currently implemented and tested functionality:

### Core Functionality
- **AMC Instance Management**: Create, configure, and manage multiple AMC instances
- **Query Builder**: 3-step wizard with SQL editor, schema explorer, and test execution
- **Workflow Management**: Create, edit, duplicate, and organize SQL workflows
- **Query Execution**: Execute workflows on AMC with parameter substitution
- **Data Source Browser**: Explore AMC schemas with field details and examples
- **Query Library**: Pre-built templates for common AMC queries
- **Execution History**: Track all executions with results and error details

### Workflow Scheduling System
Complete automated scheduling implementation with flexible recurring intervals and comprehensive execution tracking.

#### Key Features
- **Flexible Intervals**: 
  - Preset options: Daily, Every 3/7/14/30/60/90 days
  - Weekly on specific days
  - Monthly on specific dates
  - Business days only
  - Custom CRON expressions
- **Smart Date Parameters**: 
  - Dynamic date calculations (e.g., "last 7 days")
  - Fixed date ranges
  - Timezone-aware scheduling
- **Execution Management**:
  - Automatic retry on failure with configurable delays
  - Auto-pause after consecutive failures
  - Cost tracking and limits
  - Email notifications on success/failure
- **Comprehensive History**:
  - Timeline view of all executions
  - Metrics dashboard with success rates
  - Cost analysis and trending
  - Detailed error tracking

#### Scheduling UI/UX Patterns

**Schedule Creation Wizard**:
1. **Workflow Selection**: Choose workflow to schedule
2. **Interval Configuration**: Select preset or custom CRON
3. **Parameter Defaults**: Override workflow parameters
4. **Notification Settings**: Configure email alerts

**Schedule Management Dashboard**:
- **Grid View**: Card layout with key metrics
- **List View**: Table with sortable columns
- **Quick Actions**: Pause/resume, test run, view history
- **Status Indicators**: Active, paused, failed states

**Schedule Detail Modal**:
- **Details Tab**: Configuration and next run info
- **History Tab**: Execution timeline with filters
- **Settings Tab**: Edit schedule configuration

**History Viewer**:
- **Timeline View**: Chronological execution list
- **Table View**: Sortable data grid
- **Metrics View**: Charts and statistics
- **Export Options**: Download history as CSV/JSON

#### Implementation Architecture

**Backend Services**:
- `EnhancedScheduleService`: CRUD operations with CRON validation
- `ScheduleExecutorService`: Background worker checking every minute
- `ScheduleHistoryService`: History tracking and metrics calculation

**Frontend Components**:
- `ScheduleManager`: Main dashboard page
- `ScheduleWizard`: Multi-step creation flow
- `ScheduleDetailModal`: View/edit interface
- `ScheduleHistory`: Execution history overlay

**Database Schema**:
- `workflow_schedules`: Schedule configurations
- `schedule_runs`: Execution history records

#### Common Scheduling Pitfalls

1. **Workflow ID Type Mismatch**:
   ```python
   # Always convert string IDs to UUID for database
   workflow_uuid = UUID(workflow_id) if isinstance(workflow_id, str) else workflow_id
   ```

2. **DateTime Serialization**:
   ```python
   # Convert datetime to ISO string for JSON responses
   schedule['next_run'] = schedule['next_run'].isoformat()
   ```

3. **Supabase Client Usage**:
   ```python
   # Supabase client is synchronous - no await!
   result = self.client.table('schedules').select().execute()
   ```

4. **Modal Rendering**:
   ```tsx
   // ScheduleHistory must be overlay, not embedded
   {showHistory && <ScheduleHistory />}  // Separate modal
   ```

5. **CRON Expression Validation**:
   ```python
   # Validate before saving to prevent execution errors
   from croniter import croniter
   if not croniter.is_valid(cron_expression):
       raise ValueError("Invalid CRON expression")
   ```

## 📚 API Documentation

### Core API Endpoints

#### Authentication
```http
POST   /api/auth/login              # Email/password login
POST   /api/auth/amazon/callback    # OAuth callback
POST   /api/auth/logout             # Clear session
GET    /api/auth/me                 # Current user info
```

#### Workflows
```http
GET    /api/workflows/              # List workflows (trailing slash!)
POST   /api/workflows/              # Create workflow
GET    /api/workflows/{id}          # Get workflow details
PUT    /api/workflows/{id}          # Update workflow
DELETE /api/workflows/{id}          # Delete workflow
POST   /api/workflows/{id}/execute  # Execute workflow
```

#### AMC Instances
```http
GET    /api/instances/              # List instances
POST   /api/instances/              # Create instance
GET    /api/instances/{id}          # Get instance
PUT    /api/instances/{id}          # Update instance
DELETE /api/instances/{id}          # Delete instance
```

#### Schedules
```http
GET    /api/schedules/              # List schedules
POST   /api/schedules/              # Create schedule
GET    /api/schedules/{id}          # Get schedule with relations
PUT    /api/schedules/{id}          # Update schedule
DELETE /api/schedules/{id}          # Delete schedule
POST   /api/schedules/{id}/pause    # Pause schedule
POST   /api/schedules/{id}/resume   # Resume schedule
GET    /api/schedules/{id}/history  # Get execution history
```

#### Data Sources
```http
GET    /api/data-sources/           # List AMC schemas
GET    /api/data-sources/{id}       # Get schema with fields
GET    /api/data-sources/{id}/examples  # Get query examples
```

### Common Workflows

#### Creating and Executing a Query
```python
# 1. Create workflow
workflow = await workflow_service.create_workflow(
    name="My Query",
    sql_query="SELECT * FROM dsp_impressions WHERE dt >= '{{startDate}}'",
    parameters={"startDate": "2025-07-01T00:00:00"},
    user_id=user_id
)

# 2. Execute on AMC instance
execution = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance.instance_id,  # Use AMC ID!
    workflow_id=workflow.id,
    user_id=user_id,
    entity_id=instance.entity_id
)

# 3. Poll for results (automatic via background service)
# Or manually:
result = await amc_execution_service.poll_and_update_execution(
    execution_id=execution.id,
    user_id=user_id
)
```

#### Setting Up a Schedule
```python
# 1. Create schedule with preset interval
schedule = await schedule_service.create_schedule(
    workflow_id=workflow_id,
    name="Daily Report",
    interval_preset="daily",
    timezone="America/New_York",
    default_parameters={
        "startDate": "dynamic:yesterday",
        "endDate": "dynamic:today"
    },
    user_id=user_id
)

# 2. Schedule executor will automatically run it
# Background service checks every minute for due schedules
```

#### Handling AMC Errors
```python
try:
    result = await amc_api_client.execute_query(...)
except HTTPException as e:
    if e.status_code == 400:
        # Parse AMC-specific error
        detail = e.detail
        if isinstance(detail, dict) and 'details' in detail:
            error_info = detail['details']
            line = error_info.get('line')
            column = error_info.get('column')
            message = error_info.get('message', '')
            
            # Handle specific errors
            if 'table not found' in message.lower():
                # Table doesn't exist in AMC
                pass
            elif 'syntax error' in message.lower():
                # SQL syntax issue
                pass
```

## 📋 Recent Changes & Improvements

Latest updates to be aware of:

### Query Builder Enhancements (2025-08-19)
- **Full Width Layout**: QueryReviewStep now uses full viewport width
- **Better Space Distribution**: SQL preview uses 75% width (3/4 columns)
- **Scrollable SQL Window**: Fixed height with internal scrolling
- **No Page Scroll Required**: Create Workflow button always accessible

### Schedule Management System (2025-08-18)
- **Complete Scheduling**: Full CRUD operations with CRON support
- **History Tracking**: Comprehensive execution history with metrics
- **Smart Retries**: Automatic retry logic with configurable delays
- **Cost Management**: Track and limit execution costs

### Recent Fixes (2025-08-13)
- **Dynamic Schema Loading**: Removed hardcoded tables, loads from API
- **SessionStorage Integration**: Examples populate in query editor
- **Dual Results View**: Inline and full modal viewing options
- **React Fragment Fixes**: Proper JSX structure throughout
- **Modal Z-Index Layering**: Correct stacking for nested modals

## 🎯 Future Enhancements

Planned improvements and features:
- Real-time collaboration on workflows
- Advanced query optimization suggestions
- Automated anomaly detection in results
- Template marketplace for sharing queries
- Multi-region instance management
- Advanced cost optimization analytics
- Webhook integrations for execution events
- Custom dashboard builder with widgets