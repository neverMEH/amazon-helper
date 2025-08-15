# Architecture Documentation - RecomAMP

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TypeScript)                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐    │
│  │    Pages        │  │   Components    │  │    Services     │    │
│  │                 │  │                 │  │                 │    │
│  │ - QueryBuilder  │  │ - DataSources   │  │ - API Client    │    │
│  │ - DataSources   │  │ - SQLEditor     │  │ - Auth Service  │    │
│  │ - DataDetail    │  │ - FieldExplorer │  │ - Data Service  │    │
│  │ - MyQueries     │  │ - TOC           │  │ - Workflow      │    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │              State Management Layer                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │    │
│  │  │ React Query │  │ Context API │  │ SessionStore│       │    │
│  │  │ (Caching)   │  │ (Auth State)│  │ (Temp Data) │       │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘       │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │              Error Boundary & Monitoring                  │    │
│  │         (Graceful error handling & performance)           │    │
│  └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTPS + JWT + Token Refresh
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Security & Rate Limiting                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │ Rate Limiter│  │  Security   │  │    CORS     │  │  Request    ││
│  │  (SlowAPI)  │  │  Headers    │  │ Middleware  │  │ Validation  ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                             │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                Input Validation (Pydantic)                │     │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────┐  ┌─────────┐  │     │
│  │  │  Auth   │  │  Workflow   │  │Template │  │DataSrc  │  │     │
│  │  │ Schema  │  │   Schema    │  │ Schema  │  │ Schema  │  │     │
│  │  └─────────┘  └─────────────┘  └─────────┘  └─────────┘  │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                    API Routes Layer                       │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────┐ │     │
│  │  │  Auth   │ │Workflow │ │Template │ │DataSrc  │ │Exec │ │     │
│  │  │/api/auth│ │/api/wf  │ │/api/tmpl│ │/api/ds  │ │/api/│ │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────┘ │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                   Service Layer                            │     │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────┐ │     │
│  │  │  Database   │ │ AMC Client  │ │   Token     │ │ Data │ │     │
│  │  │  Service    │ │  + Retry    │ │   Service   │ │Source│ │     │
│  │  │             │ │             │ │             │ │      │ │     │
│  │  │ - Base CRUD │ │ - Execute   │ │ - Encrypt   │ │-Schema│ │     │
│  │  │ - Auto      │ │ - Monitor   │ │ - Decrypt   │ │-Fields│ │     │
│  │  │   Reconnect │ │ - Results   │ │ - Refresh   │ │-Search│ │     │
│  │  │ - 30min TTL │ │ - Retry401  │ │ - Validate  │ │-Filter│ │     │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────┘ │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                Background Services                         │     │
│  │  ┌─────────────────┐           ┌─────────────────┐        │     │
│  │  │ Token Refresh   │           │ Execution Poll  │        │     │
│  │  │ - Every 10min   │           │ - Every 15sec   │        │     │
│  │  │ - 15min buffer  │           │ - Auto cleanup  │        │     │
│  │  │ - Track users   │           │ - Status update │        │     │
│  │  └─────────────────┘           └─────────────────┘        │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        External Services                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │  Supabase   │  │   AMC API   │  │   Amazon    │  │   GitHub    ││
│  │ PostgreSQL  │  │             │  │    OAuth    │  │   (Docs)    ││
│  │             │  │- Workflows  │  │- Token Mgmt │  │             ││
│  │- Users      │  │- Executions │  │- Entity ID  │  │- Templates  ││
│  │- Workflows  │  │- Results    │  │- Refresh    │  │- Examples   ││
│  │- Instances  │  │- Schemas    │  │- Validation │  │- Schemas    ││
│  │- DataSources│  │- Test Exec  │  │             │  │             ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Critical Implementation Patterns

#### AMC ID Field Duality
The system manages two types of IDs that must be carefully handled:
```typescript
// AMC's actual instance ID (use for API calls)
instanceId: string  // e.g., "amcinstance123"

// Internal UUID (use for database relationships)  
id: string         // e.g., "550e8400-e29b-41d4-a716-446655440000"

// CORRECT: Use instanceId for AMC API
await amcApiClient.executeQuery(instance.instanceId, query)

// WRONG: Internal UUID causes 403 errors
await amcApiClient.executeQuery(instance.id, query)  // ✗
```

#### Token Auto-Refresh Architecture
```typescript
// Frontend: Request queuing during token refresh
let isRefreshing = false;
const failedQueue: QueuedRequest[] = [];

api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401 && !isRefreshing) {
      isRefreshing = true;
      // Queue all subsequent requests
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      });
    }
  }
);

// Backend: Automatic retry with fresh tokens
@execute_with_retry
async def api_call(instance_id, user_id, entity_id, ...):
    # Automatically retries with refreshed token on 401
```

#### Date Handling for AMC
```python
# AMC requires specific date format WITHOUT timezone
'2025-07-15T00:00:00'    # ✓ Correct
'2025-07-15T00:00:00Z'   # ✗ Causes empty results

# Account for 14-day data lag
end_date = datetime.utcnow() - timedelta(days=14)
start_date = end_date - timedelta(days=7)
```

#### JSON Field Parsing from Supabase
```python
def parse_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Supabase JSON array returns properly"""
    # Supabase returns JSON arrays as strings, need to parse
    if isinstance(data.get('tags'), str):
        try:
            data['tags'] = json.loads(data['tags'])
        except json.JSONDecodeError:
            data['tags'] = []
    return data
```

#### Frontend Component Communication
```tsx
// SessionStorage for cross-route communication
sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
  sql_query: example.sql_query,
  name: example.name,
  parameters: example.parameters || {}
}));

// QueryBuilder loads and immediately clears
const draft = sessionStorage.getItem('queryBuilderDraft');
if (draft) {
  setQueryState(JSON.parse(draft));
  sessionStorage.removeItem('queryBuilderDraft');  // Prevent stale data
}
```

### Recent Updates (2025-08-15)

#### Component Consolidation
- Merged DataSourceDetailV2 features into main DataSourceDetail
- Added two-panel layout with Table of Contents
- Integrated FieldExplorer for advanced field browsing
- Removed card view from DataSources (list view only)

#### Enhanced Error Handling
- Full-screen error viewer with structured/raw/SQL views
- One-click copy for all error sections
- Export error reports as JSON
- SQL compilation error extraction with line/column info

#### Data Sources Improvements
- Advanced filter builder with nested AND/OR conditions
- Compare mode for side-by-side schema comparison
- Command palette (Cmd+K) for fuzzy search
- Bulk export to JSON/CSV

#### Background Services Enhancement
- Token refresh every 10 minutes with 15-minute buffer
- Execution polling every 15 seconds with auto-cleanup
- Request queuing during token refresh
- Automatic fallback to workflow creation on 404

### 1. Frontend Layer

#### Component Structure
```
frontend/src/
├── components/           # UI Components
│   ├── ErrorBoundary.tsx    # Global error handling
│   ├── workflows/           # Workflow management
│   ├── instances/           # Instance management
│   └── query-templates/     # Template management
├── services/            # API communication
│   ├── api.ts              # Axios client with interceptors
│   ├── authService.ts      # Authentication logic
│   └── workflowService.ts  # Workflow operations
├── hooks/               # Custom React hooks
│   ├── useAuth.ts          # Authentication state
│   └── useWorkflow.ts      # Workflow operations
└── types/               # TypeScript definitions
```

#### State Management
- **React Query**: Server state caching and synchronization
- **Context API**: Global application state (auth, theme)
- **Local State**: Component-specific state

### 2. Security Middleware Layer

#### Rate Limiting Architecture
```python
# Configured per endpoint
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://"  # In-memory storage
)
```

#### Security Headers Middleware
- Applied to all HTTP responses
- Environment-specific configuration
- HSTS only in production

### 3. Backend API Layer

#### FastAPI Application Structure
```
amc_manager/
├── api/                 # API endpoints
│   └── supabase/           # Supabase-specific routes
│       ├── auth.py         # Authentication endpoints
│       ├── workflows.py    # Workflow CRUD
│       └── templates.py    # Template management
├── schemas/             # Pydantic models (NEW)
│   ├── auth.py            # Authentication validation
│   ├── workflow.py        # Workflow validation
│   └── template.py        # Template validation
├── services/            # Business logic
│   ├── db_service.py      # Database operations
│   ├── amc_execution_service.py  # AMC integration
│   └── token_service.py   # Token encryption
└── core/                # Core utilities
    ├── supabase_client.py # Database connection
    └── logger_simple.py   # Logging configuration
```

### 4. API Endpoints Overview

#### Authentication Endpoints
```
POST /api/auth/login          # Amazon OAuth login
POST /api/auth/refresh        # Refresh JWT token  
GET  /api/auth/user          # Current user info
POST /api/auth/logout        # Logout user
```

#### AMC Instance Management
```
GET    /api/instances        # List user instances
POST   /api/instances        # Create new instance
PUT    /api/instances/{id}   # Update instance details
DELETE /api/instances/{id}   # Delete instance
```

#### Workflow Management
```
GET    /api/workflows        # List user workflows
POST   /api/workflows        # Create workflow
PUT    /api/workflows/{id}   # Update workflow
DELETE /api/workflows/{id}   # Delete workflow
POST   /api/workflows/{id}/execute  # Execute workflow
POST   /api/workflows/{id}/sync     # Sync to AMC
```

#### Execution Management
```
GET    /api/executions       # List executions
GET    /api/executions/{id}  # Get execution details
GET    /api/executions/{id}/status   # Check status
GET    /api/executions/{id}/results  # Get results
POST   /api/executions/{id}/cancel   # Cancel execution
```

#### Data Source Management
```
GET    /api/data-sources     # List AMC schemas
GET    /api/data-sources/{id}         # Get schema details
GET    /api/data-sources/search       # Search schemas
GET    /api/data-sources/compare      # Compare schemas
GET    /api/data-sources/categories   # List categories
```

#### Query Template Management
```
GET    /api/query-templates           # List templates
GET    /api/query-templates/{id}      # Get template
POST   /api/query-templates/{id}/create-workflow  # Create from template
```

### 5. Service Layer Architecture

#### Database Service Pattern
```python
class DatabaseService:
    def __init__(self):
        self._client: Optional[Client] = None
        self._connection_timeout_minutes = 30
    
    @property
    def client(self) -> Client:
        # Auto-reconnect after timeout
        if self._needs_refresh():
            self._client = SupabaseManager.get_client()
        return self._client
    
    @with_connection_retry
    def get_user(self, user_id: str):
        # Automatic retry on connection errors
        return self.client.table('users').select('*').eq('id', user_id).execute()
```

#### Token Service Architecture
```python
class TokenService:
    def __init__(self):
        self.fernet = Fernet(key)  # Symmetric encryption
    
    def encrypt_token(self, token: str) -> str:
        # Encrypt for storage
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted: str) -> str:
        # Decrypt for use
        return self.fernet.decrypt(encrypted.encode()).decode()
```

### 5. Data Flow Architecture

#### Request Flow
```
1. User Action (Frontend)
   ↓
2. API Request (Axios + JWT)
   ↓
3. Rate Limit Check (slowapi)
   ↓
4. Security Headers (Middleware)
   ↓
5. JWT Validation (Auth Dependency)
   ↓
6. Input Validation (Pydantic Schema)
   ↓
7. Business Logic (Service Layer)
   ↓
8. Database Operation (Supabase)
   ↓
9. Response Transformation
   ↓
10. Client Response (with caching)
```

#### Error Flow
```
1. Error Occurs
   ↓
2. Exception Caught
   ↓
3. Error Logged (with context)
   ↓
4. HTTPException Raised (sanitized message)
   ↓
5. Frontend Error Handler
   ↓
6. Error Boundary (if component error)
   ↓
7. User-Friendly Message
```

## Database Architecture

### Schema Design
```sql
-- Core Tables
users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE,
    auth_tokens TEXT,  -- Encrypted OAuth tokens
    created_at TIMESTAMP
)

workflows (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    name VARCHAR,
    sql_query TEXT,  -- With {{parameter}} placeholders
    parameters JSONB,
    instance_id UUID REFERENCES amc_instances,
    created_at TIMESTAMP
)

workflow_executions (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows,
    status VARCHAR,  -- pending, running, completed, failed
    amc_execution_id VARCHAR,
    result_data JSONB,
    created_at TIMESTAMP
)

query_templates (
    template_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    sql_template TEXT,
    parameters_schema JSONB,
    is_public BOOLEAN,
    usage_count INTEGER
)
```

### Performance Indexes
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Workflow queries
CREATE INDEX idx_workflows_user_id ON workflows(user_id);
CREATE INDEX idx_workflows_instance_id ON workflows(instance_id);

-- Execution tracking
CREATE INDEX idx_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_status ON workflow_executions(status);

-- Template search
CREATE INDEX idx_templates_category ON query_templates(category);
CREATE INDEX idx_templates_public ON query_templates(is_public);
```

## Security Architecture

### Authentication Flow
```
1. User Login
   ↓
2. Credentials Validation
   ↓
3. JWT Token Generation (24h expiry)
   ↓
4. Token Sent to Client
   ↓
5. Client Stores Token (localStorage)
   ↓
6. Token Sent with Each Request (Bearer)
   ↓
7. Server Validates Token
   ↓
8. User Context Extracted
```

### Encryption Architecture
```
OAuth Tokens:
Raw Token → Fernet Encryption → Encrypted Token → Database

API Requests:
JWT Token → Bearer Header → HTTPS Transport → Server Validation

Database:
Application → SSL/TLS Connection → Supabase → PostgreSQL
```

## Deployment Architecture

### Container Structure
```dockerfile
# Single container serves both frontend and backend
/app/
├── main_supabase.py      # FastAPI application
├── amc_manager/          # Backend code
├── frontend/
│   └── dist/            # Built React app
└── requirements.txt      # Python dependencies
```

### Production Configuration
```
Environment Variables:
- ENVIRONMENT=production
- JWT_SECRET_KEY=<secure-random>
- FERNET_KEY=<encryption-key>
- ALLOWED_ORIGINS=https://app.domain.com
- SUPABASE_URL=<project-url>
- SUPABASE_ANON_KEY=<public-key>
- SUPABASE_SERVICE_ROLE_KEY=<service-key>
```

## Scalability Considerations

### Horizontal Scaling
- Stateless API design allows multiple instances
- Session data stored in database
- Rate limiting uses shared Redis (optional)

### Performance Optimization
- Database connection pooling
- Query result caching (React Query)
- Gzip compression for responses
- Virtual scrolling for large datasets
- Lazy loading of components

### Monitoring Points
- API response times
- Database query performance
- Error rates by endpoint
- Rate limit violations
- Token refresh failures

## Integration Points

### External Services
1. **Supabase**: Database and authentication
2. **Amazon AMC API**: Query execution
3. **Amazon OAuth**: User authentication
4. **AWS S3**: Result storage (via AMC)

### Webhook Support
- Execution completion notifications
- Error alerting
- Status updates

## Development Workflow

### Local Development
```bash
# Backend
python main_supabase.py  # Port 8001

# Frontend
cd frontend && npm run dev  # Port 5173

# Both
./start_services.sh
```

### Testing Architecture
```
Unit Tests → Integration Tests → E2E Tests
    ↓              ↓                ↓
  Services    API Endpoints    User Flows
```

### CI/CD Pipeline
```
1. Code Push
2. Automated Tests
3. Security Scanning
4. Build Docker Image
5. Deploy to Staging
6. Run E2E Tests
7. Deploy to Production
8. Monitor Deployment
```

## Future Architecture Enhancements

### Planned Improvements
1. **Caching Layer**: Redis for session and query caching
2. **Message Queue**: Celery for async execution
3. **Websockets**: Real-time execution updates
4. **Microservices**: Separate execution service
5. **API Gateway**: Kong or AWS API Gateway

### Scaling Path
```
Current: Monolith
    ↓
Phase 1: Separate Frontend CDN
    ↓
Phase 2: Containerized Services
    ↓
Phase 3: Kubernetes Orchestration
    ↓
Phase 4: Microservices Architecture
```