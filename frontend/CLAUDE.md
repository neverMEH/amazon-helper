# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Frontend Overview

React-based frontend for the RecomAMP (Amazon Marketing Cloud) platform, providing query building, execution monitoring, and data visualization capabilities for AMC instances.

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

# Preview production build
npm run preview

# E2E testing with Playwright
npx playwright test                     # Run all tests
npx playwright test --ui               # Interactive mode
npx playwright test test-name.spec.ts  # Specific test file
npx playwright test -g "test name"     # Specific test by name
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
1. **QueryEditorStep**: Monaco Editor for SQL with parameter extraction
2. **QueryConfigurationStep**: Instance selection, parameters, export settings
3. **QueryReviewStep**: Final review with cost estimation

State flows down through props, updates bubble up through setState callbacks.

### Execution Modal Hierarchy
Two separate execution viewing systems:
- **AMCExecutionDetail**: Primary component for AMC executions (with rerun/refresh)
- **ExecutionDetailModal**: Legacy component for workflow executions

### Export Name Auto-Generation
Export names follow pattern: `[Query Name] - [Instance] - [Date Range] - [DateTime]`
- Auto-generated on parameter change
- User-editable but not required
- Removed email/format/password fields per AMP-1

## Common Pitfalls and Solutions

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

### Navigation After Actions
```typescript
// Use React Router's navigate, not window.location
navigate('/workflows')           // ✓ Preserves SPA behavior
window.location.href = '/workflows'  // ✗ Full page reload
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