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

### 🔄 In Progress
- Token validation for Amazon OAuth
- API server startup and testing
- Campaign data import from Amazon API

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
# Install all dependencies (has some conflicts, needs cleanup)
pip install -r requirements.txt

# Start the application
python main.py  # API will be available at http://localhost:8000

# Note: Celery/Redis setup is optional with Supabase
# Supabase Edge Functions can replace background tasks
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

- `amc_manager/config/settings.py`: Configuration management using Pydantic
- `amc_manager/models/`: SQLAlchemy ORM models for database entities
- `amc_manager/api/routers/`: FastAPI route handlers
- `amc_manager/utils/`: Utility functions for S3, encryption, etc.
- `amc_manager/web/`: Frontend assets (HTML, CSS, JS)

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

### Important Scripts

- `test_supabase_simple.py`: Quick Supabase connection test
- `scripts/import_initial_data.py`: Import user, accounts, and instances
- `scripts/create_sample_workflow.py`: Create template workflows
- `scripts/test_auth_flow.py`: Test Amazon OAuth tokens

### Security Considerations

- All tokens are encrypted in the database using Fernet encryption
- API endpoints require authentication via JWT
- Rate limiting prevents API abuse
- Never log or expose client secrets or tokens