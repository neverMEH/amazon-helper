# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Frontend Overview

React-based frontend for the RecomAMP (Amazon Marketing Cloud) platform, providing query building, execution monitoring, and data visualization capabilities for AMC instances.

## Development Commands

```bash
# Install dependencies
npm install

# Development server (port 5173)
npm run dev

# Production build
npm run build

# Linting
npm run lint

# TypeScript type checking (no npm script, use directly)
npx tsc --noEmit

# E2E testing with Playwright
npx playwright test
npx playwright test --ui  # Interactive mode
```

## Architecture

### Core Stack
- **React 19.1.0** with TypeScript 5.8
- **React Router v7** for routing
- **TanStack Query v5** for server state management
- **Tailwind CSS** for styling
- **Vite** for build tooling

### Key Libraries
- **Monaco Editor**: SQL query editing with syntax highlighting
- **Recharts**: Data visualization and charting
- **React Window**: Virtual scrolling for large datasets
- **React Hook Form**: Form state management
- **Axios**: HTTP client with interceptors
- **Lucide React**: Icon library
- **date-fns**: Date manipulation

## Project Structure

```
src/
├── components/
│   ├── common/           # Reusable UI components
│   ├── executions/       # Execution monitoring and results
│   ├── instances/        # AMC instance management
│   ├── query-builder/    # Query creation workflow
│   ├── query-templates/  # Template management
│   └── workflows/        # Workflow execution
├── services/            # API service layer
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── pages/              # Route components
```

## Critical Implementation Patterns

### API Communication
```typescript
// All API calls go through axios instance with auth interceptor
import api from '../services/api';

// Consistent naming pattern for service methods
const service = {
  list: () => api.get('/items'),
  get: (id) => api.get(`/items/${id}`),
  create: (data) => api.post('/items/', data),  // Note trailing slash for POST
  update: (id, data) => api.put(`/items/${id}`, data),
  delete: (id) => api.delete(`/items/${id}`)
};
```

### React Query Usage
```typescript
// Use TanStack Query v5 patterns
const { data, isLoading, error } = useQuery({
  queryKey: ['items', id],
  queryFn: () => service.get(id),
  staleTime: 5 * 60 * 1000,  // 5 minutes
  gcTime: 10 * 60 * 1000,    // Use gcTime, not cacheTime (deprecated)
});
```

### TypeScript Imports
```typescript
// Use type-only imports when verbatimModuleSyntax is enabled
import type { QueryTemplate } from '../types/queryTemplate';
import { queryTemplateService } from '../services/queryTemplateService';
```

### Component Patterns
```typescript
// Export default for pages, named exports for components
export default function PageComponent() { ... }
export function UtilityComponent() { ... }

// Props interfaces follow naming convention
interface ComponentNameProps {
  required: string;
  optional?: number;
}
```

## Key Components and Their Responsibilities

### Query Builder Flow
1. **QueryBuilder** (`pages/QueryBuilder.tsx`) - Main wizard controller
2. **QueryEditorStep** - SQL editing with Monaco Editor
3. **QueryConfigurationStep** - Instance selection and export settings
4. **QueryReviewStep** - Final review before execution

### Execution Components
- **AMCExecutionDetail** - Primary execution viewer with rerun/refresh
- **ExecutionDetailModal** - Legacy workflow execution viewer
- **DataVisualization** - Auto-generates charts from result data
- **VirtualizedTable** - Performance-optimized large data tables

### Instance Management
- **InstanceSelector** - Searchable dropdown with brand display
- **InstanceWorkflows** - Queries tab in instance detail
- **BrandSelector** - Autocomplete brand selection with creation

## Common Pitfalls and Solutions

### API Trailing Slashes
```typescript
// POST endpoints require trailing slash
api.post('/workflows/', data)   // ✓ Correct
api.post('/workflows', data)     // ✗ Returns 405
```

### Instance ID Usage
```typescript
// Use instanceId (AMC ID) not id (internal UUID)
<option value={instance.instanceId}>  // ✓ Correct - AMC instance ID
<option value={instance.id}>          // ✗ Wrong - causes 403
```

### Export Name Auto-Generation
```typescript
// Export names follow format: [Query] - [Instance] - [Date Range] - [DateTime]
// Auto-generated in QueryConfigurationStep but user-editable
const exportName = `${queryName} - ${instanceName} - ${dateRange} - ${dateTimeRan}`;
```

### Execution Parameters
```typescript
// Parameters are at root level in execution objects
execution.executionParameters  // ✓ Correct
execution.parameters           // ✗ Wrong
```

### Date Formatting for AMC
```typescript
// AMC requires dates without timezone suffix
'2025-07-15T00:00:00'    // ✓ Correct
'2025-07-15T00:00:00Z'   // ✗ Causes empty results
```

## Testing

### Type Checking
```bash
npx tsc --noEmit  # Run before committing
```

### E2E Tests
```bash
npx playwright test                    # Run all tests
npx playwright test --ui              # Interactive UI
npx playwright test test-name.spec.ts # Specific test
```

## Environment Variables

Frontend expects backend at `http://localhost:8001` in development. This is configured in `vite.config.ts` proxy settings.

## Recent Changes (as of latest commit)

- **AMP-1**: Auto-fill export name, removed unused email/format/password fields
- **AMP-11**: Added breadcrumb navigation across all pages
- **AMP-16**: Fixed execution status display in list view
- **AMP-17**: Auto-open new execution modal after rerun
- **AMP-20**: Changed "Queries" to "Workflows" in instance detail

## Performance Considerations

- Use React.memo for expensive components
- Implement virtual scrolling for large lists (react-window)
- Leverage React Query's caching (5-minute staleTime)
- Lazy load heavy components (Monaco Editor, charts)

## Debugging Tips

- Check Network tab for API failures (especially 403/405 errors)
- Verify trailing slashes on POST requests
- Ensure using correct ID fields (instanceId vs id)
- Check React Query DevTools for cache state
- Use `console.log(execution)` to inspect data structure