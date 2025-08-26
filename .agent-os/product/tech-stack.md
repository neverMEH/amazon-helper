# RecomAMP Technical Stack

> Last Updated: 2025-08-26
> Version: 2.0.0
> Status: Production

## Application Architecture

- **Pattern:** Full-stack web application with microservices background workers
- **Deployment:** Single-server with Docker containerization
- **Environment:** Production on Railway.app with PostgreSQL managed database

## Backend Stack

### Core Framework
- **Framework:** FastAPI 0.104+
- **Version:** Python 3.11
- **Pattern:** Async/await with dependency injection
- **API Documentation:** Automatic OpenAPI/Swagger generation

### Database & ORM
- **Primary Database:** PostgreSQL 15+ (Supabase managed)
- **Connection:** Supabase Python client with connection pooling
- **Migrations:** Manual SQL scripts with version tracking
- **Real-time:** Supabase real-time subscriptions for live updates

### Authentication & Security
- **OAuth Provider:** Amazon Advertising API OAuth 2.0
- **Token Storage:** Fernet symmetric encryption (AES-256)
- **Session Management:** JWT tokens with automatic refresh
- **Security:** Row Level Security (RLS) policies in Supabase

### External Integrations
- **Amazon APIs:**
  - Amazon Marketing Cloud (AMC) API
  - Amazon Advertising API v3
  - Selling Partner API (SP-API) integration planned
- **HTTP Client:** httpx with tenacity for retry logic
- **Rate Limiting:** Custom implementation with exponential backoff

### Background Services
- **Task Queue:** Custom async task system with croniter scheduling
- **Services:**
  - Token refresh service (10-minute intervals)
  - Execution status poller (15-second intervals)  
  - Schedule executor (60-second intervals)
- **Monitoring:** Structured logging with JSON formatting

## Frontend Stack

### Core Framework
- **Framework:** React 19.1.0
- **Language:** TypeScript 5.8 with strict mode
- **Build Tool:** Vite 6.0 with HMR and fast refresh
- **Bundle Analysis:** Built-in Vite bundle analyzer

### State Management & Data Fetching
- **Data Fetching:** TanStack Query v5 (React Query)
- **State:** React Context + useReducer for complex state
- **Caching Strategy:** Aggressive caching with background refetching
- **Optimistic Updates:** Enabled for mutations

### Routing & Navigation
- **Router:** React Router v7 with data loading
- **Navigation:** Programmatic navigation with type safety
- **Protected Routes:** Authentication-based route guards

### UI Framework & Styling
- **CSS Framework:** Tailwind CSS 3.4+
- **Components:** Custom component library with consistent design system
- **Icons:** Lucide React for consistent iconography
- **Responsive:** Mobile-first responsive design

### Code Editor & Advanced UI
- **Code Editor:** Monaco Editor (VS Code engine)
- **SQL Highlighting:** Custom SQL syntax highlighting and completion
- **Schema Integration:** Live AMC schema documentation
- **Tables:** TanStack Table v8 for advanced data grids

### Form Handling & Validation
- **Forms:** React Hook Form with resolver pattern
- **Validation:** Zod schema validation with TypeScript inference
- **Complex Forms:** Multi-step forms with state persistence

## Development & DevOps

### Package Management
- **Package Manager:** npm 10+ with exact version locking
- **Node Version:** Node.js 20 LTS
- **Dependency Strategy:** Minimal dependencies, prefer native solutions

### Code Quality & Standards
- **Type Checking:** TypeScript strict mode with verbatimModuleSyntax
- **Linting:** ESLint with TypeScript rules
- **Formatting:** Prettier with consistent configuration
- **Import Strategy:** Type-only imports where applicable

### Testing Framework
- **Unit Tests:** Pytest for Python, Jest for TypeScript (planned)
- **Integration Tests:** FastAPI TestClient with async support
- **E2E Tests:** Playwright (planned for critical user flows)
- **Coverage:** Target 80% backend coverage

### Build & Deployment
- **Container:** Docker with multi-stage builds
- **Platform:** Railway.app with automatic deployments
- **Environment:** Staging and production environments
- **Monitoring:** Railway metrics with custom alerting

### Development Tools
- **Environment:** Cross-platform development (Windows WSL2, macOS, Linux)
- **Database:** Local Supabase or remote development instance
- **Debugging:** Python debugger integration, React DevTools
- **Performance:** Chrome DevTools, Lighthouse auditing

## Infrastructure & External Services

### Database Configuration
- **Primary:** Supabase PostgreSQL with connection pooling
- **Indexes:** Optimized indexes for query performance
- **Backups:** Automated daily backups via Supabase
- **Scaling:** Connection pooling with pgbouncer

### File Storage & Assets
- **Static Assets:** Bundled with Vite, served via CDN
- **File Uploads:** Direct Supabase storage integration (planned)
- **Media Processing:** Client-side processing for CSV/JSON exports

### Monitoring & Analytics
- **Application Monitoring:** Custom logging with structured JSON
- **Error Tracking:** Console-based error tracking (Sentry planned)
- **Performance:** Web Vitals tracking via built-in browser APIs
- **Usage Analytics:** Privacy-focused internal tracking

### Environment Management
- **Configuration:** Environment variables with validation
- **Secrets:** Railway secret management
- **Feature Flags:** Environment-based feature toggling
- **Multi-Environment:** Development, staging, production separation

## Key Technical Decisions

### Database Choice: Supabase PostgreSQL
- **Rationale:** Managed PostgreSQL with real-time subscriptions, built-in auth, and RLS
- **Alternative Considered:** Raw PostgreSQL, PlanetScale MySQL
- **Benefits:** Reduced operational overhead, instant APIs, real-time capabilities

### Frontend Framework: React 19 + TypeScript
- **Rationale:** Team expertise, mature ecosystem, TypeScript for type safety
- **Alternative Considered:** Vue.js, Svelte
- **Benefits:** Strong typing, extensive library ecosystem, familiar patterns

### State Management: TanStack Query + Context
- **Rationale:** Server state vs client state separation, powerful caching
- **Alternative Considered:** Redux Toolkit, Zustand
- **Benefits:** Automatic background refetching, optimistic updates, cache management

### Code Editor: Monaco Editor
- **Rationale:** Full VS Code experience in browser, excellent SQL support
- **Alternative Considered:** CodeMirror, Ace Editor
- **Benefits:** Superior syntax highlighting, IntelliSense, familiar UX

### Deployment: Railway.app
- **Rationale:** Simple deployment, integrated database, good developer experience
- **Alternative Considered:** Vercel, Heroku, AWS
- **Benefits:** Zero-config deployment, integrated PostgreSQL, cost-effective

## Performance Considerations

### Backend Optimizations
- **Async Operations:** Full async/await pattern implementation
- **Connection Pooling:** Supabase automatic connection management
- **Query Optimization:** Indexed queries and efficient data fetching
- **Caching:** In-memory caching for frequently accessed data

### Frontend Optimizations
- **Code Splitting:** Route-based code splitting with React.lazy
- **Bundle Size:** Tree shaking and dynamic imports
- **Caching Strategy:** Aggressive TanStack Query caching
- **Image Optimization:** Modern formats and responsive images

### Database Optimizations
- **Indexing Strategy:** Compound indexes for common query patterns
- **Row Level Security:** Efficient RLS policies
- **Query Performance:** EXPLAIN ANALYZE for slow query identification
- **Connection Management:** Optimal connection pool sizing

## Security Implementation

### Data Protection
- **Encryption:** AES-256 for sensitive data at rest
- **Transport:** HTTPS/TLS 1.3 for all communications
- **Token Security:** Encrypted OAuth tokens with automatic rotation
- **Database Security:** RLS policies prevent unauthorized data access

### Authentication Flow
- **OAuth 2.0:** Amazon Advertising API integration
- **JWT Tokens:** Short-lived access tokens with refresh capability
- **Session Management:** Secure session handling with automatic cleanup
- **Multi-Factor:** OAuth provider handles MFA requirements

### API Security
- **Rate Limiting:** Custom implementation with exponential backoff
- **Input Validation:** Pydantic models for all API inputs
- **SQL Injection:** Parameterized queries and ORM usage
- **CORS:** Configured for specific origins only