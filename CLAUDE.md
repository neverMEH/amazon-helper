# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RecomAMP - Amazon Marketing Cloud (AMC) query development and execution platform for managing AMC instances, creating and executing SQL queries with iterative workflow tracking, and building a comprehensive query library.

## Tech Stack

### Backend
- **FastAPI** (0.109.0): Async web framework with automatic OpenAPI docs
- **Supabase**: PostgreSQL database with built-in auth & realtime
- **Python 3.11**: With full async/await support
- **Fernet**: Symmetric encryption for OAuth tokens
- **httpx/tenacity**: HTTP client with retry logic

### Frontend  
- **React 19.1.0**: With new JSX transform
- **TypeScript 5.8**: With verbatimModuleSyntax enabled
- **TanStack Query v5**: Server state management
- **React Router v7**: Client-side routing
- **Monaco Editor**: SQL editing with syntax highlighting
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Build tool and dev server

## Development Commands

### Quick Start
```bash
# Start both backend and frontend services
./start_services.sh

# Services:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001  
# API Docs: http://localhost:8001/docs
```

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
# Run backend server
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

# Token management
python test_token_refresh.py                 # Test automatic token refresh
python scripts/validate_tokens.py            # Validate encrypted tokens
python scripts/fix_token_encryption.py       # Fix token encryption issues
```

### Frontend Commands
```bash
cd frontend
npm install                                  # Install dependencies
npm run dev                                  # Dev server on port 5173
npm run build                                # Production build
npm run lint                                 # ESLint
npm run preview                              # Preview production build
npx tsc --noEmit                            # TypeScript type checking
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
│       └── token_service.py  # OAuth token management
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
│  • Background services (token refresh, execution polling)     │
│  • Token encryption with Fernet                               │
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
└── amc_execution_service.py   # Execution lifecycle management
```

### Frontend Component Architecture

```
src/
├── pages/                      # Route components
│   ├── QueryBuilder.tsx        # 3-step wizard with test execution
│   ├── DataSources.tsx         # List view with side panel preview
│   ├── DataSourceDetail.tsx    # Enhanced with TOC, field explorer
│   ├── MyQueries.tsx          # Workflows with advanced filtering/sorting
│   └── InstanceDetail.tsx     # Instance management with tabs
├── components/
│   ├── query-builder/          # Wizard steps
│   │   ├── QueryEditorStep.tsx       # SQL editor + schema explorer
│   │   ├── QueryConfigurationStep.tsx # Instance & parameters
│   │   └── QueryReviewStep.tsx       # Final review & cost
│   ├── data-sources/           # Data source UI components
│   ├── workflows/              # Workflow management
│   │   ├── WorkflowFilters.tsx       # Advanced filter sidebar
│   │   ├── WorkflowSortDropdown.tsx  # Sort options dropdown
│   │   ├── ActiveFilterBadges.tsx    # Filter status display
│   │   └── ExecutionModal.tsx        # Execution tracking modal
│   ├── executions/             # Execution viewing
│   │   ├── AMCExecutionDetail.tsx    # Primary execution viewer
│   │   └── ExecutionResults.tsx      # Results table/chart view
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
    └── amcExecutionService.ts  # Execution lifecycle
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
/profile                           // User settings
```

## Critical Implementation Patterns

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

## Database Schema

Key Supabase tables and their relationships (RLS enabled on all tables):

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

## Common Pitfalls & Solutions

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

## Background Services

The application runs two critical background services:

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
- **Features**:
  - Polls only PENDING/RUNNING executions
  - Fetches results when execution completes
  - Updates error details on failure
  - Auto-cleanup: Removes completed executions from polling
  - Handles AMC API rate limits

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

## Testing Strategy

### Backend Testing
```bash
# Unit tests
pytest tests/ -v

# Integration tests (requires DB)
pytest tests/integration/ --tb=short

# AMC API tests (requires credentials)
AMC_USE_REAL_API=true pytest tests/amc/

# Test coverage
pytest --cov=amc_manager tests/
```

### Frontend Testing
```bash
# Type checking
npx tsc --noEmit
npx tsc --noEmit --watch  # Watch mode

# E2E tests with Playwright
npx playwright test
npx playwright test --ui  # Interactive mode
npx playwright test --debug  # Debug mode

# Linting
npm run lint
```

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

### AMC API Rate Limits
- AMC API has undocumented rate limits
- Implement exponential backoff on 429 errors
- Use batch operations where possible

## Debugging Tips

### Common Error Patterns
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
```

## Architecture Decisions

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