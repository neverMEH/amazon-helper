# Component Catalog - RecomAMP

## Purpose
Detailed inventory of all reusable components, their APIs, usage patterns, and integration guidelines for the RecomAMP application.

---

## Backend Services

### DatabaseService (SupabaseService)
**Location**: `amc_manager/services/db_service.py`

**Purpose**: Base class for all database operations with automatic reconnection

**API**:
```python
class DatabaseService:
    async def ensure_connection() -> None
    async def execute_query(query: str, params: dict) -> Any
    async def get_client() -> SupabaseClient
```

**Usage Pattern**:
```python
class MyService(DatabaseService):
    async def my_method(self):
        await self.ensure_connection()
        result = await self.execute_query(...)
```

**Key Features**:
- 30-minute automatic reconnection
- Connection pooling
- Error recovery
- Thread-safe operations

---

### TokenService
**Location**: `amc_manager/services/token_service.py`

**Purpose**: Secure token encryption and storage using Fernet

**API**:
```python
class TokenService:
    @staticmethod
    def encrypt_tokens(tokens: dict) -> str
    @staticmethod
    def decrypt_tokens(encrypted: str) -> dict
    async def update_user_tokens(user_id: str, tokens: dict) -> None
    async def get_user_tokens(user_id: str) -> Optional[dict]
```

**Dependencies**:
- cryptography.fernet
- DatabaseService

**Usage Example**:
```python
service = TokenService()
encrypted = service.encrypt_tokens({"access_token": "xxx"})
tokens = await service.get_user_tokens(user_id)
```

**Security Notes**:
- FERNET_KEY must remain consistent
- Tokens auto-clear on decryption failure
- Handles token rotation

---

### AMCAPIClient
**Location**: `amc_manager/services/amc_api_client.py`

**Purpose**: Direct AMC API integration with comprehensive error handling

**API**:
```python
class AMCAPIClient:
    async def create_workflow(instance_id: str, workflow: dict) -> dict
    async def execute_workflow(instance_id: str, workflow_id: str, params: dict) -> dict
    async def get_execution_status(instance_id: str, execution_id: str) -> dict
    async def get_execution_results(instance_id: str, execution_id: str) -> dict
    async def test_execute_query(instance_id: str, query: str, params: dict) -> dict
```

**Error Handling**:
- Parses AMC SQL compilation errors
- Extracts line/column information
- Handles 14-day data lag
- Date format validation

**Critical Patterns**:
```python
# CORRECT: Use instanceId for AMC API
await client.execute_workflow(instance.instanceId, ...)

# WRONG: Internal UUID causes 403
await client.execute_workflow(instance.id, ...)
```

---

### AMCAPIClientWithRetry
**Location**: `amc_manager/services/amc_api_client_with_retry.py`

**Purpose**: Enhanced AMC client with automatic token refresh on 401 errors

**API**:
```python
async def execute_with_retry(
    func: Callable,
    user_id: str,
    entity_id: str,
    *args,
    **kwargs
) -> Any
```

**Decorator Pattern**:
```python
@execute_with_retry
async def api_call(instance_id, user_id, entity_id, ...):
    # Automatic retry with refreshed token
    pass
```

**Features**:
- Automatic token refresh
- Max 2 retry attempts
- Preserves original errors
- User context tracking

---

### WorkflowService
**Location**: `amc_manager/services/workflow_service.py`

**Purpose**: Workflow lifecycle management with AMC synchronization

**API**:
```python
class WorkflowService(DatabaseService):
    async def create_workflow(data: WorkflowCreate) -> Workflow
    async def update_workflow(id: str, data: WorkflowUpdate) -> Workflow
    async def sync_to_amc(workflow_id: str, instance_id: str) -> dict
    async def delete_workflow(id: str, hard_delete: bool = False) -> None
    async def get_user_workflows(user_id: str) -> List[Workflow]
```

**Workflow ID Format**: `wf_XXXXXXXX` (8 random characters)

**Sync States**:
- `is_synced_to_amc`: Boolean flag
- `amc_workflow_id`: AMC's workflow identifier
- Auto-creates missing AMC workflows

---

### ExecutionService
**Location**: `amc_manager/services/amc_execution_service.py`

**Purpose**: Workflow execution management with comprehensive error handling

**API**:
```python
class ExecutionService(DatabaseService):
    async def create_execution(workflow_id: str, instance_id: str, params: dict) -> Execution
    async def poll_execution_status(execution_id: str) -> ExecutionStatus
    async def fetch_execution_results(execution_id: str) -> dict
    async def handle_execution_error(execution_id: str, error: dict) -> None
```

**Error Structure**:
```python
{
    "type": "SQL_COMPILATION_ERROR",
    "message": "Error message",
    "details": {
        "line": 5,
        "column": 10,
        "suggestion": "Check table name"
    }
}
```

---

### DataSourceService
**Location**: `amc_manager/services/data_source_service.py`

**Purpose**: AMC schema documentation and field management

**API**:
```python
class DataSourceService(DatabaseService):
    async def get_all_data_sources(filters: dict = None) -> List[DataSource]
    async def get_data_source_by_schema_id(schema_id: str) -> DataSource
    async def search_data_sources(query: str) -> List[DataSource]
    async def get_schema_fields(schema_id: str) -> List[SchemaField]
    def parse_json_fields(data: dict) -> dict
```

**JSON Parsing Pattern**:
```python
# Handles Supabase JSON array returns
if isinstance(data.get('tags'), str):
    data['tags'] = json.loads(data['tags'])
```

**Features**:
- Category filtering
- Tag management
- Field type documentation
- Example queries

---

### Background Services

#### TokenRefreshService
**Location**: `amc_manager/services/token_refresh_service.py`

**Purpose**: Background service for automatic token refresh

**API**:
```python
class TokenRefreshService:
    async def start() -> None
    async def stop() -> None
    async def refresh_all_tokens() -> None
    def get_active_users() -> List[str]
```

**Configuration**:
- Interval: 10 minutes
- Buffer: 15 minutes before expiry
- Auto-start on app launch

#### ExecutionStatusPoller
**Location**: `amc_manager/services/execution_status_poller.py`

**Purpose**: Background polling for execution status updates

**API**:
```python
class ExecutionStatusPoller:
    async def start() -> None
    async def stop() -> None
    async def poll_pending_executions() -> None
    def add_execution(execution_id: str) -> None
    def remove_execution(execution_id: str) -> None
```

**Configuration**:
- Interval: 15 seconds
- Auto-cleanup on completion
- Concurrent polling support

---

## Frontend Components

### Core Components

#### SQLEditor
**Location**: `frontend/src/components/common/SQLEditor.tsx`

**Purpose**: Monaco Editor wrapper for SQL editing

**Props**:
```typescript
interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: string;  // MUST be pixels for Monaco
  readOnly?: boolean;
  language?: 'sql' | 'json';
  theme?: 'vs-dark' | 'vs-light';
  onMount?: (editor: any) => void;
}
```

**Usage**:
```tsx
<SQLEditor
  value={query}
  onChange={setQuery}
  height="400px"  // Critical: explicit pixel height
  language="sql"
/>
```

**Known Issues**:
- Requires explicit pixel heights
- May fail in flex containers without min-height

---

#### DataTable
**Location**: `frontend/src/components/common/DataTable.tsx`

**Purpose**: Reusable data table with sorting and pagination

**Props**:
```typescript
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  onSort?: (field: string, direction: 'asc' | 'desc') => void;
  onPageChange?: (page: number) => void;
  totalPages?: number;
  currentPage?: number;
  loading?: boolean;
}
```

**Features**:
- Column sorting
- Pagination
- Loading states
- Custom cell renderers

---

### Query Builder Components

#### QueryBuilderWizard
**Location**: `frontend/src/components/query-builder/`

**Components**:
1. **QueryBuilderStep1**: Basic information
2. **QueryBuilderStep2**: SQL editor with schema browser
3. **QueryBuilderStep3**: Parameter configuration

**Shared State**:
```typescript
interface QueryBuilderState {
  name: string;
  description: string;
  sql_query: string;
  parameters: Record<string, any>;
  instance_id: string;
}
```

**Parameter Detection**:
```typescript
// Automatically detects {{param}} placeholders
const params = detectParameters(sqlQuery);
```

---

#### TestExecutionButton
**Location**: `frontend/src/components/query-builder/TestExecutionButton.tsx`

**Purpose**: Test query execution without saving

**Props**:
```typescript
interface TestExecutionProps {
  query: string;
  parameters: Record<string, any>;
  instanceId: string;
  onSuccess?: (results: any) => void;
  onError?: (error: any) => void;
}
```

---

### Data Source Components

#### DataSourceList
**Location**: `frontend/src/components/data-sources/DataSourceList.tsx`

**Purpose**: List view with filtering and selection

**Props**:
```typescript
interface DataSourceListProps {
  dataSources: DataSource[];
  selectedIds: Set<string>;
  onSelect: (id: string) => void;
  onSelectAll: () => void;
  onPreview: (dataSource: DataSource) => void;
}
```

**Features**:
- Multi-select support
- Bulk actions
- Side panel preview
- Keyboard navigation

---

#### TableOfContents
**Location**: `frontend/src/components/data-sources/TableOfContents.tsx`

**Purpose**: Scroll-synced navigation for schema documentation

**Props**:
```typescript
interface TableOfContentsProps {
  sections: TOCSection[];
  activeSection: string;
  onSectionClick: (sectionId: string) => void;
}
```

**Scroll Sync Pattern**:
```typescript
useEffect(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      // Update active section based on viewport
    },
    { threshold: 0.5 }
  );
});
```

---

#### FieldExplorer
**Location**: `frontend/src/components/data-sources/FieldExplorer.tsx`

**Purpose**: Advanced field browsing with type filtering

**Props**:
```typescript
interface FieldExplorerProps {
  fields: SchemaField[];
  onFieldSelect?: (field: SchemaField) => void;
  filters?: {
    type?: string[];
    required?: boolean;
    searchTerm?: string;
  };
}
```

**Features**:
- Type-based filtering
- Search functionality
- Collapsible categories
- Field details panel

---

#### FilterBuilder
**Location**: `frontend/src/components/data-sources/FilterBuilder.tsx`

**Purpose**: Advanced filter construction with AND/OR conditions

**Props**:
```typescript
interface FilterBuilderProps {
  filters: FilterGroup;
  onChange: (filters: FilterGroup) => void;
  fields: FilterField[];
}

interface FilterGroup {
  operator: 'AND' | 'OR';
  conditions: (FilterCondition | FilterGroup)[];
}
```

---

### Execution Components

#### ExecutionStatus
**Location**: `frontend/src/components/executions/ExecutionStatus.tsx`

**Purpose**: Real-time execution status display

**Props**:
```typescript
interface ExecutionStatusProps {
  execution: Execution;
  polling?: boolean;
  onStatusChange?: (status: string) => void;
}
```

**Status Values**:
- `PENDING`: Queued for execution
- `RUNNING`: Currently executing
- `SUCCEEDED`: Completed successfully
- `FAILED`: Execution failed

---

#### ErrorDetailsModal
**Location**: `frontend/src/components/executions/ErrorDetailsModal.tsx`

**Purpose**: Comprehensive error display with multiple views

**Props**:
```typescript
interface ErrorDetailsModalProps {
  error: ExecutionError;
  isOpen: boolean;
  onClose: () => void;
}
```

**Views**:
1. **Structured**: Parsed error information
2. **Raw**: Original error response
3. **SQL**: Query with error highlighting

**Features**:
- One-click copy
- Export as JSON
- Line/column highlighting

---

#### ResultsViewer
**Location**: `frontend/src/components/executions/ResultsViewer.tsx`

**Purpose**: Query results display with export options

**Props**:
```typescript
interface ResultsViewerProps {
  results: any;
  mode: 'inline' | 'modal' | 'fullscreen';
  onExport?: (format: 'json' | 'csv') => void;
}
```

---

### Common UI Components

#### CommandPalette
**Location**: `frontend/src/components/common/CommandPalette.tsx`

**Purpose**: Cmd+K fuzzy search interface

**Props**:
```typescript
interface CommandPaletteProps {
  items: CommandItem[];
  onSelect: (item: CommandItem) => void;
  placeholder?: string;
}
```

**Keyboard Shortcuts**:
- `Cmd+K` / `Ctrl+K`: Open
- `Arrow Keys`: Navigate
- `Enter`: Select
- `Escape`: Close

---

#### ConfirmDialog
**Location**: `frontend/src/components/common/ConfirmDialog.tsx`

**Purpose**: Confirmation modal for destructive actions

**Props**:
```typescript
interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'warning' | 'info';
}
```

---

## Service Layer Components

### API Client
**Location**: `frontend/src/services/api.ts`

**Purpose**: Axios instance with interceptors and token management

**Configuration**:
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
});
```

**Interceptors**:
1. **Request**: Add auth headers
2. **Response**: Handle token refresh
3. **Error**: Queue requests during refresh

**Request Queuing Pattern**:
```typescript
let isRefreshing = false;
const failedQueue: QueuedRequest[] = [];

// During refresh, queue all requests
if (isRefreshing) {
  return new Promise((resolve, reject) => {
    failedQueue.push({ resolve, reject });
  });
}
```

---

### Service Modules

#### AuthService
**Location**: `frontend/src/services/authService.ts`

**API**:
```typescript
class AuthService {
  login(code: string): Promise<User>
  logout(): Promise<void>
  refreshToken(): Promise<string>
  getCurrentUser(): Promise<User>
}
```

#### WorkflowService
**Location**: `frontend/src/services/workflowService.ts`

**API**:
```typescript
class WorkflowService {
  create(data: WorkflowCreate): Promise<Workflow>
  update(id: string, data: WorkflowUpdate): Promise<Workflow>
  execute(id: string, params: ExecutionParams): Promise<Execution>
  getExecutionStatus(executionId: string): Promise<ExecutionStatus>
  getExecutionResults(executionId: string): Promise<any>
}
```

#### DataSourceService
**Location**: `frontend/src/services/dataSourceService.ts`

**API**:
```typescript
class DataSourceService {
  getAll(filters?: DataSourceFilters): Promise<DataSource[]>
  getById(id: string): Promise<DataSource>
  search(query: string): Promise<DataSource[]>
  compare(ids: string[]): Promise<ComparisonResult>
}
```

---

## Custom Hooks

### useAuth
**Location**: `frontend/src/hooks/useAuth.ts`

**Purpose**: Authentication state management

**API**:
```typescript
function useAuth() {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}
```

### useDebounce
**Location**: `frontend/src/hooks/useDebounce.ts`

**Purpose**: Debounce input values

**API**:
```typescript
function useDebounce<T>(value: T, delay: number = 500): T
```

### useInfiniteScroll
**Location**: `frontend/src/hooks/useInfiniteScroll.ts`

**Purpose**: Infinite scrolling for lists

**API**:
```typescript
function useInfiniteScroll(
  callback: () => void,
  options?: IntersectionObserverInit
): RefObject<HTMLElement>
```

---

## Type Definitions

### Core Types
**Location**: `frontend/src/types/`

```typescript
// User
interface User {
  id: string;
  email: string;
  name?: string;
  auth_tokens?: any;
}

// Workflow
interface Workflow {
  id: string;
  workflow_id: string;
  name: string;
  sql_query: string;
  parameters: Record<string, any>;
  is_synced_to_amc: boolean;
  amc_workflow_id?: string;
}

// Execution
interface Execution {
  id: string;
  workflow_id: string;
  amc_execution_id: string;
  status: ExecutionStatus;
  results?: any;
  error_details?: ErrorDetails;
}

// DataSource
interface DataSource {
  id: string;
  schema_id: string;
  name: string;
  category: string;
  description?: string;
  fields: SchemaField[];
  tags: string[];
}
```

---

## Integration Patterns

### Component Communication

#### Via Props
```tsx
// Parent to child
<ChildComponent data={data} onUpdate={handleUpdate} />
```

#### Via Context
```tsx
// Global state sharing
const ThemeContext = createContext<Theme>('light');
```

#### Via SessionStorage
```tsx
// Cross-route communication
sessionStorage.setItem('queryDraft', JSON.stringify(draft));
```

### Data Flow Patterns

#### Query Caching
```tsx
// React Query caching
const { data } = useQuery({
  queryKey: ['dataSource', id],
  queryFn: () => fetchDataSource(id),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

#### Optimistic Updates
```tsx
const mutation = useMutation({
  mutationFn: updateWorkflow,
  onMutate: async (newData) => {
    // Optimistically update cache
    queryClient.setQueryData(['workflow', id], newData);
  },
});
```

---

## Testing Patterns

### Component Testing
```tsx
describe('DataSourceList', () => {
  it('should render data sources', () => {
    render(<DataSourceList dataSources={mockData} />);
    expect(screen.getByText('Source 1')).toBeInTheDocument();
  });
});
```

### Service Testing
```typescript
describe('WorkflowService', () => {
  it('should create workflow', async () => {
    const result = await service.create(mockWorkflow);
    expect(result.workflow_id).toMatch(/^wf_/);
  });
});
```

---

## Performance Considerations

### Component Optimization
- Use `React.memo` for expensive renders
- Implement `useMemo` for computed values
- Apply `useCallback` for stable callbacks
- Lazy load heavy components

### Data Optimization
- Implement pagination for large lists
- Use virtual scrolling for long lists
- Cache API responses with React Query
- Debounce search inputs

---

## Maintenance Guidelines

1. **Component Updates**: Update this catalog when modifying component APIs
2. **Breaking Changes**: Document migration paths
3. **New Components**: Add complete documentation before merging
4. **Deprecation**: Mark deprecated components and provide alternatives

---

## Version History

- **v1.0.0** (2025-08-15): Initial catalog creation
- Components: 45+
- Services: 23
- Hooks: 8
- Types: 20+