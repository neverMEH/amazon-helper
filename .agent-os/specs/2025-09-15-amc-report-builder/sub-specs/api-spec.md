# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-15-amc-report-builder/spec.md

## API Endpoints

### Template Management

#### GET /api/report-builder/templates

**Purpose:** List all available report templates with filtering and pagination
**Parameters:**
- `category` (query, optional): Filter by template category
- `report_type` (query, optional): Filter by report type
- `instance_id` (query, optional): Filter by instance compatibility
- `search` (query, optional): Search in name and description
- `page` (query, optional): Page number for pagination
- `limit` (query, optional): Items per page (default: 20)

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "name": "Campaign Performance Analysis",
      "description": "Analyze campaign metrics",
      "category": "performance",
      "report_type": "campaign_analysis",
      "parameter_definitions": {},
      "ui_schema": {},
      "report_config": {}
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```
**Errors:** 401 Unauthorized, 500 Internal Server Error

#### GET /api/report-builder/templates/{template_id}

**Purpose:** Get detailed template information including parameter definitions
**Parameters:**
- `template_id` (path, required): Template UUID

**Response:** Complete template object with sql_template, parameter_definitions, ui_schema, and report_config
**Errors:** 401 Unauthorized, 404 Not Found

#### POST /api/report-builder/templates/{template_id}/validate-parameters

**Purpose:** Validate parameters against template requirements before execution
**Parameters:**
- `template_id` (path, required): Template UUID
- Body: `{ "parameters": {}, "instance_id": "uuid" }`

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "preview_sql": "SELECT...",
  "estimated_cost": "low"
}
```
**Errors:** 400 Bad Request (validation errors), 404 Not Found

#### POST /api/report-builder/templates/{template_id}/execute

**Purpose:** Execute template ad-hoc without creating a report definition
**Parameters:**
- `template_id` (path, required): Template UUID
- Body:
```json
{
  "instance_id": "uuid",
  "parameters": {},
  "time_window": {
    "start": "2025-01-01T00:00:00",
    "end": "2025-01-31T23:59:59"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_abc123",
  "status": "pending",
  "amc_execution_id": null,
  "created_at": "2025-09-15T10:00:00Z"
}
```
**Errors:** 400 Bad Request, 403 Forbidden (no instance access), 429 Too Many Requests

### Report Management

#### POST /api/report-builder/reports

**Purpose:** Create a new report definition with optional immediate execution
**Parameters:**
- Body:
```json
{
  "template_id": "uuid",
  "instance_id": "uuid",
  "name": "Monthly Campaign Report",
  "description": "Optional description",
  "parameters": {
    "campaign_ids": ["123", "456"],
    "metrics": ["impressions", "clicks"]
  },
  "run": {
    "type": "once|recurring|backfill",
    "frequency": "daily|weekly|monthly|quarterly",
    "timezone": "America/New_York",
    "execute_now": true,
    "backfill": {
      "segment": "weekly",
      "lookback_days": 180
    }
  }
}
```

**Response:**
```json
{
  "report_id": "rpt_abc123",
  "uuid": "uuid",
  "dashboard_id": "uuid",
  "execution_id": "exec_123",
  "schedule_id": "sch_123"
}
```
**Errors:** 400 Bad Request, 403 Forbidden, 409 Conflict (duplicate report_id)

#### GET /api/report-builder/reports

**Purpose:** List user's reports with filtering and status information
**Parameters:**
- `instance_id` (query, optional): Filter by AMC instance
- `owner_id` (query, optional): Filter by owner (admin only)
- `state` (query, optional): active|inactive|paused
- `frequency` (query, optional): once|daily|weekly|monthly|quarterly
- `search` (query, optional): Search in name and description
- `page` (query, optional): Page number
- `limit` (query, optional): Items per page

**Response:** Array of report definitions from report_runs_overview view
**Errors:** 401 Unauthorized, 403 Forbidden

#### GET /api/report-builder/reports/{report_id}

**Purpose:** Get detailed report information including execution history
**Parameters:**
- `report_id` (path, required): Report UUID or report_id string

**Response:** Complete report object with recent executions and schedule details
**Errors:** 401 Unauthorized, 403 Forbidden, 404 Not Found

#### PATCH /api/report-builder/reports/{report_id}

**Purpose:** Update report configuration or state
**Parameters:**
- `report_id` (path, required): Report UUID
- Body:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_active": false,
  "parameters": {}
}
```

**Response:** Updated report object
**Errors:** 400 Bad Request, 403 Forbidden, 404 Not Found

#### POST /api/report-builder/reports/{report_id}/run

**Purpose:** Manually trigger report execution
**Parameters:**
- `report_id` (path, required): Report UUID
- Body (optional): `{ "parameters": {} }` to override defaults

**Response:**
```json
{
  "execution_id": "exec_456",
  "status": "pending"
}
```
**Errors:** 403 Forbidden, 404 Not Found, 429 Too Many Requests

#### POST /api/report-builder/reports/{report_id}/backfill

**Purpose:** Initiate historical data backfill for a report
**Parameters:**
- `report_id` (path, required): Report UUID
- Body:
```json
{
  "segment": "daily|weekly|monthly",
  "lookback_days": 90,
  "end_date": "2025-09-15"
}
```

**Response:**
```json
{
  "collection_id": "col_123",
  "total_segments": 13,
  "status": "pending"
}
```
**Errors:** 400 Bad Request (exceeds 365 days), 403 Forbidden, 409 Conflict (backfill in progress)

### Schedule Management

#### POST /api/report-builder/reports/{report_id}/schedules

**Purpose:** Create or update schedule for a report
**Parameters:**
- `report_id` (path, required): Report UUID
- Body:
```json
{
  "schedule_type": "daily|weekly|monthly|quarterly|custom",
  "cron_expression": "0 2 * * *",
  "timezone": "America/New_York",
  "default_parameters": {}
}
```

**Response:** Created schedule object
**Errors:** 400 Bad Request, 403 Forbidden, 409 Conflict (schedule exists)

#### PATCH /api/report-builder/schedules/{schedule_id}

**Purpose:** Update schedule configuration or pause/resume
**Parameters:**
- `schedule_id` (path, required): Schedule UUID
- Body:
```json
{
  "is_paused": true,
  "cron_expression": "0 3 * * *",
  "default_parameters": {}
}
```

**Response:** Updated schedule object
**Errors:** 403 Forbidden, 404 Not Found

#### DELETE /api/report-builder/schedules/{schedule_id}

**Purpose:** Delete a schedule (does not delete the report)
**Parameters:**
- `schedule_id` (path, required): Schedule UUID

**Response:** 204 No Content
**Errors:** 403 Forbidden, 404 Not Found

### Execution Monitoring

#### GET /api/report-builder/executions

**Purpose:** List report executions with filtering
**Parameters:**
- `report_id` (query, optional): Filter by report
- `instance_id` (query, optional): Filter by instance
- `status` (query, optional): pending|running|completed|failed
- `triggered_by` (query, optional): manual|schedule|backfill
- `start_date` (query, optional): Filter by execution start date
- `end_date` (query, optional): Filter by execution end date

**Response:** Array of execution records with status and timing information
**Errors:** 401 Unauthorized

#### GET /api/report-builder/executions/{execution_id}

**Purpose:** Get detailed execution information including results
**Parameters:**
- `execution_id` (path, required): Execution UUID or execution_id string

**Response:** Complete execution object with output location and error details
**Errors:** 401 Unauthorized, 403 Forbidden, 404 Not Found

#### POST /api/report-builder/executions/{execution_id}/cancel

**Purpose:** Cancel a pending or running execution
**Parameters:**
- `execution_id` (path, required): Execution UUID

**Response:**
```json
{
  "status": "cancelled",
  "cancelled_at": "2025-09-15T10:00:00Z"
}
```
**Errors:** 400 Bad Request (not cancellable), 403 Forbidden, 404 Not Found

### Dashboard Integration

#### GET /api/dashboards

**Purpose:** List all dashboards including report-generated ones
**Parameters:** Standard dashboard filters plus `report_id` filter

**Response:** Array of dashboard objects with report association
**Errors:** 401 Unauthorized

#### POST /api/dashboards/{dashboard_id}/favorite

**Purpose:** Add dashboard to user's favorites
**Parameters:**
- `dashboard_id` (path, required): Dashboard UUID

**Response:** 201 Created
**Errors:** 403 Forbidden, 404 Not Found, 409 Conflict (already favorited)

#### DELETE /api/dashboards/{dashboard_id}/favorite

**Purpose:** Remove dashboard from user's favorites
**Parameters:**
- `dashboard_id` (path, required): Dashboard UUID

**Response:** 204 No Content
**Errors:** 404 Not Found

#### POST /api/dashboards/{dashboard_id}/export

**Purpose:** Export dashboard to PDF or PowerPoint
**Parameters:**
- `dashboard_id` (path, required): Dashboard UUID
- `format` (query, required): pdf|pptx
- `include_data` (query, optional): Include raw data tables

**Response:** Binary file stream or job ID for async generation
**Errors:** 403 Forbidden, 404 Not Found, 422 Unprocessable (no data)

### AI Integration

#### POST /api/dashboards/{dashboard_id}/ai/query

**Purpose:** Query dashboard data using natural language
**Parameters:**
- `dashboard_id` (path, required): Dashboard UUID
- Body: `{ "query": "Why did ROAS drop last week?" }`

**Response:**
```json
{
  "answer": "ROAS decreased by 15% due to...",
  "supporting_data": [],
  "confidence": 0.85
}
```
**Errors:** 403 Forbidden, 404 Not Found, 422 Unprocessable

#### GET /api/dashboards/{dashboard_id}/ai/insights

**Purpose:** Get AI-generated insights for dashboard data
**Parameters:**
- `dashboard_id` (path, required): Dashboard UUID

**Response:**
```json
{
  "insights": [
    {
      "type": "trend",
      "message": "Campaign X shows declining performance",
      "severity": "warning",
      "data_points": []
    }
  ]
}
```
**Errors:** 403 Forbidden, 404 Not Found

### Metadata Services

#### GET /api/report-builder/metadata/campaigns

**Purpose:** Get campaigns for parameter selection
**Parameters:**
- `instance_id` (query, required): AMC instance UUID
- `search` (query, optional): Search term

**Response:** Array of campaign objects with id and name
**Errors:** 403 Forbidden

#### GET /api/report-builder/metadata/asins

**Purpose:** Get ASINs for parameter selection
**Parameters:**
- `instance_id` (query, required): AMC instance UUID
- `search` (query, optional): Search term

**Response:** Array of ASIN objects
**Errors:** 403 Forbidden

## WebSocket Events

### Report Execution Updates
```javascript
// Subscribe to execution updates
ws.send({
  "action": "subscribe",
  "type": "execution",
  "execution_id": "exec_123"
});

// Receive updates
{
  "type": "execution_update",
  "execution_id": "exec_123",
  "status": "running",
  "progress": 45,
  "message": "Processing segment 3 of 7"
}
```

### Schedule Notifications
```javascript
// Subscribe to schedule events
ws.send({
  "action": "subscribe",
  "type": "schedule",
  "report_id": "rpt_123"
});

// Receive notifications
{
  "type": "schedule_triggered",
  "schedule_id": "sch_123",
  "execution_id": "exec_456",
  "next_run_at": "2025-09-16T02:00:00Z"
}
```

## Error Response Format

All errors follow consistent format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameters provided",
    "details": {
      "field": "campaign_ids",
      "reason": "At least one campaign ID required"
    }
  },
  "request_id": "req_abc123",
  "timestamp": "2025-09-15T10:00:00Z"
}
```

## Rate Limiting

- Template execution: 10 per minute per user
- Report creation: 20 per hour per user
- Backfill initiation: 5 per day per instance
- Dashboard export: 10 per hour per user

Headers included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp for limit reset