# Spec Tasks - Fix Workflow ID UUID/String Mismatch

## Tasks

- [ ] 1. Fix Backend Workflow API Endpoint ID Handling
  - [ ] 1.1 Write tests for workflow GET endpoint with both UUID and string IDs
  - [ ] 1.2 Update GET /api/workflows/{workflow_id} endpoint to use db_service dual-lookup
  - [ ] 1.3 Ensure all workflow API endpoints handle both ID types consistently
  - [ ] 1.4 Add validation to detect and properly route ID types
  - [ ] 1.5 Verify all tests pass for workflow endpoints

- [ ] 2. Update Database Service Methods
  - [ ] 2.1 Write tests for get_workflow_by_id_sync with mixed ID types
  - [ ] 2.2 Audit all workflow database queries for proper ID handling
  - [ ] 2.3 Ensure consistent use of dual-lookup pattern across services
  - [ ] 2.4 Add error handling for invalid UUID format exceptions
  - [ ] 2.5 Verify all database service tests pass

- [ ] 3. Fix Frontend Workflow Service
  - [ ] 3.1 Write tests for frontend workflow service ID handling
  - [ ] 3.2 Ensure frontend consistently uses the correct ID field
  - [ ] 3.3 Update WorkflowDetail component to handle both ID types
  - [ ] 3.4 Fix any hardcoded assumptions about ID format
  - [ ] 3.5 Verify all frontend tests pass

- [ ] 4. Audit Related Services for ID Issues
  - [ ] 4.1 Check collection services for workflow ID references
  - [ ] 4.2 Review schedule services for proper workflow ID handling
  - [ ] 4.3 Verify execution services use correct ID fields
  - [ ] 4.4 Fix any discovered ID type mismatches
  - [ ] 4.5 Ensure all integration tests pass

- [ ] 5. End-to-End Testing and Documentation
  - [ ] 5.1 Test creating a workflow and retrieving it by both IDs
  - [ ] 5.2 Test workflow execution with string workflow_id
  - [ ] 5.3 Test workflow listing and filtering
  - [ ] 5.4 Update CLAUDE.md with ID handling documentation
  - [ ] 5.5 Verify all E2E tests pass with no regressions