# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Frontend Overview

React-based frontend for the RecomAMP (Amazon Marketing Cloud) platform, providing query building, execution monitoring, and data visualization capabilities for AMC instances.

## Working Features (as of 2025-08-13)

### ✅ UI Components
- **Query Builder**: 3-step wizard with Monaco SQL editor
- **Schema Explorer**: Dynamic AMC data sources from database
- **Execution Modal**: Progress tracking with inline and full results views
- **Data Sources Browser**: Category-based with SQL examples
- **Instance Manager**: Add, edit, remove AMC instances
- **Query Library**: Template browsing with search

### ✅ Recent UI Improvements (2025-08-13)
- **Dynamic Schema Loading**: Removed hardcoded tables, loads from API
- **SessionStorage Integration**: Examples populate in query editor
- **Dual Results View**: "View Results Here" (inline) and "Open Full Results" (modal)
- **React Fragment Fixes**: Proper JSX structure in ExecutionModal
- **Modal Z-Index Layering**: Correct stacking for nested modals

## Development Commands

```bash
# Install dependencies
npm install

# Development server (port 5173, proxies /api to backend on 8001)
npm run dev

# Production build
npm run build

# Linting
npm run lint

# TypeScript type checking (no npm script, use directly)
npx tsc --noEmit
npx tsc --noEmit --watch      # Watch mode during development

# Preview production build
npm run preview

# E2E testing with Playwright
npx playwright test                     # Run all tests
npx playwright test --ui               # Interactive mode
npx playwright test test-name.spec.ts  # Specific test file
npx playwright test -g "test name"     # Specific test by name
npx playwright test --debug            # Debug mode with inspector
```

## Architecture

### Core Stack
- **React 19.1.0** with TypeScript 5.8
- **React Router v7** for routing
- **TanStack Query v5** for server state management
- **Tailwind CSS** with @tailwindcss/forms and @tailwindcss/typography
- **Vite** for build tooling and dev server
- **Axios** for HTTP client with auth interceptors

### Key Libraries
- **Monaco Editor** (`@monaco-editor/react`): SQL query editing with syntax highlighting
- **Recharts**: Data visualization and charting
- **React Window**: Virtual scrolling for large datasets
- **React Hook Form** with resolvers: Form state management
- **Lucide React**: Icon library
- **date-fns**: Date manipulation
- **lodash**: Utility functions (use sparingly)
- **react-hot-toast**: Toast notifications

### TypeScript Configuration
- **verbatimModuleSyntax**: true - Requires type-only imports for types
- **strict**: true - Full strict mode enabled
- **noEmit**: true - TypeScript only for type checking, not compilation
- **target**: ES2022 - Modern JavaScript features
- **jsx**: react-jsx - New JSX transform

## Critical Architecture Patterns

### API Layer Architecture
```typescript
// All API calls flow through axios instance with interceptors (src/services/api.ts)
// - Request interceptor adds Bearer token from localStorage
// - Response interceptor handles 401s with debounced logout
// - Base URL is '/api' which proxies to backend on port 8001 in dev

// Service pattern for API calls (example: src/services/workflowService.ts)
const service = {
  list: () => api.get('/workflows'),
  get: (id) => api.get(`/workflows/${id}`),
  create: (data) => api.post('/workflows/', data),  // POST requires trailing slash
  update: (id, data) => api.put(`/workflows/${id}`, data),
  delete: (id) => api.delete(`/workflows/${id}`)
};
```

### React Query Data Flow
```typescript
// TanStack Query v5 manages all server state
// - 5-minute staleTime for caching
// - 10-minute gcTime (garbage collection)
// - Automatic refetch on window focus and reconnect
// - Exponential backoff for retries

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      staleTime: 5 * 60 * 1000,
      gcTime: 10 * 60 * 1000,  // NOT cacheTime (deprecated)
    },
  },
});
```

### Routing Architecture
```typescript
// Main routes defined in App.tsx
// - Protected routes wrap authenticated pages
// - Layout component provides common UI wrapper
// - Legacy redirects maintain backward compatibility

// Route structure:
/login                                  // Public
/dashboard                             // Protected, default route
/instances                             // Instance list
/instances/:instanceId                 // Instance detail with tabs
/workflows/:workflowId                 // Workflow detail
/query-builder/new                     // New query wizard
/query-builder/edit/:workflowId       // Edit existing
/query-builder/copy/:workflowId       // Copy workflow
/query-library                         // Template library
/my-queries                           // User's queries list
/executions                           // All executions
/profile                              // User profile
```

### Component Communication Patterns
```typescript
// Parent-child: Props drilling for 1-2 levels
// Cross-component: React Query for server state
// Local state: useState for UI state
// Forms: React Hook Form with controlled inputs
// Modals: Local state with isOpen/onClose pattern
// Navigation state: React Router's state prop for passing data
```

## Recent Changes (2025-08-13)

### Query Builder Enhancements
1. **Schema Explorer Updates**
   - File: `src/components/query-builder/QueryEditorStep.tsx`
   - Removed all hardcoded standard tables
   - Added data source fetching from API
   - Integrated with `dataSourceService.listDataSources()`

2. **Query Example Population**
   - File: `src/pages/QueryBuilder.tsx`
   - Added useEffect to load from sessionStorage
   - Clears sessionStorage after loading to prevent stale data
   - Works with examples from DataSourceDetail component

3. **Execution Results Modal**
   - File: `src/components/workflows/ExecutionModal.tsx`
   - Added AMCExecutionDetail modal integration
   - Fixed React Fragment syntax errors
   - Added "Open Full Results" button alongside inline viewer
   - Proper modal z-index layering (z-50 for main, higher for nested)

### SessionStorage Usage Pattern
```typescript
// DataSourceDetail stores example:
sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
  sql_query: example.sql_query,
  name: example.name,
  description: example.description,
  parameters: example.parameters || {}
}));

// QueryBuilder loads and clears:
useEffect(() => {
  if (!templateId && !workflowId) {
    const draft = sessionStorage.getItem('queryBuilderDraft');
    if (draft) {
      const parsedDraft = JSON.parse(draft);
      setQueryState(prev => ({...prev, ...parsedDraft}));
      sessionStorage.removeItem('queryBuilderDraft');
    }
  }
}, []);
```

## Key Architectural Decisions

### ID Field Duality
The system uses two different ID systems that must be carefully managed:
- **instanceId**: AMC's actual instance ID (used in API calls to AMC)
- **id**: Internal UUID (used for database relationships)

```typescript
// CORRECT: Use instanceId for AMC API calls
<InstanceSelector value={state.instanceId} />  // ✓

// WRONG: Using internal UUID causes 403 errors
<InstanceSelector value={instance.id} />  // ✗
```

### Query Builder Wizard Flow
Three-step wizard with state management in parent:
1. **QueryEditorStep**: SQL editor with AMC schema explorer
   - **Schema Explorer**: Shows AMC data sources from database (no hardcoded tables)
   - **Dynamic Loading**: Fields lazy-loaded when expanding data sources
   - **Categories**: Grouped by category (Attribution, Conversion, Audience tables, etc.)
   - **Field Info**: Shows dimension (D) or metric (M) indicators
   - **Search**: Filters schemas and fields across all categories
   - **Monaco Editor**: SQL editing with parameter detection
2. **QueryConfigurationStep**: Instance selection, parameters, export settings
3. **QueryReviewStep**: Final review with cost estimation

State flows down through props, updates bubble up through setState callbacks.

### Execution Modal Hierarchy
Two separate execution viewing systems:
- **AMCExecutionDetail**: Primary component for AMC executions (with rerun/refresh)
  - Supports `onRerunSuccess` callback for auto-navigation to new execution
  - Polls execution status every 5 seconds while open
  - Has view mode toggle between table and charts
  - **NEW**: Expand button for SQL editor to view in full-screen modal
- **ExecutionDetailModal**: Legacy component for workflow executions

### Export Name Auto-Generation
Export names follow pattern: `[Query Name] - [Instance] - [Date Range] - [DateTime]`
- Auto-generated on parameter change via useEffect
- User-editable but not required
- Removed email/format/password fields per AMP-1

### SQL Display Features
The execution details modal now includes:
- **SQLEditor Component**: Monaco Editor for syntax-highlighted SQL display
- **Expand Feature**: Maximize button to open SQL in full-screen modal
  - 80vh height editor for maximum visibility
  - Shows instance and query context
  - Higher z-index (60-70) to overlay main modal
- **Collapsible Sections**: Query and parameters sections with chevron toggles

## Common Pitfalls and Solutions

### React Fragment Usage
```typescript
// CORRECT: Wrap multiple elements in Fragment
return (
  <>
    <div className="modal">...</div>
    {showDetail && <DetailModal />}
  </>
);

// WRONG: Multiple elements without wrapper
return (
  <div className="modal">...</div>  // Error!
  {showDetail && <DetailModal />}
);
```

### Modal Z-Index Stacking
```typescript
// Main modal: z-50
<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">

// Nested modal: Higher z-index
<AMCExecutionDetail className="z-60" />  // Appears above main modal
```

### API Trailing Slashes
```typescript
// FastAPI requires trailing slash on POST/PUT to collection endpoints
api.post('/workflows/', data)   // ✓ Correct - returns 201
api.post('/workflows', data)     // ✗ Wrong - returns 405 Method Not Allowed
```

### TypeScript Type-Only Imports
```typescript
// verbatimModuleSyntax requires explicit type imports
import type { QueryTemplate } from '../types/queryTemplate';  // ✓
import { QueryTemplate } from '../types/queryTemplate';       // ✗ Error
```

### React Query Key Management
```typescript
// Query keys must be consistent for caching
['workflows', workflowId]  // ✓ Consistent structure
['workflow', id]           // ✗ Different key structure breaks cache
```

### Date Formatting for AMC
```typescript
// AMC API requires specific date format without timezone
'2025-07-15T00:00:00'    // ✓ Correct format
'2025-07-15T00:00:00Z'   // ✗ 'Z' suffix causes empty results
'2025-07-15'             // ✗ Missing time component
```

### Navigation Patterns
```typescript
// Use React Router's navigate, not window.location
navigate('/workflows')                              // ✓ Preserves SPA behavior
navigate('/query-builder/new', { state: { data }}) // ✓ Pass data via state
window.location.href = '/workflows'                // ✗ Full page reload

// Navigation to non-existent routes
navigate(`/workflows/${id}`)     // ✓ Correct route exists
navigate(`/my-queries/${id}`)    // ✗ Route doesn't exist (fixed in AMP-21)
```

### Execution Rerun Pattern
```typescript
// AMCExecutionDetail supports callback for auto-navigation after rerun
<AMCExecutionDetail
  onRerunSuccess={(newExecutionId) => {
    // Automatically switch to new execution
    setExecutionId(newExecutionId);
  }}
/>
```

## Testing Strategy

### Type Checking
```bash
npx tsc --noEmit              # Full type check
npx tsc --noEmit --watch      # Watch mode during development
```

### E2E Test Structure
Tests are in `tests/e2e/` directory:
- Uses Playwright with Chromium
- Runs dev server automatically (`npm run dev`)
- Base URL: `http://localhost:5173`
- HTML reporter for test results

## Performance Optimization Points

- **Virtual Scrolling**: React Window for tables > 100 rows
- **Code Splitting**: Monaco Editor lazy loaded
- **Query Caching**: 5-minute staleTime prevents redundant fetches
- **Debounced Search**: 300ms delay on search inputs
- **Memoization**: React.memo for expensive render components
- **Polling Optimization**: 5-second interval for execution status, only when modal open

## Build and Deployment

### Development Server
- Vite dev server on port 5173
- API proxy: `/api` → `http://127.0.0.1:8001`
- Hot Module Replacement enabled
- Host: `0.0.0.0` for network access

### Production Build
- Output: `dist/` directory
- Assets: `dist/assets/` with content hashing
- Deployed via parent Dockerfile (serves from `/frontend/dist`)

## Debugging Utilities

### Network Issues
- Check trailing slashes on POST/PUT requests
- Verify Bearer token in request headers
- Check for 401/403/405 status codes
- Confirm instanceId vs id usage

### State Issues
- React Query DevTools available in development
- Check queryKey consistency
- Verify staleTime/gcTime settings
- Look for race conditions in mutations

### Type Issues
- Run `npx tsc --noEmit` for full check
- Check for type-only import requirements
- Verify prop interface naming conventions

### SQL Display Issues
- Check SQLEditor component integration
- Verify Monaco Editor loading
- Look for readOnly prop settings
- Check expand modal z-index layering

### Monaco Editor Height Issues
- **Critical**: Monaco Editor requires explicit pixel height (e.g., `height="400px"`)
- Percentage heights (`height="100%"`) often fail in flex containers
- Using viewport heights (`60vh`) can be unreliable with nested containers
- For modals with Monaco Editor:
  - Use flex column layout for the modal
  - Set `flex-shrink-0` on header/footer sections
  - Use `flex-1 min-h-0 overflow-hidden` on editor container
  - Provide explicit pixel height to SQLEditor component
- Example working structure:
  ```tsx
  <div className="flex flex-col max-h-[90vh]">
    <header className="flex-shrink-0">...</header>
    <div className="flex-1 min-h-0 overflow-hidden">
      <SQLEditor height="400px" />
    </div>
    <footer className="flex-shrink-0">...</footer>
  </div>
  ```

## Recent Issue Fixes

### AMP-1: Export Name Auto-Generation
- Export name now auto-generates with format
- Removed unused email, format, password fields
- User can still customize the generated name

### AMP-19: SQL Query Formatting
- Replaced SQLHighlight with SQLEditor (Monaco)
- Fixed HTML artifacts in SQL display
- Added proper syntax highlighting via Monaco

### AMP-21: View Button Navigation
- Fixed View button in InstanceWorkflows
- Changed navigation from `/my-queries/${id}` to `/workflows/${id}`

### AMP-17: Auto-Open After Rerun
- AMCExecutionDetail now supports `onRerunSuccess` callback
- Modal automatically transitions to new execution after rerun

### SQL Editor Expand Feature
- Added maximize button to SQL query section
- Opens SQL in full-screen modal (80vh height)
- Shows instance and query context in expanded view
- Higher z-index layering for proper modal stacking

### Quick Edit Modal Height Fix (Latest)
- Fixed Monaco Editor not displaying in Quick Edit modal
- Issue: Complex flex layouts and percentage heights prevented editor rendering
- Solution: Use explicit pixel height (400px) for Monaco Editor
- Modal uses flex column with proper section management
- Key learning: Monaco Editor requires pixel heights, not percentages
## Recent Critical Fixes


### 2025-08-28 - 15:15:37
**fix**: Add debugging and test page for campaign selector issues
**Context**: Frontend changes
**Stats**:  4 files changed, 102 insertions(+), 5 deletions(-)


### 2025-08-28 - 15:04:47
**fix**: Fix campaign selector selection logic and add debugging
**Context**: Frontend changes
**Stats**:  2 files changed, 35 insertions(+), 7 deletions(-)


### 2025-08-28 - 12:39:45
**fix**: Enhance parameter detection to support campaign type and value type filtering
**Context**: Frontend changes
**Stats**:  4 files changed, 80 insertions(+), 24 deletions(-)


### 2025-08-28 - 12:25:29
**fix**: Fix campaign selection to use brand tags from instance_brands table
**Context**: Frontend changes
**Stats**:  5 files changed, 133 insertions(+), 80 deletions(-)


### 2025-08-28 - 09:13:59
**fix**: Fix ASIN selection modal value parsing and add debug logging
**Context**: Frontend changes
**Stats**:  2 files changed, 14 insertions(+), 3 deletions(-)


### 2025-08-28 - 09:04:28
**fix**: Fix TypeScript errors in campaign selection components
**Context**: Frontend changes
**Stats**:  2 files changed, 6 insertions(+), 5 deletions(-)


### 2025-08-27 - 18:34:54
**fix**: feat: Add comprehensive ASIN management system with query builder integration
**Context**: Frontend changes
**Stats**:  30 files changed, 120389 insertions(+), 6 deletions(-)


### 2025-08-27 - 15:36:25
**fix**: feat: Add campaign page optimizations with sorting, filters, and faster brand dropdown
**Context**: Frontend changes
**Stats**:  6 files changed, 1381 insertions(+), 4 deletions(-)


### 2025-08-27 - 10:04:06
**fix**: feat: Add ability to schedule workflow runs at specific times today
**Context**: Frontend changes
**Stats**:  5 files changed, 470 insertions(+), 69 deletions(-)


### 2025-08-27 - 09:24:53
**fix**: Fix schedule execution failures - Add entity_id join and improve error handling
**Context**: Frontend changes
**Stats**:  5 files changed, 93 insertions(+), 7069 deletions(-)


### 2025-08-26 - 22:10:20
**fix**: feat: Fetch and display brands from instance_brands table
**Context**: Frontend changes
**Stats**:  4 files changed, 29 insertions(+), 9 deletions(-)


**fix**: fix: Remove brands field references - column doesn't exist yet
**Context**: Frontend changes
**Stats**:  4 files changed, 11 insertions(+), 8 deletions(-)


**fix**: feat: Add instance brand names to schedule displays
**Context**: Frontend changes
**Stats**:  3 files changed, 29 insertions(+), 3 deletions(-)

**fix**: Fix schedule test runs and lookback period defaults
**Context**: Frontend changes
**Stats**:  4 files changed, 51 insertions(+), 8 deletions(-)
