# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-09-05-reports-analytics-platform/spec.md

> Created: 2025-09-05
> Version: 1.0.0

## Endpoints

### Dashboard Management

#### GET /api/dashboards/
**Purpose:** List all dashboards for the current user with optional filtering
**Parameters:** 
- `template_type` (optional): Filter by dashboard template type
- `is_public` (optional): Include public dashboards
- `search` (optional): Search by name or description
**Response:** Array of dashboard objects with metadata
**Errors:** 401 (Unauthorized), 500 (Server Error)

#### POST /api/dashboards/
**Purpose:** Create a new dashboard
**Parameters:** 
- `name` (required): Dashboard name
- `description` (optional): Dashboard description
- `template_type` (optional): Dashboard template type
- `layout_config` (optional): Initial layout configuration
**Response:** 201 Created with dashboard object
**Errors:** 400 (Validation Error), 401 (Unauthorized), 500 (Server Error)

#### GET /api/dashboards/{dashboard_id}
**Purpose:** Get specific dashboard with all widgets and configuration
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
**Response:** Complete dashboard object with widgets array
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

#### PUT /api/dashboards/{dashboard_id}
**Purpose:** Update dashboard metadata and layout
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- Request body: Updated dashboard fields
**Response:** Updated dashboard object
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden), 400 (Validation Error)

#### DELETE /api/dashboards/{dashboard_id}
**Purpose:** Delete dashboard and all associated widgets
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
**Response:** 204 No Content
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

### Dashboard Widgets

#### POST /api/dashboards/{dashboard_id}/widgets/
**Purpose:** Add new widget to dashboard
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- Request body: Widget configuration (type, title, data_source, etc.)
**Response:** 201 Created with widget object
**Errors:** 404 (Dashboard Not Found), 400 (Validation Error), 401 (Unauthorized)

#### PUT /api/dashboards/{dashboard_id}/widgets/{widget_id}
**Purpose:** Update widget configuration
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `widget_id` (path): Widget identifier
- Request body: Updated widget fields
**Response:** Updated widget object
**Errors:** 404 (Not Found), 400 (Validation Error), 401 (Unauthorized)

#### DELETE /api/dashboards/{dashboard_id}/widgets/{widget_id}
**Purpose:** Remove widget from dashboard
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `widget_id` (path): Widget identifier
**Response:** 204 No Content
**Errors:** 404 (Not Found), 401 (Unauthorized)

### Data Collection Management

#### GET /api/data-collections/
**Purpose:** List data collection operations for the current user
**Parameters:** 
- `status` (optional): Filter by collection status
- `workflow_id` (optional): Filter by workflow
- `instance_id` (optional): Filter by AMC instance
**Response:** Array of collection objects with progress information
**Errors:** 401 (Unauthorized), 500 (Server Error)

#### POST /api/data-collections/
**Purpose:** Start new historical data collection (backfill)
**Parameters:** 
- `workflow_id` (required): Workflow to execute
- `instance_id` (required): AMC instance for execution
- `target_weeks` (required): Number of weeks to collect
- `start_date` (required): Collection start date
- `end_date` (required): Collection end date
- `collection_type` (optional): 'backfill' or 'weekly_update'
**Response:** 201 Created with collection object
**Errors:** 400 (Validation Error), 401 (Unauthorized), 409 (Collection Already Running)

#### GET /api/data-collections/{collection_id}
**Purpose:** Get collection status and detailed progress
**Parameters:** 
- `collection_id` (path): Collection identifier
**Response:** Collection object with week-by-week progress
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

#### POST /api/data-collections/{collection_id}/pause
**Purpose:** Pause running data collection
**Parameters:** 
- `collection_id` (path): Collection identifier
**Response:** Updated collection object
**Errors:** 404 (Not Found), 401 (Unauthorized), 400 (Invalid State)

#### POST /api/data-collections/{collection_id}/resume
**Purpose:** Resume paused data collection
**Parameters:** 
- `collection_id` (path): Collection identifier
**Response:** Updated collection object
**Errors:** 404 (Not Found), 401 (Unauthorized), 400 (Invalid State)

#### DELETE /api/data-collections/{collection_id}
**Purpose:** Cancel and delete data collection
**Parameters:** 
- `collection_id` (path): Collection identifier
**Response:** 204 No Content
**Errors:** 404 (Not Found), 401 (Unauthorized), 409 (Cannot Delete Running Collection)

### Dashboard Data

#### GET /api/dashboards/{dashboard_id}/data
**Purpose:** Get aggregated data for dashboard widgets
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `date_range` (optional): Date range filter (e.g., "2024-01-01,2024-12-31")
- `aggregation` (optional): Aggregation level ('daily', 'weekly', 'monthly')
- `widgets` (optional): Comma-separated widget IDs to load
**Response:** Object with widget data keyed by widget_id
**Errors:** 404 (Not Found), 401 (Unauthorized), 400 (Invalid Parameters)

#### GET /api/dashboards/{dashboard_id}/export
**Purpose:** Export dashboard data as CSV or PDF
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `format` (query): Export format ('csv', 'pdf')
- `date_range` (optional): Date range filter
**Response:** File download with appropriate content-type
**Errors:** 404 (Not Found), 401 (Unauthorized), 400 (Invalid Format)

### AI Insights

#### POST /api/ai/insights/
**Purpose:** Generate AI insights from natural language query
**Parameters:** 
- `query` (required): Natural language question about data
- `dashboard_id` (optional): Dashboard context for the query
- `date_range` (optional): Time period to analyze
- `instance_ids` (optional): AMC instances to include in analysis
**Response:** AI insight object with response text and confidence score
**Errors:** 400 (Invalid Query), 401 (Unauthorized), 429 (Rate Limited), 500 (AI Service Error)

#### GET /api/ai/insights/
**Purpose:** Get user's AI insight history
**Parameters:** 
- `dashboard_id` (optional): Filter by dashboard
- `limit` (optional): Number of insights to return (default 20)
- `offset` (optional): Pagination offset
**Response:** Array of AI insight objects
**Errors:** 401 (Unauthorized), 500 (Server Error)

#### GET /api/ai/insights/{insight_id}
**Purpose:** Get specific AI insight details
**Parameters:** 
- `insight_id` (path): Insight identifier
**Response:** Complete insight object with context data
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

### Dashboard Sharing

#### POST /api/dashboards/{dashboard_id}/share
**Purpose:** Share dashboard with another user
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `user_email` (required): Email of user to share with
- `permission` (required): Permission level ('view' or 'edit')
**Response:** Share object with confirmation
**Errors:** 404 (Dashboard/User Not Found), 401 (Unauthorized), 400 (Invalid Permission)

#### GET /api/dashboards/{dashboard_id}/shares
**Purpose:** List users with access to dashboard
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
**Response:** Array of share objects with user information
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

#### DELETE /api/dashboards/{dashboard_id}/shares/{user_id}
**Purpose:** Remove user access to dashboard
**Parameters:** 
- `dashboard_id` (path): Dashboard identifier
- `user_id` (path): User identifier to remove
**Response:** 204 No Content
**Errors:** 404 (Not Found), 401 (Unauthorized), 403 (Forbidden)

### Dashboard Templates

#### GET /api/dashboard-templates/
**Purpose:** List available dashboard templates
**Parameters:** 
- `category` (optional): Filter by template category
**Response:** Array of template objects with preview configurations
**Errors:** 401 (Unauthorized), 500 (Server Error)

#### POST /api/dashboard-templates/{template_id}/create
**Purpose:** Create dashboard from template
**Parameters:** 
- `template_id` (path): Template identifier
- `name` (required): Name for new dashboard
- `instance_id` (required): AMC instance to use
- `workflow_ids` (required): Array of workflow IDs for data source
**Response:** 201 Created with new dashboard object
**Errors:** 404 (Template Not Found), 400 (Validation Error), 401 (Unauthorized)

## Controllers

### DashboardController
- **create_dashboard()** - Handle dashboard creation with validation and user assignment
- **update_dashboard()** - Update dashboard metadata and layout configuration
- **get_dashboard_data()** - Aggregate and format data from multiple workflows for widgets
- **export_dashboard()** - Generate PDF/CSV exports with proper formatting
- **share_dashboard()** - Manage dashboard sharing permissions and notifications

### DataCollectionController
- **start_collection()** - Initialize historical data backfill with progress tracking
- **monitor_collection()** - Track collection progress and handle failures
- **merge_collection_data()** - Intelligent data merging with duplicate detection
- **pause_resume_collection()** - Control collection execution state
- **cleanup_failed_collections()** - Handle cleanup of incomplete collections

### AIInsightsController
- **generate_insight()** - Process natural language queries and generate business insights
- **format_ai_context()** - Prepare data context for LLM consumption
- **validate_ai_response()** - Ensure AI responses are relevant and accurate
- **store_insight_history()** - Save insights for future reference and learning
- **get_insight_suggestions()** - Provide suggested questions based on available data

### AggregationController
- **compute_aggregates()** - Calculate weekly/monthly aggregates from raw execution data
- **update_aggregates()** - Incremental updates when new data arrives
- **optimize_aggregates()** - Cleanup and optimization of aggregate data
- **validate_aggregates()** - Data quality checks for aggregated metrics

### TemplateController
- **list_templates()** - Provide available dashboard templates by category
- **create_from_template()** - Initialize dashboard from template with user-specific data sources
- **validate_template_compatibility()** - Ensure template works with user's workflows and instances