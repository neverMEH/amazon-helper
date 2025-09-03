# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-03-query-flow-templates/spec.md

> Created: 2025-09-03
> Version: 1.0.0

## Endpoints

### Template Management

#### GET /api/query-flow-templates/
List all available query flow templates with filtering and search capabilities.

**Query Parameters:**
- `category`: Filter by template category
- `tags`: Filter by tags (comma-separated)
- `difficulty`: Filter by difficulty level
- `search`: Search in name and description
- `featured_only`: Show only featured templates
- `user_favorites`: Show only user's favorited templates

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "template_id": "supergoog_branded_search_trends",
      "name": "Supergoog Branded Search Trend Analysis",
      "description": "Analyze search trends and performance...",
      "category": "Brand Analysis",
      "tags": ["supergoog", "branded", "trends"],
      "difficulty_level": "intermediate",
      "estimated_runtime_seconds": 120,
      "is_featured": true,
      "usage_count": 45,
      "rating": 4.2,
      "is_favorited": false,
      "created_at": "2025-09-03T10:00:00Z",
      "parameter_count": 4,
      "chart_count": 3
    }
  ],
  "total": 1,
  "categories": ["Brand Analysis", "Campaign Performance"],
  "available_tags": ["supergoog", "branded", "trends", "campaigns"]
}
```

#### GET /api/query-flow-templates/{template_id}
Get detailed information about a specific template including parameters and chart configurations.

**Response:**
```json
{
  "id": "uuid",
  "template_id": "supergoog_branded_search_trends",
  "name": "Supergoog Branded Search Trend Analysis",
  "description": "Analyze search trends and performance...",
  "category": "Brand Analysis",
  "sql_template": "WITH campaign_performance AS (...)",
  "parameters": [
    {
      "parameter_name": "start_date",
      "display_name": "Start Date",
      "parameter_type": "date",
      "is_required": true,
      "default_value": "30 days ago",
      "display_order": 1,
      "help_text": "Beginning of analysis period",
      "validation_rules": {"min_date": "2020-01-01"}
    }
  ],
  "chart_configs": [
    {
      "chart_id": "trend_line",
      "chart_type": "line",
      "title": "Sales Trend Over Time",
      "description": "Shows sales performance over time by campaign",
      "data_mapping": {
        "x": "period",
        "y": "sales", 
        "color": "campaign_name"
      },
      "styling": {
        "color_scheme": "category10",
        "show_legend": true,
        "show_grid": true
      },
      "display_order": 1,
      "is_default_view": true
    }
  ],
  "is_favorited": false,
  "usage_count": 45,
  "rating": 4.2
}
```

#### POST /api/query-flow-templates/
Create a new query flow template (admin only).

**Request Body:**
```json
{
  "template_id": "new_template_id",
  "name": "Template Name",
  "description": "Template description",
  "category": "Analysis Category",
  "sql_template": "SELECT ...",
  "tags": ["tag1", "tag2"],
  "difficulty_level": "intermediate",
  "estimated_runtime_seconds": 60,
  "parameters": [...],
  "chart_configs": [...]
}
```

#### PUT /api/query-flow-templates/{template_id}
Update an existing template (admin only).

#### DELETE /api/query-flow-templates/{template_id}
Soft delete a template (admin only).

### Template Execution

#### POST /api/query-flow-templates/{template_id}/execute
Execute a template with provided parameters.

**Request Body:**
```json
{
  "instance_id": "uuid",
  "parameters": {
    "start_date": "2025-08-01",
    "end_date": "2025-09-01", 
    "campaign_ids": ["123", "456"],
    "aggregation_level": "week"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "template_execution_id": "uuid",
  "workflow_execution_id": "uuid", 
  "status": "pending",
  "generated_sql": "WITH campaign_performance AS (...)",
  "estimated_completion": "2025-09-03T10:02:00Z",
  "created_at": "2025-09-03T10:00:00Z"
}
```

#### GET /api/query-flow-templates/executions/{execution_id}
Get execution status and results.

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "template_id": "supergoog_branded_search_trends",
  "template_name": "Supergoog Branded Search Trend Analysis",
  "status": "completed",
  "parameters": {...},
  "generated_sql": "WITH campaign_performance AS (...)",
  "results": {
    "columns": ["period", "campaign_name", "sales", "ctr"],
    "rows": [
      ["2025-08-01", "Campaign A", 1500.00, 2.4],
      ["2025-08-01", "Campaign B", 1200.00, 3.1]
    ],
    "row_count": 2
  },
  "charts": [
    {
      "chart_id": "trend_line",
      "chart_type": "line",
      "title": "Sales Trend Over Time",
      "data": [...],
      "config": {...}
    }
  ],
  "execution_time_seconds": 45,
  "started_at": "2025-09-03T10:00:00Z",
  "completed_at": "2025-09-03T10:00:45Z"
}
```

#### GET /api/query-flow-templates/executions/
List user's template executions with filtering.

**Query Parameters:**
- `template_id`: Filter by template
- `status`: Filter by execution status
- `limit`: Number of results (default 50)
- `offset`: Pagination offset

### Parameter Validation

#### POST /api/query-flow-templates/{template_id}/validate-parameters
Validate parameters before execution.

**Request Body:**
```json
{
  "parameters": {
    "start_date": "2025-08-01",
    "end_date": "2025-09-01",
    "campaign_ids": ["123", "456"]
  }
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "parameter": "campaign_ids", 
      "message": "Campaign 456 has no recent activity"
    }
  ],
  "generated_sql_preview": "WITH campaign_performance AS (...)"
}
```

### User Interactions

#### POST /api/query-flow-templates/{template_id}/favorite
Toggle template favorite status.

**Response:**
```json
{
  "is_favorited": true
}
```

#### POST /api/query-flow-templates/{template_id}/rate
Rate and review a template.

**Request Body:**
```json
{
  "rating": 5,
  "review": "Excellent template for brand analysis"
}
```

#### GET /api/query-flow-templates/{template_id}/usage-stats
Get template usage statistics (admin only).

**Response:**
```json
{
  "total_executions": 156,
  "unique_users": 23,
  "avg_rating": 4.2,
  "execution_history": [
    {
      "date": "2025-09-01",
      "executions": 12,
      "unique_users": 8
    }
  ],
  "popular_parameters": {
    "aggregation_level": {
      "day": 45,
      "week": 78,
      "month": 33
    }
  }
}
```

## Controllers

### QueryFlowTemplateController
Main controller handling all template CRUD operations, search, and filtering functionality.

**Key Methods:**
- `list_templates()`: Handle GET /api/query-flow-templates/ with filtering
- `get_template()`: Handle GET /api/query-flow-templates/{template_id}
- `create_template()`: Handle POST /api/query-flow-templates/ (admin)
- `update_template()`: Handle PUT /api/query-flow-templates/{template_id} (admin)
- `delete_template()`: Handle DELETE /api/query-flow-templates/{template_id} (admin)

### TemplateExecutionController
Controller for template execution and result management.

**Key Methods:**
- `execute_template()`: Handle POST /api/query-flow-templates/{template_id}/execute
- `get_execution()`: Handle GET /api/query-flow-templates/executions/{execution_id}
- `list_executions()`: Handle GET /api/query-flow-templates/executions/
- `validate_parameters()`: Handle POST /api/query-flow-templates/{template_id}/validate-parameters

### TemplateInteractionController
Controller for user interactions with templates (favorites, ratings).

**Key Methods:**
- `toggle_favorite()`: Handle POST /api/query-flow-templates/{template_id}/favorite
- `rate_template()`: Handle POST /api/query-flow-templates/{template_id}/rate
- `get_usage_stats()`: Handle GET /api/query-flow-templates/{template_id}/usage-stats

### Parameter Processing Service
Backend service for parameter validation, type conversion, and SQL injection.

**Key Functionality:**
- Parameter type validation (date, number, array, etc.)
- SQL injection prevention and sanitization
- Parameter dependency resolution
- Default value computation
- Integration with existing campaign/ASIN selection systems

### Chart Configuration Service
Service for managing chart configurations and data transformation.

**Key Functionality:**
- Chart configuration validation
- Data mapping from SQL results to chart format
- Chart-specific data transformations
- Export functionality for charts and data