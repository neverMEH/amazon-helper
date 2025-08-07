# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon Marketing Cloud (AMC) Manager - a full-stack application for managing AMC instances, creating and executing SQL queries, and tracking campaign performance across multiple brands.

Core features:
- AMC instance management with searchable, filterable interface
- Query builder with template library for reusable AMC SQL queries
- Query execution with real-time status tracking and data visualization
- Campaign tracking with automatic brand filtering
- Enhanced execution results with charts, tables, and export capabilities
- JWT authentication with encrypted OAuth token storage

## Development Commands

### Quick Start
```bash
# Start both backend and frontend services
./start_services.sh

# Services will be available at:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001  
# API Docs: http://localhost:8001/docs
# Default login: nick@nevermeh.com (no password required in dev)
```

### Backend Development
```bash
# Run backend server (FastAPI with Supabase)
python main_supabase.py  # Runs on port 8001

# Run specific test
pytest tests/test_api_auth.py::test_login_success

# Code quality
black amc_manager/          # Format code
flake8 amc_manager/         # Lint
mypy amc_manager/           # Type checking

# Database scripts
python test_supabase_simple.py              # Test connection
python scripts/import_initial_data.py       # Import initial data
python scripts/apply_performance_indexes.py # Apply DB indexes

# Test workflow execution (mock or real)
python scripts/demo_execution.py    # Demo success/failure scenarios
```

### Frontend Development
```bash
cd frontend
npm run dev       # Development server on port 5173
npm run build     # Production build with TypeScript checking
npm run lint      # ESLint checking
npm run typecheck # Alias for tsc --noEmit
npx tsc --noEmit  # TypeScript type checking only

# E2E tests
npx playwright test
npx playwright test --ui  # Interactive mode
```

## Architecture

### Backend Structure
- **FastAPI Application**: `main_supabase.py` - Main entry point
- **Service Layer Pattern**: Business logic isolated in `amc_manager/services/`
  - `SupabaseService`: Base class with automatic reconnection after 30-minute timeout
  - `db_service.py`: Database operations and query helpers
  - `amc_execution_service.py`: Workflow execution (mock/real modes)
  - `amc_api_client.py`: Direct AMC API integration with proper auth headers
  - `query_template_service.py`: Query template CRUD operations
  - `instance_service.py`: AMC instance and brand management
  - `brand_service.py`: Brand management and associations
  - `campaign_service.py`: Campaign data synchronization
  - `token_service.py`: Token encryption/decryption with Fernet
  - `data_analysis_service.py`: Pattern detection and data analysis
  - `WorkflowService`: Workflow operations with execution tracking
  - `ExecutionService`: Handles AMC query execution lifecycle
- **API Endpoints**: RESTful design in `amc_manager/api/supabase/`
  - All endpoints use dependency injection for authentication
  - Consistent error handling with HTTPException
- **Authentication**: JWT tokens with Fernet encryption stored in `auth_tokens` field

### Frontend Architecture  
- **React + TypeScript**: Component-based UI with strict typing
- **Routing**: React Router v7 with protected routes
  - `/dashboard` - Main dashboard
  - `/instances` - Searchable AMC instances list
  - `/instances/:id` - Instance detail with queries tab
  - `/query-builder/new` - Create new query
  - `/query-builder/edit/:id` - Edit existing query
  - `/my-queries` - User's saved queries
  - `/query-library` - Browse query templates
  - `/query-templates` - Manage templates
  - `/profile` - User profile with re-authentication
- **State Management**: TanStack Query (React Query) v5 for server state
  - 5-minute cache duration (staleTime: 5 * 60 * 1000)
  - Automatic retries with exponential backoff
  - Note: Use `gcTime` instead of deprecated `cacheTime`
- **Styling**: Tailwind CSS with @tailwindcss/forms and @tailwindcss/typography
- **API Client**: Axios with interceptors for auth and error handling
- **Code Editor**: Monaco Editor for SQL syntax highlighting
- **Data Visualization**: Recharts for charts, react-window for virtualization
- **Key Components**:
  - `QueryBuilder`: Main query creation interface
  - `QueryTemplates`: Full CRUD UI for template management
  - `QueryTemplateModal`: Create/edit modal with parameter detection
  - `InstanceSelector`: Searchable dropdown with brand display
  - `ExecutionModal`: Real-time execution monitoring (2-second polling)
  - `ExecutionDetailModal`: Results with table/charts/AI views
  - `DataVisualization`: Auto-generated charts based on data types
  - `VirtualizedTable`: Performance-optimized for large datasets
  - `EnhancedResultsTable`: Advanced filtering, sorting, export
  - `InstanceWorkflows`: Instance-specific query management
  - `BrandSelector`: Autocomplete brand selection with creation
  - `AMCSyncStatus`: Optional AMC workflow sync with benefits display

### Database Schema (Supabase)
Key tables:
- `users`: User accounts with encrypted auth tokens
  - `auth_tokens` field stores Fernet-encrypted OAuth tokens
- `amc_instances`: AMC instance configurations  
  - `instance_id`: AMC instance ID (used in API calls)
  - `id`: Internal UUID (used for relationships)
- `instance_brands`: Many-to-many brand associations
- `workflows`: Query definitions and parameters
  - `sql_query`: AMC SQL query with {{parameter}} placeholders
  - `parameters`: JSONB field for parameter values
- `workflow_executions`: Execution history and results
  - Tracks status: pending, running, completed, failed
  - Stores AMC execution IDs and result locations
- `query_templates`: Reusable query templates
  - `template_id`: Unique identifier (e.g., "conversion-path-analysis")
  - `parameters_schema`: JSONB schema for template parameters
  - `usage_count`: Tracks template popularity
- `campaign_mappings`: Campaign data with brand associations

### Critical Implementation Details

#### AMC API Authentication
```python
# Entity ID must be passed as header, NOT query parameter
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-MarketplaceId': marketplace_id,
    'Amazon-Advertising-API-AdvertiserId': entity_id  # Critical - must be header!
}

# OAuth token refresh flow
if token_expired:
    new_tokens = refresh_oauth_tokens(refresh_token)
    # Tokens are automatically encrypted before storage

# Date format for AMC API - CRITICAL
# Use this format (without timezone):
params['minCreationTime'] = datetime.strftime('%Y-%m-%dT%H:%M:%S')
# NOT this (causes "Must provide either workflowId or minCreationTime" error):
params['minCreationTime'] = datetime.isoformat() + 'Z'
```

#### CSV Data Processing
```python
# Transform CSV from array of arrays to objects with column names
def download_and_parse_csv(self, url, access_token):
    # ... download CSV ...
    reader = csv.reader(StringIO(text))
    headers = next(reader)
    rows = list(reader)
    
    # Transform to objects (required for frontend display)
    data_objects = []
    for row in rows:
        row_object = {}
        for i, header in enumerate(headers):
            row_object[header] = row[i] if i < len(row) else None
        data_objects.append(row_object)
    
    return {
        'columns': [{'name': h, 'type': 'string'} for h in headers],
        'rows': rows,  # Keep for compatibility
        'data': data_objects  # Use this for table display
    }
```

#### FastAPI Route Trailing Slashes
```python
# Routes with trailing slashes require exact matching
@router.post("/")  # Accessed as /api/workflows/ (with trailing slash)
@router.get("")    # Accessed as /api/workflows (no trailing slash)

# Frontend must match exactly:
await api.post('/workflows/', data)  # Correct
await api.post('/workflows', data)   # Wrong - returns 405
```

#### TypeScript Type Imports
```typescript
// Use type-only imports when verbatimModuleSyntax is enabled
import type { QueryTemplate } from '../types/queryTemplate';
import { queryTemplateService } from '../services/queryTemplateService';  // Regular import for values

// This will cause an error:
import { QueryTemplate } from '../types/queryTemplate';  // Error: must use type-only import
```

#### Workflow Instance IDs
```javascript
// Use instanceId (AMC ID) not id (internal UUID) for API calls
<option value={instance.instanceId}>  // Correct - AMC instance ID
<option value={instance.id}>          // Wrong - internal UUID causes 403

// Backend converts instanceId to internal UUID:
const instance = await getInstanceByInstanceId(workflow.instance_id);
workflow_data.instance_id = instance.id;  // Store internal UUID
```

## Environment Configuration

### Required Environment Variables
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Public anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for admin operations
- `AMAZON_CLIENT_ID`: Amazon Advertising API client ID
- `AMAZON_CLIENT_SECRET`: Client secret for OAuth
- `AMC_USE_REAL_API`: Set to "true" for real AMC API calls (default: mock)
- `FERNET_KEY`: Encryption key for auth tokens (auto-generated if not set)

### Deployment (Railway)
- Uses Dockerfile for consistent builds
- Frontend built during Docker image creation
- Single container serves both frontend and backend
- Frontend files served from `/frontend/dist`

## Common Development Tasks

### Adding a New API Endpoint
1. Create route in `amc_manager/api/supabase/[module].py`
   - Use `@router.get/post/put/delete` decorators
   - Add `current_user: Dict[str, Any] = Depends(get_current_user)` for auth
2. Add service method in `amc_manager/services/[service].py`
   - Inherit from `SupabaseService` for automatic reconnection
   - Return data directly, let routes handle HTTPException
3. Update frontend API service in `frontend/src/services/`
   - Use consistent naming: `listItems`, `getItem`, `createItem`, etc.
4. Add TypeScript types in `frontend/src/types/`
   - Use interfaces for data models
   - Export type-only when possible

### Creating a Query Template  
1. Templates stored in `query_templates` table
2. Use `{{variable}}` syntax for parameters
   - Parameters auto-detected by frontend
   - Default values based on parameter names (dates, windows, etc.)
3. Support for public/private visibility
4. Track usage automatically via `increment_usage`
5. Categories for organization (e.g., "attribution", "campaign", "audience")
6. Tags stored as JSONB array

### Working with Workflows
1. Workflows link to AMC instances by instance_id
   - Frontend sends instanceId (AMC ID)
   - Backend converts to internal UUID for storage
2. Support template-based creation
   - Template selection in WorkflowForm
   - Auto-populate name, description, query, parameters
3. Parameters stored as JSONB
   - Support for dynamic parameter substitution
   - Default values applied during execution
4. Execution tracked in `workflow_executions` table
   - Real-time status updates via polling
   - Results stored with S3 URLs

## Testing Guidelines

- **Mock Mode**: Default for development (no real AMC API calls)
- **Sandbox Instances**: `amchnfozgta` or `amcfo8abayq` for testing
- **Real API Mode**: Set `AMC_USE_REAL_API=true` environment variable
- **Test Users**: Use nick@nevermeh.com for development

## Performance Optimizations

- Supabase queries use joins to minimize round trips
- React Query caches API responses for 5 minutes
- Database indexes on frequently queried columns
- Automatic connection refresh after 30-minute timeout
- Gzip compression for API responses > 1KB

## Known Issues and Solutions

### API Errors
- **405 Method Not Allowed**: Check trailing slashes on POST endpoints
  - Solution: Use `/workflows/` not `/workflows` for POST
- **403 Forbidden on Workflow Creation**: Ensure using instanceId not internal UUID
  - Solution: Use `instance.instanceId` in frontend forms
- **404 on Query Templates**: Wrong API path
  - Solution: Use `/query-templates` not `/queries/templates`
- **AMC Execution Fails**: Date format must exclude timezone
  - Solution: Format dates as `YYYY-MM-DD` without `+00:00` suffix

### TypeScript Errors  
- **Type must be imported using type-only import**: verbatimModuleSyntax enabled
  - Solution: Change `import { Type }` to `import type { Type }`
- **Cannot find module**: Check relative import paths
  - Solution: Use `../` for parent directory imports
- **React Query Deprecated Props**: Use gcTime instead of cacheTime
  - Solution: Replace `cacheTime: 5 * 60 * 1000` with `gcTime: 5 * 60 * 1000`

### Database Issues
- **Supabase Timeout After 30 Minutes**: Connection expires
  - Solution: Automatic reconnection in SupabaseService base class
- **Empty Results After Idle**: Stale cache
  - Solution: React Query refetches on window focus

### Development Tips
- **Module Not Found in Backend**: Check imports match actual file structure
  - Example: `from ...services.query_template_service import QueryTemplateService`
- **JWT Decode Errors**: Use `jwt.DecodeError` not `jwt.JWTError`
- **CORS Issues**: Backend serves frontend in production, proxy in dev
- **CSV Results Processing**: Transform array format to objects for proper display
  - Use `transformCsvData` helper in `frontend/src/utils/csvHelpers.ts`

## Query Templates Feature

### Overview
Query templates allow users to create reusable AMC SQL queries with parameters that can be filled in during workflow creation.

### Implementation Details

#### Backend Components
- **Service**: `amc_manager/services/query_template_service.py`
  - Full CRUD operations with access control
  - Public/private template support
  - Usage tracking for analytics
- **API Routes**: `amc_manager/api/supabase/query_templates.py`
  - RESTful endpoints at `/api/query-templates/`
  - Template building endpoint for parameter substitution
  - Category management endpoints

#### Frontend Components  
- **Main UI**: `frontend/src/components/query-templates/QueryTemplates.tsx`
  - Table view with search, filter, and sort
  - Create/Edit/Delete operations
  - Category and visibility filters
- **Modal**: `frontend/src/components/query-templates/QueryTemplateModal.tsx`
  - Monaco editor for SQL editing
  - Real-time parameter detection
  - Parameter schema builder
- **Selector**: `frontend/src/components/workflows/QueryTemplateSelector.tsx`
  - Template browser in workflow creation
  - Search and category filtering
  - Preview with parameter highlighting

#### Template Syntax
```sql
-- Use double curly braces for parameters
SELECT 
    campaign_id,
    SUM(impressions) as total_impressions
FROM campaign_data
WHERE 
    event_date >= '{{start_date}}'
    AND event_date <= '{{end_date}}'
    AND brand_id = '{{brand_id}}'
GROUP BY campaign_id
HAVING total_impressions > {{min_impressions}}
```

#### Usage Flow
1. User creates template with parameters
2. Template saved with parameter schema
3. User selects template in workflow creation
4. Parameters auto-populate with defaults
5. User adjusts parameter values
6. Workflow created with filled template
7. Template usage count incremented

### Best Practices
- Use descriptive parameter names
- Provide default values in schema
- Add clear descriptions for templates
- Use categories for organization
- Make templates public for team sharing

## Performance Features

### Virtual Scrolling
- **VirtualizedTable Component**: Handles large datasets efficiently
  - Uses react-window for row virtualization
  - Supports 10,000+ rows without performance degradation
  - Auto-calculates column widths

### Lazy Loading
- **React Suspense Integration**: Components load on demand
  - DataVisualization component loads only when needed
  - ExecutionDetailModal loads data progressively
  - Image and chart lazy loading

### Data Caching
- **React Query Optimization**:
  - 5-minute cache with `staleTime: 5 * 60 * 1000`
  - Garbage collection with `gcTime: 30 * 60 * 1000`
  - Automatic background refetch on window focus
  - Query invalidation on mutations

### Searchable Instances
- **Comprehensive Filtering**: Handle 100+ instances efficiently
  - Multi-field search (name, ID, brands, account)
  - Filter by region, type, status, brand
  - Memoized filtering with useMemo
  - Debounced search input

## Data Visualization

### Recharts Integration
- **DataVisualization Component**: Auto-generates charts from data
  - Detects data types and suggests appropriate charts
  - Time series for date columns
  - Bar charts for categorical data
  - Pie charts for distribution analysis
  - Scatter plots for correlations

### Chart Features
- Interactive tooltips and legends
- Responsive design with auto-sizing
- Export to PNG/SVG
- Custom color schemes
- Support for multiple Y-axes

## Git Workflows

### Feature Development
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push -u origin feature/your-feature-name
```

### Commit Message Format
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build process or auxiliary tool changes

## Additional Resources

### Template Library Planning
- See `/docs/template-library-plan.md` for comprehensive AMC instructional query template system design
- Includes SP/DSP overlap analysis template
- 6-phase implementation roadmap

### Dependencies
- **Frontend**: See `frontend/package.json` for complete list
  - Key additions: recharts, react-window, @types/react-window
- **Backend**: See `requirements_supabase.txt`
  - FastAPI, Supabase, cryptography for token encryption

### Monitoring
- Check execution logs: `python scripts/check_execution_logs.py`
- Database performance: Apply indexes with `scripts/apply_performance_indexes.py`
- API performance: FastAPI automatic docs at `/docs`