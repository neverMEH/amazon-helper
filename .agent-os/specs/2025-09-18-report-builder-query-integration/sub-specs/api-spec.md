# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-18-report-builder-query-integration/spec.md

> Created: 2025-09-18
> Version: 1.0.0

## Endpoints

### GET /api/query-library/templates

**Purpose:** Fetch query templates for Report Builder template selection
**Parameters:**
- `category` (string, optional): Filter by template category
- `search` (string, optional): Search term for template name/description
- `tags` (array, optional): Filter by template tags
- `sort_by` (string, optional): Sort order (usage_count, created_at, name)
- `page` (int, optional): Page number for pagination
- `limit` (int, optional): Results per page (default: 50)
- `include_public` (boolean, optional): Include public templates from other users

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "category": "string",
      "sqlTemplate": "string",
      "parameters": {},
      "tags": ["string"],
      "usage_count": 0,
      "difficulty_level": "BEGINNER",
      "created_at": "datetime",
      "author": {
        "id": "uuid",
        "name": "string"
      }
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 10
}
```
**Errors:**
- 401: Unauthorized - User not authenticated
- 500: Internal server error

### GET /api/query-library/templates/{templateId}/full

**Purpose:** Get complete template details including parameters schema for Report Builder
**Parameters:**
- `templateId` (UUID, required): Template identifier

**Response:**
```json
{
  "template": {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "sqlTemplate": "string",
    "parameters": {
      "paramName": {
        "type": "string",
        "label": "string",
        "description": "string",
        "required": boolean,
        "default_value": "any",
        "validation_rules": {}
      }
    },
    "parametersSchema": {},
    "report_config": {},
    "usage_count": 0,
    "version": 1,
    "parent_template_id": "uuid"
  },
  "instances": [],
  "reports": []
}
```
**Errors:**
- 404: Template not found
- 401: Unauthorized - No access to template

### POST /api/query-library/templates/{templateId}/increment-usage

**Purpose:** Increment template usage count when selected in Report Builder
**Parameters:**
- `templateId` (UUID, required): Template identifier

**Response:**
```json
{
  "success": true,
  "usage_count": 101
}
```
**Errors:**
- 404: Template not found
- 401: Unauthorized

### POST /api/query-library/templates/detect-parameters

**Purpose:** Detect parameters and their contexts from SQL for custom queries
**Parameters:**
```json
{
  "sql_query": "string"
}
```

**Response:**
```json
{
  "parameters": [
    {
      "name": "string",
      "type": "asin_list|campaign_list|date_range|string|number",
      "contexts": [
        {
          "type": "LIKE|IN|VALUES|BETWEEN|EQUALS",
          "formatHint": "string",
          "example": "string"
        }
      ],
      "suggestedInputType": "string",
      "position": 0
    }
  ]
}
```
**Errors:**
- 400: Invalid SQL query
- 500: Parameter detection failed

### POST /api/reports/create-from-template

**Purpose:** Create a new report from a query template with parameters
**Parameters:**
```json
{
  "templateId": "uuid",
  "reportName": "string",
  "reportDescription": "string",
  "instanceId": "string",
  "parameters": {
    "paramName": "value"
  },
  "executionType": "once|recurring|backfill",
  "scheduleConfig": {
    "frequency": "daily|weekly|monthly",
    "time": "09:00",
    "dayOfWeek": 0,
    "dayOfMonth": 1
  },
  "backfillPeriod": 7
}
```

**Response:**
```json
{
  "reportId": "uuid",
  "status": "created",
  "message": "Report created successfully",
  "firstExecution": {
    "scheduledAt": "datetime",
    "estimatedDuration": "5 minutes"
  }
}
```
**Errors:**
- 400: Invalid parameters or configuration
- 404: Template not found
- 401: Unauthorized
- 422: Parameter validation failed

### GET /api/query-library/categories

**Purpose:** Get available template categories with counts for navigation
**Parameters:** None

**Response:**
```json
{
  "categories": [
    {
      "name": "Attribution",
      "count": 15,
      "icon": "🎯",
      "description": "Cross-channel attribution analysis"
    },
    {
      "name": "Performance Analysis",
      "count": 23,
      "icon": "📊",
      "description": "Campaign and ad performance metrics"
    }
  ]
}
```
**Errors:**
- 500: Internal server error

### POST /api/query-library/templates/{templateId}/validate-parameters

**Purpose:** Validate parameter values against template schema before report creation
**Parameters:**
```json
{
  "parameters": {
    "paramName": "value"
  }
}
```

**Response:**
```json
{
  "valid": boolean,
  "errors": {
    "paramName": ["Validation error message"]
  },
  "warnings": {
    "paramName": ["Warning message"]
  }
}
```
**Errors:**
- 404: Template not found
- 400: Invalid request format

## Controllers

### QueryLibraryController

**Actions:**
- `listTemplates()`: Retrieve paginated templates with filters
- `getTemplateDetails()`: Get full template information
- `incrementUsage()`: Track template usage
- `detectParameters()`: Analyze SQL for parameters
- `validateParameters()`: Check parameter values against schema
- `getCategories()`: List template categories

### ReportBuilderController

**Actions:**
- `createFromTemplate()`: Create report from template
- `validateReportConfig()`: Validate report configuration
- `estimateExecution()`: Calculate execution time/cost

## Purpose

The API enhancements enable the Report Builder to:
- Browse and select from Query Library templates
- Detect and validate parameters with context awareness
- Create reports directly from templates with proper parameter injection
- Track template usage for analytics and recommendations
- Provide real-time parameter validation before execution