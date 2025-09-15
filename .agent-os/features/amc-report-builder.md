# AMC Report Builder System

## Overview

The AMC Report Builder is a comprehensive new feature that replaces the traditional workflow-based system with direct ad-hoc execution for AMC queries. This represents a major architectural shift in RecomAMP, eliminating workflow overhead and providing streamlined report generation capabilities with enhanced performance and agency-focused features.

## Recent Changes (2025-09-15)

### Major Architectural Transformation - Report Builder Implementation
- **Database Schema Migration**: Complete new table structure implemented via Supabase MCP
- **Service Layer Rewrite**: Four new specialized services for report management
- **Direct AMC Execution**: Eliminated workflow creation overhead for improved performance
- **Enterprise Scheduling**: Advanced cron-based scheduling with timezone support
- **Historical Backfill**: Up to 365-day historical data collection capabilities
- **Dashboard Integration**: Automatic dashboard generation from template configurations

## Database Schema Changes (2025-09-15)

### New Core Tables

#### `report_definitions`
Primary table for user-configured reports with template-based generation:
```sql
- id: UUID (Primary Key)
- report_id: TEXT (Unique identifier like "rpt_abc12345")
- name: Report display name
- description: Optional report description
- template_id: UUID reference to query_templates
- instance_id: UUID reference to amc_instances
- owner_id: UUID reference to users
- parameters: JSONB configuration object
- frequency: TEXT (once|daily|weekly|monthly|quarterly)
- timezone: TEXT for scheduling (default UTC)
- is_active: BOOLEAN status flag
- dashboard_id: UUID reference to dashboards (optional)
- last_execution_id: UUID tracking
- execution_count: INTEGER counter
- created_at/updated_at: TIMESTAMPTZ timestamps
```

#### `report_executions`
Comprehensive execution tracking with AMC integration:
```sql
- id: UUID (Primary Key)
- execution_id: TEXT (Unique like "exec_xyz98765")
- report_id: UUID reference to report_definitions
- template_id: UUID reference to query_templates
- instance_id: UUID reference to amc_instances
- user_id: UUID reference to users
- triggered_by: TEXT (manual|schedule|backfill|api)
- schedule_id: UUID reference to report_schedules (optional)
- collection_id: UUID reference to report_data_collections (optional)
- status: TEXT (pending|running|completed|failed|cancelled)
- amc_execution_id: TEXT from AMC API response
- output_location: TEXT S3 path for results
- row_count: INTEGER result metrics
- size_bytes: BIGINT result size
- error_message: TEXT for failures
- parameters_snapshot: JSONB execution parameters
- time_window_start/end: TIMESTAMPTZ for date ranges
- started_at/completed_at: TIMESTAMPTZ execution timing
```

#### `report_schedules`
Advanced scheduling system with cron expressions:
```sql
- id: UUID (Primary Key)
- schedule_id: TEXT (Unique like "sch_def54321")
- report_id: UUID reference to report_definitions
- schedule_type: TEXT (daily|weekly|monthly|quarterly|custom)
- cron_expression: TEXT for precise timing
- timezone: TEXT for schedule calculations
- default_parameters: JSONB for scheduled runs
- is_active/is_paused: BOOLEAN status controls
- last_run_at: TIMESTAMPTZ tracking
- last_run_status: TEXT result tracking
- next_run_at: TIMESTAMPTZ calculated field
- run_count/failure_count: INTEGER metrics
```

#### `dashboard_favorites`
User personalization for dashboard management:
```sql
- id: UUID (Primary Key)
- dashboard_id: UUID reference to dashboards
- user_id: UUID reference to users
- created_at: TIMESTAMPTZ
- UNIQUE constraint on (dashboard_id, user_id)
```

### Extended Tables

#### `query_templates` Extensions
Enhanced with report generation capabilities:
```sql
- report_type: TEXT classification
- report_config: JSONB dashboard configuration
- ui_schema: JSONB UI generation metadata
```

#### `report_data_collections` Extensions
Updated for report-based backfills:
```sql
- report_id: UUID reference to report_definitions
- segment_type: TEXT (daily|weekly|monthly|quarterly)
- max_lookback_days: INTEGER (365-day limit)
```

### Performance Optimizations
- **Composite Indexes**: Multi-column indexes for common query patterns
- **Conditional Indexes**: WHERE clauses for active records only
- **Status Tracking**: Optimized indexes for execution monitoring
- **Foreign Key Constraints**: Proper cascading delete relationships

## Backend Services Architecture (2025-09-15)

### ReportService
Complete CRUD operations for report definitions:
```python
# Key Methods
- create_report(report_data): Generate new report with unique ID
- get_report(report_id): Retrieve by UUID or string ID
- update_report(report_id, update_data): Modify configuration
- delete_report(report_id): Remove report and cascading data
- list_reports(filters): Paginated listing with filtering
- get_report_with_details(report_id): Join template and instance data
- create_report_with_dashboard(report_data): Auto-generate dashboard
- activate_report/deactivate_report: Status management
- increment_execution_count: Tracking metrics
- get_reports_overview: Use report_runs_overview view
```

### ReportExecutionService
Direct ad-hoc execution via AMC API (no workflow creation):
```python
# Core Execution Method
async def execute_report_adhoc(
    report_id, instance_id, sql_query, parameters,
    user_id, entity_id, triggered_by='manual',
    schedule_id=None, collection_id=None,
    time_window_start=None, time_window_end=None
):
    # 1. Create execution record with pending status
    # 2. Call AMC API directly with SQL query
    # 3. Track AMC execution ID
    # 4. Return execution record for monitoring
```

### ReportScheduleService
Advanced scheduling with timezone support:
```python
# Schedule Management
- create_schedule(report_id, schedule_data): Setup recurring execution
- update_schedule(schedule_id, update_data): Modify timing/parameters
- pause_schedule/resume_schedule: Runtime control
- delete_schedule: Remove scheduling
- get_due_schedules(timezone): Find ready-to-run schedules
- calculate_next_run(cron_expression, timezone): Smart scheduling
- update_last_run(schedule_id, status): Execution tracking
```

### ReportBackfillService
Historical data collection orchestration:
```python
# Backfill Management
- create_backfill_collection: Setup historical data gathering
- start_backfill_execution: Begin segmented backfill
- get_collection_progress: Track completion status
- retry_failed_segments: Handle partial failures
- estimate_backfill_time: Calculate duration estimates
```

## Key Features and Capabilities

### Direct AMC API Execution
- **No Workflow Overhead**: Queries execute immediately via ad-hoc AMC API
- **Unlimited Query Size**: Eliminates 50KB workflow creation limits
- **Simplified Architecture**: Reduces complexity and improves performance
- **Real-time Execution**: Direct API calls without intermediate workflow steps

### Advanced Parameter Injection
- **Context-Aware Formatting**: Intelligent parameter substitution based on SQL context
- **Type Detection**: Automatic parameter type inference from query patterns
- **Validation Engine**: Parameter validation before execution
- **Snapshot Storage**: Parameters captured for each execution for audit trail

### Enterprise Scheduling
- **Cron Expression Support**: Flexible scheduling with standard cron syntax
- **Timezone Awareness**: Schedule calculations respect user timezones
- **Pause/Resume Controls**: Runtime schedule management
- **Failure Tracking**: Monitor and handle execution failures
- **Next Run Calculation**: Automatic scheduling of future executions

### Historical Data Backfill
- **365-Day Lookback**: Maximum historical data collection period
- **Segmented Processing**: Configurable daily/weekly/monthly/quarterly segments
- **Parallel Execution**: Multiple backfill segments run concurrently
- **Progress Tracking**: Real-time monitoring of backfill completion
- **Failure Recovery**: Automatic retry of failed segments

### Dashboard Generation
- **Template-Based Creation**: Dashboards auto-generated from report configurations
- **Widget Configuration**: Automatic widget setup based on query structure
- **User Favorites**: Personal dashboard favoriting system
- **Sharing Integration**: Leverages existing dashboard sharing permissions

## Migration from Workflow System

### Architectural Changes
- **Deprecated Tables**: workflows, workflow_executions, workflow_schedules marked as deprecated
- **Data Archival**: Existing workflow data archived in backup tables
- **Service Migration**: amc_execution_service simplified to always use ad-hoc execution
- **API Compatibility**: Existing endpoints maintained for backward compatibility

### Benefits of New Architecture
- **Performance Improvement**: Eliminates workflow creation/update/sync overhead
- **Simplified Maintenance**: Fewer moving parts and reduced complexity
- **Enhanced Scalability**: Direct API calls scale better than workflow management
- **Agency Focus**: Better suited for high-volume agency environments

## Technical Implementation Details

### Service Layer Integration
All services inherit from `DatabaseService` with connection retry logic:
```python
from amc_manager.services.db_service import DatabaseService, with_connection_retry

class ReportService(DatabaseService):
    @with_connection_retry
    def create_report(self, report_data):
        # Implementation with automatic retry on connection issues
```

### AMC API Integration
Direct execution without workflow creation:
```python
# Old workflow-based approach (deprecated)
workflow = await create_workflow(sql_query)
execution = await create_workflow_execution(workflow_id)

# New ad-hoc approach (current)
execution = await amc_api_client_with_retry.create_workflow_execution(
    instance_id=instance_id,
    user_id=user_id,
    entity_id=entity_id,
    sql_query=sql_query,
    time_window_start=formatted_start,
    time_window_end=formatted_end
)
```

### Database View Optimization
`report_runs_overview` view provides comprehensive reporting dashboard:
```sql
-- Combines report definitions, executions, schedules, and user data
-- Optimized for dashboard display with status aggregation
-- Includes favorite tracking and next run calculations
```

## Testing Infrastructure (2025-09-15)

### Comprehensive Test Suite
- **Schema Validation**: `test_report_builder_schema.py` validates all new tables and indexes
- **Service Testing**: `test_report_service.py` covers all CRUD operations
- **Mock Integration**: Fixtures for database and AMC client testing
- **Error Handling**: Tests for failure scenarios and edge cases

### Test Coverage Areas
- **Report CRUD Operations**: Create, read, update, delete functionality
- **Execution Tracking**: Status monitoring and result processing
- **Schedule Management**: Cron expression handling and timezone calculations
- **Backfill Operations**: Historical data collection and progress tracking
- **Dashboard Integration**: Template-based dashboard creation

## Performance Considerations

### Query Optimization
- **Indexed Queries**: All common query patterns have supporting indexes
- **Execution Monitoring**: Optimized for real-time status tracking
- **Large Result Handling**: Efficient processing of AMC result sets
- **Connection Pooling**: Database connection management for high throughput

### Scalability Features
- **Concurrent Executions**: Multiple reports can execute simultaneously
- **Resource Management**: AMC API rate limiting and throttling
- **Background Processing**: Asynchronous execution and monitoring
- **Result Caching**: Intelligent caching of execution results

## Agency-Focused Enhancements

### Multi-Client Management
- **Instance Isolation**: Reports scoped to specific AMC instances
- **User Permissions**: Owner-based access control
- **Resource Allocation**: Balanced execution across client instances
- **Usage Tracking**: Execution metrics per client/instance

### Operational Efficiency
- **Batch Operations**: Multiple report executions in parallel
- **Template Reuse**: Standardized queries across multiple clients
- **Automated Scheduling**: Reduce manual execution overhead
- **Dashboard Standardization**: Consistent reporting across clients

## Future Roadmap

### Frontend Integration (Next Phase)
- **Report Builder UI**: User interface for report creation and management
- **Execution Monitoring**: Real-time status tracking and result display
- **Schedule Management**: UI for creating and managing recurring reports
- **Dashboard Integration**: Seamless connection to dashboard system

### Advanced Features (Planned)
- **Report Sharing**: Cross-user report sharing capabilities
- **Template Marketplace**: Shared template library for common use cases
- **Advanced Analytics**: Execution performance and usage analytics
- **API Extensions**: RESTful API for programmatic report management

## Interconnections

### With Query Templates System
- **Template Extension**: Enhanced templates with report generation metadata
- **Parameter Intelligence**: Leverages existing context-aware parameter detection
- **SQL Analysis**: Uses sqlParameterAnalyzer for intelligent formatting

### With Dashboard System
- **Auto-Generation**: Reports automatically create configured dashboards
- **Widget Integration**: Report results feed into dashboard widgets
- **Sharing Integration**: Leverages existing dashboard sharing permissions

### With Instance Management
- **Instance Validation**: Reports require valid AMC instance configuration
- **Entity Resolution**: Uses instance->account->entity_id lookup pattern
- **Resource Allocation**: Execution distributed across available instances

### With Background Services
- **Schedule Execution**: Integrates with existing background service infrastructure
- **Status Polling**: Leverages execution monitoring for real-time updates
- **Token Management**: Uses existing token refresh and management services

## Monitoring and Debugging

### Execution Tracking
```sql
-- Monitor active report executions
SELECT * FROM report_executions
WHERE status IN ('pending', 'running')
ORDER BY started_at DESC;

-- Report execution overview
SELECT * FROM report_runs_overview
WHERE owner_id = 'user-uuid'
ORDER BY last_run_at DESC;
```

### Performance Metrics
- **Execution Time Tracking**: Start/completion timestamps for performance analysis
- **Resource Usage**: Row counts and result sizes for capacity planning
- **Error Analysis**: Failure patterns and error message aggregation
- **Schedule Reliability**: Success rates and failure counts for scheduled reports

## Critical Implementation Notes

### AMC Instance ID Resolution
- **UUID vs String**: Reports store instance UUID but AMC API requires string instance_id
- **Join Pattern**: Always join amc_instances table to get actual instance_id
- **Entity Lookup**: Requires amc_accounts.account_id for AMC API calls

### Parameter Handling
- **Snapshot Storage**: Parameters captured at execution time for audit trail
- **Type Validation**: Parameter types validated against SQL context
- **Format Consistency**: Date formatting matches AMC API requirements (no 'Z' suffix)

### Error Recovery
- **Retry Logic**: Built-in retry for transient failures
- **Status Tracking**: Comprehensive execution status monitoring
- **Failure Analysis**: Detailed error messages and recovery suggestions

This AMC Report Builder represents the evolution of RecomAMP from a simple query execution tool to a comprehensive report generation platform optimized for agency environments and high-volume operations.