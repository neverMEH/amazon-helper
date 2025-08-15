# Functionality Registry - RecomAMP

## Purpose
This registry serves as a searchable catalog of all implemented features, utilities, and capabilities to prevent code duplication and ensure consistent implementation across the codebase.

---

## Authentication & Authorization

### OAuth Token Management
- **Location**: `amc_manager/services/token_service.py`
- **Functions**: 
  - `encrypt_tokens()` - Fernet encryption for secure token storage
  - `decrypt_tokens()` - Safe token decryption with error handling
  - `update_user_tokens()` - Store encrypted tokens in database
  - `get_user_tokens()` - Retrieve and decrypt user tokens
- **Used By**: All AMC API operations, token refresh service

### Token Auto-Refresh
- **Location**: `amc_manager/services/token_refresh_service.py`
- **Functions**:
  - `TokenRefreshService.start()` - Background service initialization
  - `refresh_user_tokens()` - Refresh OAuth tokens before expiry
  - `track_active_users()` - Monitor users with valid tokens
- **Schedule**: Every 10 minutes
- **Buffer**: 15 minutes before expiration

### AMC API Client with Retry
- **Location**: `amc_manager/services/amc_api_client_with_retry.py`
- **Functions**:
  - `execute_with_retry()` - Automatic token refresh on 401 errors
  - `create_workflow_execution()` - Create AMC execution with retry
  - `get_execution_status()` - Check execution status with retry
- **Pattern**: Decorator-based retry mechanism

---

## AMC Instance Management

### Instance CRUD Operations
- **Location**: `amc_manager/services/instance_service.py`
- **Functions**:
  - `create_instance()` - Create new AMC instance
  - `update_instance()` - Update instance details
  - `get_user_instances()` - List user's instances
  - `delete_instance()` - Remove instance
- **Features**: Brand tagging, entity ID management

### Brand Management
- **Location**: `amc_manager/services/brand_service.py`
- **Functions**:
  - `get_all_brands()` - Retrieve unique brand list
  - `update_instance_brands()` - Update brand associations
  - `filter_by_brands()` - Filter campaigns by brand
- **Storage**: PostgreSQL array field

---

## Workflow Management

### Workflow CRUD
- **Location**: `amc_manager/services/workflow_service.py`
- **Functions**:
  - `create_workflow()` - Create workflow with auto-generated ID
  - `sync_to_amc()` - Sync workflow to AMC API
  - `update_workflow()` - Update workflow SQL and parameters
  - `delete_workflow()` - Soft/hard delete workflow
- **ID Format**: `wf_XXXXXXXX` (8 random chars)

### Workflow Execution
- **Location**: `amc_manager/services/amc_execution_service.py`
- **Functions**:
  - `create_execution()` - Initialize workflow execution
  - `poll_execution_status()` - Check execution progress
  - `fetch_execution_results()` - Retrieve query results
  - `handle_execution_error()` - Parse AMC error responses
- **Error Parsing**: Extracts SQL compilation errors with line/column info

### Execution Status Polling
- **Location**: `amc_manager/services/execution_status_poller.py`
- **Functions**:
  - `ExecutionStatusPoller.start()` - Background polling service
  - `poll_pending_executions()` - Update execution statuses
  - `auto_cleanup()` - Remove completed from polling
- **Schedule**: Every 15 seconds

---

## Data Source Management

### Schema Documentation
- **Location**: `amc_manager/services/data_source_service.py`
- **Functions**:
  - `get_all_data_sources()` - List AMC schemas with fields
  - `get_data_source_by_schema_id()` - Get specific schema
  - `search_data_sources()` - Fuzzy search schemas
  - `get_schema_fields()` - Get field definitions
  - `parse_json_fields()` - Handle Supabase JSON arrays
- **Features**: Category filtering, tag management, field explorer

### Query Template Library
- **Location**: `amc_manager/services/query_template_service.py`
- **Functions**:
  - `get_templates()` - List query templates
  - `get_template_by_id()` - Get specific template
  - `create_from_template()` - Generate workflow from template
  - `detect_parameters()` - Extract {{param}} placeholders
- **Categories**: Attribution, Audience, Performance, Custom

---

## Query Building & Execution

### SQL Query Builder
- **Location**: `amc_manager/services/query_builder.py`
- **Functions**:
  - `build_query()` - Construct SQL from components
  - `validate_query()` - Check SQL syntax
  - `extract_parameters()` - Find parameter placeholders
  - `apply_parameters()` - Replace placeholders with values
- **Validation**: AMC-specific SQL rules

### Test Execution
- **Location**: `amc_manager/services/amc_api_client.py`
- **Functions**:
  - `test_execute_query()` - Ad-hoc query execution
  - `validate_date_format()` - Ensure AMC date compatibility
  - `handle_empty_results()` - Process no-data responses
- **Date Format**: `YYYY-MM-DDTHH:MM:SS` (no timezone)

---

## Campaign Management

### Campaign Filtering
- **Location**: `amc_manager/services/campaign_service.py`
- **Functions**:
  - `get_campaigns()` - List campaigns with filters
  - `filter_by_brand()` - Brand-based filtering
  - `get_campaign_metrics()` - Performance metrics
- **Integration**: Works with brand associations

---

## Database Operations

### Base Database Service
- **Location**: `amc_manager/services/db_service.py`
- **Alias**: `SupabaseService`
- **Functions**:
  - `ensure_connection()` - Auto-reconnect every 30 minutes
  - `execute_query()` - Run PostgreSQL queries
  - `handle_connection_error()` - Reconnection logic
- **Pattern**: All services inherit from this base class

### Data Analysis
- **Location**: `amc_manager/services/data_analysis_service.py`
- **Functions**:
  - `analyze_results()` - Process query results
  - `generate_insights()` - Create data insights
  - `export_results()` - Export to CSV/JSON
- **Features**: Statistical analysis, trend detection

---

## Frontend Services

### API Client
- **Location**: `frontend/src/services/api.ts`
- **Functions**:
  - `setupInterceptors()` - Request/response interceptors
  - `queueRequest()` - Queue during token refresh
  - `processQueue()` - Execute queued requests
  - `handleTokenRefresh()` - Frontend token refresh
- **Features**: Automatic retry, request queuing

### Data Source Service
- **Location**: `frontend/src/services/dataSourceService.ts`
- **Functions**:
  - `getDataSources()` - Fetch with caching
  - `getDataSourceDetail()` - Get schema details
  - `searchDataSources()` - Fuzzy search
  - `compareDataSources()` - Side-by-side comparison

### Workflow Service
- **Location**: `frontend/src/services/workflowService.ts`
- **Functions**:
  - `createWorkflow()` - Create new workflow
  - `executeWorkflow()` - Start execution
  - `getExecutionStatus()` - Poll status
  - `getExecutionResults()` - Fetch results

---

## UI Components

### Query Builder Components
- **Location**: `frontend/src/components/query-builder/`
- **Components**:
  - `QueryBuilderStep1.tsx` - Basic info input
  - `QueryBuilderStep2.tsx` - SQL editor with Monaco
  - `QueryBuilderStep3.tsx` - Parameter configuration
  - `TestExecutionButton.tsx` - Test query execution
- **Features**: 3-step wizard, parameter detection

### Data Source Components
- **Location**: `frontend/src/components/data-sources/`
- **Components**:
  - `DataSourceList.tsx` - List view with filtering
  - `DataSourcePreview.tsx` - Side panel preview
  - `TableOfContents.tsx` - Scroll-synced navigation
  - `FieldExplorer.tsx` - Advanced field browser
  - `FilterBuilder.tsx` - AND/OR condition builder
- **Features**: Multi-select, bulk actions, advanced filtering

### Execution Components
- **Location**: `frontend/src/components/executions/`
- **Components**:
  - `ExecutionStatus.tsx` - Status indicators
  - `ExecutionResults.tsx` - Result display
  - `ErrorDetailsModal.tsx` - Full error viewer
  - `ResultsViewer.tsx` - Inline/modal results
- **Features**: Live polling, error parsing, export

### Common Components
- **Location**: `frontend/src/components/common/`
- **Components**:
  - `SQLEditor.tsx` - Monaco editor wrapper
  - `LoadingSpinner.tsx` - Loading states
  - `ErrorMessage.tsx` - Error display
  - `ConfirmDialog.tsx` - Confirmation modals
  - `CommandPalette.tsx` - Cmd+K search

---

## Utility Functions

### Frontend Utilities
- **Location**: `frontend/src/utils/`
- **Functions**:
  - `formatDate()` - AMC date formatting
  - `parseError()` - Error message extraction
  - `debounce()` - Input debouncing
  - `copyToClipboard()` - One-click copy
  - `exportData()` - JSON/CSV export

### Backend Utilities
- **Location**: `amc_manager/core/`
- **Functions**:
  - `generate_workflow_id()` - Create unique IDs
  - `validate_entity_id()` - Entity ID validation
  - `parse_amc_error()` - AMC error parsing
  - `format_amc_date()` - Date formatting

---

## Background Services

### Token Refresh Service
- **Type**: Background service
- **Schedule**: Every 10 minutes
- **Purpose**: Refresh OAuth tokens before expiry
- **Location**: `amc_manager/services/token_refresh_service.py`

### Execution Status Poller
- **Type**: Background service
- **Schedule**: Every 15 seconds
- **Purpose**: Update pending execution statuses
- **Location**: `amc_manager/services/execution_status_poller.py`

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - Amazon OAuth login
- `POST /api/auth/refresh` - Refresh JWT token
- `GET /api/auth/user` - Current user info
- `POST /api/auth/logout` - Logout user

### AMC Instances
- `GET /api/instances` - List instances
- `POST /api/instances` - Create instance
- `PUT /api/instances/{id}` - Update instance
- `DELETE /api/instances/{id}` - Delete instance

### Workflows
- `GET /api/workflows` - List workflows
- `POST /api/workflows` - Create workflow
- `PUT /api/workflows/{id}` - Update workflow
- `DELETE /api/workflows/{id}` - Delete workflow
- `POST /api/workflows/{id}/execute` - Execute workflow
- `POST /api/workflows/{id}/sync` - Sync to AMC

### Executions
- `GET /api/executions` - List executions
- `GET /api/executions/{id}` - Get execution details
- `GET /api/executions/{id}/status` - Check status
- `GET /api/executions/{id}/results` - Get results

### Data Sources
- `GET /api/data-sources` - List schemas
- `GET /api/data-sources/{id}` - Get schema details
- `GET /api/data-sources/search` - Search schemas
- `GET /api/data-sources/compare` - Compare schemas

### Query Templates
- `GET /api/query-templates` - List templates
- `GET /api/query-templates/{id}` - Get template
- `POST /api/query-templates/{id}/create-workflow` - Create from template

---

## Error Handling Patterns

### AMC Error Parsing
- **400 Errors**: Extract SQL compilation errors
- **401 Errors**: Trigger token refresh
- **403 Errors**: Check entity ID and permissions
- **404 Errors**: Workflow not found, auto-recreate
- **500 Errors**: AMC service errors, retry logic

### Frontend Error Handling
- **Network Errors**: Display retry options
- **Validation Errors**: Inline field errors
- **API Errors**: Modal with details
- **Auth Errors**: Redirect to login

---

## Testing Utilities

### Backend Testing
- **Location**: `tests/`
- **Utilities**:
  - Mock AMC API responses
  - Supabase test fixtures
  - Token encryption tests
  - Service integration tests

### Frontend Testing
- **Location**: `frontend/tests/`
- **Utilities**:
  - Playwright E2E tests
  - Component unit tests
  - API mock handlers
  - Test data generators

---

## Configuration Management

### Environment Variables
- **Backend**: `.env` file processing
- **Frontend**: `import.meta.env` for Vite
- **Secrets**: Fernet key for encryption
- **API Keys**: Amazon OAuth credentials

### Feature Flags
- **AMC_USE_REAL_API**: Toggle mock/real AMC
- **ENABLE_BACKGROUND_SERVICES**: Control pollers
- **DEBUG_MODE**: Enhanced logging

---

## Security Features

### Token Encryption
- **Algorithm**: Fernet symmetric encryption
- **Storage**: Encrypted in database
- **Rotation**: Automatic refresh before expiry

### Input Validation
- **Backend**: Pydantic models
- **Frontend**: TypeScript types
- **SQL**: Parameter sanitization

### Rate Limiting
- **Tool**: SlowAPI
- **Default**: 100 requests/minute
- **Configurable**: Via environment variables

---

## Performance Optimizations

### Caching
- **Frontend**: React Query caching
- **Backend**: In-memory result caching
- **Database**: Query result caching

### Lazy Loading
- **Components**: Dynamic imports
- **Data**: Pagination support
- **Images**: Lazy image loading

### Connection Pooling
- **Database**: Supabase connection pool
- **API**: HTTP connection reuse

---

## Monitoring & Logging

### Application Logging
- **Backend**: Python logging module
- **Frontend**: Console logging with levels
- **Errors**: Structured error logging

### Performance Monitoring
- **Query Performance**: Execution time tracking
- **API Latency**: Response time logging
- **Background Services**: Health checks

---

## Data Export/Import

### Export Formats
- **JSON**: Full data export
- **CSV**: Tabular data export
- **SQL**: Query export

### Import Support
- **Query Templates**: JSON import
- **Workflows**: Bulk import
- **Results**: CSV import

---

## Usage Guidelines

1. **Before Creating New Functions**: Search this registry for existing implementations
2. **When Adding Features**: Update this registry immediately
3. **For Refactoring**: Check all "Used By" references
4. **During Code Review**: Verify no duplicate functionality

## Maintenance Notes

- Last Updated: 2025-08-15
- Total Functions: 150+
- Services: 23
- Components: 45+
- API Endpoints: 30+