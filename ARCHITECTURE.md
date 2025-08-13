# Architecture Documentation - Recom AMP

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Components │  │   Services   │  │    Hooks     │      │
│  │              │  │              │  │              │      │
│  │ - Workflows  │  │ - API Client │  │ - useAuth    │      │
│  │ - Instances  │  │ - Auth       │  │ - useQuery   │      │
│  │ - Templates  │  │ - Workflow   │  │ - useMutation│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Error Boundary Layer                   │    │
│  │         (Graceful error handling & recovery)        │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS + JWT Auth
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Security Middleware Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Rate Limiter │  │   Security   │  │     CORS     │      │
│  │   (slowapi)  │  │   Headers    │  │  Middleware  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                          │
│  ┌────────────────────────────────────────────────────┐      │
│  │            Input Validation Layer (Pydantic)        │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │      │
│  │  │   Auth   │  │ Workflow │  │   Template   │    │      │
│  │  │  Schema  │  │  Schema  │  │    Schema    │    │      │
│  │  └──────────┘  └──────────┘  └──────────────┘    │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │                  API Routes Layer                   │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │      │
│  │  │   Auth   │  │ Workflows│  │   Templates  │    │      │
│  │  │ /login   │  │ /api/    │  │ /api/query-  │    │      │
│  │  │ /refresh │  │ workflows│  │  templates   │    │      │
│  │  └──────────┘  └──────────┘  └──────────────┘    │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │                  Service Layer                      │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │      │
│  │  │   Database   │  │     AMC      │  │  Token  │ │      │
│  │  │   Service    │  │   Service    │  │ Service │ │      │
│  │  │              │  │              │  │         │ │      │
│  │  │ - User CRUD  │  │ - Execute    │  │ - Encrypt│ │      │
│  │  │ - Workflow   │  │ - Monitor    │  │ - Decrypt│ │      │
│  │  │ - Instance   │  │ - Results    │  │ - Refresh│ │      │
│  │  └──────────────┘  └──────────────┘  └─────────┘ │      │
│  └────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     External Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Supabase   │  │   AMC API    │  │    Amazon    │      │
│  │   Database   │  │              │  │     OAuth    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

## Component Architecture

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

### 4. Service Layer Architecture

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