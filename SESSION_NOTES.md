# Session Notes - AMC Manager Development

## Date: 2025-08-05

### Overview
This session focused on transforming the AMC Manager application's query and workflow management system to align with Amazon's official AMC Workflow Management Service API v3.0 specification. We replaced the existing Query Templates and Workflows UI with a professional AMC Query Builder interface.

## Major Changes Implemented

### 1. Frontend Query Builder Transformation
**Previous State**: Basic workflow list and template management
**New Implementation**: Professional 3-step AMC Query Builder wizard

#### New Components Created:
- **QueryLibrary** (`/frontend/src/pages/QueryLibrary.tsx`)
  - Replaced QueryTemplates component
  - Category-based template browsing
  - Search and filter functionality
  - Template cards with usage statistics

- **QueryBuilder** (`/frontend/src/pages/QueryBuilder.tsx`)
  - 3-step wizard interface
  - Step 1: Query Editor with schema browser
  - Step 2: Configuration (instance, parameters, export)
  - Step 3: Review and Execute
  - Handles both new queries and editing existing ones

- **MyQueries** (`/frontend/src/pages/MyQueries.tsx`)
  - Replaced Workflows list
  - Shows saved queries with sync status
  - Quick actions: execute, edit, schedule, delete
  - Displays last execution time and status

#### Query Builder Sub-components:
- **QueryEditorStep** (`/frontend/src/components/query-builder/QueryEditorStep.tsx`)
  - Monaco SQL editor with syntax highlighting
  - Collapsible AMC schema browser
  - Real-time parameter detection (`{{parameter}}` syntax)
  - Table and field exploration with icons

- **QueryConfigurationStep** (`/frontend/src/components/query-builder/QueryConfigurationStep.tsx`)
  - Instance selection with sandbox indicator
  - Timezone configuration
  - Dynamic parameter value input
  - Export settings (format, email, password protection)
  - Advanced options (data gaps, threshold columns)

- **QueryReviewStep** (`/frontend/src/components/query-builder/QueryReviewStep.tsx`)
  - Configuration summary cards
  - Cost and runtime estimation
  - Parameter substitution preview
  - Final SQL with replaced values
  - Warning notifications

### 2. AMC Schema Integration
Created comprehensive AMC table definitions (`/frontend/src/constants/amcSchema.ts`):
- **Categories**: Campaign Data, Product Data, User Data, Aggregated Data
- **Tables with full field definitions**:
  - amazon_attributed_events
  - amazon_campaign_hourly_metrics
  - amazon_dsp_events
  - amazon_dsp_impressions
  - amazon_dsp_clicks
  - amazon_dsp_purchases
  - And 15+ more tables
- Field type icons and descriptions
- Collapsible category navigation

### 3. Backend API Alignment with AMC Specification

#### Workflow Creation/Update Enhancement:
- Added `outputFormat` parameter (CSV, PARQUET, JSON)
- Proper distinction between saved workflows and ad-hoc queries
- AMC workflow ID generation following Amazon's rules (alphanumeric + periods, dashes, underscores)

#### Execution Flow Improvements:
- **Saved Workflows**: Pass `workflowId` and `parameterValues` separately (not substituted locally)
- **Ad-hoc Queries**: Pass full SQL with parameters already substituted
- Both modes include output format specification

### 4. Database Enhancements

#### New Migration (`09_amc_workflow_tracking.sql`):
```sql
ALTER TABLE workflows
ADD COLUMN amc_workflow_id TEXT,
ADD COLUMN is_synced_to_amc BOOLEAN DEFAULT false,
ADD COLUMN amc_sync_status TEXT DEFAULT 'not_synced',
ADD COLUMN last_synced_at TIMESTAMP WITH TIME ZONE;
```

#### Connection Resilience:
- Added `@with_connection_retry` decorator to all sync database methods
- Handles Supabase 30-minute timeout automatically
- Forces reconnection and retries on "Server disconnected" errors

### 5. Bug Fixes Implemented

#### Issue 1: 403 Forbidden on Workflow Creation
- **Problem**: Frontend sending internal UUID instead of AMC instance ID
- **Fix**: Updated instance select to use `instanceId` instead of `id`
- **Files Modified**: 
  - `/frontend/src/components/query-builder/QueryConfigurationStep.tsx`
  - `/frontend/src/components/query-builder/QueryReviewStep.tsx`

#### Issue 2: SQL Editor Minimized/Not Visible
- **Problem**: Editor using percentage height without proper parent constraints
- **Fix**: Set fixed height of 450px and increased padding (p-6)
- **File Modified**: `/frontend/src/components/query-builder/QueryEditorStep.tsx`

#### Issue 3: Blank Screen After Query Execution
- **Problem**: Navigation to non-existent `/executions` route
- **Fix**: Navigate to `/workflows/{workflowId}` to show execution details
- **File Modified**: `/frontend/src/pages/QueryBuilder.tsx`

#### Issue 4: Server Disconnected Errors
- **Problem**: Supabase connection timing out after 30 minutes
- **Fix**: Added connection retry decorator to database service methods
- **File Modified**: `/frontend/src/services/db_service.py`

#### Issue 5: TypeScript Build Errors
- **Fixed Issues**:
  - Installed missing `date-fns` dependency
  - Removed unused imports
  - Fixed type annotations for RegExpMatchArray
  - Updated format types to uppercase (CSV, PARQUET, JSON)
  - Removed non-existent SQLEditor placeholder prop

### 6. Navigation Updates

#### Routes Structure:
```
/query-library          - Browse template library
/my-queries            - View saved queries (replaced /workflows)
/query-builder/new     - Create new query
/query-builder/template/:templateId - Create from template
/query-builder/edit/:workflowId    - Edit existing query
/workflows/:workflowId - View workflow details and executions
```

### 7. UI/UX Improvements

- **Multi-step Wizard Pattern**: Clear progression through query creation
- **Schema Browser**: Collapsible tree view of all AMC tables
- **Parameter Detection**: Automatic detection and highlighting
- **Real-time Validation**: Instance access checks, parameter validation
- **Cost Estimation**: Shows estimated runtime and costs
- **Sync Status Indicators**: Cloud icons showing AMC sync status
- **Responsive Design**: Proper spacing with increased padding

## Pending Issue to Fix

### Executions List 400 Error
**Error**: "Must provide either workflowId or minCreationTime"
**Location**: When fetching workflow executions
**Solution Needed**: Add workflowId parameter when calling list executions API

## Dependencies Added
- `date-fns`: For date formatting in execution history

## Environment Variables Used
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Public anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key
- `AMAZON_CLIENT_ID`: Amazon Advertising API client ID
- `AMAZON_CLIENT_SECRET`: Client secret for OAuth
- `AMC_USE_REAL_API`: Set to "true" for real AMC API calls
- `FERNET_KEY`: Encryption key for auth tokens

## Testing Notes
- Sandbox instances: `amchnfozgta` or `amcfo8abayq`
- Test user: nick@nevermeh.com
- Mock mode is default (AMC_USE_REAL_API=false)

## Next Steps
1. Fix the executions list 400 error by providing workflowId
2. Implement workflow scheduling functionality
3. Add execution results visualization
4. Implement template favorites functionality
5. Add workflow version history
6. Enhance error handling for AMC API errors

## Key Files Modified
- Frontend (18 files):
  - New pages: QueryLibrary, QueryBuilder, MyQueries
  - New components: QueryEditorStep, QueryConfigurationStep, QueryReviewStep
  - New constants: amcSchema, templateCategories
  - Modified: App.tsx, Layout.tsx
  
- Backend (5 files):
  - `/amc_manager/services/amc_api_client.py` - Added outputFormat
  - `/amc_manager/services/amc_execution_service.py` - Updated execution flow
  - `/amc_manager/services/db_service.py` - Added retry decorator
  - `/amc_manager/api/supabase/workflows.py` - Workflow sync logic
  - `/database/supabase/migrations/09_amc_workflow_tracking.sql` - New fields

## Git Commits Made
1. "feat: Align workflow execution with AMC API specification"
2. "fix: Resolve TypeScript errors and build issues"
3. "fix: Set fixed height for SQL editor to prevent minimized display"
4. "style: Increase padding around SQL editor for better spacing"
5. "fix: Fix 403 error when creating workflows - use correct instance ID"
6. "fix: Add connection retry decorator to sync database methods"
7. "fix: Fix blank screen after query execution - navigate to workflow detail"