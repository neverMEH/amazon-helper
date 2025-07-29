# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Amazon Marketing Cloud (AMC) management application that helps users:
- Manage multiple AMC instances across different brands
- Build and execute AMC SQL queries using templates or custom parameters
- Track workflow executions and retrieve results
- Map campaign IDs to names with brand tagging
- Schedule recurring reports with CRON expressions

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

### Setup and Running
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment (copy and edit with your credentials)
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the application
python main.py  # API will be available at http://localhost:8000

# Run Celery worker (in separate terminal)
celery -A amc_manager.tasks worker --loglevel=info

# Run Celery beat scheduler (in separate terminal)
celery -A amc_manager.tasks beat --loglevel=info
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

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
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

3. **Service Layer Pattern**
   - `AMCInstanceService`: Manages AMC instances, requires entity_id as header
   - `WorkflowService`: Creates and manages AMC workflows
   - `DataRetrievalService`: Fetches campaign and ASIN data
   - `ExecutionTrackingService`: Monitors workflow executions
   - `SchedulingService`: Manages CRON-based schedules

4. **Query Builder** (`amc_manager/services/query_builder.py`)
   - Pre-built templates for common analyses
   - YAML parameter support for dynamic queries
   - SQL validation and safety checks

### Key Files and Their Purposes

- `amc_manager/config/settings.py`: Configuration management using Pydantic
- `amc_manager/models/`: SQLAlchemy ORM models for database entities
- `amc_manager/api/routers/`: FastAPI route handlers
- `amc_manager/utils/`: Utility functions for S3, encryption, etc.
- `amc_manager/web/`: Frontend assets (HTML, CSS, JS)

### Database Schema

Key models include:
- `User`: Stores encrypted tokens and profile information
- `Workflow`: AMC workflow definitions with SQL queries
- `WorkflowExecution`: Execution history and status tracking
- `CampaignMapping`: Maps campaign IDs to readable names
- `BrandConfiguration`: Brand-specific settings and parameters
- `QueryTemplate`: Reusable query templates

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
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: For Celery task queue
- `S3_BUCKET_NAME`: For storing query results

### Debugging Tips

1. For AMC API errors, check headers first (especially `Amazon-Advertising-API-AdvertiserId`)
2. Token refresh issues: Check token expiration and refresh token validity
3. Database connection issues: Verify PostgreSQL is running and migrations are applied
4. For 403 errors: Verify the user has access to the requested AMC instance

### Security Considerations

- All tokens are encrypted in the database using Fernet encryption
- API endpoints require authentication via JWT
- Rate limiting prevents API abuse
- Never log or expose client secrets or tokens