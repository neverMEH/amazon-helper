# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-16-report-builder-flow-update/spec.md

> Created: 2025-09-16
> Version: 1.0.0

## New Endpoints

### Report Builder Configuration

#### POST /api/report-builder/validate-parameters
**Purpose:** Validate parameter selection including lookback window configuration
**Request Body:**
```json
{
  "workflow_id": "uuid",
  "parameters": {
    "campaigns": ["campaign_id1", "campaign_id2"],
    "asins": ["B001", "B002"]
  },
  "lookback_config": {
    "type": "relative",  // or "custom"
    "value": 7,
    "unit": "days",
    "startDate": null,  // for custom type
    "endDate": null     // for custom type
  }
}
```
**Response:**
```json
{
  "valid": true,
  "estimated_data_points": 1250,
  "date_range": {
    "start": "2025-01-09",
    "end": "2025-01-16"
  },
  "warnings": []
}
```
**Errors:** 400 (Invalid parameters), 422 (Date range exceeds retention)

#### POST /api/report-builder/preview-schedule
**Purpose:** Generate preview of schedule configuration with backfill details
**Request Body:**
```json
{
  "schedule_type": "backfill_with_schedule",  // "once", "scheduled", "backfill_with_schedule"
  "schedule_config": {
    "frequency": "weekly",
    "time": "09:00",
    "timezone": "America/New_York"
  },
  "backfill_config": {
    "days": 365,
    "segmentation": "weekly",  // "daily", "weekly", "monthly"
    "parallel_limit": 10
  },
  "lookback_config": {...}  // from step 1
}
```
**Response:**
```json
{
  "total_executions": 52,
  "segments": [
    {"week_start": "2024-01-15", "week_end": "2024-01-21"},
    {"week_start": "2024-01-22", "week_end": "2024-01-28"}
  ],
  "estimated_completion_time": "2025-01-17T15:30:00Z",
  "next_scheduled_run": "2025-01-23T09:00:00-05:00"
}
```
**Errors:** 400 (Invalid configuration), 429 (Would exceed rate limits)

#### POST /api/report-builder/submit
**Purpose:** Submit the complete report configuration for execution
**Request Body:**
```json
{
  "workflow_id": "uuid",
  "parameters": {...},
  "lookback_config": {...},
  "schedule_type": "backfill_with_schedule",
  "schedule_config": {...},
  "backfill_config": {...}
}
```
**Response:**
```json
{
  "status": "submitted",
  "collection_id": "uuid",  // for backfill
  "schedule_id": "uuid",    // for scheduled
  "execution_id": "uuid",   // for once
  "tracking_url": "/executions/uuid"
}
```
**Errors:** 400 (Invalid submission), 409 (Duplicate schedule), 503 (AMC unavailable)

## Modified Endpoints

### GET /api/workflows/{workflow_id}/available-parameters
**Enhancement:** Add lookback window constraints
**Additional Response Fields:**
```json
{
  "existing_fields": "...",
  "lookback_constraints": {
    "max_days": 425,  // 14 months AMC limit
    "min_days": 1,
    "suggested_options": [7, 14, 30],
    "data_availability_start": "2023-10-01"
  }
}
```

### POST /api/data-collections/
**Enhancement:** Support lookback and segmentation configuration
**Additional Request Fields:**
```json
{
  "existing_fields": "...",
  "lookback_config": {
    "type": "relative",
    "value": 365,
    "unit": "days"
  },
  "segmentation_config": {
    "type": "weekly",
    "parallel_limit": 10,
    "retry_failed": true
  },
  "linked_schedule_id": "uuid"  // Optional link to schedule
}
```

### GET /api/data-collections/{collection_id}/progress
**Enhancement:** Include segment-level progress details
**Additional Response Fields:**
```json
{
  "existing_fields": "...",
  "segmentation_progress": {
    "total_segments": 52,
    "completed_segments": 15,
    "failed_segments": 2,
    "in_progress_segments": 3,
    "segments": [
      {
        "segment_id": "week_2024_01",
        "status": "completed",
        "start_date": "2024-01-01",
        "end_date": "2024-01-07",
        "execution_id": "amc_exec_123",
        "records_processed": 5432
      }
    ]
  }
}
```

### POST /api/schedules/
**Enhancement:** Support backfill linkage
**Additional Request Fields:**
```json
{
  "existing_fields": "...",
  "backfill_collection_id": "uuid",  // Links to backfill collection
  "schedule_config": {
    "frequency": "weekly",
    "time": "09:00",
    "timezone": "America/New_York",
    "daysOfWeek": [1, 3, 5],  // For weekly schedules
    "dayOfMonth": 15          // For monthly schedules
  }
}
```

## WebSocket Events (Future Enhancement)

### /ws/report-builder/{session_id}
**Purpose:** Real-time progress updates during backfill
**Events:**
```javascript
// Segment completed
{
  "event": "segment_completed",
  "data": {
    "segment_id": "week_2024_01",
    "progress": 0.29,  // 15/52
    "estimated_remaining": "45 minutes"
  }
}

// Backfill completed
{
  "event": "backfill_completed",
  "data": {
    "collection_id": "uuid",
    "total_segments": 52,
    "successful": 50,
    "failed": 2
  }
}
```

## Rate Limiting Considerations

### Backfill Operations
- Maximum 5 concurrent backfill operations per user
- Maximum 10 parallel segment executions per backfill
- Automatic throttling when AMC API returns 429 status

### Schedule Creation
- Maximum 100 active schedules per user
- Minimum interval between scheduled runs: 1 hour
- Automatic deduplication of identical schedules

## Error Response Format

All endpoints follow consistent error format:
```json
{
  "error": {
    "code": "INVALID_LOOKBACK_RANGE",
    "message": "Lookback period exceeds AMC's 14-month data retention limit",
    "details": {
      "requested_days": 500,
      "maximum_days": 425
    },
    "timestamp": "2025-01-16T10:30:00Z"
  }
}
```

## Authentication

All endpoints require Bearer token authentication:
```
Authorization: Bearer <jwt_token>
```

Token must include:
- user_id
- instance_id (for AMC operations)
- scopes: ["reports:write", "collections:write", "schedules:write"]