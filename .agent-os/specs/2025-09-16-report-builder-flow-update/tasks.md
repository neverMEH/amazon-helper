# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-16-report-builder-flow-update/spec.md

> Created: 2025-09-16
> Status: Ready for Implementation

## Tasks

- [x] 1. Database Schema Updates and Migrations
  - [x] 1.1 Write tests for database migration scripts
  - [x] 1.2 Create migration script for report_data_collections table modifications (lookback_config, segmentation_config)
  - [x] 1.3 Create migration script for workflow_schedules table modifications (backfill_status, schedule_config)
  - [x] 1.4 Create report_builder_audit table with appropriate indexes
  - [x] 1.5 Add performance indexes for lookback queries and backfill operations
  - [x] 1.6 Test migrations on development database
  - [x] 1.7 Update Pydantic models for new database fields
  - [x] 1.8 Verify all database tests pass

- [ ] 2. Backend API Implementation
  - [ ] 2.1 Write tests for report-builder validation endpoints
  - [ ] 2.2 Implement POST /api/report-builder/validate-parameters endpoint
  - [ ] 2.3 Implement POST /api/report-builder/preview-schedule endpoint
  - [ ] 2.4 Implement POST /api/report-builder/submit endpoint
  - [ ] 2.5 Enhance existing /api/data-collections/ endpoint for lookback config
  - [ ] 2.6 Create BackfillService for managing 365-day historical processing
  - [ ] 2.7 Add rate limiting and error handling for backfill operations
  - [ ] 2.8 Verify all API tests pass

- [ ] 3. Frontend Parameter Selection (Step 1)
  - [ ] 3.1 Write tests for ReportBuilderParameters component
  - [ ] 3.2 Create enhanced ReportBuilderParameters.tsx with lookback window UI
  - [ ] 3.3 Implement date picker component for custom date ranges
  - [ ] 3.4 Add predefined lookback buttons (7, 14, 30 days, week, month)
  - [ ] 3.5 Implement toggle between calendar and relative date modes
  - [ ] 3.6 Add validation for AMC's 14-month data retention limit
  - [ ] 3.7 Integrate with existing parameter selection logic
  - [ ] 3.8 Verify all component tests pass

- [ ] 4. Frontend Schedule Selection (Step 2)
  - [ ] 4.1 Write tests for ReportScheduleSelection component
  - [ ] 4.2 Rename and refactor execution step to ReportScheduleSelection.tsx
  - [ ] 4.3 Implement schedule type selection UI (once, scheduled, backfill with schedule)
  - [ ] 4.4 Create backfill configuration interface with segmentation options
  - [ ] 4.5 Add schedule frequency selector for recurring schedules
  - [ ] 4.6 Implement progress calculation for 365-day segments
  - [ ] 4.7 Add timezone selection for scheduled reports
  - [ ] 4.8 Verify all component tests pass

- [ ] 5. Frontend Review and Submission (Steps 3-4)
  - [ ] 5.1 Write tests for ReportReviewStep component
  - [ ] 5.2 Create ReportReviewStep.tsx with comprehensive review interface
  - [ ] 5.3 Implement SQL query preview with Monaco Editor (read-only)
  - [ ] 5.4 Create parameter and lookback window visualization
  - [ ] 5.5 Simplify ReportSubmission.tsx with single-action button
  - [ ] 5.6 Implement success/error handling with appropriate redirects
  - [ ] 5.7 Add progress tracking UI for backfill operations
  - [ ] 5.8 Verify all component tests pass