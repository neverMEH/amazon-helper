# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-23-report-builder-dashboards/spec.md

> Created: 2025-09-23
> Version: 1.0.0

## Endpoints

### Report Configuration

#### POST /api/reports/configure
**Purpose:** Enable or disable report generation for a workflow
**Parameters:**
- Body: `{ workflow_id: UUID, enabled: boolean, dashboard_type?: string, visualization_config?: object }`
**Response:** `{ id: UUID, workflow_id: UUID, enabled: boolean, dashboard_type: string, created_at: timestamp }`
**Errors:** 404 (workflow not found), 400 (invalid configuration)

#### GET /api/reports/configurations
**Purpose:** List all report-enabled workflows for current user
**Parameters:**
- Query: `?enabled=true&dashboard_type=funnel`
**Response:** `[{ id: UUID, workflow_id: UUID, workflow_name: string, enabled: boolean, dashboard_type: string, last_updated: timestamp }]`
**Errors:** 401 (unauthorized)

#### PUT /api/reports/configure/{config_id}
**Purpose:** Update report configuration settings
**Parameters:**
- Path: `config_id` (UUID)
- Body: `{ enabled?: boolean, dashboard_type?: string, visualization_config?: object }`
**Response:** `{ id: UUID, workflow_id: UUID, updated_at: timestamp }`
**Errors:** 404 (configuration not found), 403 (forbidden)

### Dashboard Generation

#### POST /api/dashboards/generate
**Purpose:** Trigger dashboard generation for a workflow
**Parameters:**
- Body: `{ workflow_id: UUID, execution_ids?: UUID[], date_range?: { start: date, end: date } }`
**Response:** `{ dashboard_id: UUID, status: 'processing', estimated_completion: timestamp }`
**Errors:** 404 (workflow not found), 400 (no data available), 429 (rate limited)

#### GET /api/dashboards/{dashboard_id}
**Purpose:** Retrieve generated dashboard data
**Parameters:**
- Path: `dashboard_id` (UUID)
- Query: `?include_insights=true`
**Response:**
```json
{
  "id": "UUID",
  "workflow_id": "UUID",
  "data_range": { "start": "date", "end": "date" },
  "metrics": { "revenue": 0, "roas": 0, "purchases": 0 },
  "charts": { "funnel": [], "trends": [], "distributions": [] },
  "insights": [{ "type": "string", "text": "string", "confidence": 0.95 }],
  "created_at": "timestamp"
}
```
**Errors:** 404 (dashboard not found), 403 (forbidden)

#### GET /api/dashboards
**Purpose:** List available dashboards for user
**Parameters:**
- Query: `?workflow_id=UUID&limit=10&offset=0`
**Response:** `{ dashboards: [], total: 0, has_more: false }`
**Errors:** 401 (unauthorized)

### Historical Data Collection

#### POST /api/reports/collect-historical
**Purpose:** Start historical data collection for report generation
**Parameters:**
- Body: `{ workflow_id: UUID, weeks_back: number, parallel_executions?: number }`
**Response:** `{ collection_id: UUID, status: 'queued', estimated_duration_minutes: 30 }`
**Errors:** 404 (workflow not found), 409 (collection already in progress)

#### GET /api/reports/collection-status/{collection_id}
**Purpose:** Check status of historical data collection
**Parameters:**
- Path: `collection_id` (UUID)
**Response:** `{ id: UUID, status: 'processing', progress: 0.75, completed_weeks: 39, total_weeks: 52 }`
**Errors:** 404 (collection not found)

### AI Insights

#### POST /api/insights/generate
**Purpose:** Generate AI insights for dashboard data
**Parameters:**
- Body: `{ dashboard_id: UUID, insight_types?: string[], regenerate?: boolean }`
**Response:** `{ insights: [{ type: string, text: string, confidence: number, data_points: object }] }`
**Errors:** 404 (dashboard not found), 429 (AI rate limited), 503 (AI service unavailable)

#### GET /api/insights/{dashboard_id}
**Purpose:** Retrieve previously generated insights
**Parameters:**
- Path: `dashboard_id` (UUID)
- Query: `?type=performance&limit=5`
**Response:** `{ insights: [], generated_at: timestamp, model_version: string }`
**Errors:** 404 (no insights found)

### Export

#### POST /api/dashboards/{dashboard_id}/export
**Purpose:** Export dashboard as PDF or image
**Parameters:**
- Path: `dashboard_id` (UUID)
- Body: `{ format: 'pdf'|'png', include_insights: boolean, paper_size?: 'a4'|'letter' }`
**Response:** `{ export_id: UUID, status: 'processing', estimated_completion: timestamp }`
**Errors:** 404 (dashboard not found), 400 (invalid format)

#### GET /api/exports/{export_id}/download
**Purpose:** Download exported dashboard file
**Parameters:**
- Path: `export_id` (UUID)
**Response:** Binary file stream with appropriate Content-Type header
**Errors:** 404 (export not found), 410 (export expired)

## WebSocket Events

### Dashboard Updates
```javascript
// Subscribe to dashboard updates
ws.subscribe('dashboard:workflow:{workflow_id}')

// Events
{
  type: 'dashboard.updated',
  payload: { dashboard_id: UUID, workflow_id: UUID }
}

{
  type: 'dashboard.processing',
  payload: { progress: 0.5, current_step: 'aggregating_data' }
}

{
  type: 'insights.generated',
  payload: { dashboard_id: UUID, insight_count: 5 }
}
```

## Rate Limiting

- Dashboard generation: 10 per hour per user
- AI insights: 20 per hour per user
- Exports: 50 per day per user
- Historical collection: 2 concurrent per user

## Error Response Format

```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "The specified workflow does not exist",
    "details": { "workflow_id": "UUID" },
    "request_id": "req_123abc"
  }
}
```

## Authentication

All endpoints require Bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

Report configurations and dashboards are scoped to the authenticated user through RLS policies.