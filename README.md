# Amazon Marketing Cloud (AMC) Manager

A comprehensive application for managing Amazon Marketing Cloud instances, building AMC SQL queries, and tracking workflow executions.

## Features

### Core Functionality
- **AMC Instance Management**: View and manage multiple AMC instances
- **Workflow Creation & Management**: Create, update, and delete AMC workflows
- **Query Builder**: Build AMC SQL queries using templates or custom parameters
- **Execution Tracking**: Monitor workflow executions in real-time
- **Campaign Management**: Map campaign IDs to names with brand tagging
- **Scheduling**: Schedule workflows with CRON expressions
- **Results Retrieval**: Access execution results from S3

### Key Components
1. **Authentication**: OAuth 2.0 with Login with Amazon (LWA)
2. **API Integration**: Full Amazon Advertising API v3 integration
3. **Rate Limiting**: Built-in rate limiting and retry logic
4. **Query Templates**: Pre-built templates for common AMC queries
5. **YAML Parameters**: Support for YAML-based query configuration
6. **Brand Tagging**: Organize campaigns by brand with custom parameters

## Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Redis (for Celery task queue)
- Amazon Advertising API credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd amazon-helper
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
alembic upgrade head
```

6. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- API Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

### Project Structure
```
amc_manager/
├── api/          # FastAPI routers and endpoints
├── core/         # Core functionality (auth, API client)
├── models/       # SQLAlchemy database models
├── services/     # Business logic services
├── utils/        # Utility functions
├── web/          # Web UI assets
└── config/       # Configuration management
```

### Key Services
- **AMCInstanceService**: Manage AMC instances
- **WorkflowService**: Create and manage workflows
- **DataRetrievalService**: Retrieve campaign and ASIN data
- **ExecutionTrackingService**: Monitor executions
- **AMCQueryBuilder**: Build and validate queries

### Database Models
- **User**: User authentication and profiles
- **Workflow**: AMC workflow definitions
- **WorkflowExecution**: Execution history
- **CampaignMapping**: Campaign ID to name mappings
- **BrandConfiguration**: Brand-specific settings
- **QueryTemplate**: Saved query templates

## Query Templates

Built-in templates include:
- Path to Conversion Analysis
- New-to-Brand Customer Analysis
- Cart Abandonment Analysis
- Cross-Channel Performance
- Attribution Model Comparison

## API Endpoints

### Authentication
- `GET /api/auth/login` - Initiate OAuth flow
- `GET /api/auth/callback` - OAuth callback
- `POST /api/auth/refresh` - Refresh tokens

### Instances
- `GET /api/instances` - List AMC instances
- `GET /api/instances/{id}` - Get instance details
- `GET /api/instances/{id}/metrics` - Get instance metrics

### Workflows
- `POST /api/workflows` - Create workflow
- `GET /api/workflows/{instance_id}` - List workflows
- `POST /api/workflows/{instance_id}/{workflow_id}/execute` - Execute workflow

### Campaigns
- `GET /api/campaigns/dsp` - Get DSP campaigns
- `GET /api/campaigns/sponsored` - Get Sponsored Ads campaigns
- `POST /api/campaigns/sync` - Sync campaigns from API

### Queries
- `GET /api/queries/templates` - List query templates
- `POST /api/queries/build` - Build query from template
- `POST /api/queries/validate` - Validate AMC SQL query

## Environment Variables

Key configuration options:
- `AMAZON_CLIENT_ID`: Amazon Advertising API client ID
- `AMAZON_CLIENT_SECRET`: API client secret
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery
- `S3_BUCKET_NAME`: S3 bucket for results

## Security Considerations

- All API endpoints require authentication
- Tokens are encrypted in the database
- Rate limiting prevents API abuse
- CORS configured for specific origins

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black amc_manager/
flake8 amc_manager/
```

### Database Migrations
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## License

[Your License Here]