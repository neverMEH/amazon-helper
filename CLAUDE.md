# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon Marketing Cloud (AMC) management application that helps users:
- Manage multiple AMC instances across different brands
- Build and execute AMC SQL queries using templates or custom parameters
- Track workflow executions and retrieve results
- Map campaign IDs to names with brand tagging
- Schedule recurring reports with CRON expressions

## Current Status (Updated: January 2025)

### ✅ Completed Setup
- **Supabase Integration**: Database is fully configured and populated
- **User Account**: Created for nick@nevermeh.com (ID: fe841586-7807-48b1-8808-02877834fce0)
- **AMC Data Imported**: 
  - 2 AMC accounts (Recommerce Brands, NeverMeh AMC)
  - 58 AMC instances (56 production, 2 sandbox)
- **Sample Workflows**: 3 analysis templates created
- **Query Templates**: Reusable templates configured
- **API Server**: FastAPI running on port 8001 with all endpoints
- **Campaign Management**: 
  - Import service for DSP/SP/SD/SB campaigns
  - Auto-tagging with brand names
  - ASIN tracking per campaign
  - Mock data for testing (8 campaigns across 8 brands)
- **Authentication**: JWT-based auth with token encryption
- **React Frontend**: Full UI built with React, TypeScript, and Vite
  - AMC instances list with enhanced table view
  - Instance detail pages with tabs (Overview, Campaigns, Workflows, Queries)
  - Campaign management with brand filtering
  - Dashboard with overview statistics
- **Enhanced Instance Display**:
  - Shows instance name, ID, account, and associated brands
  - Workflow counts and statistics
  - Click-through to detailed view
  - Brand badges aggregated from campaign data
- **Editable Brand Tags** (NEW):
  - Direct brand association with AMC instances
  - Add/remove brands with visual editor
  - Autocomplete search for existing brands
  - Campaign filtering based on instance brands
  - Database migration with `instance_brands` table
- **Railway Deployment**:
  - Successfully deployed to Railway.app
  - Frontend and backend served from single URL
  - Environment-based configuration
  - Automatic builds with Dockerfile
- **Workflow Execution** (NEW):
  - Execute workflows with custom parameters
  - Real-time progress monitoring with status updates
  - Error handling with detailed error messages
  - Mock execution engine for testing (completes in ~3 seconds)
- **Execution History & Details** (NEW):
  - Clickable execution rows in history table
  - Comprehensive execution detail modal
  - View execution parameters and error messages
  - Download results as CSV (when result storage is fixed)
  - Performance metrics display

### 🔄 In Progress
- Real Amazon OAuth token integration
- AMC API integration for actual query execution
- Result data persistence (currently returns empty values)

### 🚀 Performance Optimizations (NEW)
- **Optimized Database Queries**: 
  - Single query to fetch instances with stats and brands (reduced from 232+ queries to 1-3)
  - Batch loading of related data using Supabase joins
  - 90%+ reduction in database load
- **API Improvements**:
  - Added pagination support (limit/offset parameters)
  - Gzip compression for responses (minimum 1KB)
  - Optimized data formatting
- **Database Indexes**:
  - Added indexes on frequently queried columns
  - Migration script: `scripts/apply_performance_indexes.py`
- **Frontend Optimizations**:
  - React Query caching (5-minute stale time)
  - Loading state indicators
  - Pagination-ready implementation

## Key Discovery: AMC API Authentication

**CRITICAL**: The AMC instances API requires the entity ID to be passed as the `Amazon-Advertising-API-AdvertiserId` header, NOT as a query parameter. This was a major breakthrough that solved the "entityId provided is null" errors.

Correct header format:
```python
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-MarketplaceId': marketplace_id,
    'Amazon-Advertising-API-AdvertiserId': entity_id  # This is the key!
}
```

## Quick Start Guide

### Local Development
```bash
# 1. Clone and navigate to the project
cd /root/amazon-helper

# 2. Start both backend and frontend
./start_services.sh

# 3. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs

# 4. Login with: nick@nevermeh.com (no password required)
```

### Railway Deployment
```bash
# 1. Push to GitHub
git push origin main

# 2. Connect Railway to your GitHub repo

# 3. Add environment variables in Railway:
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_key

# 4. Railway will build and deploy automatically
```

## Development Commands

### Quick Start with Supabase
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies for Supabase
pip install supabase pydantic-settings python-dotenv httpx requests

# Test Supabase connection
python test_supabase_simple.py

# Import initial data (if not already done)
python scripts/import_initial_data.py

# Create sample workflows
python scripts/create_sample_workflow.py
```

### Full Application Setup
```bash
# Backend setup
cd /root/amazon-helper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_supabase.txt

# Frontend setup
cd frontend
npm install

# Start both services
cd /root/amazon-helper
./start_services.sh

# Or manually:
# Backend: python main_supabase.py  # Runs on http://localhost:8001
# Frontend: cd frontend && npm run dev  # Runs on http://localhost:5173

# Note: The backend uses main_supabase.py on port 8001 (not main.py on 8000)
```

### Testing and Quality
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api_auth.py

# Run with coverage
pytest --cov=amc_manager tests/

# Code formatting
black amc_manager/
flake8 amc_manager/

# Type checking
mypy amc_manager/
```

### Database Management with Supabase
```bash
# Database is managed through Supabase Dashboard
# Access at: https://supabase.com/dashboard/project/loqaorroihxfkjvcrkdv

# To run SQL scripts:
# 1. Open Supabase SQL Editor
# 2. Run scripts from database/supabase/ directory

# For local development with migrations:
# Use Supabase CLI instead of Alembic
```

## Architecture and Code Structure

### Core Components

1. **Authentication Flow** (`amc_manager/core/auth.py`)
   - OAuth 2.0 with Login with Amazon (LWA)
   - Token refresh mechanism
   - User profile retrieval and entity discovery

2. **API Client** (`amc_manager/core/api_client.py`)
   - Rate limiting with retry logic
   - Custom headers support (critical for AMC API)
   - Automatic token refresh on 401 errors

3. **Supabase Integration** (`amc_manager/core/supabase_client.py`)
   - Singleton client manager
   - Service role support for admin operations
   - Base service class for all Supabase operations

4. **Service Layer Pattern**
   - `SupabaseService`: Base class for all services
   - `CampaignMappingService`: Manages campaign data with ASIN tracking
   - `BrandConfigurationService`: Brand settings and auto-tagging
   - `WorkflowService`: AMC workflow management
   - `AMCInstanceService`: Instance access and validation

5. **Query Builder** (`amc_manager/services/query_builder.py`)
   - Pre-built templates for common analyses
   - YAML parameter support for dynamic queries
   - SQL validation and safety checks

### Key Files and Their Purposes

**Backend**:
- `main_supabase.py`: Main FastAPI application entry point (port 8001)
- `amc_manager/config/settings.py`: Configuration management using Pydantic
- `amc_manager/core/supabase_client.py`: Supabase client singleton manager
- `amc_manager/services/db_service.py`: Database service with retry logic
- `amc_manager/api/supabase/`: API endpoints using Supabase
  - `auth.py`: Authentication endpoints
  - `instances_simple.py`: AMC instances endpoints
  - `campaigns.py`: Campaign management endpoints
  - `workflows.py`: Workflow management endpoints
  - `queries.py`: Query template endpoints

**Frontend** (`frontend/`):
- `src/App.tsx`: Main React application with routing
- `src/components/auth/`: Authentication components
- `src/components/instances/`: Instance list and detail components
- `src/components/campaigns/`: Campaign management UI
- `src/components/workflows/`: Workflow management UI
- `src/services/api.ts`: Axios API client configuration
- `src/services/auth.ts`: Authentication service
- `vite.config.ts`: Vite configuration with API proxy

### Database Schema (Supabase)

All tables are created in Supabase with RLS enabled:
- `users`: User accounts with profile and marketplace IDs
- `amc_accounts`: AMC account entities (2 imported)
- `amc_instances`: AMC instance configurations (58 imported)
- `workflows`: AMC workflow definitions with SQL queries
- `workflow_executions`: Execution history and status tracking
- `campaign_mappings`: Campaign ID to name mappings with ASIN tracking
- `brand_configurations`: Brand settings with ASIN associations
- `query_templates`: Reusable query templates (3 created)
- `workflow_schedules`: CRON-based scheduling
- `amc_query_results`: Query result caching

### AMC Instance Details

The application manages 58 AMC instances across two accounts:
- **Recommerce Brands** (ENTITYEJZCBSCBH4HZ): 50 instances
- **NeverMeh AMC** (ENTITY277TBI8OBF435): 8 instances

Each account has one SANDBOX instance for testing.

### Common AMC SQL Query Templates

The system includes templates for:
- Path to Conversion Analysis
- New-to-Brand Customer Analysis
- Cart Abandonment Analysis
- Cross-Channel Performance
- Attribution Model Comparison
- Audience Overlap Analysis
- Campaign Reach & Frequency

### API Integration Notes

1. Always use `https://advertising-api.amazon.com` as the base URL
2. Include marketplace ID in headers (US: ATVPDKIKX0DER)
3. Rate limits: 10 requests per second (handled automatically)
4. Token expiration: 1 hour (auto-refresh implemented)

### Testing Approach

- Use sandbox instances (`amchnfozgta` or `amcfo8abayq`) for development
- Test scripts available in root directory (e.g., `amc_instances_working.py`)
- Integration tests should mock external API calls

### Environment Variables

Critical variables that must be set:
- `AMAZON_CLIENT_ID`: From Amazon Advertising console
- `AMAZON_CLIENT_SECRET`: Keep secure, never commit
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Public anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key for admin operations
- `DATABASE_URL`: Optional - for SQLAlchemy compatibility
- `REDIS_URL`: Optional - if using Celery instead of Edge Functions
- `S3_BUCKET_NAME`: Optional - Supabase Storage can be used instead

### Debugging Tips

1. For AMC API errors, check headers first (especially `Amazon-Advertising-API-AdvertiserId`)
2. Token refresh issues: Check token expiration and refresh token validity
3. Supabase connection issues: Verify project URL and keys in .env
4. For 403 errors: Verify the user has access to the requested AMC instance
5. RLS errors: Check that user ID matches in requests
6. Data not showing after idle period: 
   - Supabase connection times out after ~30 minutes
   - Automatic reconnection implemented in `db_service.py`
   - Frontend will refetch on window focus
   - Hard refresh (Ctrl+F5) if needed
7. JWT errors: Fixed by using `jwt.DecodeError` instead of `jwt.JWTError`

### Important Scripts

- `test_supabase_simple.py`: Quick Supabase connection test
- `scripts/import_initial_data.py`: Import user, accounts, and instances
- `scripts/create_sample_workflow.py`: Create template workflows
- `scripts/test_auth_flow.py`: Test Amazon OAuth tokens
- `scripts/test_campaign_import_mock.py`: Import mock campaign data with brands
- `scripts/test_instance_brands.py`: Test instance brand functionality
- `scripts/apply_instance_brands_migration.py`: Apply database migration for brands
- `scripts/apply_performance_indexes.py`: Apply performance optimization indexes
- `start_services.sh`: Start both backend and frontend services
- `prepare_railway.sh`: Prepare app for Railway deployment
- `test_execution.py`: Test workflow execution functionality
- `test_execution_detail.py`: Test execution detail viewing
- `demo_execution.py`: Demonstrate execution success/failure scenarios

### Performance Optimization Steps

To apply the performance optimizations:
1. Run the index migration: `python scripts/apply_performance_indexes.py`
2. Restart the backend service to use the new optimized queries
3. The frontend will automatically benefit from faster API responses

### Recent Architectural Changes (January 2025)

1. **Workflow Execution Features**:
   - Added ExecutionModal component for running workflows
   - Real-time status polling with React Query
   - Parameter configuration before execution
   - Progress tracking with visual indicators
   - Error display in dedicated UI components
   - CSV download functionality (pending result storage fix)

2. **Execution History Enhancement**:
   - Created ExecutionDetailModal for viewing full execution details
   - Made execution history rows clickable
   - Added comprehensive execution information display
   - Integrated status icons and progress visualization
   - Added API endpoint `/executions/{execution_id}/detail`

### Current Architectural State (January 2025)

1. **Frontend Implementation**:
   - Built complete React UI with TypeScript and Vite
   - Used React Query for data fetching with automatic retries
   - Implemented React Router for navigation
   - Added Tailwind CSS for styling
   - Created reusable components for instances, campaigns, workflows

2. **Backend Improvements**:
   - Fixed async/sync compatibility issues with Supabase Python client
   - Added connection retry logic with `@with_connection_retry` decorator
   - Implemented automatic Supabase reconnection after 30 minutes
   - Fixed JWT authentication errors (jwt.DecodeError)
   - Enhanced API endpoints to include brand and stats information
   - Fixed workflow execution errors by removing non-existent database columns
   - Added timezone-aware datetime handling for execution timestamps

3. **Data Architecture**:
   - All data is stored in and served from Supabase (not direct Amazon API)
   - Brands are now directly associated with instances via `instance_brands` table
   - Instance stats are calculated from workflows table
   - Connection pooling handled by Supabase client
   - Campaign filtering based on instance brand associations

4. **UI/UX Enhancements**:
   - Table view for AMC instances with sortable columns
   - Clickable rows for navigation to detail views
   - Tabbed interface for instance details
   - Editable brand tags with add/remove functionality
   - Brand selector with autocomplete search
   - Responsive design for different screen sizes
   - Workflow execution modal with parameter configuration
   - Real-time execution progress monitoring
   - Clickable execution history with detailed view modal
   - Results visualization with table/insights toggle
   - CSV download for execution results

5. **Brand Tag Feature**:
   - New `instance_brands` junction table for many-to-many relationships
   - Brand service for managing brand operations
   - API endpoints for updating instance brands
   - Frontend components: BrandTag and BrandSelector
   - Campaigns automatically filter based on instance brands

6. **Railway Deployment**:
   - Dockerfile-based deployment for consistency
   - Single URL serves both frontend and backend
   - Environment variables for configuration
   - Automatic builds on git push
   - Health check at `/api/health`

### Security Considerations

- All tokens are encrypted in the database using Fernet encryption
- API endpoints require authentication via JWT
- Rate limiting prevents API abuse
- Never log or expose client secrets or tokens
- Frontend stores JWT in localStorage (consider moving to httpOnly cookies for production)