# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RecomAMP - Amazon Marketing Cloud (AMC) query development and execution platform for managing AMC instances, creating and executing SQL queries with iterative workflow tracking, and building a comprehensive query library.

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

### Backend Commands
```bash
# Run backend server
python main_supabase.py                      # Port 8001

# Testing
pytest tests/                                # All tests
pytest tests/test_api_auth.py::test_login_success  # Specific test
pytest tests/integration/                    # Integration tests only
pytest tests/supabase/                       # Supabase tests only
pytest tests/amc/                            # AMC API tests (requires credentials)

# Code quality
black amc_manager/                           # Format
flake8 amc_manager/                          # Lint
mypy amc_manager/                            # Type check

# Database operations
python scripts/check_supabase_connection.py  # Check connection
python scripts/import_amc_schemas.py         # Import AMC schema documentation
python scripts/apply_performance_indexes.py  # Apply indexes
python scripts/create_cja_workflow.py        # Create CJA workflow

# Token testing
python test_token_refresh.py                 # Test automatic token refresh
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
├── amc_api_client.py           # Direct AMC API integration
├── amc_api_client_with_retry.py # Enhanced with auto token refresh
├── token_service.py            # Fernet encryption for OAuth tokens
├── token_refresh_service.py    # Background token refresh (10-min intervals)
├── execution_status_poller.py  # Background polling (15-second intervals)
├── data_source_service.py      # AMC schema documentation
├── workflow_service.py         # Query workflow management
├── instance_service.py         # AMC instance CRUD
└── db_service.py              # Base class with reconnection logic
```

### Frontend Component Architecture

```
src/
├── pages/                      # Route components
│   ├── QueryBuilder.tsx        # 3-step wizard with test execution
│   ├── DataSources.tsx         # List view with side panel preview
│   ├── DataSourceDetail.tsx    # Enhanced with TOC, field explorer, and quick actions
│   └── MyQueries.tsx          # Workflows with advanced filtering/sorting
├── components/
│   ├── query-builder/          # Wizard steps
│   ├── data-sources/           # Data source UI components
│   ├── workflows/              # Workflow management components
│   │   ├── WorkflowFilters.tsx        # Advanced filter sidebar
│   │   ├── WorkflowSortDropdown.tsx   # Sort options dropdown
│   │   └── ActiveFilterBadges.tsx     # Filter status display
│   ├── executions/             # Error display and results
│   └── common/                 # Shared components
└── services/
    ├── api.ts                  # Axios instance with interceptors & token refresh
    └── *Service.ts             # API service modules
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

Key Supabase tables and their relationships:

```sql
users
├── id (uuid, PK)
├── email
├── auth_tokens (encrypted JSON)  -- Fernet encrypted, auto-refreshed
└── created_at

amc_instances
├── id (uuid, PK)                 -- Internal ID
├── instance_id (text, unique)     -- AMC's actual ID
├── name
├── entity_id                      -- For API headers
├── brands (text[])                -- Brand associations for filtering
└── user_id (FK → users)

workflows
├── id (uuid, PK)
├── workflow_id (text)             -- Format: wf_XXXXXXXX
├── name
├── sql_query
├── parameters (jsonb)
├── amc_workflow_id                -- AMC API workflow ID
├── is_synced_to_amc               -- Sync status
├── tags (text[])                  -- Workflow tags
├── status                         -- active/draft/archived
├── last_executed_at               -- For sorting
├── execution_count                -- Track usage
└── user_id (FK → users)

workflow_executions
├── id (uuid, PK)
├── workflow_id (FK → workflows)
├── amc_execution_id               -- From AMC API
├── status                         -- PENDING/RUNNING/SUCCEEDED/FAILED
├── results (jsonb)
└── error_details (jsonb)          -- Structured error information

amc_data_sources                  -- Schema documentation
├── id (uuid, PK)
├── schema_id (text, unique)       -- Hyphenated ID (e.g., 'dsp-impressions')
├── name                           -- AMC table name (e.g., 'dsp_impressions')
├── data_sources (jsonb)           -- Array of actual AMC table names
├── tags (jsonb)                   -- Array of tag strings
├── category
└── fields (relation → amc_schema_fields)

query_templates                   -- Pre-built query library
├── id (uuid, PK)
├── name
├── description
├── sql_template
├── parameters (jsonb)
└── category
```

## Environment Variables

Required for operation:
```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# Amazon Advertising API
AMAZON_CLIENT_ID=xxx
AMAZON_CLIENT_SECRET=xxx
AMC_USE_REAL_API=true              # Set to "false" for mock responses

# Security
FERNET_KEY=xxx                      # Auto-generated if missing, keep consistent!
JWT_SECRET_KEY=xxx                  # For JWT tokens

# Rate Limiting (optional)
SLOWAPI_LIMIT=100                   # Requests per minute
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
    <SQLEditor height="400px" />
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

### 2. Execution Status Poller
- **Frequency**: Every 15 seconds
- **Purpose**: Updates status of pending AMC executions
- **Features**: Fetches results when execution completes
- **Auto-cleanup**: Removes completed executions from polling

## AMC Data Sources

AMC schemas are imported from markdown files in `amc_dataset/` directory:
- Run `python scripts/import_amc_schemas.py` to import/update schemas
- Schemas are stored with proper AMC table names (e.g., `dsp_impressions`)
- Each schema includes fields, examples, and relationships

## Deployment

### Docker Build
```bash
docker build -t recomamp .
docker run -p 8001:8001 --env-file .env recomamp
```

### Railway Deployment
- Uses single Dockerfile for both frontend and backend
- Frontend built during image creation
- Single container serves both frontend (`/frontend/dist`) and backend
- Use `./prepare_railway.sh` for deployment preparation

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