# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-08-28-universal-parameter-selection/spec.md

> Created: 2025-08-28
> Status: Ready for Implementation

## Tasks

- [ ] 1. Backend Parameter Detection and API Development
  - [ ] 1.1 Write tests for parameter detection service
  - [ ] 1.2 Implement regex-based parameter detection engine for SQL queries
  - [ ] 1.3 Create GET /api/workflows/{workflow_id}/parameters endpoint
  - [ ] 1.4 Create GET /api/asins endpoint with brand filtering
  - [ ] 1.5 Create GET /api/campaigns endpoint with brand filtering
  - [ ] 1.6 Implement POST /api/workflows/{workflow_id}/validate-parameters endpoint
  - [ ] 1.7 Add proper database indexes for performance optimization
  - [ ] 1.8 Verify all backend tests pass

- [ ] 2. Frontend Parameter Detection Components
  - [ ] 2.1 Write tests for ParameterDetector component
  - [ ] 2.2 Implement ParameterDetector component with regex pattern matching
  - [ ] 2.3 Create UniversalParameterSelector container component
  - [ ] 2.4 Implement detection result caching and debouncing
  - [ ] 2.5 Verify parameter detection tests pass

- [ ] 3. ASIN and Campaign Selection Components
  - [ ] 3.1 Write tests for ASINSelector component
  - [ ] 3.2 Implement ASINSelector with multi-select and search functionality
  - [ ] 3.3 Write tests for CampaignSelector component
  - [ ] 3.4 Implement CampaignSelector with brand filtering
  - [ ] 3.5 Add virtualization for large dropdown lists
  - [ ] 3.6 Implement data caching with React Query
  - [ ] 3.7 Verify all selection component tests pass

- [ ] 4. Date Range Selection Component
  - [ ] 4.1 Write tests for DateRangeSelector component
  - [ ] 4.2 Implement preset options (Last 7/14/30 days)
  - [ ] 4.3 Add custom date range picker functionality
  - [ ] 4.4 Implement AMC date format handling (no timezone suffix)
  - [ ] 4.5 Add date validation logic
  - [ ] 4.6 Verify date selector tests pass

- [ ] 5. Workflow Form Integration and End-to-End Testing
  - [ ] 5.1 Write integration tests for workflow parameter flow
  - [ ] 5.2 Integrate parameter detection into WorkflowForm component
  - [ ] 5.3 Implement parameter value storage in workflow metadata
  - [ ] 5.4 Update workflow execution service for array parameter handling
  - [ ] 5.5 Add error handling and loading states
  - [ ] 5.6 Perform end-to-end testing with real workflows
  - [ ] 5.7 Update documentation and add examples
  - [ ] 5.8 Verify all integration tests pass