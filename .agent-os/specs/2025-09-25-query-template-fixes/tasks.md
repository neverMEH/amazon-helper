# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-09-25-query-template-fixes/spec.md reference the C:\Users\Aeciu\Projects\amazon-helper-2\.agent-os\features folder and files to understand the codebase and how to integrate the new features effectively without rewriting code and messing the structure up.

> Created: 2025-09-25
> Status: Ready for Implementation

## Tasks

- [x] 1. Fix CampaignSelector Integration in TemplateEditor
  - [x] 1.1 Write tests for CampaignSelector integration in TemplateEditor
  - [x] 1.2 Import CampaignSelector component into TemplateEditor.tsx
  - [x] 1.3 Replace textarea with CampaignSelector for campaign_list parameters
  - [x] 1.4 Update parameter onChange handlers to work with CampaignSelector output
  - [x] 1.5 Test campaign selection with multi-select and brand filtering
  - [x] 1.6 Ensure campaign IDs are properly formatted for SQL preview
  - [x] 1.7 Add error handling for campaign API failures
  - [x] 1.8 Verify all tests pass

- [x] 2. Implement Persistent Template Name Header
  - [x] 2.1 Write tests for persistent template name display
  - [x] 2.2 Restructure TemplateEditor component layout with persistent header
  - [x] 2.3 Move template name input field outside of tab content area
  - [x] 2.4 Ensure template name remains visible across all tabs
  - [x] 2.5 Add auto-save functionality for template name changes
  - [x] 2.6 Style the persistent header to match existing UI design
  - [x] 2.7 Test template name persistence across page refreshes
  - [x] 2.8 Verify all tests pass

- [x] 3. Fix Parameter State Persistence
  - [x] 3.1 Write tests for parameter metadata persistence
  - [x] 3.2 Debug updateParameter function to identify state loss issues
  - [x] 3.3 Ensure all parameter properties are included in save operations
  - [x] 3.4 Verify parameters_schema JSON structure in database saves
  - [x] 3.5 Test loading templates with complex parameter schemas
  - [x] 3.6 Add validation for required parameter fields
  - [x] 3.7 Verify all tests pass

- [ ] 4. Integrate Query Library with Report Builder
  - [ ] 4.1 Write tests for Report Builder template integration
  - [ ] 4.2 Create API endpoint for Report Builder template retrieval
  - [ ] 4.3 Add Query Library Templates section to Report Builder UI
  - [ ] 4.4 Implement template selection and parameter configuration modal
  - [ ] 4.5 Connect template application to Report Builder's SQL editor
  - [ ] 4.6 Add "Save as Template" feature for successful queries
  - [ ] 4.7 Test end-to-end template usage in Report Builder
  - [ ] 4.8 Verify all tests pass

- [ ] 5. Create Enhanced Parameter Input Components
  - [ ] 5.1 Write tests for specialized parameter input components
  - [ ] 5.2 Create ParameterInputs.tsx with type-specific components
  - [ ] 5.3 Implement validation for each parameter type
  - [ ] 5.4 Add visual indicators for required fields
  - [ ] 5.5 Test all parameter types with edge cases
  - [ ] 5.6 Verify all tests pass