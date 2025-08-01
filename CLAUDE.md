# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon Marketing Cloud (AMC) management application that helps users:
- Manage multiple AMC instances across different brands
- Build and execute AMC SQL queries using templates or custom parameters
- Track workflow executions and retrieve results
- Map campaign IDs to names with brand tagging
- Schedule recurring reports with CRON expressions

## Development Commands

### Quick Start
```bash
# Start both backend and frontend services
./start_services.sh

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
# Login: nick@nevermeh.com (no password required)
```

### Backend Development
```bash
# Run backend server (uses Supabase, not SQLAlchemy)
python main_supabase.py  # Runs on port 8001

# Run specific test
pytest tests/test_api_auth.py::test_login_success

# Code formatting and linting
black amc_manager/
flake8 amc_manager/
mypy amc_manager/
```

### Frontend Development
```bash
cd frontend
npm run dev      # Development server on port 5173
npm run build    # Production build with TypeScript checking
npm run lint     # ESLint checking

# E2E tests with Playwright
npx playwright test
```

### Database Operations
```bash
# Test Supabase connection
python test_supabase_simple.py

# Import initial data
python scripts/import_initial_data.py

# Apply performance indexes
python scripts/apply_performance_indexes.py

# Test workflow execution
python test_execution.py
python demo_execution.py  # Shows success/failure scenarios
```

## High-Level Architecture

### Backend Structure
- **FastAPI Application**: `main_supabase.py` serves API on port 8001
- **Service Layer Pattern**: All business logic in `amc_manager/services/`
  - Base class: `SupabaseService` handles connection retry logic
  - Key services: `WorkflowService`, `ExecutionService`, `AMCInstanceService`
- **Authentication**: JWT-based with token encryption via Fernet
- **API Client**: Custom AMC API client with rate limiting and automatic token refresh

### Frontend Architecture
- **React + TypeScript**: Using Vite for fast development
- **React Query**: Data fetching with 5-minute cache and automatic retries
- **Component Structure**:
  - `/instances`: Table view with clickable rows, brand tags
  - `/workflows`: Execution modal with real-time progress
  - `/campaigns`: Filtered by instance brands
- **API Proxy**: Vite proxies `/api` to backend during development

### Database Design (Supabase)
- **instance_brands**: Junction table for many-to-many brand associations
- **workflow_executions**: Tracks execution status with timezone-aware timestamps
- **Connection Handling**: Automatic reconnection after 30-minute timeout
- **Performance**: Optimized queries with joins to reduce round trips by 90%

### Critical AMC API Integration Details
```python
# MUST use entity ID as header, not query parameter
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-MarketplaceId': marketplace_id,
    'Amazon-Advertising-API-AdvertiserId': entity_id  # Critical!
}
```

### Deployment Configuration
- **Railway**: Uses Dockerfile for consistent builds
- **Environment Variables**:
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `AMC_USE_REAL_API`: Toggle real/mock execution
  - `AMAZON_CLIENT_ID`, `AMAZON_CLIENT_SECRET`: For OAuth
- **Single URL**: Frontend served from backend in production

## Key Implementation Notes

### Workflow Execution Flow
1. Frontend sends execution request with parameters
2. Backend creates execution record with "pending" status
3. Execution service (real or mock) processes the workflow
4. Status updates polled every 2 seconds by frontend
5. Results stored and downloadable as CSV

### Brand Tag System
- Brands directly associated with instances via `instance_brands` table
- Campaigns automatically filter based on instance brands
- BrandSelector component provides autocomplete search
- Changes persist immediately to database

### Performance Considerations
- Database queries use Supabase joins to minimize round trips
- React Query caches data for 5 minutes
- Gzip compression on API responses > 1KB
- Indexes on frequently queried columns (instance_id, user_id, status)

### Common Issues and Solutions
- **JWT Errors**: Use `jwt.DecodeError` instead of `jwt.JWTError`
- **Supabase Timeout**: Automatic reconnection implemented in `db_service.py`
- **AMC API 403**: Verify user has access to requested instance
- **Empty Results After Idle**: Frontend refetches on window focus

## Testing Strategy
- **Sandbox Instances**: Use `amchnfozgta` or `amcfo8abayq` for testing
- **Mock Execution**: Enabled by default for development
- **Real Execution**: Set `AMC_USE_REAL_API=true` in environment

