# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## ⚡ Critical Gotchas

1. **AMC ID Duality**: Always use `instance_id` for AMC API calls, not the internal `id` UUID
2. **Date Format**: AMC requires dates without timezone: `2025-07-15T00:00:00` (no 'Z')
3. **Token Refresh**: Use `amc_api_client_with_retry` for automatic token handling
4. **Async/Await**: Always await async methods, but Supabase client is synchronous (no await)
5. **Type Imports**: Use `import type` for TypeScript type-only imports
6. **Monaco Editor**: Must use pixel heights, not percentages
7. **FastAPI Routes**: Collections need trailing slash for POST/PUT
8. **Environment**: Use `python` not `python3` in scripts (alias if needed)
9. **Schedule Deduplication**: Schedules check for recent runs within 5 minutes to prevent duplicates
10. **Token Method**: Use `refresh_access_token()` not `refresh_token()` in TokenService

## 🚀 Quick Start

```bash
# Start everything with one command
./start_services.sh

# This launches:
# ✓ Backend API: http://localhost:8001
# ✓ Frontend UI: http://localhost:5173
# ✓ API Documentation: http://localhost:8001/docs
# ✓ Background services (token refresh, execution polling, scheduling)
```

## Project Overview

**RecomAMP** - Amazon Marketing Cloud (AMC) platform for:
- Managing multiple AMC instances across advertiser accounts
- Building SQL queries with visual editor and schema explorer
- Executing workflows with parameter substitution
- Scheduling automated recurring executions
- Query library with templates and examples
- Execution history with comprehensive error reporting

## Tech Stack

**Backend**: FastAPI, Supabase, Python 3.11, Fernet encryption, httpx/tenacity, croniter
**Frontend**: React 19.1.0, TypeScript 5.8, TanStack Query v5, React Router v7, Monaco Editor, Tailwind CSS, Vite

## Project Structure

```
amazon-helper/
├── amc_manager/           # Backend Python package
│   ├── api/              # API endpoints
│   ├── core/             # Core utilities
│   └── services/         # Business logic layer
├── frontend/             # React application
│   ├── src/              # Source code
│   └── dist/             # Production build
├── scripts/              # Utility and migration scripts
├── tests/                # Test suites
├── main_supabase.py      # FastAPI application entry
└── start_services.sh     # Local development launcher
```

## 🔴 ID Fields Reference Guide

**ALWAYS use the correct ID field to avoid 404/403 errors:**

### AMC Instances
- `id` (UUID): Internal database primary key - NEVER use for AMC API calls
- `instance_id` (string): AMC's actual instance identifier - ALWAYS use for AMC API calls
- `instance_name` (string): Display name - Note: column is `instance_name` NOT `name`

### Workflow Executions  
- `id` (UUID): Internal database primary key
- `amc_execution_id` (string): AMC's execution identifier - ALWAYS use for AMC API calls
- `workflow_execution_id` in schedule_runs: Should reference `amc_execution_id` NOT internal `id`

### Workflows
- `id` (UUID): Internal database primary key
- `workflow_id` (string, e.g., "wf_xxxxx"): Human-readable identifier
- `amc_workflow_id` (string): AMC's workflow identifier when synced
- `instance_id` (UUID FK): References amc_instances.id - needs join to get actual instance_id

### Schedules
- `id` (UUID): Internal database primary key  
- `schedule_id` (string, e.g., "sched_xxxxx"): Human-readable identifier
- When fetching schedules, must include full relations: `workflows(*, amc_instances(...))`

## 📐 Critical Patterns

### Backend Patterns

```python
# Service Layer - ALL services inherit from DatabaseService
class MyService(DatabaseService):
    def __init__(self):
        super().__init__()
    
    @with_connection_retry
    async def my_method(self):
        # Database operations auto-retry on disconnect
        pass

# Token Management - Always use retry client for AMC operations
from amc_manager.services.amc_api_client_with_retry import amc_api_client_with_retry

result = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,  # Use AMC instance ID, not UUID!
    user_id=user_id,
    entity_id=entity_id,
)

# Date Handling for AMC
'2025-07-15T00:00:00'    # ✓ Correct
'2025-07-15T00:00:00Z'   # ✗ Causes empty results

# Async/Await Patterns
result = await async_method()  # ✓ Correct
result = async_method()  # ✗ Returns coroutine, not result

# Supabase client is synchronous
result = self.client.table('schedules').select().execute()  # No await!
```

### Frontend Patterns

```tsx
// Type Imports (verbatimModuleSyntax)
import type { FC, ReactNode } from 'react';  // ✓
import { FC, ReactNode } from 'react';       // ✗

// React Query Keys - Must be consistent for caching
['dataSource', schemaId]        // ✓ Consistent
['data-source', id]             // ✗ Different structure breaks cache

// Modal Z-Index Layering
<MainModal className="z-50">
  {showNested && <NestedModal className="z-60" />}
  {showError && <ErrorModal className="z-70" />}
</MainModal>

// Monaco Editor - MUST use pixel heights
<SQLEditor height="400px" />     // ✓ Works
<SQLEditor height="100%" />      // ✗ Often fails
```

## 📊 Key Database Tables

```sql
users                      -- User accounts with encrypted OAuth tokens
amc_instances              -- AMC instance configurations
workflows                  -- SQL query workflows
workflow_executions        -- Execution history with results
workflow_schedules         -- Automated execution schedules
schedule_runs              -- Schedule execution history
amc_data_sources          -- AMC schema documentation
amc_schema_fields         -- Field metadata
query_templates           -- Pre-built query library

-- Build Guides Tables (Added 2025-08-21)
build_guides               -- Main guide metadata and configuration
build_guide_sections       -- Guide content sections with markdown
build_guide_queries        -- SQL queries associated with guides
build_guide_examples       -- Example results and interpretations
build_guide_metrics        -- Metric/dimension definitions
user_guide_progress        -- User progress tracking
user_guide_favorites       -- User's favorite guides
```

## Background Services

1. **Token Refresh Service** (every 10 minutes): Refreshes OAuth tokens before expiry
2. **Execution Status Poller** (every 15 seconds): Updates status of pending AMC executions
3. **Schedule Executor Service** (every 60 seconds): Executes scheduled workflows at due times

## 🔧 Common Issues & Solutions

### "Failed to decrypt token"
User must re-authenticate - FERNET_KEY may have changed

### Empty AMC Query Results
- Check date format (no 'Z' suffix)
- Account for 14-day data lag

### 403 Forbidden on AMC API
- Use `instance_id` not internal UUID
- Ensure entity_id in headers

### Schedule Not Executing
- Check schedule is active
- Verify user has valid tokens
- Check timezone calculations

### TypeScript Build Errors
```bash
# Fix type-only imports
import type { Workflow } from '../types';  # ✓ Correct
import { Workflow } from '../types';       # ✗ Error
```

### FastAPI Trailing Slashes
```python
api.post('/workflows/', data)      # ✓ Returns 201
api.post('/workflows', data)        # ✗ Returns 405
```

## Essential Commands

### Development
```bash
# Backend
python main_supabase.py                      # Start backend
pytest tests/ -v                             # Run tests
python scripts/check_supabase_connection.py  # Check DB connection

# Frontend
cd frontend
npm run dev                                  # Start frontend
npm run typecheck                           # Check TypeScript types
npm run build                               # Production build

# Database
python scripts/import_amc_schemas.py        # Import AMC schemas
python scripts/apply_performance_indexes.py # Apply indexes
python scripts/validate_schedules.py        # Validate schedules

# Build Guides
python scripts/build_guides_migration_ready.sql  # Apply Build Guides schema
python scripts/seed_creative_asin_guide.py       # Seed example guide
```

### Common Fixes
```bash
# Token encryption issues
python scripts/fix_token_encryption.py

# Apply migrations
python scripts/apply_schedule_migrations.py
python scripts/apply_performance_indexes.py
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
AMC_USE_REAL_API=true  # Set to "false" for mock responses
ENVIRONMENT=development
DEBUG=true
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

# Data Sources
GET    /api/data-sources/
GET    /api/data-sources/{id}
```

## Recent Critical Fixes (2025-08-21)

1. **Schedule Executor Token Refresh**: Changed from `refresh_token()` to `refresh_access_token()`
2. **Schedule Deduplication**: Added 5-minute window to prevent rapid re-executions
3. **Next Run Updates**: Updates immediately to prevent infinite loops

## 📚 Build Guides Feature (Added 2025-08-21)

### Overview
Build Guides provide step-by-step tactical guidance for AMC query use cases. Each guide includes:
- Structured content sections with markdown support
- Pre-built SQL queries with parameter templates
- Example results with interpretation guidance
- Progress tracking and favorites system
- Metrics/dimensions definitions

### Implementation Details

#### Database Schema
```sql
-- 7 tables for complete Build Guides functionality
build_guides               -- Main guide metadata (guide_id, name, category, difficulty, etc.)
build_guide_sections       -- Markdown content sections (supports tables, code blocks, lists)
build_guide_queries        -- SQL queries with parameters (linked to query_templates)
build_guide_examples       -- Sample data and interpretation (JSON rows + markdown)
build_guide_metrics        -- Metric/dimension definitions for the guide
user_guide_progress        -- Tracks completion status per user
user_guide_favorites       -- User's favorited guides
```

#### Key Frontend Components
- **BuildGuides.tsx**: Main listing page with filtering and search
- **BuildGuideDetail.tsx**: Individual guide view with TOC and progress tracking
- **buildGuideService.ts**: API service layer for all guide operations

#### Markdown Rendering Configuration
```typescript
// Uses react-markdown with remark-gfm for enhanced formatting
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Custom components for tables, code blocks, etc.
const markdownComponents = {
  table: // Responsive with overflow, striped rows
  code: // Dark background for blocks, light for inline
  // ... other components
};

// Render with: 
<ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
  {content}
</ReactMarkdown>
```

#### Sample Data Table Rendering
```typescript
// Converts JSON sample_data.rows to HTML tables
const renderSampleDataTable = (sampleData: any) => {
  // Auto-formats column headers (snake_case to Title Case)
  // Number formatting with toLocaleString()
  // Consistent styling with markdown tables
};
```

#### API Endpoints
```http
GET    /api/build-guides/              # List all guides (public for published)
GET    /api/build-guides/{guide_id}    # Get specific guide (uses guide_id string, not UUID)
POST   /api/build-guides/{guide_id}/start      # Start/resume guide
PUT    /api/build-guides/{guide_id}/progress   # Update progress
POST   /api/build-guides/{guide_id}/favorite   # Toggle favorite
```

#### Authentication Pattern
```python
# Optional authentication for published guides
@router.get("/{guide_id}")
async def get_guide(
    guide_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    # Published guides viewable without auth
    # Unpublished guides require authentication
```

#### Table of Contents Navigation
- Smooth scrolling with offset for sticky header
- Active section tracking on scroll
- Bidirectional navigation (click to scroll, scroll updates highlight)

#### Progress Tracking
- Automatic start when opening guide
- Section completion tracking
- Query execution tracking
- Progress percentage calculation
- Status: not_started, in_progress, completed

### Seeding Guide Data
```python
# Use scripts/seed_creative_asin_guide.py as template
# Structure:
1. Create guide with metadata
2. Add sections with markdown content
3. Add queries (exploratory and main_analysis types)
4. Add example results with sample_data JSON
5. Define metrics and dimensions
```

### Critical Implementation Notes

1. **Guide ID Pattern**: Use descriptive string IDs like `guide_creative_asin_impact` not UUIDs
2. **Markdown Tables**: Require remark-gfm plugin and custom table components
3. **Sample Data**: Store as JSON with `rows` array, render with custom function
4. **Full Width Layout**: Removed `max-w-7xl` constraints for better screen utilization
5. **Section IDs**: Must be unique strings for TOC navigation to work
6. **Query Examples**: Include both `sample_data` (JSON) and `interpretation_markdown`

### Common Issues & Solutions

#### Tables Not Rendering
- Ensure `remark-gfm` is installed: `npm install remark-gfm`
- Add `remarkPlugins={[remarkGfm]}` to ReactMarkdown
- Provide custom table components in `components` prop

#### TOC Not Scrolling
- Sections need `id={section.section_id}` attribute
- Use `scrollToSection` function with proper offset
- Account for sticky header height in calculations

#### 404 on Guide API
- FastAPI routes need trailing slash: `/api/build-guides/`
- Use `guide_id` string, not internal UUID
- Check if guide is published or user is authenticated

#### Sample Data Not Showing
- Check `sample_data.rows` exists in database
- Use `renderSampleDataTable` helper function
- Ensure proper JSON structure with array of objects

## Testing

```bash
# Backend
pytest tests/ -v                            # All tests
pytest tests/test_api_auth.py -v           # Specific test file
pytest --cov=amc_manager tests/             # With coverage

# Frontend
npm run typecheck                          # Type checking
npx playwright test                        # E2E tests
npx playwright test --ui                   # Interactive mode
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

## Workflow Scheduling Features

- **Flexible Intervals**: Daily, weekly, monthly, custom CRON expressions
- **Smart Date Parameters**: Dynamic date calculations, timezone-aware
- **Execution Management**: Auto-retry, auto-pause on failures, cost tracking
- **Comprehensive History**: Timeline view, metrics dashboard, error tracking

## Debugging Commands

```bash
# Check API routes
curl http://localhost:8001/api/debug/routes

# Test Supabase connection
python scripts/check_supabase_connection.py

# Check running executions
python scripts/find_running_executions.py

# Monitor server logs
tail -f server.log
```