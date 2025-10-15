# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-10-15-instance-templates/spec.md

> Created: 2025-10-15
> Status: Ready for Implementation

## Tasks

- [x] 1. Database Schema and Migration
  - [x] 1.1 Write database migration script to create instance_templates table with all fields, indexes, and RLS policies
  - [x] 1.2 Create rollback migration script for reverting changes
  - [x] 1.3 Test migration script on local Supabase instance
  - [x] 1.4 Verify RLS policies work correctly (users can only access their own templates)
  - [x] 1.5 Verify foreign key constraints and cascade deletes work properly

- [x] 2. Backend Service Layer and API
  - [x] 2.1 Write unit tests for InstanceTemplateService (create, read, update, delete, list operations)
  - [x] 2.2 Create InstanceTemplateService class extending DatabaseService with @with_connection_retry decorator
  - [x] 2.3 Implement CRUD methods with proper error handling and caching
  - [x] 2.4 Create Pydantic schemas (InstanceTemplateCreate, InstanceTemplateUpdate, InstanceTemplateResponse)
  - [x] 2.5 Create FastAPI router in amc_manager/api/supabase/instance_templates.py
  - [x] 2.6 Implement all 6 REST endpoints with proper authentication and validation
  - [x] 2.7 Register router in main_supabase.py
  - [x] 2.8 Verify all unit tests pass and endpoints work via /docs

- [x] 3. Frontend Types and API Service
  - [x] 3.1 Write TypeScript interface tests for InstanceTemplate type
  - [x] 3.2 Create types/instanceTemplate.ts with InstanceTemplate interface
  - [x] 3.3 Create services/instanceTemplateService.ts with API methods (list, create, get, update, delete, use)
  - [x] 3.4 Add proper error handling and TypeScript types to service layer
  - [x] 3.5 Verify TypeScript compilation passes with no errors

- [x] 4. Template Editor Modal Component
  - [x] 4.1 Write component tests for InstanceTemplateEditor modal
  - [x] 4.2 Create components/instances/InstanceTemplateEditor.tsx modal component
  - [x] 4.3 Implement form fields (name, description, SQL query with Monaco editor)
  - [x] 4.4 Add form validation and error display
  - [x] 4.5 Implement save/cancel handlers with TanStack Query mutations
  - [x] 4.6 Add toast notifications for success/error feedback
  - [x] 4.7 Verify modal opens, closes, and saves correctly in browser

- [x] 5. Instance Templates List Component
  - [x] 5.1 Write component tests for InstanceTemplates list view
  - [x] 5.2 Create components/instances/InstanceTemplates.tsx component
  - [x] 5.3 Implement template list with TanStack Query for data fetching
  - [x] 5.4 Add template cards with Edit, Delete, and "Use Template" actions
  - [x] 5.5 Implement delete confirmation dialog
  - [x] 5.6 Add empty state with "Create Template" CTA
  - [x] 5.7 Integrate InstanceTemplateEditor modal
  - [x] 5.8 Verify list displays correctly, CRUD operations work, and cache invalidates properly

- [x] 6. Instance Detail Page Integration
  - [x] 6.1 Update InstanceDetail.tsx tab configuration to replace "Workflows" with "Templates"
  - [x] 6.2 Update tab routing to show InstanceTemplates component
  - [x] 6.3 Test tab navigation and template list rendering
  - [x] 6.4 Verify templates are properly scoped to the selected instance

- [x] 7. Query Builder Integration for "Use Template"
  - [x] 7.1 Update QueryBuilder component to accept template SQL via navigation state
  - [x] 7.2 Implement "Use Template" navigation from InstanceTemplates to QueryBuilder
  - [x] 7.3 Pre-populate SQL editor with template query and pre-select instance
  - [x] 7.4 Call increment usage endpoint when template is used
  - [x] 7.5 Verify end-to-end flow: template selection → pre-filled query builder → workflow creation

- [x] 8. Testing and Documentation
  - [x] 8.1 Run full backend test suite (pytest tests/ -v)
  - [x] 8.2 Run frontend tests (npm test)
  - [x] 8.3 Perform manual end-to-end testing of all workflows
  - [x] 8.4 Update CLAUDE.md with instance templates feature documentation
  - [x] 8.5 Verify all tests pass and feature works as specified
