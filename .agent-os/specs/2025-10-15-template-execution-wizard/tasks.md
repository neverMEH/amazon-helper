# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-10-15-template-execution-wizard/spec.md

> Created: 2025-10-15
> Status: ✅ **IMPLEMENTATION COMPLETE** - Ready for Manual Testing

## Tasks

- [x] 1. Backend Service Layer and API Endpoints
  - [x] 1.1 Create Pydantic schemas in `amc_manager/schemas/template_execution.py`
    - [x] 1.1.1 Define `TemplateExecutionRequest` schema with validation
    - [x] 1.1.2 Define `ScheduleConfigSchema` with frequency and date range validation
    - [x] 1.1.3 Define `TemplateScheduleRequest` schema
    - [x] 1.1.4 Define response schemas (`TemplateExecutionResponse`, `TemplateScheduleResponse`)
  - [x] 1.2 Create FastAPI router in `amc_manager/api/supabase/template_execution.py`
    - [x] 1.2.1 Implement `POST /instances/{instance_id}/templates/{template_id}/execute` endpoint
    - [x] 1.2.2 Add template ownership verification
    - [x] 1.2.3 Implement AMC API call with retry logic for immediate execution
    - [x] 1.2.4 Store execution record with Snowflake metadata
    - [x] 1.2.5 Implement `POST /instances/{instance_id}/templates/{template_id}/schedule` endpoint
    - [x] 1.2.6 Create workflow from template with metadata
    - [x] 1.2.7 Create schedule with rolling date range support
  - [x] 1.3 Register router in `main_supabase.py`
  - [x] 1.4 Write unit tests for both endpoints
    - [x] 1.4.1 Test template ownership verification
    - [x] 1.4.2 Test immediate execution flow
    - [x] 1.4.3 Test schedule creation flow
    - [x] 1.4.4 Test error handling (404, 401, 400)
  - [x] 1.5 Verify endpoints work via `/docs` (Swagger UI)

- [x] 2. Frontend Types and Services
  - [x] 2.1 Create TypeScript types in `frontend/src/types/templateExecution.ts`
    - [x] 2.1.1 Define `TemplateExecutionRequest` interface
    - [x] 2.1.2 Define `TemplateScheduleRequest` interface
    - [x] 2.1.3 Define response interfaces
  - [x] 2.2 Create API service in `frontend/src/services/templateExecutionService.ts`
    - [x] 2.2.1 Implement `execute()` method for run once
    - [x] 2.2.2 Implement `createSchedule()` method for recurring
    - [x] 2.2.3 Add proper error handling and TypeScript types
  - [x] 2.3 Write TypeScript interface tests
  - [x] 2.4 Verify TypeScript compilation passes with no errors

- [x] 3. Template Execution Wizard Component
  - [x] 3.1 Create base wizard component in `frontend/src/components/instances/TemplateExecutionWizard.tsx`
    - [x] 3.1.1 Set up modal structure with header, content, and footer
    - [x] 3.1.2 Implement step indicator with 4 steps
    - [x] 3.1.3 Add state management for wizard flow
    - [x] 3.1.4 Implement step navigation (next/back buttons)
  - [x] 3.2 Implement Step 1: Display Step
    - [x] 3.2.1 Show template name as heading
    - [x] 3.2.2 Display instance badge with brand name
    - [x] 3.2.3 Add SQL preview with read-only Monaco editor (300px height)
    - [x] 3.2.4 Add "Next" button to proceed
  - [x] 3.3 Implement Step 2: Execution Type Selection
    - [x] 3.3.1 Create radio button card for "Run Once"
    - [x] 3.3.2 Create radio button card for "Recurring Schedule"
    - [x] 3.3.3 Add hover effects and selection styling
    - [x] 3.3.4 Update state on selection
  - [x] 3.4 Implement Step 3A: Date Range Selection (Run Once)
    - [x] 3.4.1 Add AMC data lag warning banner
    - [x] 3.4.2 Implement rolling window toggle checkbox
    - [x] 3.4.3 Add window size preset buttons (7, 14, 30, 60, 90 days)
    - [x] 3.4.4 Add custom window size input field
    - [x] 3.4.5 Implement date range calculation logic (accounting for 14-day lag)
    - [x] 3.4.6 Add start date picker (HTML5 date input)
    - [x] 3.4.7 Add end date picker (HTML5 date input)
    - [x] 3.4.8 Show calculated range preview
    - [x] 3.4.9 Set default to last 30 days minus 14-day lag
  - [x] 3.5 Implement Step 3B: Schedule Configuration (Recurring)
    - [x] 3.5.1 Import and integrate existing `DateRangeStep` component
    - [x] 3.5.2 Pass schedule config state and onChange handler
    - [x] 3.5.3 Verify all schedule options work (daily/weekly/monthly)
  - [x] 3.6 Implement Step 4: Review Step
    - [x] 3.6.1 Display execution details section (name, type, instance, template)
    - [x] 3.6.2 Show date range (run once) or schedule info (recurring)
    - [x] 3.6.3 Add collapsible SQL preview
    - [x] 3.6.4 Implement Snowflake integration toggle (run once only)
    - [x] 3.6.5 Add conditional Snowflake fields (table name, schema name)
    - [x] 3.6.6 Add "Submit" button with loading state
  - [x] 3.7 Implement auto-generated naming logic
    - [x] 3.7.1 Create `generateExecutionName()` utility function
    - [x] 3.7.2 Extract brand name from instance info
    - [x] 3.7.3 Format: "{Brand} - {Template} - {StartDate} - {EndDate}"
  - [x] 3.8 Implement submission handlers
    - [x] 3.8.1 Handle run once submission (call execute endpoint)
    - [x] 3.8.2 Handle recurring schedule submission (call schedule endpoint)
    - [x] 3.8.3 Add toast notifications for success/error
    - [x] 3.8.4 Navigate to appropriate page (Executions or Schedules)
    - [x] 3.8.5 Call `onComplete()` callback

- [x] 4. Integration with InstanceTemplates Component
  - [x] 4.1 Update `frontend/src/components/instances/InstanceTemplates.tsx`
    - [x] 4.1.1 Add state for wizard modal (open/closed)
    - [x] 4.1.2 Add state for selected template
    - [x] 4.1.3 Update "Use Template" button click handler
    - [x] 4.1.4 Remove old navigation to Query Builder
    - [x] 4.1.5 Open TemplateExecutionWizard modal instead
  - [x] 4.2 Add wizard component to render tree
    - [x] 4.2.1 Import TemplateExecutionWizard component
    - [x] 4.2.2 Render wizard with conditional based on state
    - [x] 4.2.3 Pass template and instance info as props
    - [x] 4.2.4 Handle wizard close and complete callbacks
  - [x] 4.3 Add cache invalidation on completion
    - [x] 4.3.1 Invalidate templates query to refresh usage count
    - [x] 4.3.2 Invalidate executions query (if on executions page)
    - [x] 4.3.3 Invalidate schedules query (if on schedules page)

- [x] 5. Styling and UX Polish
  - [x] 5.1 Ensure consistent styling with existing modals
  - [x] 5.2 Add smooth transitions between wizard steps
  - [x] 5.3 Implement proper focus management (auto-focus first field)
  - [x] 5.4 Add loading spinners during API calls
  - [x] 5.5 Implement proper error message display
  - [x] 5.6 Test responsive layout on mobile/tablet
  - [x] 5.7 Add keyboard navigation support (Tab, Enter, Escape)
  - [x] 5.8 Verify accessibility with screen reader

- [x] 6. Testing and Validation
  - [x] 6.1 Write component tests for TemplateExecutionWizard
    - [x] 6.1.1 Test step navigation
    - [x] 6.1.2 Test execution type selection
    - [x] 6.1.3 Test date range calculation
    - [x] 6.1.4 Test schedule configuration
    - [x] 6.1.5 Test submission handlers
  - [x] 6.2 Run backend unit tests (`pytest tests/ -v`)
  - [x] 6.3 Run frontend tests (`npm test`)
  - [ ] 6.4 Perform manual end-to-end testing
    - [ ] 6.4.1 Test run once execution with default dates
    - [ ] 6.4.2 Test run once execution with custom dates
    - [ ] 6.4.3 Test run once with Snowflake enabled
    - [ ] 6.4.4 Test daily schedule creation
    - [ ] 6.4.5 Test weekly schedule creation
    - [ ] 6.4.6 Test monthly schedule creation
    - [ ] 6.4.7 Verify executions appear in Executions page
    - [ ] 6.4.8 Verify schedules appear in Schedules page
    - [ ] 6.4.9 Verify auto-generated names are correct
    - [ ] 6.4.10 Test error scenarios (invalid template, missing instance)

- [x] 7. Documentation Updates
  - [x] 7.1 Update `CLAUDE.md` with Template Execution Wizard feature
    - [x] 7.1.1 Add feature description to main features list
    - [x] 7.1.2 Document new API endpoints
    - [x] 7.1.3 Add user workflow examples
    - [x] 7.1.4 Document auto-naming convention
  - [x] 7.2 Update related feature documentation
    - [x] 7.2.1 Update Instance Templates section with new workflow
    - [x] 7.2.2 Document integration with Schedules feature
    - [x] 7.2.3 Document Snowflake integration usage
  - [x] 7.3 Add inline code comments for complex logic
    - [x] 7.3.1 Comment date calculation logic
    - [x] 7.3.2 Comment auto-naming logic
    - [x] 7.3.3 Comment step navigation logic

- [ ] 8. Performance Optimization
  - [ ] 8.1 Lazy load TemplateExecutionWizard component
  - [ ] 8.2 Optimize Monaco editor rendering
  - [ ] 8.3 Test wizard performance with large SQL queries
  - [ ] 8.4 Verify no memory leaks on modal close
  - [ ] 8.5 Test with slow network connections

- [ ] 9. Final Integration and Deployment
  - [ ] 9.1 Merge all changes to main branch
  - [ ] 9.2 Deploy backend changes to staging
  - [ ] 9.3 Deploy frontend changes to staging
  - [ ] 9.4 Perform smoke tests on staging
  - [ ] 9.5 Deploy to production
  - [ ] 9.6 Monitor error logs for 24 hours
  - [ ] 9.7 Verify feature is working in production

## Implementation Notes

### Critical Gotchas
1. **Instance ID Format**: Always use UUID for API calls (not AMC instance string)
2. **Date Format**: Use ISO date format without timezone (YYYY-MM-DD)
3. **AMC Data Lag**: Always account for 14-day data processing lag in date calculations
4. **Template Ownership**: Always verify user owns template before execution
5. **Navigation State**: Use React Router's `navigate()` function, not window.location
6. **Snowflake Config**: Store in execution metadata JSONB field, not separate columns

### Reusable Components
- **DateRangeStep**: Reuse from schedules wizard for schedule configuration
- **Monaco Editor**: Use existing SQLEditor wrapper component
- **InstanceSelector**: Not needed (instance is pre-selected from context)
- **Schedule Configuration**: Leverage existing schedule creation logic

### Testing Priorities
1. **High**: Template ownership verification (security)
2. **High**: Date calculation logic (correctness)
3. **High**: Auto-naming convention (user experience)
4. **Medium**: Snowflake integration (optional feature)
5. **Medium**: Schedule configuration (reuses existing logic)
6. **Low**: Styling and animations (polish)

### Migration Path
- No database migrations required (uses existing schema)
- No breaking changes to existing features
- Can be deployed incrementally (backend first, then frontend)
- Old "Use Template" navigation can coexist during testing

### Rollback Plan
If issues arise post-deployment:
1. Revert frontend changes (remove wizard modal)
2. Restore old "Use Template" navigation to Query Builder
3. Backend endpoints can remain (no harm if unused)
4. No data cleanup needed (executions/schedules are normal records)
