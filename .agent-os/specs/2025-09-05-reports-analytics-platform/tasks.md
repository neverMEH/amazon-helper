# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-05-reports-analytics-platform/spec.md

> Created: 2025-09-05
> Status: In Progress
> Last Updated: 2025-09-05
> Progress: Phase 1-3 Complete (3/8 phases, 9 tasks completed)
> Implementation Completed: 2025-09-06

## Phase 1: Database Foundation ✅

### Task 1.1: Create Reporting Database Schema ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Implement all new tables for the reporting platform with proper indexes and constraints.

**Technical Details:**
- ✅ Created migration script: `scripts/migrations/003_create_reporting_tables.sql`
- ✅ Implemented all 7 new tables: `dashboards`, `dashboard_widgets`, `report_data_collections`, `report_data_weeks`, `report_data_aggregates`, `ai_insights`, `dashboard_shares`
- ✅ Added all performance indexes as specified in database-schema.md
- ✅ Created update triggers for `updated_at` columns
- ✅ Added foreign key constraints with proper CASCADE settings
- ✅ Created migration helper: `scripts/apply_reporting_migration.py`

**Dependencies:** None

**Testing Requirements:**
- Verify all tables created successfully
- Test foreign key constraints
- Validate index creation and performance impact
- Test update triggers functionality

**Complexity:** Simple

**Implementation Notes:**
- Migration ready to apply via Supabase SQL Editor
- All constraints and indexes properly defined
- Rollback script included in migration comments

### Task 1.2: Create Database Service Layer ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Extend existing DatabaseService pattern for reporting platform operations.

**Technical Details:**
- ✅ Created `amc_manager/services/reporting_database_service.py`
- ✅ Inherited from existing `DatabaseService` with `@with_connection_retry`
- ✅ Implemented dashboard methods: `create_dashboard()`, `get_dashboard_with_widgets()`, `update_dashboard()`, `delete_dashboard()`, `get_user_dashboards()`
- ✅ Added widget management methods: `create_widget()`, `update_widget()`, `delete_widget()`, `reorder_widgets()`
- ✅ Implemented data collection tracking: `create_collection()`, `update_collection_progress()`, `get_collection_status()`, `create_week_record()`, `check_duplicate_week()`
- ✅ Added aggregation methods: `create_or_update_aggregate()`, `get_aggregates_for_dashboard()`, `cleanup_old_aggregates()`
- ✅ Implemented AI insights: `create_insight()`, `get_user_insights()`
- ✅ Added sharing functionality: `share_dashboard()`, `revoke_dashboard_share()`, `user_can_access_dashboard()`
- ✅ Created template system: `get_dashboard_templates()`, `create_dashboard_from_template()`

**Dependencies:** Task 1.1

**Testing Requirements:**
- Unit tests for all CRUD operations
- Test connection retry behavior
- Validate proper foreign key handling
- Test transaction rollback scenarios

**Complexity:** Medium

**Implementation Notes:**
- Full CRUD operations for all reporting entities
- Proper error handling and logging
- Checksum-based duplicate detection
- Permission system for dashboard sharing

## Phase 2: Backend Core Services ✅

### Task 2.1: Historical Data Collection Service ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Create service to manage 52-week historical data backfill operations.

**Technical Details:**
- ✅ Created `amc_manager/services/historical_collection_service.py`
- ✅ Implemented `start_backfill()` method with date parameter substitution
- ✅ Created week-by-week execution scheduling using existing `AMCExecutionService`
- ✅ Added progress tracking with database updates every completed week
- ✅ Implemented duplicate detection using data checksums
- ✅ Handled AMC API rate limiting with delays between executions (2 seconds default)
- ✅ Supported pause/resume functionality for long-running collections
- ✅ Added `execute_collection_week()` for individual week processing
- ✅ Created `get_collection_progress()` with detailed statistics
- ✅ Implemented `cleanup_abandoned_collections()` for stale collection handling

**Dependencies:** Task 1.2, existing `AMCExecutionService`

**Testing Requirements:**
- Test 52-week date range calculation
- Mock AMC API responses for testing
- Test progress tracking accuracy
- Validate duplicate detection logic
- Test pause/resume state management

**Complexity:** Complex

**Implementation Notes:**
- Handles multiple date parameter formats (start_date, week_start, date_from, etc.)
- Respects AMC 14-day data lag
- Maximum 52 weeks for backfill
- Automatic week record creation for progress tracking

### Task 2.2: Data Aggregation Service ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Create service to pre-compute aggregated data for fast dashboard queries.

**Technical Details:**
- ✅ Created `amc_manager/services/data_aggregation_service.py`
- ✅ Implemented `compute_weekly_aggregates()` from `workflow_executions` results
- ✅ Added `compute_monthly_aggregates()` for longer-term trends
- ✅ Created incremental update logic with `update_incremental_aggregates()`
- ✅ Implemented common metrics: ROAS, ACOS, CTR, CVR, CPC, CPM, NTB%
- ✅ Stored aggregates in `report_data_aggregates` table with JSONB metrics
- ✅ Added cleanup methods for old/invalid aggregates
- ✅ Extracted dimensions (campaigns, ASINs, keywords, placements, audiences)
- ✅ Created `get_metric_trends()` for time-series data
- ✅ Combined aggregation logic for rolling up weekly to monthly

**Dependencies:** Task 1.2, existing workflow execution data

**Testing Requirements:**
- Test aggregation calculations accuracy
- Validate incremental update logic
- Test performance with large datasets
- Verify JSONB storage and retrieval

**Complexity:** Medium

**Implementation Notes:**
- Supports 10 standard AMC metrics
- Calculates 8 derived metrics
- Extracts and limits dimensions (100-200 items per type)
- Handles multiple date formats for parsing

### Task 2.3: Dashboard Data Service ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Service to query and format data for dashboard widgets.

**Technical Details:**
- ✅ Created `amc_manager/services/dashboard_data_service.py`
- ✅ Implemented `get_widget_data()` method supporting 9 chart types
- ✅ Added time-series data formatting for line/area charts
- ✅ Implemented data filtering by date ranges, instances, campaigns
- ✅ Supported multiple aggregation levels (daily, weekly, monthly, quarterly, yearly)
- ✅ Added in-memory caching with 5-minute TTL for frequently requested data
- ✅ Implemented data export formatting for CSV/JSON generation
- ✅ Created specialized methods for each chart type (line, bar, pie, area, table, metric card)
- ✅ Added chart color management and metric label formatting
- ✅ Implemented cache key generation and expiration management

**Dependencies:** Task 2.2, Task 1.2

**Testing Requirements:**
- Test data formatting for different chart types
- Validate filtering and aggregation accuracy
- Test caching behavior and invalidation
- Performance test with large date ranges

**Complexity:** Medium

**Implementation Notes:**
- Supports Chart.js format for frontend visualization
- Maximum 365 data points for time series
- Maximum 1000 rows for table widgets
- Simple in-memory cache with 100 entry limit
- 10 predefined chart colors with cycling support

### Task 2.4: AI Insights Service ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Service to generate business insights using LLM integration.

**Technical Details:**
- ✅ Created `amc_manager/services/ai_insights_service.py`
- ✅ Implemented OpenAI API integration with tenacity retry patterns
- ✅ Added Anthropic Claude API as fallback option
- ✅ Created `generate_insight()` method with data context preparation
- ✅ Built 6 prompt templates for different insight types (trends, anomalies, optimization, comparison, forecast, summary)
- ✅ Implemented conversation context management for multi-turn queries
- ✅ Added confidence scoring (0.85 for GPT-4, 0.82 for Claude, 0.5 for mock)
- ✅ Stored insight history in `ai_insights` table
- ✅ Created `analyze_anomalies()` method with statistical detection
- ✅ Added `get_suggested_questions()` based on current data
- ✅ Implemented mock responses when no AI API configured

**Dependencies:** Task 1.2, existing token management

**Testing Requirements:**
- Test AI API integration with mock responses
- Validate context preparation accuracy
- Test conversation memory functionality
- Verify insight storage and retrieval

**Complexity:** Complex

**Implementation Notes:**
- Supports both OpenAI and Anthropic APIs
- Conversation context limited to 10 messages
- Automatic metric extraction from AI responses
- Z-score based anomaly detection with configurable sensitivity
- Mock responses for development without API keys

## Phase 3: Historical Data Collection ✅

### Task 3.1: Backfill API Endpoints ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Create FastAPI endpoints for managing historical data collection operations.

**Technical Details:**
- ✅ Added routes to `amc_manager/api/data_collections.py`
- ✅ Implemented `POST /api/data-collections/` for starting backfill
- ✅ Added `GET /api/data-collections/` for listing user collections
- ✅ Created `GET /api/data-collections/{collection_id}` for detailed progress
- ✅ Implemented pause/resume endpoints: `POST /api/data-collections/{collection_id}/pause` and `/resume`
- ✅ Added authentication and user validation for all endpoints
- ✅ Included rate limiting to prevent excessive backfill requests
- ✅ Added retry failed weeks endpoint: `POST /api/data-collections/{collection_id}/retry-failed`
- ✅ Implemented cancel collection endpoint: `DELETE /api/data-collections/{collection_id}`

**Dependencies:** Task 2.1

**Testing Requirements:**
- Test all CRUD operations
- Validate authentication and authorization
- Test rate limiting functionality
- Verify proper error responses

**Complexity:** Medium

**Implementation Notes:**
- Full Pydantic models for request/response validation
- Comprehensive error handling with proper HTTP status codes
- Background task support for async processing
- Collection progress tracking with statistics

### Task 3.2: Background Collection Executor ✅
**Status:** COMPLETED (2025-09-05)

**Description:** Background service to execute data collection operations asynchronously.

**Technical Details:**
- ✅ Created new `CollectionExecutorService` following existing patterns
- ✅ Added collection polling every 30 seconds for pending operations
- ✅ Implemented atomic collection claiming to prevent conflicts
- ✅ Added retry logic for failed week executions (max 3 retries)
- ✅ Supported parallel collection processing (5 collections, 10 weeks concurrent)
- ✅ Implemented cleanup for abandoned/stale collections (24 hour timeout)
- ✅ Added comprehensive logging and monitoring for collection operations
- ✅ Integrated with main application lifecycle (startup/shutdown)
- ✅ Rate limiting between AMC API calls (2 second delay)

**Dependencies:** Task 2.1, existing background service infrastructure

**Testing Requirements:**
- Test atomic claiming behavior with concurrent access
- Validate retry logic and backoff intervals
- Test parallel processing without conflicts
- Verify proper logging and error handling

**Complexity:** Complex

**Implementation Notes:**
- Semaphore-based concurrency control
- Automatic pause detection during execution
- Progress tracking with percentage calculation
- Failed collection retry with exponential backoff
- Cleanup task runs hourly for abandoned collections

### Task 3.3: Collection Progress UI ✅
**Status:** COMPLETED (2025-09-06)

**Description:** Frontend interface for monitoring and managing data collection operations.

**Technical Details:**
- ✅ Created `frontend/src/components/reports/DataCollections.tsx` main component
- ✅ Implemented collection list view with animated status indicators and progress bars
- ✅ Added `CollectionProgress.tsx` detailed view showing week-by-week completion
- ✅ Created `StartCollectionModal.tsx` with workflow/instance selection
- ✅ Added pause/resume/cancel/retry controls for all collection states
- ✅ Implemented real-time progress updates using React Query polling (5s list, 3s details)
- ✅ Added comprehensive error display and retry options for failed weeks
- ✅ Created `dataCollectionService.ts` API service and TypeScript types
- ✅ Updated App.tsx routing and Layout.tsx navigation with Calendar icon
- ✅ Created `WorkflowSelector.tsx` searchable dropdown component for improved UX
- ✅ **Reference Design:** Followed design patterns from reports components for consistency

**Dependencies:** Task 3.1

**Testing Requirements:**
- ✅ Tested real-time progress updates - working with 5s/3s polling
- ✅ Validated form submission and error handling - all errors properly displayed
- ✅ Tested collection creation, pause, resume, cancel operations
- ✅ Verified polling behavior and performance - optimized intervals

**Complexity:** Medium

**Implementation Issues Fixed (2025-09-06):**
1. **403 Forbidden** - Fixed instance access check to use UUID instead of AMC instance_id
2. **500 Server Error** - Fixed date serialization by converting to ISO strings
3. **Workflow Not Found** - Updated lookup to support both UUID and string IDs
4. **404 Not Found** - Fixed workflows API to return UUID as id field
5. **strftime Error** - Added date string to object conversion
6. **Datetime Serialization** - Fixed week status update serialization
7. **Instance Not Found** - Updated instance lookup to support UUIDs
8. **No Execution ID** - Added missing id field to execution results
9. **Undefined Variable** - Fixed execution variable scope issue

**Final Status:** Fully functional with all issues resolved. Collections successfully executing 52-week historical backfills with proper progress tracking.

## Phase 4: Basic Dashboard Visualization

### Task 4.1: Dashboard Management API
**Description:** Create FastAPI endpoints for dashboard CRUD operations.

**Technical Details:**
- Add routes to `amc_manager/api/dashboards.py`
- Implement `GET /api/dashboards/` with filtering and search
- Create `POST /api/dashboards/` for dashboard creation
- Add `GET /api/dashboards/{dashboard_id}` with widget loading
- Implement `PUT /api/dashboards/{dashboard_id}` for updates
- Add `DELETE /api/dashboards/{dashboard_id}` with cascade delete
- Include sharing and permission validation logic

**Dependencies:** Task 1.2, Task 2.3

**Testing Requirements:**
- Test all CRUD operations with proper validation
- Verify cascade delete for widgets
- Test permission and sharing logic
- Validate search and filtering functionality

**Complexity:** Medium

### Task 4.2: Widget Configuration System
**Description:** Backend system for managing dashboard widget configurations and data sources.

**Technical Details:**
- Create widget configuration validation in dashboard service
- Implement data source validation (workflow IDs, metrics, filters)
- Add widget type validation (chart, table, metric_card, text)
- Create configuration templates for common widget types
- Implement widget data source mapping to aggregated data
- Add widget positioning and layout validation
- Support dynamic widget configuration updates

**Dependencies:** Task 2.3, Task 4.1

**Testing Requirements:**
- Test all widget type configurations
- Validate data source mapping accuracy
- Test layout and positioning validation
- Verify configuration update handling

**Complexity:** Medium

### Task 4.3: Chart Components Library
**Description:** Create React components for different chart types using Chart.js.

**Technical Details:**
- Install Chart.js and react-chartjs-2: `npm install chart.js react-chartjs-2`
- Create base `frontend/src/components/charts/BaseChart.tsx` component
- Implement `LineChart.tsx` for time-series data with proper date formatting
- Add `BarChart.tsx` for comparative analysis with category support
- Create `PieChart.tsx` for composition analysis with legends
- Implement `MetricCard.tsx` for KPI display with trend indicators
- Add `DataTable.tsx` for tabular data with sorting and pagination
- Ensure all components are responsive and theme-consistent
- **Reference Design:** See component examples in `@.agent-os/specs/2025-09-05-reports-analytics-platform/design-reference.md` for TrendChart.tsx and ComparisonChart.tsx implementations

**Dependencies:** None

**Testing Requirements:**
- Test all chart types with sample data
- Validate responsive behavior
- Test interactive features (tooltips, legends)
- Verify theme consistency

**Complexity:** Medium

### Task 4.4: Basic Dashboard Interface
**Description:** Create main dashboard interface with widget display and basic interactions.

**Technical Details:**
- Create `frontend/src/pages/reports/Dashboards.tsx` main page
- Implement dashboard list view with creation and edit options
- Add `DashboardView.tsx` component for displaying configured dashboards
- Create basic widget rendering system using chart components
- Implement date range filtering for all dashboard widgets
- Add loading states and error handling for widget data
- Support basic dashboard sharing (view-only links)
- **Reference Design:** Use `DashboardLayout.tsx`, `ReportCard.tsx`, `MetricCard.tsx`, and `FilterControls.tsx` from `@.agent-os/specs/2025-09-05-reports-analytics-platform/design-reference.md` as implementation templates

**Dependencies:** Task 4.1, Task 4.3

**Testing Requirements:**
- Test dashboard creation and editing flow
- Validate widget rendering with different data types
- Test date range filtering functionality
- Verify error handling and loading states

**Complexity:** Medium

## Phase 5: Dashboard Builder Interface

### Task 5.1: Drag-and-Drop Dashboard Builder
**Description:** Implement advanced dashboard builder with drag-and-drop widget positioning.

**Technical Details:**
- Install React DnD: `npm install react-dnd react-dnd-html5-backend`
- Create `frontend/src/components/reports/DashboardBuilder.tsx`
- Implement drag-and-drop grid system for widget positioning
- Add widget palette with available chart types and configurations
- Create widget configuration modal for data source selection
- Implement grid snapping and collision detection
- Add undo/redo functionality for layout changes
- Support widget resize handles and real-time layout updates

**Dependencies:** Task 4.4, Task 4.3

**Testing Requirements:**
- Test drag-and-drop functionality across different browsers
- Validate grid snapping and collision detection
- Test widget configuration modal
- Verify undo/redo functionality

**Complexity:** Complex

### Task 5.2: Widget Configuration UI
**Description:** Create comprehensive widget configuration interface for data sources and styling.

**Technical Details:**
- Create `frontend/src/components/reports/WidgetConfigModal.tsx`
- Implement data source selection with workflow and instance dropdowns
- Add metric selection interface with AMC field mapping
- Create filter configuration (date ranges, campaigns, ASINs)
- Implement chart styling options (colors, axes, legends)
- Add aggregation level selection (daily, weekly, monthly)
- Support advanced chart options (multiple series, dual axes)
- Include configuration validation and preview functionality

**Dependencies:** Task 5.1, existing workflow/instance data

**Testing Requirements:**
- Test all configuration options and validation
- Verify data source selection accuracy
- Test chart styling and preview functionality
- Validate filter configuration logic

**Complexity:** Complex

### Task 5.3: Dashboard Templates System
**Description:** Create pre-built dashboard templates for common AMC use cases.

**Technical Details:**
- Create `amc_manager/services/dashboard_template_service.py`
- Implement template storage and retrieval logic
- Create template configurations for:
  - Performance Dashboard (ROAS, ACOS, Spend trends)
  - Attribution Dashboard (View-through, Click-through analysis)
  - Audience Dashboard (Reach, Frequency, Demographics)
  - Campaign Comparison Dashboard (Multi-campaign analysis)
- Add template instantiation with user-specific data sources
- Implement template preview functionality
- Support template customization after instantiation

**Dependencies:** Task 4.1, Task 4.3

**Testing Requirements:**
- Test template creation and instantiation
- Validate all template types with sample data
- Test template customization functionality
- Verify preview accuracy

**Complexity:** Medium

### Task 5.4: Dashboard Export Functionality
**Description:** Implement dashboard export to PDF and CSV formats.

**Technical Details:**
- Install jsPDF and html2canvas: `npm install jspdf html2canvas`
- Create `frontend/src/services/dashboardExportService.ts`
- Implement PDF export with proper layout and chart rendering
- Add CSV export for underlying widget data
- Create export configuration options (date ranges, format settings)
- Support batch export for multiple dashboards
- Add email sharing functionality for exported reports
- Implement export history and download management

**Dependencies:** Task 4.4, Task 4.3

**Testing Requirements:**
- Test PDF generation with different dashboard layouts
- Validate CSV export data accuracy
- Test export with various date ranges
- Verify email sharing functionality

**Complexity:** Medium

## Phase 6: Automated Weekly Updates

### Task 6.1: Weekly Data Collection Scheduler
**Description:** Extend existing scheduling system to support automated weekly data collection.

**Technical Details:**
- Extend `ScheduleExecutorService` to handle data collection schedules
- Add weekly schedule detection and execution logic
- Implement smart date parameter calculation for weekly updates
- Create overlap detection to prevent duplicate data collection
- Add schedule-based execution using existing croniter infrastructure
- Support multiple instance scheduling with staggered execution
- Implement error handling and retry logic for failed weekly updates

**Dependencies:** Task 2.1, existing `ScheduleExecutorService`

**Testing Requirements:**
- Test weekly schedule execution accuracy
- Validate date parameter calculation
- Test overlap detection logic
- Verify error handling and retry behavior

**Complexity:** Medium

### Task 6.2: Intelligent Data Merging
**Description:** Implement smart data merging that prevents duplicates and handles schema changes.

**Technical Details:**
- Create `amc_manager/services/data_merge_service.py`
- Implement duplicate detection using data checksums and key fields
- Add conflict resolution for overlapping date ranges
- Create schema validation for incoming data consistency
- Implement incremental merge logic for large datasets
- Add data quality checks and validation rules
- Support manual conflict resolution interface for edge cases

**Dependencies:** Task 2.1, Task 6.1

**Testing Requirements:**
- Test duplicate detection accuracy
- Validate conflict resolution logic
- Test schema change handling
- Verify data quality validation

**Complexity:** Complex

### Task 6.3: Automated Schedule Management UI
**Description:** Frontend interface for managing automated data collection schedules.

**Technical Details:**
- Create `frontend/src/components/reports/DataSchedules.tsx`
- Implement schedule creation form with workflow and frequency selection
- Add schedule list view with status indicators and controls
- Create schedule editing interface for frequency and configuration changes
- Implement pause/resume controls for active schedules
- Add schedule history view showing past executions and results
- Support schedule templates for common collection patterns
- **Reference Design:** Use `ReportsNavigation.tsx` and `ReportsFilters.tsx` from `@.agent-os/specs/2025-09-05-reports-analytics-platform/design-reference.md` for navigation and filtering patterns

**Dependencies:** Task 6.1, existing schedule management UI patterns

**Testing Requirements:**
- Test schedule creation and editing functionality
- Validate schedule control operations
- Test history view and filtering
- Verify template functionality

**Complexity:** Medium

## Phase 7: AI-Powered Insights

### Task 7.1: AI Insights API Integration
**Description:** Create FastAPI endpoints for AI-powered business insights and analysis.

**Technical Details:**
- Add routes to `amc_manager/api/ai_insights.py`
- Implement `POST /api/ai/insights/` for natural language queries
- Create `GET /api/ai/insights/` for insight history retrieval
- Add `GET /api/ai/insights/{insight_id}` for detailed insight view
- Implement rate limiting to prevent AI API abuse
- Add query validation and context preparation logic
- Include confidence scoring and insight categorization

**Dependencies:** Task 2.4

**Testing Requirements:**
- Test AI API integration with various query types
- Validate rate limiting and quota management
- Test context preparation accuracy
- Verify insight storage and retrieval

**Complexity:** Medium

### Task 7.2: Conversational AI Interface
**Description:** Create chat-like interface for interacting with AI insights system.

**Technical Details:**
- Create `frontend/src/components/reports/AIInsights.tsx`
- Implement chat interface with message history and real-time responses
- Add suggested questions based on available data and common queries
- Create data visualization integration (AI can generate chart suggestions)
- Implement conversation context management and follow-up questions
- Add insight bookmarking and sharing functionality
- Support voice input and text-to-speech for accessibility
- **Reference Design:** Use `InsightsPanel.tsx` from `@.agent-os/specs/2025-09-05-reports-analytics-platform/design-reference.md` as the base template for the AI insights interface

**Dependencies:** Task 7.1, Task 4.3

**Testing Requirements:**
- Test real-time chat functionality
- Validate conversation context handling
- Test suggested questions accuracy
- Verify accessibility features

**Complexity:** Complex

### Task 7.3: Automated Insight Generation
**Description:** Background service to generate proactive insights and anomaly detection.

**Technical Details:**
- Create `amc_manager/services/automated_insights_service.py`
- Implement trend analysis algorithms for automatic insight generation
- Add anomaly detection for significant performance changes
- Create insight scheduling for weekly/monthly analysis reports
- Implement insight notification system for critical alerts
- Add insight categorization and priority scoring
- Support user preference settings for insight types and frequency

**Dependencies:** Task 2.4, Task 6.1

**Testing Requirements:**
- Test trend analysis accuracy
- Validate anomaly detection sensitivity
- Test notification delivery and timing
- Verify insight categorization logic

**Complexity:** Complex

## Phase 8: Export and Sharing

### Task 8.1: Advanced Sharing System
**Description:** Implement comprehensive dashboard sharing with permissions and collaboration.

**Technical Details:**
- Extend dashboard sharing API with granular permissions
- Implement user invitation system with email notifications
- Add collaborative editing with real-time updates using WebSockets
- Create shared dashboard discovery and browsing interface
- Implement public dashboard publishing with access controls
- Add comment system for collaborative dashboard analysis
- Support team-based dashboard organization and access management

**Dependencies:** Task 4.1, existing authentication system

**Testing Requirements:**
- Test permission system accuracy
- Validate real-time collaboration features
- Test email notification delivery
- Verify access control enforcement

**Complexity:** Complex

### Task 8.2: Scheduled Report Generation
**Description:** Automated system for generating and distributing regular reports.

**Technical Details:**
- Create `amc_manager/services/report_generation_service.py`
- Implement scheduled report generation using existing scheduling infrastructure
- Add email report distribution with PDF attachments
- Create report templates with executive summary and key insights
- Implement recipient management and subscription system
- Add report customization options (metrics, date ranges, formats)
- Support report versioning and historical archive

**Dependencies:** Task 5.4, Task 6.1, existing scheduling system

**Testing Requirements:**
- Test scheduled report generation accuracy
- Validate email delivery and attachment handling
- Test report template rendering
- Verify subscription management functionality

**Complexity:** Medium

### Task 8.3: Mobile Dashboard Support
**Description:** Optimize dashboard viewing and interaction for mobile devices.

**Technical Details:**
- Implement responsive design improvements for dashboard viewing
- Create mobile-optimized chart rendering with touch interactions
- Add mobile dashboard navigation and widget scrolling
- Implement swipe gestures for dashboard and widget navigation
- Create mobile-specific widget layouts and sizing
- Add progressive web app (PWA) support for offline viewing
- Implement mobile push notifications for critical insights

**Dependencies:** Task 4.4, Task 7.2

**Testing Requirements:**
- Test responsive behavior across different mobile devices
- Validate touch interactions and gestures
- Test PWA functionality and offline capabilities
- Verify push notification delivery

**Complexity:** Medium

### Task 8.4: Integration Testing and Performance Optimization
**Description:** Comprehensive testing and performance optimization for the complete platform.

**Technical Details:**
- Create end-to-end testing suite covering complete user workflows
- Implement performance monitoring and optimization for dashboard loading
- Add database query optimization and index tuning
- Create load testing scenarios for concurrent dashboard usage
- Implement caching strategies for frequently accessed data
- Add monitoring and alerting for system health and performance
- Create backup and disaster recovery procedures for reporting data

**Dependencies:** All previous phases

**Testing Requirements:**
- Comprehensive end-to-end test coverage
- Performance benchmarking and optimization validation
- Load testing under realistic usage scenarios
- Disaster recovery testing procedures

**Complexity:** Complex

## Implementation Notes

### Critical Integration Points
1. **AMC API Rate Limits**: All historical collection must respect existing rate limiting in `amc_api_client_with_retry`
2. **Database Patterns**: Follow existing patterns with `@with_connection_retry` and proper transaction handling
3. **Authentication**: Use existing JWT authentication and user context throughout
4. **Background Services**: Extend existing background service patterns for collection and insight generation

### Performance Considerations
1. **Database Indexing**: Critical for time-series dashboard queries - implement all specified indexes
2. **Data Aggregation**: Pre-compute common metrics to avoid real-time calculations
3. **Caching**: Implement strategic caching for frequently accessed dashboard data
4. **Background Processing**: Use async processing for resource-intensive operations

### Security Requirements
1. **Data Access**: Ensure proper user isolation for all dashboard and collection data
2. **AI Context**: Never send sensitive business data to AI APIs - use anonymized metrics only
3. **Sharing Permissions**: Validate all dashboard access and sharing permissions
4. **Token Management**: Use existing encrypted token storage patterns

### Testing Strategy
1. **Unit Tests**: Focus on data aggregation accuracy and API endpoint validation
2. **Integration Tests**: Test complete data collection and dashboard creation workflows
3. **Performance Tests**: Validate dashboard loading times with large datasets
4. **E2E Tests**: Test complete user journeys from data collection to insight generation

### Deployment Considerations
1. **Migration Strategy**: Database changes must be backward compatible during deployment
2. **Background Services**: Plan for graceful shutdown and restart of collection processes
3. **AI API Keys**: Manage OpenAI API keys and usage quotas appropriately
4. **Monitoring**: Implement comprehensive logging for debugging collection and insight issues