# API Routes Documentation

## Overview

RecomAMP provides a comprehensive REST API built with FastAPI, following OpenAPI 3.0 standards. The API is organized by domain areas and provides consistent patterns for CRUD operations, authentication, and error handling.

## Base Configuration

### API Structure
- **Base URL**: `http://localhost:8001/api`
- **Documentation**: `http://localhost:8001/docs` (Swagger UI)
- **OpenAPI Spec**: `http://localhost:8001/openapi.json`
- **Content Type**: `application/json`
- **Authentication**: Bearer JWT tokens

### Standard Response Formats
```json
// Success Response
{
  "data": {...},
  "message": "Operation successful",
  "status": "success"
}

// Error Response
{
  "detail": "Error message",
  "status_code": 400,
  "errors": {...} // Optional validation errors
}

// Paginated Response
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 150,
    "total_pages": 3
  }
}
```

## Authentication Routes

### POST /api/auth/login
Initiate Amazon OAuth login flow.

```http
POST /api/auth/login
Content-Type: application/json

{
  "redirect_uri": "http://localhost:5173/auth/callback"
}
```

**Response:**
```json
{
  "auth_url": "https://www.amazon.com/ap/oa?client_id=...",
  "state": "secure_random_state_token"
}
```

### POST /api/auth/amazon/callback
Handle Amazon OAuth callback and create user session.

```http
POST /api/auth/amazon/callback
Content-Type: application/json

{
  "code": "authorization_code_from_amazon",
  "state": "state_token_from_login"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### GET /api/auth/me
Get current authenticated user information.

```http
GET /api/auth/me
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "timezone": "UTC",
  "email_notifications": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### POST /api/auth/logout
Logout user and invalidate session.

```http
POST /api/auth/logout
Authorization: Bearer <jwt_token>
```

## Workflow Routes

### GET /api/workflows/
List user's workflows with optional filtering.

```http
GET /api/workflows/?instance_id=uuid&search=query&tags=tag1,tag2&page=1&page_size=50
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `instance_id` (optional): Filter by AMC instance
- `search` (optional): Search in name and description
- `tags` (optional): Comma-separated tag filter
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "workflow-uuid",
      "name": "Campaign Analysis",
      "description": "Daily campaign performance analysis",
      "sql_query": "SELECT * FROM campaigns WHERE date >= '{{start_date}}'",
      "instance_id": "instance-uuid",
      "parameters": {"start_date": "2024-01-01"},
      "tags": ["analysis", "campaigns"],
      "is_public": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "last_executed_at": "2024-01-01T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 25,
    "total_pages": 1
  }
}
```

### POST /api/workflows/
Create new workflow. **Note the trailing slash!**

```http
POST /api/workflows/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "New Workflow",
  "description": "Workflow description",
  "sql_query": "SELECT * FROM campaigns LIMIT {{limit}}",
  "instance_id": "instance-uuid",
  "template_id": "template-uuid", // optional
  "parameters": {"limit": 100},
  "tags": ["new", "analysis"],
  "is_public": false
}
```

**Response:**
```json
{
  "id": "workflow-uuid",
  "name": "New Workflow",
  // ... other workflow fields
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### GET /api/workflows/{workflow_id}
Get specific workflow details.

```http
GET /api/workflows/workflow-uuid
Authorization: Bearer <jwt_token>
```

### PUT /api/workflows/{workflow_id}
Update existing workflow.

```http
PUT /api/workflows/workflow-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Workflow Name",
  "description": "Updated description",
  "sql_query": "SELECT * FROM campaigns WHERE status = 'ENABLED'",
  "parameters": {"limit": 200},
  "tags": ["updated", "analysis"]
}
```

### DELETE /api/workflows/{workflow_id}
Delete workflow and all associated executions.

```http
DELETE /api/workflows/workflow-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/workflows/{workflow_id}/execute
Execute workflow with parameters.

```http
POST /api/workflows/workflow-uuid/execute
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "campaign_ids": ["camp1", "camp2"],
    "limit": 1000
  }
}
```

**Response:**
```json
{
  "id": "execution-uuid",
  "workflow_id": "workflow-uuid",
  "status": "PENDING",
  "parameters": {"start_date": "2024-01-01", "limit": 1000},
  "created_at": "2024-01-01T12:00:00Z",
  "amc_execution_id": "amc-exec-123"
}
```

### POST /api/workflows/{workflow_id}/preview
Preview SQL query with parameter substitution.

```http
POST /api/workflows/workflow-uuid/preview
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "parameters": {
    "start_date": "2024-01-01",
    "campaign_ids": ["camp1", "camp2"]
  }
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM campaigns WHERE date >= '2024-01-01' AND campaign_id IN ('camp1', 'camp2')",
  "parameters_used": {
    "start_date": "2024-01-01",
    "campaign_ids": ["camp1", "camp2"]
  }
}
```

### GET /api/workflows/{workflow_id}/executions
Get execution history for workflow.

```http
GET /api/workflows/workflow-uuid/executions?limit=20&status=SUCCESS
Authorization: Bearer <jwt_token>
```

## Execution Routes

### GET /api/executions/{execution_id}
Get execution details and status.

```http
GET /api/executions/execution-uuid
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "execution-uuid",
  "workflow_id": "workflow-uuid",
  "amc_execution_id": "amc-exec-123",
  "status": "SUCCESS",
  "parameters": {"limit": 100},
  "result_rows": 1234,
  "result_size_bytes": 56789,
  "execution_duration": 45,
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:05Z",
  "completed_at": "2024-01-01T12:00:50Z"
}
```

### GET /api/executions/{execution_id}/results
Get execution results data.

```http
GET /api/executions/execution-uuid/results?format=json&limit=1000
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `format` (optional): `json` or `csv` (default: json)
- `limit` (optional): Limit result rows (default: 10000)

**Response:**
```json
{
  "data": [
    {
      "campaign_id": "camp1",
      "impressions": 1000,
      "clicks": 50,
      "spend": 25.50
    }
  ],
  "metadata": {
    "total_rows": 1234,
    "execution_time": 45,
    "query": "SELECT campaign_id, impressions, clicks, spend FROM campaigns"
  }
}
```

### DELETE /api/executions/{execution_id}
Cancel running execution or delete completed execution.

```http
DELETE /api/executions/execution-uuid
Authorization: Bearer <jwt_token>
```

## AMC Instance Routes

### GET /api/instances/
List user's AMC instances.

```http
GET /api/instances/?active_only=true
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "instance-uuid",
      "instance_id": "amcibersblt", // AMC string ID
      "name": "Production AMC",
      "description": "Main production instance",
      "region": "us-east-1",
      "account_id": "account-uuid",
      "is_active": true,
      "health_status": "HEALTHY",
      "created_at": "2024-01-01T00:00:00Z",
      "amc_accounts": {
        "account_id": "entity-123",
        "account_name": "My Amazon Account"
      }
    }
  ]
}
```

### POST /api/instances/
Create new AMC instance.

```http
POST /api/instances/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "instance_id": "amcnewinstance",
  "name": "Development AMC",
  "description": "Development and testing instance",
  "region": "us-east-1",
  "account_id": "account-uuid"
}
```

### GET /api/instances/{instance_id}
Get specific instance details.

```http
GET /api/instances/instance-uuid
Authorization: Bearer <jwt_token>
```

### PUT /api/instances/{instance_id}
Update instance configuration.

```http
PUT /api/instances/instance-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Instance Name",
  "description": "Updated description",
  "is_active": true
}
```

### DELETE /api/instances/{instance_id}
Delete instance and all associated workflows.

```http
DELETE /api/instances/instance-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/instances/{instance_id}/test-connection
Test AMC instance connectivity.

```http
POST /api/instances/instance-uuid/test-connection
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "response_time_ms": 234,
  "amc_version": "2.1",
  "data_freshness": "2024-01-01T06:00:00Z"
}
```

## Schedule Routes

### GET /api/schedules/
List user's workflow schedules.

```http
GET /api/schedules/?active_only=true&workflow_id=workflow-uuid
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "schedule-uuid",
      "name": "Daily Report",
      "workflow_id": "workflow-uuid",
      "cron_expression": "0 9 * * *",
      "timezone": "America/New_York",
      "is_active": true,
      "next_run_at": "2024-01-02T09:00:00Z",
      "parameters": {"date": "yesterday"},
      "total_runs": 45,
      "successful_runs": 44,
      "failed_runs": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /api/schedules/
Create new workflow schedule.

```http
POST /api/schedules/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Hourly Campaign Check",
  "workflow_id": "workflow-uuid",
  "cron_expression": "0 * * * *",
  "timezone": "UTC",
  "parameters": {
    "start_date": "today",
    "end_date": "today"
  },
  "is_active": true
}
```

### GET /api/schedules/{schedule_id}
Get schedule details.

```http
GET /api/schedules/schedule-uuid
Authorization: Bearer <jwt_token>
```

### PUT /api/schedules/{schedule_id}
Update schedule configuration.

```http
PUT /api/schedules/schedule-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Schedule",
  "cron_expression": "0 */2 * * *", // Every 2 hours
  "is_active": false
}
```

### POST /api/schedules/{schedule_id}/pause
Pause schedule execution.

```http
POST /api/schedules/schedule-uuid/pause
Authorization: Bearer <jwt_token>
```

### POST /api/schedules/{schedule_id}/resume
Resume paused schedule.

```http
POST /api/schedules/schedule-uuid/resume
Authorization: Bearer <jwt_token>
```

### GET /api/schedules/{schedule_id}/history
Get schedule execution history.

```http
GET /api/schedules/schedule-uuid/history?limit=50&status=SUCCESS
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "run-uuid",
      "schedule_id": "schedule-uuid",
      "execution_id": "execution-uuid",
      "status": "SUCCESS",
      "duration_seconds": 45,
      "created_at": "2024-01-01T09:00:00Z"
    }
  ]
}
```

### DELETE /api/schedules/{schedule_id}
Delete schedule.

```http
DELETE /api/schedules/schedule-uuid
Authorization: Bearer <jwt_token>
```

## Campaign Routes

### GET /api/campaigns/
List campaigns with filtering. **Updated 2025-09-25**: Fixed campaign selector pagination limits to prevent 422 validation errors. **Updated 2025-09-11**: Fixed routing issue, user-level filtering pending database migration.

```http
GET /api/campaigns/?instance_id=instance-uuid&campaign_type=sponsoredProducts&state=ENABLED
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `instance_id` (optional): Filter by AMC instance
- `campaign_type` (optional): sponsoredProducts, sponsoredBrands, sponsoredDisplay
- `state` (optional): ENABLED, PAUSED, ARCHIVED
- `search` (optional): Search campaign names
- `min_spend` (optional): Minimum spend filter
- `max_acos` (optional): Maximum ACoS filter
- `page_size` (optional): Results per page (max: 100, default: 50) **Updated 2025-09-25**: Fixed to respect API limits

**Security**: Authentication required. User-level data filtering not yet implemented (requires adding `user_id` column to campaigns table).

**Response:**
```json
{
  "data": [
    {
      "id": "campaign-db-uuid",
      "campaign_id": "camp123", // Amazon's campaign ID
      "name": "Summer Sale Campaign",
      "campaign_type": "sponsoredProducts",
      "state": "ENABLED",
      "instance_id": "instance-uuid",
      "impressions": 50000,
      "clicks": 2500,
      "spend": 1250.50,
      "sales": 3750.00,
      "acos": 33.33,
      "roas": 3.00,
      "start_date": "2024-01-01",
      "budget": 100.00,
      "budget_type": "DAILY",
      "last_sync_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### GET /api/campaigns/brands
List campaign brands. **Updated 2025-09-11**: Fixed routing, user filtering pending database changes.

```http
GET /api/campaigns/brands?instance_id=instance-uuid
Authorization: Bearer <jwt_token>
```

### GET /api/campaigns/stats
Get campaign statistics. **Updated 2025-09-11**: Fixed routing, user filtering pending database changes.

```http
GET /api/campaigns/stats?instance_id=instance-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/campaigns/import/{instance_id}
Import campaigns from Amazon Advertising API.

```http
POST /api/campaigns/import/instance-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "campaign_types": ["sponsoredProducts", "sponsoredBrands"],
  "states": ["ENABLED", "PAUSED"],
  "update_existing": true
}
```

**Response:**
```json
{
  "imported": 25,
  "updated": 10,
  "skipped": 5,
  "errors": [],
  "total_processed": 35
}
```

### PUT /api/campaigns/{campaign_id}/sync
Sync specific campaign data.

```http
PUT /api/campaigns/campaign-db-uuid/sync
Authorization: Bearer <jwt_token>
```

## ASIN Routes

### GET /api/asins/
List user's ASINs.

```http
GET /api/asins/?search=B08N5WRWNW&brand=Nike&category=Shoes
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "asin-db-uuid",
      "asin": "B08N5WRWNW",
      "title": "Nike Air Max Sneakers",
      "brand": "Nike",
      "category": "Shoes",
      "image_url": "https://images.amazon.com/...",
      "price": 129.99,
      "sales_rank": 1234,
      "review_count": 567,
      "average_rating": 4.3,
      "tags": ["footwear", "athletic"],
      "notes": "High performing product",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "last_validated_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### POST /api/asins/
Create/import ASINs.

```http
POST /api/asins/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "asins": ["B08N5WRWNW", "B07FZ8S74R"],
  "validate": true,
  "tags": ["new-import"]
}
```

**Response:**
```json
{
  "imported": 2,
  "updated": 0,
  "invalid": [],
  "errors": []
}
```

### DELETE /api/asins/{asin_id}
Delete ASIN.

```http
DELETE /api/asins/asin-db-uuid
Authorization: Bearer <jwt_token>
```

## Data Collection Routes

### GET /api/data-collections/
List data collections.

```http
GET /api/data-collections/?status=ACTIVE&workflow_id=workflow-uuid
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "collection-uuid",
      "name": "Q1 2024 Analysis",
      "workflow_id": "workflow-uuid",
      "instance_id": "instance-uuid",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "status": "ACTIVE",
      "total_weeks": 13,
      "completed_weeks": 8,
      "failed_weeks": 0,
      "progress_percentage": 61.54,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /api/data-collections/
Create new data collection.

```http
POST /api/data-collections/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Historical Campaign Analysis",
  "workflow_id": "workflow-uuid",
  "instance_id": "instance-uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "parameters": {
    "campaign_type": "sponsoredProducts"
  }
}
```

### GET /api/data-collections/{collection_id}
Get collection details with progress.

```http
GET /api/data-collections/collection-uuid
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "id": "collection-uuid",
  "name": "Historical Campaign Analysis",
  "workflow_id": "workflow-uuid",
  "status": "ACTIVE",
  "progress_percentage": 75.0,
  "weeks": [
    {
      "id": "week-uuid",
      "week_start_date": "2024-01-01",
      "week_end_date": "2024-01-07",
      "status": "SUCCESS",
      "execution_id": "execution-uuid",
      "result_rows": 1234,
      "completed_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### POST /api/data-collections/{collection_id}/pause
Pause collection execution.

```http
POST /api/data-collections/collection-uuid/pause
Authorization: Bearer <jwt_token>
```

### POST /api/data-collections/{collection_id}/resume
Resume paused collection.

```http
POST /api/data-collections/collection-uuid/resume
Authorization: Bearer <jwt_token>
```

### POST /api/data-collections/{collection_id}/retry-failed
Retry failed weeks in collection.

```http
POST /api/data-collections/collection-uuid/retry-failed
Authorization: Bearer <jwt_token>
```

## Data Source and Schema Routes

### GET /api/data-sources/
Get AMC data sources and schema information.

```http
GET /api/data-sources/?category=impressions&active_only=true
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "source-uuid",
      "name": "dsp_campaign_data",
      "display_name": "DSP Campaign Data",
      "description": "Campaign-level performance metrics",
      "category": "impressions",
      "table_type": "fact",
      "data_freshness": "Daily at 6 AM UTC",
      "is_active": true,
      "fields": [
        {
          "field_name": "campaign_id",
          "data_type": "STRING",
          "description": "Unique campaign identifier",
          "is_nullable": false
        }
      ]
    }
  ]
}
```

### GET /api/data-sources/{source_id}
Get detailed schema for specific data source.

```http
GET /api/data-sources/source-uuid
Authorization: Bearer <jwt_token>
```

## Query Library Routes

**Enhanced Query Library API (2025-09-12)** - Comprehensive template management system with advanced parameter handling, execution engine, and dashboard generation.

### Template Management

#### GET /api/query-library/templates
List templates with advanced filtering and search.

```http
GET /api/query-library/templates?category=Attribution&search=conversion&tags=campaign&include_public=true&sort_by=usage_count&page=1&limit=20
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "templateId": "tpl_12345",
    "name": "Advanced Attribution Analysis",
    "description": "Multi-touch attribution with campaign performance",
    "category": "Attribution",
    "tags": ["attribution", "campaign", "conversion"],
    "version": 2,
    "executionCount": 127,
    "isPublic": true,
    "isOwner": false,
    "createdAt": "2025-09-10T10:00:00Z",
    "updatedAt": "2025-09-11T15:30:00Z"
  }
]
```

#### POST /api/query-library/templates
Create new template with automatic parameter detection. **Updated 2025-09-25**: Fixed trailing slash endpoint consistency.

```http
POST /api/query-library/templates
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Custom Attribution Template",
  "description": "Custom analysis for brand campaigns",
  "category": "Attribution",
  "sql_template": "SELECT campaign_name, SUM(conversions) FROM attribution WHERE date >= {{start_date}} AND campaign_id IN ({{campaign_ids}}) GROUP BY 1",
  "auto_detect_parameters": true,
  "is_public": false,
  "tags": ["custom", "attribution"]
}
```

#### GET /api/query-library/templates/{template_id}/full
Get template with all related data (parameters, reports, instances).

```http
GET /api/query-library/templates/tpl_12345/full
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "templateId": "tpl_12345",
  "name": "Advanced Attribution Analysis",
  "sqlTemplate": "SELECT ...",
  "parameters": [
    {
      "parameterId": "param_1",
      "parameterName": "start_date",
      "parameterType": "date_range",
      "displayName": "Analysis Period",
      "required": true,
      "uiConfig": {
        "component": "DateRangePicker",
        "presets": ["last_7_days", "last_30_days", "this_month"]
      }
    }
  ],
  "reports": [...],
  "instances": [...]
}
```

#### PUT /api/query-library/templates/{template_id}
Update template (owner only) with automatic version incrementing.

```http
PUT /api/query-library/templates/tpl_12345
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Template Name",
  "sql_template": "SELECT ... (updated SQL)",
  "tags": ["updated", "attribution"]
}
```

#### DELETE /api/query-library/templates/{template_id}
Delete template (owner only).

```http
DELETE /api/query-library/templates/tpl_12345
Authorization: Bearer <jwt_token>
```

#### POST /api/query-library/templates/{template_id}/fork
Fork template to create customized version.

```http
POST /api/query-library/templates/tpl_12345/fork
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "My Custom Attribution Fork",
  "description": "Forked for specific analysis needs"
}
```

### Parameter Management

#### GET /api/query-library/templates/{template_id}/parameters
Get all parameters for template.

```http
GET /api/query-library/templates/tpl_12345/parameters
Authorization: Bearer <jwt_token>
```

#### POST /api/query-library/templates/{template_id}/parameters
Create new parameter for template.

```http
POST /api/query-library/templates/tpl_12345/parameters
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "parameter_name": "conversion_threshold",
  "parameter_type": "threshold_numeric",
  "display_name": "Minimum Conversions",
  "description": "Filter campaigns with at least this many conversions",
  "required": false,
  "default_value": 10,
  "validation_rules": {"min": 1, "max": 1000},
  "ui_config": {"step": 5, "unit": "conversions"}
}
```

#### POST /api/query-library/templates/{template_id}/validate-parameters
Validate parameter values before execution.

```http
POST /api/query-library/templates/tpl_12345/validate-parameters
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "parameters": {
    "start_date": "2024-01-01",
    "campaign_ids": ["12345", "67890"],
    "conversion_threshold": 5
  }
}
```

### Template Execution

#### POST /api/query-library/templates/{template_id}/execute
Execute template with parameters and AMC integration.

```http
POST /api/query-library/templates/tpl_12345/execute
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "instance_id": "amcibersblt",
  "parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "campaign_ids": ["12345", "67890"]
  },
  "time_window_start": "2024-01-01T00:00:00",
  "time_window_end": "2024-01-31T23:59:59"
}
```

**Response:**
```json
{
  "executionId": "exec_789",
  "status": "PENDING",
  "estimated_completion": "2024-01-15T10:05:00Z",
  "message": "Query execution started successfully"
}
```

### Dashboard Generation

#### POST /api/query-library/templates/{template_id}/generate-dashboard
Generate dashboard from execution results.

```http
POST /api/query-library/templates/tpl_12345/generate-dashboard
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "execution_id": "exec_789",
  "report_config": {
    "title": "Attribution Analysis Dashboard",
    "layout": "grid",
    "widget_suggestions": true
  }
}
```

**Response:**
```json
{
  "dashboardId": "dash_456",
  "widgets": [
    {
      "type": "line_chart",
      "title": "Conversion Trend",
      "size": "large",
      "config": {...}
    },
    {
      "type": "metric_card", 
      "title": "Total Conversions",
      "size": "small",
      "value": 1247
    }
  ],
  "reportId": "report_123"
}
```

### Instance Management

#### POST /api/query-library/templates/{template_id}/instances
Save parameter configuration as reusable instance.

```http
POST /api/query-library/templates/tpl_12345/instances
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "instance_name": "Monthly Brand Analysis",
  "description": "Standard monthly brand campaign analysis",
  "parameter_values": {
    "start_date": "{{first_day_of_month}}",
    "end_date": "{{last_day_of_month}}",
    "campaign_ids": ["brand_123", "brand_456"]
  },
  "is_default": false
}
```

### Utility Endpoints

#### POST /api/query-library/templates/detect-parameters
Auto-detect parameters from SQL template.

```http
POST /api/query-library/templates/detect-parameters
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "sql_template": "SELECT * FROM campaigns WHERE date >= {{start_date}} AND campaign_id IN ({{campaign_list}})"
}
```

**Response:**
```json
{
  "parameters": [
    {
      "parameter_name": "start_date",
      "parameter_type": "date",
      "suggested_display_name": "Start Date",
      "inferred_from": "date comparison pattern"
    },
    {
      "parameter_name": "campaign_list",
      "parameter_type": "campaign_list",
      "suggested_display_name": "Campaign List",
      "inferred_from": "IN clause with campaign context"
    }
  ],
  "count": 2
}
```

#### GET /api/query-library/templates/{template_id}/versions
Get all versions of template.

```http
GET /api/query-library/templates/tpl_12345/versions
Authorization: Bearer <jwt_token>
```

#### POST /api/query-library/templates/{template_id}/suggest-widgets
Suggest dashboard widgets based on sample data.

```http
POST /api/query-library/templates/tpl_12345/suggest-widgets
Authorization: Bearer <jwt_token>
Content-Type: application/json

[
  {"campaign_name": "Brand A", "conversions": 125, "date": "2024-01-01"},
  {"campaign_name": "Brand B", "conversions": 87, "date": "2024-01-01"}
]
```

## Build Guide Routes

### GET /api/build-guides/
List available build guides.

```http
GET /api/build-guides/?category=Attribution&difficulty=BEGINNER
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "guide-uuid",
      "title": "Understanding AMC Attribution",
      "description": "Learn how to analyze cross-channel attribution",
      "category": "Attribution",
      "difficulty_level": "BEGINNER",
      "estimated_time": 30,
      "section_count": 5,
      "completion_count": 123,
      "favorite_count": 45
    }
  ]
}
```

### GET /api/build-guides/{guide_id}
Get complete guide content.

```http
GET /api/build-guides/guide-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/build-guides/{guide_id}/start
Start guide and track progress.

```http
POST /api/build-guides/guide-uuid/start
Authorization: Bearer <jwt_token>
```

### PUT /api/build-guides/{guide_id}/progress
Update guide progress.

```http
PUT /api/build-guides/guide-uuid/progress
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "current_section": 3,
  "completed_section": 2
}
```

## Dashboard Routes

### GET /api/dashboards/
List user's dashboards.

```http
GET /api/dashboards/?page=1&page_size=20
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "data": [
    {
      "id": "dashboard-uuid",
      "name": "Campaign Performance",
      "description": "Daily campaign monitoring dashboard",
      "is_public": false,
      "widget_count": 6,
      "view_count": 234,
      "created_at": "2024-01-01T00:00:00Z",
      "last_viewed_at": "2024-01-01T15:30:00Z"
    }
  ]
}
```

### POST /api/dashboards/
Create new dashboard.

```http
POST /api/dashboards/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Sales Dashboard",
  "description": "Real-time sales performance monitoring",
  "layout_config": {
    "columns": 12,
    "row_height": 60
  },
  "theme": "default",
  "is_public": false
}
```

### GET /api/dashboards/{dashboard_id}
Get dashboard with widgets and data.

```http
GET /api/dashboards/dashboard-uuid
Authorization: Bearer <jwt_token>
```

### PUT /api/dashboards/{dashboard_id}
Update dashboard configuration.

```http
PUT /api/dashboards/dashboard-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Updated Dashboard Name",
  "description": "Updated description",
  "theme": "dark"
}
```

### DELETE /api/dashboards/{dashboard_id}
Delete dashboard and all widgets.

```http
DELETE /api/dashboards/dashboard-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/dashboards/{dashboard_id}/share
Share dashboard with another user.

```http
POST /api/dashboards/dashboard-uuid/share
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "user_email": "colleague@example.com",
  "permission": "view", // view or edit
  "send_notification": true
}
```

## Dashboard Widget Routes

### GET /api/dashboards/{dashboard_id}/widgets/
List dashboard widgets.

```http
GET /api/dashboards/dashboard-uuid/widgets/
Authorization: Bearer <jwt_token>
```

### POST /api/dashboards/{dashboard_id}/widgets/
Create new widget.

```http
POST /api/dashboards/dashboard-uuid/widgets/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "widget_type": "line",
  "title": "Daily Impressions",
  "data_source": "workflow",
  "data_source_id": "workflow-uuid",
  "position_x": 0,
  "position_y": 0,
  "width": 6,
  "height": 4,
  "chart_config": {
    "x_field": "date",
    "y_field": "impressions"
  }
}
```

### PUT /api/dashboards/{dashboard_id}/widgets/{widget_id}
Update widget configuration.

```http
PUT /api/dashboards/dashboard-uuid/widgets/widget-uuid
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "title": "Updated Widget Title",
  "chart_config": {
    "x_field": "date",
    "y_field": "clicks",
    "show_legend": false
  }
}
```

### DELETE /api/dashboards/{dashboard_id}/widgets/{widget_id}
Delete widget.

```http
DELETE /api/dashboards/dashboard-uuid/widgets/widget-uuid
Authorization: Bearer <jwt_token>
```

### POST /api/dashboards/{dashboard_id}/widgets/{widget_id}/data
Get widget data.

```http
POST /api/dashboards/dashboard-uuid/widgets/widget-uuid/data
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "refresh": true,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

### PUT /api/dashboards/{dashboard_id}/widgets/reorder
Update widget layout positions.

```http
PUT /api/dashboards/dashboard-uuid/widgets/reorder
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "widgets": [
    {
      "widget_id": "widget1-uuid",
      "x": 0,
      "y": 0,
      "width": 6,
      "height": 4
    },
    {
      "widget_id": "widget2-uuid", 
      "x": 6,
      "y": 0,
      "width": 6,
      "height": 4
    }
  ]
}
```

## Report Builder Routes (2025-09-15)

The Report Builder API provides comprehensive report management with direct AMC execution, scheduling, and dashboard integration.

### Report CRUD Operations

#### GET /api/reports/
List all reports for the current user with filtering and pagination.

```http
GET /api/reports/?instance_id={instance_id}&is_active={bool}&page={num}&page_size={num}
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `instance_id` (optional): Filter by AMC instance ID
- `is_active` (optional): Filter by active status (true/false)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "report_id": "rpt_abc12345",
      "name": "Campaign Performance Report",
      "description": "Weekly campaign metrics",
      "template_id": "uuid",
      "instance_id": "uuid",
      "frequency": "weekly",
      "is_active": true,
      "dashboard_id": "uuid",
      "execution_count": 15,
      "created_at": "2025-09-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

#### POST /api/reports/
Create a new report definition.

```http
POST /api/reports/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "Campaign Performance Report",
  "description": "Weekly campaign metrics analysis",
  "template_id": "template-uuid",
  "instance_id": "instance-uuid",
  "parameters": {
    "date_range": "last_7_days",
    "campaigns": ["campaign1", "campaign2"]
  },
  "frequency": "weekly",
  "create_dashboard": true
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "report_id": "rpt_abc12345",
  "name": "Campaign Performance Report",
  "template": {...},
  "instance": {...},
  "dashboard": {...} // if create_dashboard: true
}
```

#### GET /api/reports/{report_id}
Get detailed report information including template and instance details.

**Response:**
```json
{
  "id": "uuid",
  "report_id": "rpt_abc12345",
  "name": "Campaign Performance Report",
  "template": {
    "id": "uuid",
    "name": "Campaign Analysis Template",
    "category": "performance"
  },
  "instance": {
    "id": "uuid",
    "instance_id": "amcibersblt",
    "name": "Main AMC Instance"
  },
  "schedules": [...],
  "recent_executions": [...]
}
```

#### PUT /api/reports/{report_id}
Update report configuration.

```http
PUT /api/reports/{report_id}
Authorization: Bearer {jwt_token}

{
  "name": "Updated Report Name",
  "parameters": {...},
  "is_active": false
}
```

#### DELETE /api/reports/{report_id}
Delete a report and all associated data.

**Response:** `204 No Content`

### Report Execution

#### POST /api/reports/{report_id}/execute
Execute a report ad-hoc with optional parameter overrides.

```http
POST /api/reports/{report_id}/execute
Authorization: Bearer {jwt_token}

{
  "parameters": {
    "date_range": "yesterday"
  },
  "time_window_start": "2025-09-14T00:00:00",
  "time_window_end": "2025-09-14T23:59:59"
}
```

**Response:** `202 Accepted`
```json
{
  "id": "uuid",
  "execution_id": "exec_xyz98765",
  "status": "pending",
  "amc_execution_id": "amc-exec-12345",
  "started_at": "2025-09-15T10:00:00Z"
}
```

#### GET /api/reports/{report_id}/executions
List executions for a specific report.

```http
GET /api/reports/{report_id}/executions?status=completed&limit=10
```

#### GET /api/reports/executions/{execution_id}
Get detailed execution information including results.

```json
{
  "id": "uuid",
  "execution_id": "exec_xyz98765",
  "status": "completed",
  "output_location": "s3://bucket/path/results.csv",
  "row_count": 1234,
  "size_bytes": 567890,
  "started_at": "2025-09-15T10:00:00Z",
  "completed_at": "2025-09-15T10:05:30Z"
}
```

#### POST /api/reports/executions/{execution_id}/cancel
Cancel a pending or running execution.

**Response:**
```json
{
  "message": "Execution cancelled"
}
```

### Schedule Management

#### POST /api/reports/{report_id}/schedules
Create a recurring schedule for a report.

```http
POST /api/reports/{report_id}/schedules
Authorization: Bearer {jwt_token}

{
  "schedule_type": "weekly",
  "cron_expression": "0 9 * * 1",
  "timezone": "America/New_York",
  "default_parameters": {
    "date_range": "last_7_days"
  },
  "is_active": true
}
```

**Response:** `201 Created`

#### GET /api/reports/{report_id}/schedules
List all schedules for a report.

#### POST /api/reports/schedules/{schedule_id}/pause
Pause a recurring schedule.

#### POST /api/reports/schedules/{schedule_id}/resume
Resume a paused schedule.

#### DELETE /api/reports/schedules/{schedule_id}
Delete a schedule permanently.

### Template Integration

#### GET /api/reports/templates/
List available report templates with filtering.

```http
GET /api/reports/templates/?category=performance&report_type=analysis
```

#### GET /api/reports/templates/{template_id}
Get template details with report-specific configuration.

### Dashboard Integration

#### POST /api/reports/{report_id}/dashboard
Link an existing dashboard to a report.

```http
POST /api/reports/{report_id}/dashboard

{
  "dashboard_id": "dashboard-uuid"
}
```

#### DELETE /api/reports/{report_id}/dashboard
Unlink dashboard from report.

### Backfill Operations

#### POST /api/reports/{report_id}/backfill
Create a historical data backfill job.

```http
POST /api/reports/{report_id}/backfill

{
  "start_date": "2025-08-01",
  "end_date": "2025-09-14",
  "segment_type": "weekly",
  "parameters": {
    "campaigns": ["specific-campaign"]
  }
}
```

**Response:** `202 Accepted`

#### GET /api/reports/backfill/{backfill_id}
Get backfill progress and status.

```json
{
  "id": "uuid",
  "status": "running",
  "progress": {
    "total_segments": 6,
    "completed_segments": 4,
    "failed_segments": 0,
    "progress_percentage": 67
  },
  "estimated_completion": "2025-09-15T11:30:00Z"
}
```

### Metadata Services

#### GET /api/reports/overview
Get comprehensive overview of user's reports.

```json
{
  "total_reports": 12,
  "active_reports": 8,
  "total_executions": 145,
  "recent_executions": [...],
  "scheduled_reports": 5,
  "next_scheduled_run": "2025-09-16T09:00:00Z"
}
```

#### GET /api/reports/stats
Get execution statistics over time.

```http
GET /api/reports/stats?days=30
```

**Response:**
```json
{
  "period": "30_days",
  "total_executions": 89,
  "successful_executions": 83,
  "failed_executions": 6,
  "success_rate": 93.3,
  "avg_execution_time": "4.2_minutes",
  "execution_trend": [...]
}
```

## Error Responses

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content (for DELETE operations)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `422` - Unprocessable Entity (business logic error)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "detail": "Validation failed",
  "status_code": 400,
  "errors": {
    "name": ["This field is required"],
    "sql_query": ["Invalid SQL syntax"]
  }
}
```

## Rate Limiting
- **Default**: 1000 requests per hour per user
- **Authentication**: 10 login attempts per 15 minutes
- **Execution**: 100 workflow executions per hour per user
- **AMC API**: Respects Amazon's rate limits (varies by endpoint)

## WebSocket Endpoints (Future)
```
ws://localhost:8001/ws/executions/{execution_id}
ws://localhost:8001/ws/collections/{collection_id}
ws://localhost:8001/ws/dashboards/{dashboard_id}
```

## API Versioning
- Current version: v1 (implicit in all routes)
- Future versions will be prefixed: `/api/v2/workflows/`
- Backward compatibility maintained for at least 6 months

This comprehensive API documentation covers all major endpoints and operations in RecomAMP, following RESTful principles and providing consistent patterns for frontend integration.