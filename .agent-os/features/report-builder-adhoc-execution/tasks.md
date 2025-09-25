# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/features/report-builder-adhoc-execution/spec.md

> Created: 2025-01-19
> Status: Ready for Implementation

## Tasks

### Report Builder Ad-Hoc Execution Review & Implementation Tasks

Based on the review of the current implementation, here are the tasks to ensure the ad-hoc executions flow for the report builder is built correctly according to Amazon AMC API requirements:

- [x] 1. Validate Current Ad-Hoc Implementation
  - [x] 1.1 Write tests for ad-hoc execution flow in report_execution_service.py
  - [x] 1.2 Verify mutual exclusivity of sql_query and workflow_id parameters in AMC API client
  - [x] 1.3 Check SQL query presence validation before AMC API calls
  - [x] 1.4 Validate the workflow payload structure for ad-hoc executions
  - [x] 1.5 Verify all tests pass for ad-hoc execution validation

- [x] 2. Fix Time Window Handling for AMC Requirements
  - [x] 2.1 Write tests for date format handling (no 'Z' suffix requirement)
  - [x] 2.2 Update date formatting to ensure AMC-compatible format (YYYY-MM-DDTHH:MM:SS)
  - [x] 2.3 Implement 14-day data lag adjustment for end dates
  - [x] 2.4 Fix time window parameter extraction from various parameter key formats
  - [x] 2.5 Verify all date handling tests pass

- [x] 3. Enhance SQL Query Parameter Processing
  - [x] 3.1 Write tests for parameter replacement in SQL queries
  - [x] 3.2 Implement parameter replacement for large lists (campaigns, ASINs) using VALUES clause injection
  - [x] 3.3 Add parameter length validation to avoid AMC API limits
  - [x] 3.4 Ensure SQL query is properly populated from templates
  - [x] 3.5 Verify all parameter processing tests pass

- [x] 4. Improve Error Handling and Monitoring
  - [x] 4.1 Write tests for AMC API error response handling
  - [x] 4.2 Add proper logging for SQL query content at each stage
  - [x] 4.3 Implement retry logic for transient AMC API failures
  - [x] 4.4 Add execution status polling for ad-hoc workflows (existing)
  - [x] 4.5 Verify all error handling tests pass

- [x] 5. Create Comprehensive Documentation
  - [x] 5.1 Document AMC ad-hoc execution limitations in reference-docs/amc-ad-hoc-execution.md
  - [x] 5.2 Add code comments explaining the ad-hoc vs saved workflow distinction
  - [x] 5.3 Create troubleshooting guide for common ad-hoc execution issues
  - [x] 5.4 Document the execution flow from frontend to AMC API
  - [x] 5.5 Verify documentation is complete and accurate