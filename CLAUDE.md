# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Recom AMP - Amazon Marketing Cloud query development and execution platform for managing AMC instances, creating and executing SQL queries with iterative workflow tracking, and building a comprehensive query library.

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
python scripts/check_supabase_connection.py   # Check connection
python scripts/import_initial_data.py       # Import initial data
python scripts/apply_performance_indexes.py # Apply DB indexes

# Execute workflows via API
# Use the API endpoints for workflow execution
```

### Frontend Development
```bash
cd frontend
npm install       # Install dependencies
npm run dev       # Development server on port 5173
npm run build     # Production build with TypeScript checking
npm run lint      # ESLint checking
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
  - `amc_execution_service.py`: Workflow execution with real AMC API
  - `amc_api_client.py`: Direct AMC API integration with proper auth headers
  - `query_template_service.py`: Query template CRUD operations
  - `instance_service.py`: AMC instance and brand management
  - `brand_service.py`: Brand management and associations
  - `campaign_service.py`: Campaign data synchronization
  - `token_service.py`: Token encryption/decryption with Fernet
  - `token_refresh_service.py`: Background service for automatic token refresh
  - `data_analysis_service.py`: Pattern detection and data analysis
  - `execution_status_poller.py`: Background service polling execution statuses every 15 seconds
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
  - `AMCExecutionDetail`: Primary component for viewing AMC executions with rerun/refresh
  - `ExecutionDetailModal`: Legacy component for workflow executions
  - `DataVisualization`: Auto-generated charts based on data types
  - `VirtualizedTable`: Performance-optimized for large datasets
  - `EnhancedResultsTable`: Advanced filtering, sorting, export
  - `InstanceWorkflows`: Instance-specific query management
  - `BrandSelector`: Autocomplete brand selection with creation
  - `AMCSyncStatus`: Optional AMC workflow sync with benefits display
  - `Breadcrumb`: Dynamic breadcrumb navigation component
  - `AppLogo`: Application branding with PNG fallback support
  - `AuthStatusBanner`: Authentication status banner for disconnected auth

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
  - `workflow_id`: AMC-compliant identifier (format: `wf_XXXXXXXX`)
- `workflow_executions`: Execution history and results
  - Tracks status: pending, running, completed, failed
  - Stores AMC execution IDs and result locations
  - `execution_id`: Internal execution ID (format: `exec_XXXXXXXX`)
  - `amc_execution_id`: AMC's execution ID for polling status
- `query_templates`: Reusable query templates
  - `template_id`: Unique identifier (e.g., "conversion-path-analysis")
  - `parameters_schema`: JSONB schema for template parameters
  - `usage_count`: Tracks template popularity
- `campaign_mappings`: Campaign data with brand associations

### Critical Implementation Details

#### Workflow and Execution IDs

⚠️ **CRITICAL: See `/docs/ID_FIELD_REFERENCE.md` for complete ID field documentation**

```python
# Database ID relationships - THIS IS CRITICAL:
# workflows.id (UUID) - Primary key, used for foreign key relationships
# workflows.workflow_id (TEXT) - AMC-compliant string ID (wf_XXXXXXXX)
# workflow_executions.workflow_id (UUID) - Foreign key to workflows.id (NOT workflows.workflow_id!)

# CORRECT usage for execution queries:
workflow_uuids = [w['id'] for w in workflows]  # Use UUID
exec_response = client.table('workflow_executions')\
    .in_('workflow_id', workflow_uuids)\  # Foreign key expects UUID
    .execute()

# WRONG - This will cause "invalid input syntax for type uuid" error:
# workflow_ids = [w['workflow_id'] for w in workflows]  # String IDs
# exec_response = client.table('workflow_executions')\
#     .in_('workflow_id', workflow_ids)\  # FAILS - expects UUID not string
```

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
```

#### AMC Date Parameter Handling (CRITICAL - Fixed 2025-08-13)
```python
# AMC has a 14-day data lag - queries for recent data return 0 rows
# The API now properly extracts date parameters from frontend:
# - Looks for: startDate, start_date, endDate, end_date
# - Formats dates without timezone suffix (AMC requirement)
# - Defaults to 14-21 days ago if no dates provided

# CORRECT date handling (implemented in amc_api_client.py):
if not time_window_start or not time_window_end:
    # Account for AMC's 14-day data lag
    end_date = datetime.utcnow() - timedelta(days=14)  # 14 days ago
    start_date = end_date - timedelta(days=7)  # 21 days ago
    time_window_start = start_date.strftime('%Y-%m-%dT%H:%M:%S')  # No 'Z'!
    time_window_end = end_date.strftime('%Y-%m-%dT%H:%M:%S')

# Date format for AMC API - CRITICAL
# Use this format (without timezone):
params['timeWindowStart'] = '2025-07-15T00:00:00'
# NOT this (causes empty results or errors):
params['timeWindowStart'] = '2025-07-15T00:00:00Z'  # 'Z' breaks it!
```

#### Execution Status Polling (Added 2025-08-13)
```python
# Automatic status polling service runs every 15 seconds
# Updates pending/running executions from AMC API
# Located in: amc_manager/services/execution_status_poller.py

# Manual refresh available via API:
POST /api/executions/refresh-status/{execution_id}

# Polling only checks executions from last 2 hours to avoid old ones
# Status progression: pending -> running -> completed/failed

# Background service integration:
from amc_manager.services.execution_status_poller import ExecutionStatusPoller
poller = ExecutionStatusPoller()
poller.start()  # Starts background polling thread
```

#### Token Encryption and Management
```python
# Tokens are encrypted with Fernet before storage
# CRITICAL: Never change FERNET_KEY once tokens are stored
# If decryption fails, tokens are automatically cleared
# Users will be prompted to re-authenticate

# Token refresh service automatically:
# - Refreshes tokens before expiry (15-minute buffer)
# - Removes users with invalid tokens from tracking
# - Runs every 10 minutes
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

#### Execution Modal Components
```javascript
// CRITICAL: Two different components for execution details
// 1. AMCExecutionDetail - Primary component for viewing AMC executions
//    Location: frontend/src/components/executions/AMCExecutionDetail.tsx
//    Used in: Executions list, Instance workflows, anywhere AMC executions are shown
//    Features: Rerun, Refresh, Full execution details from AMC API, Chart visualization
//
// 2. ExecutionDetailModal - Legacy component for workflow executions
//    Location: frontend/src/components/workflows/ExecutionDetailModal.tsx  
//    Used in: Workflow detail page execution history
//    Features: Basic execution viewing

// AMCExecutionDetail expects workflowInfo.id for workflow ID:
const workflowId = execution?.workflowId || execution?.workflowInfo?.id;

// Execution parameters are at root level, not nested:
execution.executionParameters // Correct
execution.parameters // Wrong

// NEW: Auto-open new execution after rerun
<AMCExecutionDetail
  instanceId={instanceId}
  executionId={executionId}
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onRerunSuccess={(newExecutionId) => {
    // Automatically switch to new execution
    setExecutionId(newExecutionId);
  }}
/>

// View mode toggle for charts/table
const [viewMode, setViewMode] = useState<'table' | 'charts'>('table');
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
- `AMC_USE_REAL_API`: Always set to "true" for real AMC API calls
- `FERNET_KEY`: Encryption key for auth tokens (auto-generated if not set)

### Deployment (Railway)
- Uses Dockerfile for consistent builds
- Frontend built during Docker image creation
- Single container serves both frontend and backend
- Frontend files served from `/frontend/dist`

## Project Structure Updates

### Frontend Utilities
- **`/frontend/src/utils/`**:
  - `breadcrumbConfig.ts`: Breadcrumb route configuration and mapping
  - `dateUtils.ts`: Date formatting and manipulation utilities
  - `csvHelpers.ts`: CSV data transformation utilities (if exists)

### Common Components
- **`/frontend/src/components/common/`**:
  - `AppLogo.tsx`: Application logo component
  - `AuthStatusBanner.tsx`: Authentication disconnection warning banner
  - `Breadcrumb.tsx`: Dynamic breadcrumb navigation
  - `BrandSelector.tsx`: Brand selection with autocomplete
  - `BrandTag.tsx`: Brand display tag component
  - `DateRangeSelector.tsx`: Date range picker for queries
  - `JSONEditor.tsx`: JSON editing with Monaco Editor
  - `LazyLoad.tsx`: Lazy loading wrapper component
  - `SQLEditor.tsx`: SQL editing with syntax highlighting
  - `SQLHighlight.tsx`: SQL syntax highlighting component

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

- **Real API Mode**: Always uses real AMC API (AMC_USE_REAL_API=true)
- **Development**: Use your own AMC instances for testing
- **Authentication**: Login with your Amazon Advertising account

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
- **403 on Execution Listing**: Token encryption key mismatch or invalid entity ID
  - Solution: Users need to re-authenticate in profile settings
- **404 on Query Templates**: Wrong API path
  - Solution: Use `/query-templates` not `/queries/templates`
- **AMC Execution Fails**: Date format must exclude timezone
  - Solution: Format dates as `YYYY-MM-DD` without `+00:00` suffix
- **Workflow ID Not Found**: Workflow ID truncation issue
  - Solution: Fixed - now uses full `workflow_id` field from database

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

### Token Issues
- **Token Decryption Failures**: Fernet key mismatch
  - Solution: Tokens automatically cleared, user prompted to re-authenticate
- **Token Refresh Errors**: Invalid tokens in refresh service
  - Solution: Service automatically removes users with invalid tokens from tracking

### Development Tips
- **Module Not Found in Backend**: Check imports match actual file structure
  - Example: `from ...services.query_template_service import QueryTemplateService`
- **JWT Decode Errors**: Use `jwt.DecodeError` not `jwt.JWTError`
- **CORS Issues**: Backend serves frontend in production, proxy in dev
- **CSV Results Processing**: Transform array format to objects for proper display
  - Use `transformCsvData` helper in `frontend/src/utils/csvHelpers.ts`
- **Local Variable Errors**: Check for duplicate imports shadowing module-level imports

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

### Documentation
- `/docs/ID_FIELD_REFERENCE.md` - Critical guide for database ID relationships
- `/docs/WORKFLOW_INSTANCE_BINDING.md` - Workflow instance binding and copy feature
- `/docs/EXECUTION_DETAILS_ENHANCEMENTS.md` - Rerun/refresh functionality in execution details
- `/docs/template-library-plan.md` - AMC query template system design

### Template Library Planning
- See `/docs/template-library-plan.md` for comprehensive AMC instructional query template system design
- Includes SP/DSP overlap analysis template
- 6-phase implementation roadmap

### Dependencies
- **Frontend**: See `frontend/package.json` for complete list
  - React 19.1.0 with React Router v7
  - TanStack Query v5 for server state management
  - Tailwind CSS with forms and typography plugins
  - Monaco Editor for code editing
  - Recharts for data visualization
  - React Window for virtualized lists
  - Lucide React for icons
  - Date-fns for date utilities
  - Axios for API calls
  - React Hook Form for form management
- **Backend**: See `requirements.txt`
  - FastAPI for API framework
  - Supabase for database and auth
  - Cryptography (Fernet) for token encryption
  - Boto3 for AWS services
  - Pandas for data processing

### Monitoring
- Check execution logs: `python scripts/check_execution_logs.py`
- Database performance: Apply indexes with `scripts/apply_performance_indexes.py`
- API performance: FastAPI automatic docs at `/docs`

### Recent Fixes and Enhancements

#### 2025-08-13
- **NEW FEATURE: Auto-Open Execution Modal After Rerun (AMP-17)**
  - Added `onRerunSuccess` callback prop to AMCExecutionDetail component
  - Modal automatically transitions to new execution after rerun
  - Smooth loading states with "Loading new execution..." message
  - Users no longer need to manually navigate to find new executions
- **NEW FEATURE: Breadcrumb Navigation (AMP-11)**
  - Added breadcrumb navigation across all pages
  - Dynamic route handling with instance/workflow name fetching
  - Clean UI with home icon and chevron separators
  - Components: `Breadcrumb.tsx` and `breadcrumbConfig.ts`
- **NEW FEATURE: Chart Visualization in Execution Details**
  - Added view mode toggle between "Table" and "Charts" in AMCExecutionDetail
  - Integration with DataVisualization component for automatic chart generation
  - Support for time series, bar charts, pie charts, and scatter plots
  - Key metrics cards with trend indicators
- **NEW FEATURE: Application Branding Update**
  - Added AppLogo component with PNG logo support
  - Graceful fallback to text branding if images fail to load
  - Logo files stored in `public/branding/` directory
  - Supports both wordmark and icon variants
- **CRITICAL FIX: AMC Execution Date Parameters**
  - Fixed queries returning 0 rows due to date parameter handling
  - API now properly extracts `startDate`/`endDate` from frontend
  - Defaults to 14-21 days ago to account for AMC's data lag
  - See `/docs/AMC_EXECUTION_FIX.md` for details
- **CRITICAL FIX: Execution Status Polling**
  - Added automatic status polling service (`ExecutionStatusPoller`)
  - Polls pending/running executions every 15 seconds
  - Fixed issue where all executions remained "pending" indefinitely
  - Added manual refresh endpoint: `/api/executions/refresh-status/{execution_id}`

#### 2025-01-13
- Added rerun and refresh buttons to AMCExecutionDetail modal
- Fixed workflow ID field mapping (workflowInfo.id vs workflowId)
- Resolved TypeScript compilation errors in execution components
- Enhanced execution viewing with one-click rerun capability
- See `/docs/EXECUTION_DETAILS_ENHANCEMENTS.md` for details

#### 2025-08-08
- Fixed workflow ID truncation causing execution failures
- Resolved 403 authorization errors from token encryption key mismatch
- Improved token refresh service to handle decryption failures gracefully
- Fixed local variable access errors from duplicate imports
- See `FIXES-2025-08-08.md` for detailed information