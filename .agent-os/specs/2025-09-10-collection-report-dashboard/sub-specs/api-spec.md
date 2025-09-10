# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-10-collection-report-dashboard/spec.md

> Created: 2025-09-10
> Version: 1.0.0

## Endpoints

### GET /api/collections/{collection_id}/report-dashboard

**Purpose:** Retrieve dashboard data for a collection with optional week filtering and aggregation

**Parameters:**
- `collection_id` (path, required): UUID of the collection
- `weeks` (query, optional): Comma-separated list of week start dates to include
- `start_date` (query, optional): Start date for range filtering (ISO format)
- `end_date` (query, optional): End date for range filtering (ISO format)
- `aggregation` (query, optional): Aggregation type - 'none', 'sum', 'avg', 'min', 'max' (default: 'none')
- `group_by` (query, optional): Grouping period - 'week', 'month', 'quarter' (default: 'week')

**Response:**
```json
{
  "collection_id": "uuid",
  "collection_name": "Q1 2025 Campaign Performance",
  "metadata": {
    "total_weeks": 13,
    "successful_weeks": 12,
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-03-31"
    },
    "available_kpis": ["impressions", "clicks", "spend", "conversions", "ctr", "cpc"]
  },
  "data": [
    {
      "week_start": "2025-01-01",
      "week_end": "2025-01-07",
      "metrics": {
        "impressions": 1500000,
        "clicks": 22500,
        "spend": 4567.89,
        "conversions": 450,
        "ctr": 0.015,
        "cpc": 0.203
      },
      "execution_id": "exec-uuid",
      "row_count": 1250
    }
  ],
  "summary": {
    "total_impressions": 19500000,
    "total_clicks": 292500,
    "total_spend": 59382.57,
    "avg_ctr": 0.015,
    "avg_cpc": 0.203
  }
}
```

**Errors:**
- 404: Collection not found
- 403: User doesn't have access to collection
- 400: Invalid date parameters

### POST /api/collections/{collection_id}/report-dashboard/compare

**Purpose:** Compare two sets of weeks or periods with calculated deltas

**Parameters:**
- `collection_id` (path, required): UUID of the collection

**Request Body:**
```json
{
  "period_1": {
    "weeks": ["2025-01-01", "2025-01-08", "2025-01-15"],
    "label": "First 3 weeks"
  },
  "period_2": {
    "weeks": ["2025-02-01", "2025-02-08", "2025-02-15"],
    "label": "Month 2 - First 3 weeks"
  },
  "metrics": ["impressions", "clicks", "spend", "ctr"],
  "comparison_type": "aggregate" // or "week-by-week"
}
```

**Response:**
```json
{
  "comparison": {
    "period_1": {
      "label": "First 3 weeks",
      "metrics": {
        "impressions": 4500000,
        "clicks": 67500,
        "spend": 13703.67,
        "ctr": 0.015
      }
    },
    "period_2": {
      "label": "Month 2 - First 3 weeks",
      "metrics": {
        "impressions": 5200000,
        "clicks": 83200,
        "spend": 16536.80,
        "ctr": 0.016
      }
    },
    "delta": {
      "impressions": {
        "value": 700000,
        "percent": 15.56
      },
      "clicks": {
        "value": 15700,
        "percent": 23.26
      },
      "spend": {
        "value": 2833.13,
        "percent": 20.67
      },
      "ctr": {
        "value": 0.001,
        "percent": 6.67
      }
    }
  }
}
```

**Errors:**
- 404: Collection not found
- 400: Invalid comparison parameters
- 403: Unauthorized access

### GET /api/collections/{collection_id}/report-dashboard/chart-data

**Purpose:** Get pre-formatted data for specific chart types

**Parameters:**
- `collection_id` (path, required): UUID of the collection
- `chart_type` (query, required): 'line', 'bar', 'area', 'scatter', 'heatmap'
- `metrics` (query, required): Comma-separated list of metrics to include
- `weeks` (query, optional): Specific weeks to include
- `comparison_weeks` (query, optional): Weeks for comparison dataset

**Response:**
```json
{
  "chart_type": "line",
  "data": {
    "labels": ["Week 1", "Week 2", "Week 3"],
    "datasets": [
      {
        "label": "Impressions",
        "data": [1500000, 1600000, 1400000],
        "borderColor": "#3B82F6",
        "backgroundColor": "rgba(59, 130, 246, 0.1)"
      },
      {
        "label": "Clicks",
        "data": [22500, 24000, 21000],
        "borderColor": "#10B981",
        "backgroundColor": "rgba(16, 185, 129, 0.1)",
        "yAxisID": "y-axis-2"
      }
    ]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "legend": {
        "position": "top"
      },
      "tooltip": {
        "mode": "index",
        "intersect": false
      }
    },
    "scales": {
      "x": {
        "type": "time",
        "time": {
          "unit": "week"
        }
      }
    }
  }
}
```

**Errors:**
- 404: Collection not found
- 400: Invalid chart parameters

### POST /api/collections/{collection_id}/report-configs

**Purpose:** Save a report dashboard configuration for a collection

**Request Body:**
```json
{
  "config_name": "Q1 Performance View",
  "chart_configs": {
    "impressions": {"type": "line", "color": "#3B82F6"},
    "clicks": {"type": "bar", "color": "#10B981"},
    "spend": {"type": "area", "color": "#F59E0B"}
  },
  "default_view": "trending",
  "default_weeks_shown": 12,
  "saved_comparisons": [
    {
      "name": "Q1 vs Q2",
      "period_1": ["2025-01-01", "2025-01-08"],
      "period_2": ["2025-04-01", "2025-04-08"]
    }
  ]
}
```

**Response:**
```json
{
  "id": "config-uuid",
  "collection_id": "collection-uuid",
  "config_name": "Q1 Performance View",
  "created_at": "2025-09-10T10:00:00Z",
  "updated_at": "2025-09-10T10:00:00Z"
}
```

**Errors:**
- 400: Invalid configuration
- 409: Configuration name already exists

### GET /api/collections/{collection_id}/report-configs

**Purpose:** List saved report configurations for a collection

**Response:**
```json
{
  "configs": [
    {
      "id": "config-uuid",
      "config_name": "Q1 Performance View",
      "default_view": "trending",
      "created_at": "2025-09-10T10:00:00Z"
    }
  ]
}
```

### PUT /api/collections/{collection_id}/report-configs/{config_id}

**Purpose:** Update an existing report configuration

**Request Body:** Same as POST /report-configs

**Response:** Updated configuration object

### DELETE /api/collections/{collection_id}/report-configs/{config_id}

**Purpose:** Delete a saved report configuration

**Response:** 204 No Content

### POST /api/collections/{collection_id}/report-snapshots

**Purpose:** Create a shareable snapshot of the current report dashboard state

**Request Body:**
```json
{
  "snapshot_name": "Q1 2025 Performance Report",
  "week_range": {
    "start": "2025-01-01",
    "end": "2025-03-31"
  },
  "comparison_settings": {
    "enabled": true,
    "period_1": ["2025-01-01", "2025-01-08"],
    "period_2": ["2025-02-01", "2025-02-08"]
  },
  "include_charts": true,
  "is_public": false,
  "expires_in_days": 30
}
```

**Response:**
```json
{
  "id": "snapshot-uuid",
  "snapshot_id": "snap_q1_2025_perf",
  "share_url": "/api/report-snapshots/snap_q1_2025_perf",
  "expires_at": "2025-10-10T10:00:00Z",
  "created_at": "2025-09-10T10:00:00Z"
}
```

### GET /api/report-snapshots/{snapshot_id}

**Purpose:** Retrieve a shared report snapshot (public or authorized)

**Response:** Complete snapshot data with charts and metrics

### GET /api/collections/{collection_id}/report-dashboard/export

**Purpose:** Export report data in various formats

**Parameters:**
- `format` (query, required): 'csv', 'excel', 'pdf'
- `include_charts` (query, optional): Include chart images (default: true)
- `weeks` (query, optional): Specific weeks to export

**Response:** File download in requested format

**Errors:**
- 400: Invalid export format
- 404: Collection not found

## Controllers

### ReportDashboardController

**Actions:**
- `get_dashboard_data()`: Retrieve and format collection data for dashboard
- `compare_periods()`: Calculate comparisons between date ranges
- `get_chart_data()`: Transform data into Chart.js format
- `save_config()`: Persist user dashboard preferences
- `create_snapshot()`: Generate shareable report snapshot
- `export_report()`: Generate downloadable report files

**Business Logic:**
- Validate user access to collection data
- Parse JSONB result_rows for metric extraction
- Calculate aggregations and comparisons
- Format data for Chart.js consumption
- Handle missing or incomplete week data gracefully

**Error Handling:**
- Collection not found → 404
- Unauthorized access → 403
- Invalid parameters → 400 with details
- Database errors → 500 with generic message (log details)
- AMC API errors → 502 Bad Gateway

## Integration Points

### With Existing Collection Endpoints
- Extends `/api/data-collections/` base functionality
- Reuses authentication and authorization middleware
- Leverages existing collection data fetching services

### With Dashboard System
- Compatible with existing dashboard widget data sources
- Can be integrated as new widget type 'collection_report'
- Shares Chart.js configuration patterns

### With Export Services
- Integrates with existing PDF generation if available
- Uses common CSV/Excel export utilities
- Maintains consistent export formatting

## Rate Limiting

- Dashboard data: 60 requests per minute
- Comparisons: 30 requests per minute
- Exports: 10 requests per minute
- Snapshots: 20 per day per user

## Caching Strategy

- Dashboard data: 5-minute cache (TanStack Query)
- Chart data: 3-minute cache
- Configurations: 10-minute cache
- Snapshots: 24-hour cache for public snapshots