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
  - `token_refresh_service.py`: Background service for automatic token refresh
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
```python
# Different IDs serve different purposes:
# 1. workflow_id: Internal DB identifier (wf_XXXXXXXX)
# 2. amc_workflow_id: AMC saved workflow ID
# 3. execution_id: Internal execution tracking (exec_XXXXXXXX)
# 4. amc_execution_id: AMC's execution ID for status polling

# CRITICAL: Use workflow['id'] (UUID) for backend operations
# Use workflow['workflow_id'] for AMC API calls
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

# Date format for AMC API - CRITICAL
# Use this format (without timezone):
params['minCreationTime'] = datetime.strftime('%Y-%m-%dT%H:%M:%S')
# NOT this (causes "Must provide either workflowId or minCreationTime" error):
params['minCreationTime'] = datetime.isoformat() + 'Z'
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

### Recent Fixes (2025-08-08)
- Fixed workflow ID truncation causing execution failures
- Resolved 403 authorization errors from token encryption key mismatch
- Improved token refresh service to handle decryption failures gracefully
- Fixed local variable access errors from duplicate imports
- See `FIXES-2025-08-08.md` for detailed information