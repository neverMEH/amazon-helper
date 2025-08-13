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

### Backend Development
```bash
# Run backend server
python main_supabase.py  # Port 8001

# Testing
pytest tests/test_api_auth.py::test_login_success  # Run specific test

# Code quality
black amc_manager/          # Format
flake8 amc_manager/         # Lint
mypy amc_manager/           # Type check

# Database operations
python scripts/check_supabase_connection.py   # Check connection
python scripts/import_initial_data.py         # Import initial data
python scripts/apply_performance_indexes.py   # Apply indexes
```

### Frontend Development
```bash
cd frontend
npm install               # Install dependencies
npm run dev              # Dev server on port 5173
npm run build            # Production build
npm run lint             # ESLint
npx tsc --noEmit         # TypeScript type checking

# E2E testing
npx playwright test
npx playwright test --ui  # Interactive mode
```

## Architecture

### Backend Architecture (FastAPI + Supabase)

**Service Layer Pattern** - All business logic in `amc_manager/services/`:
- Services inherit from `DatabaseService` (aliased as `SupabaseService`) for automatic 30-minute timeout reconnection
- Critical services:
  - `amc_api_client.py`: Direct AMC API integration with proper auth headers
  - `token_service.py`: Fernet encryption for OAuth tokens
  - `execution_status_poller.py`: Background polling every 15 seconds
  - `data_source_service.py`: AMC schema documentation management

**API Routing** (`amc_manager/api/supabase/`):
- Authentication via `get_current_user` from `.auth` module
- Router registration in `main_supabase.py` with `/api` prefix
- Critical: POST endpoints require trailing slash (e.g., `/workflows/`)

### Frontend Architecture (React + TypeScript)

**State Management**:
- TanStack Query v5 for server state (5-minute staleTime, 10-minute gcTime)
- React Router v7 for routing
- React Hook Form for forms

**TypeScript Configuration**:
- `verbatimModuleSyntax: true` - Requires type-only imports (`import type`)
- Strict mode enabled

**Key Patterns**:
- API client in `services/api.ts` with auth interceptor
- Service pattern for API calls (e.g., `workflowService.ts`)
- Modal components use `isOpen/onClose` pattern

## Critical Implementation Details

### Query Builder Schema Explorer
- **Data Sources Only**: Schema explorer now exclusively shows AMC data sources from database
- **Dynamic Loading**: Fields are lazy-loaded when expanding a data source
- **Categories**: Data sources grouped by category (Attribution Tables, Conversion Tables, etc.)
- **Field Indicators**: Shows D (Dimension) or M (Metric) for each field
- **Search**: Filters both schemas and fields across all categories

### ID Field Duality
```typescript
// AMC uses two ID systems:
instanceId  // AMC's actual instance ID (for API calls)
id         // Internal UUID (for database relationships)

// CORRECT: Use instanceId for AMC API
<InstanceSelector value={state.instanceId} />

// WRONG: Internal UUID causes 403 errors
<InstanceSelector value={instance.id} />
```

### Date Handling for AMC
```python
# AMC requires dates without timezone suffix
'2025-07-15T00:00:00'    # ✓ Correct
'2025-07-15T00:00:00Z'   # ✗ Causes empty results

# Account for 14-day data lag
end_date = datetime.utcnow() - timedelta(days=14)
start_date = end_date - timedelta(days=7)
```

### API Authentication
```python
# Entity ID must be in headers, not query params
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-AdvertiserId': entity_id  # Critical!
}
```

### Token Encryption
- Tokens encrypted with Fernet before storage
- Auto-cleared on decryption failure
- Background refresh service with 15-minute buffer

### Router Registration
```python
# In data_sources.py - Don't add prefix here
router = APIRouter(tags=["Data Sources"])

# In main_supabase.py - Add full prefix here
app.include_router(data_sources_router, prefix="/api/data-sources")
```

## Environment Variables

Required for operation:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Public anon key  
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key
- `AMAZON_CLIENT_ID`: Amazon Advertising API client
- `AMAZON_CLIENT_SECRET`: OAuth secret
- `AMC_USE_REAL_API`: Set to "true" for real AMC API
- `FERNET_KEY`: Token encryption key (auto-generated if missing)

## Database Schema

Key tables in Supabase:
- `users`: Encrypted auth tokens in `auth_tokens` field
- `amc_instances`: AMC configurations (instance_id for API, id for relations)
- `workflows`: Query definitions with `workflow_id` format `wf_XXXXXXXX`
- `workflow_executions`: Execution history with AMC execution IDs
- `query_templates`: Reusable templates with parameter schemas
- `amc_data_sources`: AMC schema documentation

## Common Pitfalls

1. **FastAPI trailing slashes**: POST to collections needs trailing slash
2. **Type-only imports**: Use `import type` for TypeScript types
3. **React Query keys**: Keep consistent for caching
4. **AMC date format**: No timezone suffix
5. **Execution IDs**: Use UUID for foreign keys, not string workflow_id

## Deployment

Railway deployment via Dockerfile:
- Frontend built during image creation
- Single container serves both frontend (from `/frontend/dist`) and backend
- Frontend proxies `/api` to backend in development