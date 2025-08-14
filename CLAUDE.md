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
python -m pytest -v                          # Verbose output

# Code quality
black amc_manager/                           # Format
flake8 amc_manager/                          # Lint
mypy amc_manager/                            # Type check

# Database operations
python scripts/check_supabase_connection.py  # Check connection
python scripts/import_initial_data.py        # Import initial data
python scripts/apply_performance_indexes.py  # Apply indexes
python scripts/create_cja_workflow.py        # Create CJA workflow
python scripts/add_execution_results_fields.py  # Add results fields
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
npx playwright test -g "test name"          # Specific test by name
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
│  • Background polling service                                 │
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
├── token_service.py            # Fernet encryption for OAuth tokens
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
│   ├── DataSources.tsx         # Advanced filtering and compare mode
│   └── DataSourceDetail.tsx    # Schema detail view
├── components/
│   ├── query-builder/          # Wizard steps
│   ├── data-sources/           # Data source UI components
│   ├── workflows/              # Execution monitoring
│   ├── executions/             # Error display and results
│   └── common/                 # Shared components
└── services/
    ├── api.ts                  # Axios instance with interceptors
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

### AMC Error Handling
```python
# Extract detailed error information from AMC 400 responses
if response.status_code == 400 and 'details' in response_data:
    # Parse SQL compilation errors
    # Extract line/column information
    # Identify missing tables/columns
    # Structure into errorDetails object
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
```

### React Query Key Consistency
```typescript
// Keys must be consistent for caching
['dataSource', schemaId]        // ✓ Consistent
['data-source', id]             // ✗ Different structure breaks cache
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
├── auth_tokens (encrypted JSON)  -- Fernet encrypted
└── created_at

amc_instances
├── id (uuid, PK)                 -- Internal ID
├── instance_id (text, unique)     -- AMC's actual ID
├── name
├── entity_id                      -- For API headers
└── user_id (FK → users)

workflows
├── id (uuid, PK)
├── workflow_id (text)             -- Format: wf_XXXXXXXX
├── name
├── sql_query
├── parameters (jsonb)
└── user_id (FK → users)

workflow_executions
├── id (uuid, PK)
├── workflow_id (FK → workflows)
├── amc_execution_id               -- From AMC API
├── status                         -- PENDING/RUNNING/SUCCEEDED/FAILED
└── results (jsonb)

amc_data_sources                  -- Schema documentation
├── id (uuid, PK)
├── schema_id (text, unique)
├── name
├── category
└── fields (relation → schema_fields)
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
FERNET_KEY=xxx                      # Auto-generated if missing
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

## Recent Feature Additions (2025-08-14)

### Enhanced Error Display System
- **ErrorDetailsModal**: Full-screen error viewer with structured/raw/SQL views
- **Copy Functionality**: One-click copy for all error sections
- **Export Reports**: Download error details as JSON
- **Query Builder Integration**: Test execution with inline error display
- **AMC Compilation Errors**: Proper extraction and formatting of SQL syntax errors

### Data Sources Page Enhancements
- **Advanced Filter Builder**: Complex nested AND/OR conditions
- **Filter Presets**: 7 default presets + custom preset creation
- **Compare Mode**: Side-by-side comparison of 2-4 data sources
- **Bulk Actions**: Export JSON/CSV, copy IDs, generate documentation
- **Command Palette**: Cmd+K fuzzy search across all schemas
- **Multi-Select**: Visual bulk selection with action bar

### Query Builder Improvements
- **Test Execute Button**: Run queries during development
- **Error Display**: Immediate feedback on SQL syntax errors
- **Dynamic Schema Loading**: Real-time data source fetching from API
- **Parameter Detection**: Automatic extraction of {{parameters}}

## Deployment

Railway deployment via single Dockerfile:
- Frontend built during image creation
- Single container serves both frontend (`/frontend/dist`) and backend
- Frontend proxies `/api` to backend in development
- Use `./prepare_railway.sh` for deployment preparation

## Testing Checklist

Manual testing flow:
1. ✅ Login with Amazon OAuth
2. ✅ Add/edit AMC instance
3. ✅ Create query from template
4. ✅ Edit query in builder with schema browser
5. ✅ Execute workflow with parameters
6. ✅ View execution progress
7. ✅ View results in modal (inline and full)
8. ✅ Browse data sources with preview
9. ✅ Use Cmd+K to search schemas
10. ✅ Multi-select data sources for bulk actions
11. ✅ Apply advanced filters with nested conditions
12. ✅ Compare multiple data sources side-by-side
13. ✅ Test execute queries in Query Builder
14. ✅ View detailed error messages with copy functionality

## Known Issues & Workarounds

### Token Encryption
- If seeing "Failed to decrypt token" errors, the FERNET_KEY may have changed
- Tokens are automatically cleared and users must re-authenticate

### Execution Polling
- Background poller may show "coroutine was never awaited" warnings
- This doesn't affect functionality but indicates async/await mismatch

### AMC API Errors
- 400 errors with "unable to compile workflow" need special parsing
- Error details are in the `details` field, not `message`
- Table not found errors include line/column information