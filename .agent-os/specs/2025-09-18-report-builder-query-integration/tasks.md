# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-18-report-builder-query-integration/spec.md

> Created: 2025-09-18
> Status: Ready for Implementation

## Tasks

- [ ] 1. Enhance Report Builder Wizard with Template Selection Step
  - [ ] 1.1 Write tests for enhanced RunReportModal wizard flow
  - [ ] 1.2 Add template selection as new first wizard step with mode toggle (template/custom)
  - [ ] 1.3 Integrate QueryTemplateSelector component for template browsing
  - [ ] 1.4 Update wizard navigation to handle new step flow
  - [ ] 1.5 Add template metadata display (usage count, difficulty, tags)
  - [ ] 1.6 Implement template search and category filtering
  - [ ] 1.7 Add SQL preview for selected templates
  - [ ] 1.8 Verify all wizard navigation tests pass

- [ ] 2. Integrate Context-Aware Parameter Detection System
  - [ ] 2.1 Write tests for SQL parameter context analysis
  - [ ] 2.2 Integrate sqlParameterAnalyzer utility for context detection
  - [ ] 2.3 Implement real-time parameter detection for custom SQL mode
  - [ ] 2.4 Add parameter type inference from SQL context (LIKE, IN, VALUES, BETWEEN)
  - [ ] 2.5 Map detected contexts to appropriate input components
  - [ ] 2.6 Display parameter format hints based on SQL usage
  - [ ] 2.7 Add parameter validation based on detected types
  - [ ] 2.8 Verify all parameter detection tests pass

- [ ] 3. Implement Intelligent Parameter Input Components
  - [ ] 3.1 Write tests for dynamic parameter form generation
  - [ ] 3.2 Integrate AsinMultiSelect for ASIN parameters with bulk input
  - [ ] 3.3 Integrate CampaignSelector with wildcard pattern support
  - [ ] 3.4 Integrate DateRangePicker with presets and dynamic expressions
  - [ ] 3.5 Implement UniversalParameterSelector for dynamic component selection
  - [ ] 3.6 Add parameter grouping and organization in the UI
  - [ ] 3.7 Implement parameter value persistence and defaults from templates
  - [ ] 3.8 Verify all parameter input component tests pass

- [ ] 4. Enhance SQL Preview with Parameter Substitution
  - [ ] 4.1 Write tests for SQL preview with parameter injection
  - [ ] 4.2 Integrate ParameterProcessor for consistent SQL formatting
  - [ ] 4.3 Implement side-by-side view (template SQL vs processed SQL)
  - [ ] 4.4 Add parameter placeholder highlighting in Monaco editor
  - [ ] 4.5 Display parameter values with inline tooltips
  - [ ] 4.6 Add copy button for processed SQL
  - [ ] 4.7 Verify all SQL preview tests pass

- [ ] 5. Connect Template Usage Analytics and API Integration
  - [ ] 5.1 Write tests for template API integration
  - [ ] 5.2 Implement template usage tracking on selection
  - [ ] 5.3 Add parameter validation API calls before report creation
  - [ ] 5.4 Connect report creation from template with proper parameter injection
  - [ ] 5.5 Add error handling for template loading and validation failures
  - [ ] 5.6 Implement template metadata caching for performance
  - [ ] 5.7 Add loading states and error boundaries
  - [ ] 5.8 Verify all API integration tests pass