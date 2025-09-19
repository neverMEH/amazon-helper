# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-18-report-builder-query-integration/spec.md

> Created: 2025-09-18
> Version: 1.0.0

## Technical Requirements

### Frontend Components Integration

- **Enhanced RunReportModal Component**
  - Modify wizard flow to start with template selection step
  - Add new "Template Selection" step before current "Parameters" step
  - Integrate QueryTemplateSelector modal component
  - Add toggle between "Select Template" and "Custom SQL" modes
  - Preserve existing wizard navigation logic for subsequent steps

- **Template Selection Interface**
  - Integrate existing QueryLibrary components (TemplateGrid)
  - Add search and filter capabilities using existing QueryTemplate services
  - Display template metadata (usage count, difficulty, category, tags)
  - Implement template preview with SQL syntax highlighting
  - Add category-based navigation with expandable sections

- **Context-Aware Parameter Detection**
  - Integrate SQL parameter analyzer utility (sqlParameterAnalyzer.ts)
  - Implement real-time parameter detection as users type in custom SQL mode
  - Auto-detect parameter types from SQL context (LIKE, IN, VALUES, BETWEEN)
  - Map detected contexts to appropriate input components
  - Display parameter format hints based on SQL usage

- **Intelligent Parameter Components**
  - Integrate AsinMultiSelect component for ASIN parameters
  - Integrate CampaignSelector with wildcard pattern support
  - Integrate DateRangePicker with presets and dynamic expressions
  - Implement UniversalParameterSelector for dynamic component selection
  - Add parameter validation based on detected types

- **SQL Preview Enhancement**
  - Enhance existing SQL preview to show parameter substitution
  - Use ParameterProcessor utility for consistent formatting
  - Display both template SQL and processed SQL side-by-side
  - Highlight parameter placeholders in the SQL editor
  - Show parameter values inline with tooltips

### State Management Updates

- **RunReportModal State Extensions**
  ```typescript
  interface ExtendedReportModalState {
    // New template-related state
    selectedTemplate: QueryTemplate | null;
    templateSearchTerm: string;
    templateCategory: string;
    templateSelectionMode: 'template' | 'custom';

    // Enhanced parameter state
    detectedParameterContexts: ParameterContext[];
    parameterValidation: ValidationState;
    sqlPreviewMode: 'template' | 'processed';

    // Existing state preserved
    currentStep: WizardStep;
    parameters: Record<string, any>;
    executionType: ExecutionType;
    scheduleConfig: ScheduleConfig;
  }
  ```

### Service Layer Integration

- **Query Template Service Usage**
  - Fetch templates with filtering and pagination
  - Increment template usage count on selection
  - Support template metadata retrieval
  - Handle template parameter schemas

- **Parameter Detection Service**
  - Real-time SQL analysis for parameter extraction
  - Context detection for each parameter
  - Type inference based on naming and context
  - Validation rule generation

### Data Flow Architecture

1. **Template Selection Flow**
   - User opens Report Builder → Template selection step appears
   - Browse/search templates → Select template → Load template SQL and parameters
   - Auto-detect parameters → Generate input components → Fill parameters
   - Preview processed SQL → Continue to execution configuration

2. **Custom SQL Flow**
   - User selects "Custom SQL" option → SQL editor appears
   - Type/paste SQL → Real-time parameter detection
   - Parameters detected → Context analysis → Input components generated
   - Fill parameters → Preview processed SQL → Continue to execution configuration

### Performance Considerations

- **Lazy Loading**
  - Load Query Library components only when template mode selected
  - Defer SQL parameter analyzer until needed
  - Virtualize template list for large collections

- **Caching Strategy**
  - Cache template list with 5-minute staleTime
  - Cache parameter detection results per SQL query
  - Memoize SQL preview calculations

- **Optimization Points**
  - Debounce parameter detection (300ms)
  - Throttle SQL preview updates (100ms)
  - Use React.memo for expensive components

### UI/UX Specifications

- **Step Navigation**
  - Add "Template Selection" as new first step
  - Show step indicator with icons
  - Allow backward navigation to change template
  - Skip template step if started with custom SQL

- **Template Browser Layout**
  - Grid view with template cards (3 columns on desktop)
  - Search bar with real-time filtering
  - Category sidebar with counts
  - Sort options (popular, recent, alphabetical)

- **Parameter Input Layout**
  - Group related parameters
  - Show parameter descriptions from template
  - Inline validation messages
  - Collapsible advanced parameters section

- **SQL Preview Layout**
  - Split view: Template SQL | Processed SQL
  - Syntax highlighting with Monaco Editor
  - Parameter placeholders highlighted in different color
  - Copy button for processed SQL

### Integration Requirements

- **Component Dependencies**
  - QueryTemplateSelector from query-library components
  - AsinMultiSelect from query-library components
  - CampaignSelector from query-builder components
  - DateRangePicker from query-library components
  - SQLEditor (Monaco) from common components

- **Utility Dependencies**
  - sqlParameterAnalyzer for context detection
  - ParameterDetector for parameter extraction
  - ParameterProcessor for SQL injection
  - parameterValidation for type checking

- **Service Dependencies**
  - queryTemplateService for template operations
  - instanceService for AMC instances
  - reportService for report creation

### Testing Requirements

- Unit tests for parameter context detection
- Integration tests for template selection flow
- E2E tests for full Report Builder workflow
- Performance tests for large template lists
- Accessibility tests for keyboard navigation

### Migration Considerations

- Preserve existing Report Builder functionality
- Ensure backward compatibility with existing reports
- Migrate existing custom queries to leverage new parameter detection
- Provide option to disable template selection for simple workflows