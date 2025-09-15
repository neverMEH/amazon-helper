# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-15-amc-report-builder/spec.md

## Technical Requirements

### Core Architecture Changes
- **Remove Workflow Dependencies**: Eliminate all workflow creation logic and database references, replacing with direct ad-hoc execution paths
- **Template Extension**: Extend `query_templates` table with `report_type`, `report_config`, and `ui_schema` JSONB columns for report metadata
- **Execution Model**: Implement stateless ad-hoc execution pattern using AMC's `create_workflow_execution` endpoint with `sql_query` parameter only
- **Report Persistence**: Create new `report_definitions` table as the primary entity for user-configured reports with template references

### Frontend Components
- **Report Builder Page**: New React component at `/report-builder` with tab navigation between "Reports" and "Dashboards" views
- **Dynamic Parameter Form**: Generate form fields from template's `parameter_definitions` and `ui_schema` using React Hook Form with Zod validation
- **Template Grid**: Card-based template selector with filtering by category, instance compatibility, and report type
- **Execution Modal**: Multi-step modal for parameter collection, execution type selection (once/recurring/backfill), and schedule configuration
- **Dashboard Table**: DataTable component showing all reports with columns for status, frequency, last/next run, with inline actions

### Backend Services
- **Report Service**: New service layer managing report CRUD, parameter validation, and execution orchestration
- **Direct Execution Engine**: Bypass workflow creation, directly call AMC API with formatted SQL and track in `report_executions` table
- **Schedule Executor Service**: Background service polling `report_schedules` every 60 seconds, executing due reports, updating `next_run_at`
- **Backfill Orchestrator**: Segment historical periods into daily/weekly/monthly chunks, queue parallel executions respecting AMC rate limits
- **Parameter Injection Engine**: Enhanced template parameter system supporting date calculations, ASIN lists, campaign filters with validation

### Performance Criteria
- **Execution Latency**: Ad-hoc execution initiation within 2 seconds of user action
- **Parameter Validation**: Client-side validation response within 100ms
- **Schedule Processing**: Background service processes due schedules within 60-second window
- **Backfill Throughput**: Process up to 10 concurrent segment executions per instance
- **Dashboard Load Time**: Initial dashboard render within 3 seconds with lazy-loaded visualizations

### Integration Requirements
- **AMC API Integration**: Direct usage of ad-hoc execution endpoints, bypassing workflow creation entirely
- **Existing Template System**: Full compatibility with current `query_templates` structure and parameter engine
- **Dashboard Infrastructure**: Create report-specific dashboard tables while maintaining compatibility with existing dashboard widgets
- **Authentication/Authorization**: Leverage existing user authentication with report-level ownership permissions
- **Monitoring/Logging**: Integrate with existing logging infrastructure, add report-specific metrics

### Security Considerations
- **Parameter Sanitization**: Validate and sanitize all user inputs before SQL injection to prevent query manipulation
- **Rate Limiting**: Implement per-user and per-instance execution limits to prevent AMC API abuse
- **Data Access Control**: Enforce instance-level permissions, reports visible only to users with instance access
- **Encryption**: Maintain existing token encryption for AMC API credentials

### Migration Strategy
- **Deprecation Path**: Mark workflow-related endpoints as deprecated, maintain read-only access for 90 days
- **Data Preservation**: Archive existing workflow data to cold storage before removal
- **Feature Parity**: Ensure all workflow capabilities are available through Report Builder before deprecation
- **Rollback Plan**: Maintain database backups and feature flags for gradual rollout