# Spec Tasks

## Tasks

- [ ] 1. Database Schema and Migration Implementation
  - [ ] 1.1 Write tests for database schema changes
  - [ ] 1.2 Extend query_templates table with report columns
  - [ ] 1.3 Create report_definitions table with indexes
  - [ ] 1.4 Create report_executions table with indexes
  - [ ] 1.5 Create report_schedules table with constraints
  - [ ] 1.6 Create dashboard_favorites table
  - [ ] 1.7 Modify report_data_collections for report backfills
  - [ ] 1.8 Create report_runs_overview view
  - [ ] 1.9 Archive existing workflow tables
  - [ ] 1.10 Verify all database tests pass

- [ ] 2. Backend Report Service Implementation
  - [ ] 2.1 Write tests for report service layer
  - [ ] 2.2 Create ReportService class with CRUD operations
  - [ ] 2.3 Implement direct ad-hoc execution engine
  - [ ] 2.4 Build parameter validation and injection system
  - [ ] 2.5 Create schedule management functions
  - [ ] 2.6 Implement backfill orchestration logic
  - [ ] 2.7 Add execution monitoring and status updates
  - [ ] 2.8 Verify all backend tests pass

- [ ] 3. API Endpoints and Controllers
  - [ ] 3.1 Write tests for API endpoints
  - [ ] 3.2 Implement template management endpoints
  - [ ] 3.3 Create report CRUD endpoints
  - [ ] 3.4 Build schedule management endpoints
  - [ ] 3.5 Add execution monitoring endpoints
  - [ ] 3.6 Implement dashboard integration endpoints
  - [ ] 3.7 Create metadata service endpoints
  - [ ] 3.8 Verify all API tests pass

- [ ] 4. Frontend Report Builder Interface
  - [ ] 4.1 Write tests for React components
  - [ ] 4.2 Create ReportBuilder page with tab navigation
  - [ ] 4.3 Build TemplateGrid component for template selection
  - [ ] 4.4 Implement DynamicParameterForm with validation
  - [ ] 4.5 Create RunReportModal with execution options
  - [ ] 4.6 Build DashboardsTable for report management
  - [ ] 4.7 Add progress tracking and status indicators
  - [ ] 4.8 Verify all frontend tests pass

- [ ] 5. Background Services and Integration
  - [ ] 5.1 Write tests for background services
  - [ ] 5.2 Implement schedule executor service
  - [ ] 5.3 Create backfill executor with segmentation
  - [ ] 5.4 Update execution status poller for reports
  - [ ] 5.5 Integrate with existing dashboard system
  - [ ] 5.6 Remove workflow-related code and references
  - [ ] 5.7 Add monitoring and error handling
  - [ ] 5.8 Verify all integration tests pass