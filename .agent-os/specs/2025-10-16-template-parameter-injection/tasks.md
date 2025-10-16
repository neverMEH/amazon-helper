# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2025-10-16-template-parameter-injection/spec.md

> Created: 2025-10-16
> Status: Ready for Implementation

## Tasks

### 1. Create ParameterPreviewPanel Component

New utility component for displaying SQL preview with parameter substitution in a collapsible Monaco Editor.

- [ ] 1.1 Write tests for ParameterPreviewPanel component
  - Test component renders with SQL prop
  - Test collapsible accordion functionality (expanded/collapsed states)
  - Test Monaco Editor initialization in read-only mode
  - Test syntax highlighting for SQL language
  - Test height and layout rendering (300px fixed height)
  - Test empty SQL handling (display placeholder message)
  - Test prop updates (SQL changes trigger re-render)

- [ ] 1.2 Create component file at frontend/src/components/instances/ParameterPreviewPanel.tsx
  - Define TypeScript interface: `ParameterPreviewPanelProps { sql: string; isExpanded?: boolean; onToggle?: () => void; }`
  - Add useState for local expanded state if not controlled
  - Use Accordion from Radix UI or custom collapsible div
  - Add header with "SQL Preview" title and expand/collapse icon

- [ ] 1.3 Add Monaco Editor in read-only mode
  - Import Monaco Editor from @monaco-editor/react
  - Configure language="sql", theme="vs-dark"
  - Set readOnly={true} and minimap={{ enabled: false }}
  - Set height="300px" (fixed pixel height, not percentage)
  - Add loading skeleton/placeholder while editor loads

- [ ] 1.4 Add collapsible accordion UI
  - Use transition for smooth expand/collapse animation
  - Add chevron icon that rotates on state change
  - Add border and rounded corners for visual separation
  - Add padding and margin for spacing
  - Default to collapsed state (isExpanded={false})

- [ ] 1.5 Add syntax highlighting configuration
  - Verify SQL syntax highlighting works in Monaco
  - Add line numbers and code folding controls
  - Configure font family (monospace) and size (14px)
  - Test with complex SQL queries (JOINs, CTEs, subqueries)

- [ ] 1.6 Style with Tailwind CSS
  - Use border-gray-300, rounded-lg, shadow-sm classes
  - Add bg-white for light mode, bg-gray-800 for dark mode
  - Style header with flex, items-center, justify-between
  - Add hover effects on header (cursor-pointer, bg-gray-50)
  - Ensure responsive design (full width, proper padding)

- [ ] 1.7 Verify all tests pass
  - Run `npm test ParameterPreviewPanel.test.tsx`
  - Check for TypeScript compilation errors
  - Test component in Storybook or isolation
  - Verify accessibility (keyboard navigation, ARIA labels)

### 2. Integrate Parameter Detection into InstanceTemplateEditor

Add parameter detection, parameter selector, and state management to existing Instance Template Editor.

- [ ] 2.1 Write tests for parameter detection integration
  - Test SQL parsing extracts parameters correctly
  - Test detected parameters state updates on SQL change
  - Test parameter values state initialization
  - Test ParameterSelectorList rendering with detected parameters
  - Test parameter count badge display (0, 1, 5+ parameters)
  - Test parameter detection with various formats ({{param}}, :param, $param)

- [ ] 2.2 Add ParameterDetector component to InstanceTemplateEditor
  - Import ParameterDetector from existing utilities
  - Add after SQL editor in modal layout
  - Pass sqlQuery prop from template editor state
  - Handle onParametersDetected callback
  - Add conditional rendering (only show if parameters detected)

- [ ] 2.3 Add state management for parameters
  - Add useState: `const [detectedParameters, setDetectedParameters] = useState<Parameter[]>([])`
  - Add useState: `const [parameterValues, setParameterValues] = useState<Record<string, any>>({})`
  - Update detectedParameters on SQL change via ParameterDetector callback
  - Initialize parameterValues when new parameters detected (empty strings/arrays)
  - Clear states when modal closes or resets

- [ ] 2.4 Add useInstanceMappings hook for auto-population
  - Import useInstanceMappings from existing hook
  - Call hook with instanceId from editor state
  - Handle loading state (show spinner while fetching)
  - Handle error state (show error message if fetch fails)
  - Refetch mappings when instanceId changes

- [ ] 2.5 Display parameter detection UI below SQL editor
  - Add ParameterSelectorList component after ParameterDetector
  - Pass detectedParameters, parameterValues, onChange handler
  - Add section header: "Detected Parameters" with count badge
  - Add spacing between SQL editor and parameter inputs (mt-6)
  - Use form layout with proper labels and inputs

- [ ] 2.6 Add parameter count badge/banner
  - Show badge next to "Detected Parameters" header
  - Display count: `{detectedParameters.length} parameter(s)`
  - Style with bg-blue-100, text-blue-800, rounded-full
  - Add info icon with tooltip explaining parameter detection
  - Hide entire section if detectedParameters.length === 0

- [ ] 2.7 Verify all tests pass
  - Run `npm test InstanceTemplateEditor.test.tsx`
  - Test parameter detection with sample SQL queries
  - Verify parameter inputs render correctly
  - Check TypeScript compilation (no errors)

### 3. Implement Parameter Auto-Population Logic

Add automatic population of ASIN and campaign parameters from instance mappings with visual feedback.

- [ ] 3.1 Write tests for auto-population logic
  - Test auto-population triggers when mappings load
  - Test ASIN parameters populated from instance mappings
  - Test campaign parameters populated from instance mappings
  - Test brand parameters remain empty (no auto-population)
  - Test manual values override auto-populated values
  - Test toast notification displays on success
  - Test empty mappings scenario (no auto-population, no error)

- [ ] 3.2 Integrate parameterAutoPopulator utility
  - Import { autoPopulateFromMappings } from existing utility
  - Call function when mappings data changes (useEffect dependency)
  - Pass detectedParameters and mappings data
  - Receive auto-populated values object
  - Only populate if parameterValues are empty/default

- [ ] 3.3 Fetch instance mappings on instance selection
  - Trigger useInstanceMappings refetch when instanceId changes
  - Add loading indicator while fetching (small spinner)
  - Handle case where instanceId is empty (skip fetch)
  - Cache mappings using React Query (staleTime: 5 minutes)
  - Clear previous mappings when instance changes

- [ ] 3.4 Auto-populate ASIN parameters from mappings
  - Detect parameters with type="asin" or type="asin_list"
  - Detect parameters with name containing "asin" or "tracked"
  - Extract ASINs from mappings.asins array
  - Format as comma-separated string for single ASIN params
  - Format as array for asin_list params
  - Update parameterValues state with auto-populated ASINs

- [ ] 3.5 Auto-populate campaign parameters from mappings
  - Detect parameters with type="campaign" or type="campaign_list"
  - Detect parameters with name containing "campaign"
  - Extract campaign IDs from mappings.campaigns array
  - Exclude campaigns with promotion prefixes (coupon-, promo-, socialmedia-)
  - Format as comma-separated string or array based on type
  - Update parameterValues state with auto-populated campaigns

- [ ] 3.6 Add green "auto-populated" badges
  - Add badge component next to auto-populated parameter inputs
  - Display text: "Auto-populated from instance mappings"
  - Style with bg-green-100, text-green-800, text-xs
  - Add checkmark icon for visual feedback
  - Only show badge if value was auto-populated (not manually entered)

- [ ] 3.7 Add toast notification on success
  - Import toast from existing toast library (react-hot-toast or similar)
  - Show success toast when auto-population completes
  - Message: "Auto-populated {count} parameter(s) from instance mappings"
  - Use success variant with green color scheme
  - Auto-dismiss after 3 seconds
  - Only show if at least 1 parameter was auto-populated

- [ ] 3.8 Verify all tests pass
  - Run `npm test` for auto-population tests
  - Test with real instance mappings data
  - Verify badge rendering and styling
  - Test toast notification appearance
  - Check for TypeScript errors

### 4. Add SQL Preview and Parameter Substitution

Implement real-time SQL preview with parameter substitution using Monaco Editor in read-only mode.

- [ ] 4.1 Write tests for parameter substitution
  - Test replaceParametersInSQL utility integration
  - Test parameter replacement for {{param}} format
  - Test parameter replacement for :param format
  - Test parameter replacement for $param format
  - Test handling of missing parameter values (show placeholder)
  - Test handling of array parameters (JOIN with commas)
  - Test SQL preview updates when parameters change

- [ ] 4.2 Add ParameterPreviewPanel to template editor
  - Import ParameterPreviewPanel component
  - Add below parameter inputs section in modal
  - Pass substituted SQL as prop
  - Add section header: "SQL Preview with Parameters"
  - Add spacing (mt-8) and visual separation (border-t)

- [ ] 4.3 Implement replaceParametersInSQL utility integration
  - Import replaceParametersInSQL from existing utilities
  - Create useMemo hook for substituted SQL computation
  - Dependencies: [sqlQuery, parameterValues, detectedParameters]
  - Pass original SQL and parameter values to utility
  - Store result in local state or compute on-the-fly

- [ ] 4.4 Add debounced preview updates (300ms)
  - Import useDebouncedValue hook or create custom debounce
  - Apply debounce to sqlQuery state changes
  - Debounce parameter value changes as well
  - Prevents excessive re-computation during typing
  - Use 300ms delay for optimal UX (not too slow, not too fast)

- [ ] 4.5 Handle parameter substitution errors gracefully
  - Wrap replaceParametersInSQL in try-catch block
  - Display error message in preview panel if substitution fails
  - Log error to console for debugging
  - Show original SQL if substitution fails (fallback)
  - Add error banner with red background above preview

- [ ] 4.6 Update save logic to store complete SQL
  - Modify onSave handler in InstanceTemplateEditor
  - Use substituted SQL (with parameters replaced) when saving
  - Store original SQL with parameters in description or metadata (optional)
  - Ensure template.sqlQuery field contains complete, executable SQL
  - Update backend schema if needed (check if metadata field exists)

- [ ] 4.7 Verify all tests pass
  - Run `npm test` for SQL preview tests
  - Test preview with various parameter combinations
  - Verify debounce timing (no lag, no excessive updates)
  - Test save functionality with substituted SQL
  - Check for TypeScript compilation errors

### 5. Testing and Documentation

Comprehensive integration testing, edge case validation, and documentation updates.

- [ ] 5.1 Write integration tests for full workflow
  - Test end-to-end: SQL entry → parameter detection → auto-population → preview → save
  - Test with complex SQL queries (multiple parameters, nested queries)
  - Test with workflows (create workflow from template with parameters)
  - Test with schedules (schedule workflow with auto-populated parameters)
  - Verify template usage increments correctly
  - Test navigation from template editor to query builder

- [ ] 5.2 Test with various parameter formats
  - Test {{param}} format (double curly braces)
  - Test :param format (colon prefix)
  - Test $param format (dollar sign prefix)
  - Test mixed formats in same query
  - Test parameter names with underscores, numbers, capitals
  - Test edge cases (empty parameter names, special characters)

- [ ] 5.3 Test auto-population with missing mappings
  - Test when instance has no mappings configured
  - Test when mappings API returns empty arrays
  - Test when mappings API returns error (404, 500)
  - Verify parameters remain empty (no auto-population)
  - Verify no error toast or broken UI
  - Test manual entry still works when mappings missing

- [ ] 5.4 Test manual parameter entry
  - Test typing values into parameter inputs (overrides auto-population)
  - Test clearing auto-populated values (remove badge)
  - Test saving with manually entered parameters
  - Test SQL preview updates with manual values
  - Verify manual values persist when re-opening editor

- [ ] 5.5 Test SQL preview with complex queries
  - Test queries with CTEs (WITH clauses)
  - Test queries with subqueries and JOINs
  - Test queries with window functions and aggregations
  - Test queries with multiple parameter references (same param used twice)
  - Test queries with array parameters (IN clauses)
  - Verify syntax highlighting works correctly

- [ ] 5.6 Update CLAUDE.md with feature documentation
  - Add "Instance Template Parameter Injection" section under Instance Templates Feature
  - Document parameter detection formats supported ({{param}}, :param, $param)
  - Document auto-population behavior and requirements (instance mappings)
  - Document SQL preview functionality and debouncing
  - Add usage examples (code snippets showing parameter detection flow)
  - Add to "Critical Gotchas" if needed (parameter format precedence, auto-population timing)
  - Update project structure if new files added (ParameterPreviewPanel.tsx)

- [ ] 5.7 Create user-facing documentation (optional)
  - Create guide in .agent-os/specs/2025-10-16-template-parameter-injection/user-guide.md
  - Add screenshots or diagrams of parameter detection UI
  - Document best practices for parameter naming (use descriptive names)
  - Document mapping requirements for auto-population (ASINs and campaigns must be mapped)
  - Add troubleshooting section (common issues: mappings not loading, parameters not detected)

- [ ] 5.8 Verify all tests pass
  - Run full test suite: `npm test`
  - Check test coverage (aim for >80% on new code)
  - Run TypeScript type checking: `npx tsc --noEmit`
  - Run linter: `npm run lint`
  - Test in browser (manual QA)
  - Verify no console errors or warnings

## Implementation Notes

### Technical Dependencies

- **ParameterDetector**: Existing utility component for parsing SQL parameters
- **parameterAutoPopulator**: Existing utility for mapping instance data to parameters
- **ParameterSelectorList**: Existing component for rendering parameter input fields
- **useInstanceMappings**: Existing React hook for fetching instance mappings
- **replaceParametersInSQL**: Existing utility for substituting parameters in SQL
- **Monaco Editor**: Already integrated in project (@monaco-editor/react)

### Component Architecture

```
InstanceTemplateEditor.tsx (Modified)
├── SQL Editor (existing Monaco Editor)
├── ParameterDetector (existing component)
├── ParameterSelectorList (existing component)
│   ├── Parameter inputs with auto-populate badges
│   └── Manual value overrides
└── ParameterPreviewPanel (new component)
    └── Monaco Editor (read-only, SQL preview)
```

### State Flow

1. User enters SQL in template editor
2. ParameterDetector parses SQL → detectedParameters state
3. useInstanceMappings fetches mappings → mappings state
4. parameterAutoPopulator combines → parameterValues state (auto-populated)
5. User can override values manually
6. replaceParametersInSQL combines SQL + values → substitutedSQL
7. ParameterPreviewPanel displays substitutedSQL
8. Save stores substitutedSQL in template.sqlQuery

### Testing Strategy

- **Unit Tests**: Each component and utility function tested in isolation
- **Integration Tests**: Full workflow tested end-to-end
- **Edge Case Tests**: Missing data, errors, invalid inputs
- **Manual QA**: Browser testing with real data

### Success Criteria

- [ ] Parameter detection works for all 3 formats ({{param}}, :param, $param)
- [ ] Auto-population successfully populates ASINs and campaigns from mappings
- [ ] SQL preview displays substituted SQL with syntax highlighting
- [ ] Save functionality stores complete, executable SQL
- [ ] All tests pass (unit + integration)
- [ ] TypeScript compilation successful with no errors
- [ ] No regression in existing template functionality
- [ ] Documentation updated in CLAUDE.md

## Task Execution Order

1. **Task 1**: Create ParameterPreviewPanel Component (foundation)
2. **Task 2**: Integrate Parameter Detection (detection infrastructure)
3. **Task 3**: Implement Auto-Population (mappings integration)
4. **Task 4**: Add SQL Preview (preview rendering)
5. **Task 5**: Testing and Documentation (validation and finalization)

## Estimated Time

- **Task 1**: 2-3 hours (component creation with tests)
- **Task 2**: 3-4 hours (integration with existing editor)
- **Task 3**: 3-4 hours (auto-population logic and UI)
- **Task 4**: 3-4 hours (preview implementation and save logic)
- **Task 5**: 3-4 hours (testing and documentation)

**Total**: 14-19 hours (2-3 days of development)

## Files to Create

- `frontend/src/components/instances/ParameterPreviewPanel.tsx`
- `frontend/src/components/instances/ParameterPreviewPanel.test.tsx`

## Files to Modify

- `frontend/src/components/instances/InstanceTemplateEditor.tsx`
- `frontend/src/components/instances/InstanceTemplateEditor.test.tsx` (if exists)
- `CLAUDE.md` (documentation update)
