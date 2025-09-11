# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-11-query-library-redesign/spec.md

> Created: 2025-09-11
> Status: Ready for Implementation

## Tasks

- [x] 1. Database Schema Implementation ✅ (Completed: 2025-09-11)
  - [x] 1.1 Write tests for database migrations
  - [x] 1.2 Create migration script for enhanced query_templates table
  - [x] 1.3 Create query_template_parameters table with proper constraints
  - [x] 1.4 Create query_template_reports table for dashboard configurations
  - [x] 1.5 Create query_template_instances table for saved parameter sets
  - [x] 1.6 Implement RLS policies for all new tables
  - [x] 1.7 Create indexes for performance optimization
  - [x] 1.8 Verify all tests pass

- [ ] 2. Backend Services Development
  - [ ] 2.1 Write tests for QueryTemplateService enhancements
  - [ ] 2.2 Implement template versioning and forking in QueryTemplateService
  - [ ] 2.3 Create TemplateParameterService with parameter detection and validation
  - [ ] 2.4 Create TemplateReportService for dashboard generation
  - [ ] 2.5 Enhance ParameterEngine for new parameter types (asin_list, campaign_filter, etc.)
  - [ ] 2.6 Implement parameter validation with SQL injection prevention
  - [ ] 2.7 Add caching layer for frequently used templates
  - [ ] 2.8 Verify all tests pass

- [ ] 3. API Endpoints Implementation
  - [ ] 3.1 Write tests for query library API endpoints
  - [ ] 3.2 Create GET /api/query-library/templates endpoint with filtering
  - [ ] 3.3 Create POST endpoints for template CRUD operations
  - [ ] 3.4 Implement template execution and parameter validation endpoints
  - [ ] 3.5 Create template instance management endpoints
  - [ ] 3.6 Implement dashboard generation endpoint
  - [ ] 3.7 Add proper error handling and response formatting
  - [ ] 3.8 Verify all tests pass

- [ ] 4. Frontend Components Development
  - [ ] 4.1 Write tests for Query Library page components
  - [ ] 4.2 Create Query Library page with template gallery and search
  - [ ] 4.3 Build AsinMultiSelect component with bulk paste support (60+ items)
  - [ ] 4.4 Create CampaignSelector with wildcard pattern support
  - [ ] 4.5 Implement DateRangePicker with presets and dynamic expressions
  - [ ] 4.6 Build Template Editor with Monaco SQL editor and live parameter detection
  - [ ] 4.7 Create Report Builder interface with drag-drop layout
  - [ ] 4.8 Verify all tests pass

- [ ] 5. Integration and Migration
  - [ ] 5.1 Write tests for integration points
  - [ ] 5.2 Modify workflow creation to support "Create from Template" option
  - [ ] 5.3 Update collection creation to reference templates with batch parameters
  - [ ] 5.4 Enhance schedule system to support dynamic parameter expressions
  - [ ] 5.5 Implement backward compatibility layer for existing templates
  - [ ] 5.6 Create data migration script for existing query_templates
  - [ ] 5.7 Perform end-to-end testing of complete feature
  - [ ] 5.8 Verify all tests pass

## Implementation Notes

### Priority Order
1. Database schema (foundation for all features)
2. Backend services (business logic layer)
3. API endpoints (interface layer)
4. Frontend components (user interface)
5. Integration and migration (system-wide changes)

### Dependencies
- Database schema must be complete before backend services
- Backend services required before API endpoints
- API endpoints needed for frontend development
- Integration requires all components to be functional

### Success Criteria
- All tests passing with >80% coverage
- Support for 60+ ASIN bulk input
- Template execution time <3 seconds
- Dashboard generation time <3 seconds
- Backward compatibility maintained