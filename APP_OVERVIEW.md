# AMC Manager Application Overview

## Table of Contents
1. [Application Architecture](#application-architecture)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [API Documentation](#api-documentation)
5. [Database Schema](#database-schema)
6. [Authentication Flow](#authentication-flow)
7. [Development Guide](#development-guide)
8. [Deployment](#deployment)

## Application Architecture

AMC Manager is a full-stack application for managing Amazon Marketing Cloud (AMC) instances, creating SQL queries, and tracking campaign performance. It follows a three-tier architecture:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   Database      │
│   (React)       │     │   (FastAPI)     │     │   (Supabase)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Amazon AMC API  │
                        └─────────────────┘
```

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v7
- **State Management**: TanStack Query (React Query) v5
- **Styling**: Tailwind CSS with @tailwindcss/forms
- **UI Components**: Custom components with Lucide React icons
- **Code Editor**: Monaco Editor (VS Code editor)
- **Build Tool**: Vite
- **HTTP Client**: Axios with interceptors

### Backend
- **Framework**: FastAPI (Python)
- **Database ORM**: Supabase Python Client
- **Authentication**: JWT with Fernet encryption
- **Amazon Integration**: Custom AMC API client
- **Async Support**: asyncio for token management
- **Logging**: Python logging module

### Database
- **Provider**: Supabase (PostgreSQL)
- **Features**: Row Level Security, Real-time subscriptions
- **Migrations**: SQL migration files

## Project Structure

```
amazon-helper/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   │   ├── auth/       # Authentication components
│   │   │   ├── common/     # Shared components (editors, modals)
│   │   │   ├── query-builder/  # Query builder wizard steps
│   │   │   ├── instances/  # AMC instance management
│   │   │   ├── workflows/  # Workflow execution and history
│   │   │   └── campaigns/  # Campaign tracking
│   │   ├── pages/          # Page-level components
│   │   │   ├── QueryLibrary.tsx    # Template browsing
│   │   │   ├── QueryBuilder.tsx    # 3-step query wizard
│   │   │   └── MyQueries.tsx       # Saved queries list
│   │   ├── services/       # API services and utilities
│   │   ├── constants/      # Application constants
│   │   │   └── amcSchema.ts       # AMC table definitions
│   │   └── types/          # TypeScript type definitions
│   └── dist/               # Production build output
│
├── amc_manager/            # Backend Python application
│   ├── api/
│   │   └── supabase/      # API endpoints
│   │       ├── auth.py    # Authentication endpoints
│   │       ├── instances.py # Instance management
│   │       ├── workflows.py # Workflow CRUD and execution
│   │       └── query_templates.py # Template management
│   ├── core/              # Core utilities
│   │   ├── auth.py        # JWT authentication
│   │   ├── supabase_client.py # Database connection
│   │   └── logger_simple.py   # Logging configuration
│   └── services/          # Business logic services
│       ├── db_service.py  # Database operations
│       ├── amc_api_client.py # Amazon AMC API client
│       ├── amc_execution_service.py # Workflow execution
│       └── token_service.py # OAuth token management
│
├── database/
│   └── supabase/
│       └── migrations/    # SQL migration files
│
├── main_supabase.py      # FastAPI application entry point
├── CLAUDE.md             # AI assistant instructions
├── SESSION_NOTES.md      # Development session notes
└── APP_OVERVIEW.md       # This file
```

## API Documentation

### Base URL
- Development: `http://localhost:8001`
- Production: Configured via environment

### Authentication
All API endpoints (except login) require JWT authentication:
```
Authorization: Bearer <jwt_token>
```

### Main Endpoints

#### Authentication
```http
POST /api/auth/login
Body: { "email": "user@example.com", "password": "password" }
Response: { "token": "jwt_token", "user": {...} }
```

#### Workflows (Queries)
```http
GET /api/workflows
Get all user workflows

POST /api/workflows/
Create new workflow
Body: {
  "name": "Query Name",
  "description": "Description",
  "instance_id": "amc_instance_id",
  "sql_query": "SELECT ...",
  "parameters": {},
  "tags": []
}

GET /api/workflows/{workflow_id}
Get specific workflow details

PUT /api/workflows/{workflow_id}
Update workflow

DELETE /api/workflows/{workflow_id}
Delete workflow

POST /api/workflows/{workflow_id}/execute
Execute workflow
Body: {
  "parameter1": "value1",
  "output_format": "CSV"
}

POST /api/workflows/{workflow_id}/sync-to-amc
Sync workflow to Amazon AMC
```

#### AMC Instances
```http
GET /api/instances
Get all accessible instances

GET /api/instances/{instance_id}
Get instance details with stats

GET /api/instances/{instance_id}/campaigns
Get campaigns for instance
```

#### Query Templates
```http
GET /api/query-templates/
List all templates

GET /api/query-templates/{template_id}
Get template details

POST /api/query-templates/
Create new template

GET /api/query-templates/categories
Get available categories
```

#### Executions
```http
GET /api/executions
List all executions
Query params: workflow_id, min_creation_time

GET /api/executions/{execution_id}
Get execution details

GET /api/executions/{execution_id}/status
Check execution status
```

## Database Schema

### Core Tables

#### users
- `id` (UUID, PK): User identifier
- `email` (TEXT): User email
- `auth_tokens` (JSONB): Encrypted OAuth tokens
- `created_at` (TIMESTAMP): Account creation time

#### amc_instances
- `id` (UUID, PK): Internal identifier
- `instance_id` (TEXT): AMC instance ID
- `instance_name` (TEXT): Display name
- `region` (TEXT): AWS region
- `account_id` (UUID, FK): Link to amc_accounts

#### workflows
- `id` (UUID, PK): Internal identifier
- `workflow_id` (TEXT): Unique workflow ID (wf_xxxxx)
- `name` (TEXT): Workflow name
- `sql_query` (TEXT): AMC SQL query
- `parameters` (JSONB): Query parameters
- `instance_id` (UUID, FK): Associated instance
- `user_id` (UUID, FK): Owner
- `amc_workflow_id` (TEXT): AMC API workflow ID
- `is_synced_to_amc` (BOOLEAN): Sync status
- `amc_sync_status` (TEXT): Sync status details

#### workflow_executions
- `id` (UUID, PK): Internal identifier
- `execution_id` (TEXT): Unique execution ID
- `workflow_id` (UUID, FK): Associated workflow
- `status` (TEXT): pending/running/completed/failed
- `execution_parameters` (JSONB): Runtime parameters
- `results` (JSONB): Execution results
- `amc_execution_id` (TEXT): AMC API execution ID

#### query_templates
- `id` (UUID, PK): Internal identifier
- `template_id` (TEXT): Unique template ID
- `name` (TEXT): Template name
- `sql_template` (TEXT): Query with {{parameters}}
- `parameters_schema` (JSONB): Parameter definitions
- `category` (TEXT): Template category
- `is_public` (BOOLEAN): Visibility setting

## Authentication Flow

1. **User Login**
   - User provides email/password
   - Backend validates credentials with Supabase
   - JWT token generated and returned
   - Frontend stores token in localStorage

2. **Amazon OAuth (for AMC access)**
   - User initiates Amazon login
   - Redirected to Amazon OAuth
   - Callback returns access/refresh tokens
   - Tokens encrypted with Fernet and stored in database

3. **Token Refresh**
   - Access tokens expire after 1 hour
   - Automatic refresh using refresh token
   - New tokens encrypted and stored

## Development Guide

### Prerequisites
- Node.js 18+
- Python 3.9+
- Supabase account
- Amazon Advertising API credentials

### Environment Setup

1. **Backend Environment Variables**
```bash
# .env file
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx
AMAZON_CLIENT_ID=amzn1.application-oa2-client.xxxxx
AMAZON_CLIENT_SECRET=xxxxx
AMC_USE_REAL_API=false  # Set to true for real AMC calls
FERNET_KEY=xxxxx  # Auto-generated if not set
```

2. **Install Dependencies**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

3. **Start Development Servers**
```bash
# Backend (runs on port 8001)
python main_supabase.py

# Frontend (runs on port 5173)
cd frontend
npm run dev

# Or use the convenience script
./start_services.sh
```

### Common Development Tasks

#### Adding a New API Endpoint
1. Create route in `/amc_manager/api/supabase/[module].py`
2. Add service method in `/amc_manager/services/[service].py`
3. Update frontend API service in `/frontend/src/services/`
4. Add TypeScript types in `/frontend/src/types/`

#### Creating a Database Migration
1. Create SQL file in `/database/supabase/migrations/`
2. Name format: `XX_description.sql` (e.g., `10_add_favorites.sql`)
3. Run migration in Supabase dashboard

#### Testing
```bash
# Backend tests
pytest tests/

# Frontend type checking
npm run typecheck

# Frontend build test
npm run build

# E2E tests
npx playwright test
```

## Deployment

### Railway Deployment
The application is configured for Railway deployment using Docker:

1. **Dockerfile Configuration**
   - Multi-stage build for optimization
   - Frontend built during image creation
   - Single container serves both frontend and backend

2. **Environment Variables**
   Set in Railway dashboard:
   - All backend environment variables
   - `PORT` (automatically set by Railway)

3. **Deploy Command**
```bash
git push origin main
# Railway auto-deploys on push
```

### Manual Deployment
1. Build frontend: `npm run build`
2. Frontend files served from `/frontend/dist`
3. Backend serves static files and API
4. Configure reverse proxy for production

## API Usage Examples

### Create and Execute a Workflow
```javascript
// 1. Create workflow
const workflow = await api.post('/workflows/', {
  name: 'Campaign Analysis',
  instance_id: 'amc123',
  sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}}',
  parameters: { start_date: '2024-01-01' }
});

// 2. Execute workflow
const execution = await api.post(`/workflows/${workflow.data.workflow_id}/execute`, {
  start_date: '2024-06-01',
  output_format: 'CSV'
});

// 3. Check status
const status = await api.get(`/executions/${execution.data.execution_id}/status`);
```

### Query with Parameters
```sql
-- Template with parameters
SELECT 
  campaign_id,
  SUM(impressions) as total_impressions
FROM amazon_attributed_events
WHERE 
  event_dt >= '{{start_date}}'
  AND event_dt <= '{{end_date}}'
  AND brand IN ({{brand_list}})
GROUP BY campaign_id
HAVING total_impressions > {{min_impressions}}
```

## Troubleshooting

### Common Issues

1. **403 Forbidden on Workflow Creation**
   - Ensure using AMC instance ID, not internal UUID
   - Verify user has access to the instance

2. **Server Disconnected Errors**
   - Supabase connection timeout after 30 minutes
   - Automatic retry decorator handles reconnection

3. **Blank Screen After Execution**
   - Check browser console for route errors
   - Verify workflow detail page loads correctly

4. **Token Decryption Errors**
   - Fernet key mismatch
   - User needs to re-authenticate with Amazon

## Support and Documentation

- **API Documentation**: http://localhost:8001/docs (FastAPI auto-generated)
- **Supabase Dashboard**: Access via Supabase project URL
- **Amazon AMC Documentation**: https://advertising.amazon.com/API/docs/amc
- **Issues**: Report in GitHub repository

## Security Considerations

1. **Token Storage**: OAuth tokens encrypted with Fernet
2. **API Authentication**: JWT required for all endpoints
3. **Database Access**: Row Level Security enabled
4. **Secrets Management**: Never commit credentials
5. **CORS Configuration**: Configured for specific origins
6. **Input Validation**: SQL injection prevention
7. **Rate Limiting**: Implement for production