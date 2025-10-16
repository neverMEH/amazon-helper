# Spec Requirements Document

> Spec: Instance Template Parameter Auto-Population
> Created: 2025-10-16
> Status: Planning

## Overview

Enable parameter detection and auto-population in the Instance Template Editor to simplify template creation by automatically filling ASIN/campaign values from instance mappings and providing SQL preview before saving. This feature builds on existing parameter detection infrastructure from WorkflowParameterEditor and auto-population utilities, applying them to the template creation workflow.

When users write SQL queries with parameters (e.g., `{{asin}}`, `{{campaign_id}}`), the system will:
1. Detect parameters automatically from SQL syntax
2. Auto-populate ASIN and campaign parameters from instance mappings
3. Allow manual entry for date and custom parameters
4. Show live preview of final SQL with substituted values
5. Save the complete, parameterized SQL to the database

This eliminates the manual copy-paste workflow for large parameter lists (50+ ASINs) and ensures templates are ready to execute immediately after saving.

## User Stories

### 1. Marketing Analyst Creating ASIN-Based Template

**As a** marketing analyst managing 50+ tracked ASINs

**I want** ASIN parameters to auto-fill from instance mappings

**So that** I don't have to manually copy/paste ASIN lists every time I create a template

**Acceptance Criteria:**
- When I type `WHERE asin IN ({{tracked_asins}})` in the SQL editor
- The system detects the `tracked_asins` parameter
- ASINs from instance mappings automatically populate the parameter
- I can add/remove individual ASINs if needed
- The SQL preview shows the complete IN clause with all ASINs

### 2. Agency Manager Standardizing Campaign Queries

**As an** agency manager standardizing reporting queries

**I want** to see a preview of the final SQL before saving

**So that** I can ensure parameters are correctly substituted and the query will execute as expected

**Acceptance Criteria:**
- After configuring parameter values, a collapsible preview panel appears
- The preview shows the complete SQL with all parameters replaced
- Preview updates live as I change parameter values
- Syntax highlighting makes it easy to verify the query structure
- I can expand/collapse the preview to save screen space

### 3. Data Analyst with Mixed Parameter Types

**As a** data analyst creating date-filtered queries

**I want** to fill date parameters manually while ASINs auto-populate

**So that** I can control date ranges while benefiting from auto-population for product lists

**Acceptance Criteria:**
- When my SQL contains `{{start_date}}` and `{{tracked_asins}}`
- ASIN parameter auto-fills from mappings
- Date parameter shows empty text input for manual entry
- Both parameters display with appropriate type badges (ASIN vs Date)
- Save button remains disabled until I fill the date parameter
- Preview updates to show both substituted values

### 4. Power User Creating Reusable Templates

**As a** power user building a template library

**I want** to save templates with complete SQL (parameters already substituted)

**So that** other team members can execute them immediately without understanding parameters

**Acceptance Criteria:**
- After filling all parameters, I click Save
- The system saves the complete SQL with substituted values to `instance_templates.sql_query`
- When I or teammates use "Use Template" later, the SQL is ready to execute
- Template Execution Wizard requires no parameter configuration
- The template usage count increments as expected

## Spec Scope

### 1. Parameter Detection UI

**Display detected parameters below SQL editor:**
- Scan SQL on editor blur or manual trigger
- Support multiple parameter formats: `{{param}}`, `:param`, `$param`
- Show blue info banner: "Detected X parameters - configure values below"
- Display parameters grouped by type (ASINs, Campaigns, Other)
- Show type badges (ASIN, Campaign, Date, Text) for each parameter
- Collapsible parameter section to save screen space

**Reuse existing components:**
- `ParameterDetector` class from `frontend/src/utils/parameterDetector.ts`
- Parameter detection regex patterns already tested and working
- Type classification logic (asin, campaign, date detection)

### 2. Auto-Population for ASINs/Campaigns

**Fetch and pre-fill from instance mappings:**
- Use `useInstanceMappings` hook to fetch instance mappings on component mount
- Auto-populate when:
  - Parameter name contains "asin", "tracked", "product" (case-insensitive)
  - Parameter type detected as `asin` or `asin_list`
  - Parameter name contains "campaign" (case-insensitive)
  - Parameter type detected as `campaign` or `campaign_list`
- Display green badge indicator for auto-populated values
- Show loading spinner while fetching mappings
- Toast notification on successful auto-population

**Reuse existing utilities:**
- `parameterAutoPopulator.ts` utility from `frontend/src/utils/`
- `useInstanceMappings` hook from `frontend/src/hooks/`
- Existing mapping service for data fetching

### 3. Manual Entry for Other Parameters

**Text inputs for dates and custom fields:**
- Render text input for unrecognized parameter types
- Placeholder text: "Enter value for {parameter_name}"
- Date parameters show date picker input (type="date")
- Text parameters show standard text input
- Input validation: non-empty string required
- Real-time validation feedback (red border if empty)

**Parameter modification controls:**
- For ASIN/campaign parameters: use `ParameterSelectorList` component
- Add/remove individual values
- Clear all button
- Manual override preserves changes (no re-auto-population)

### 4. SQL Preview Panel

**Live preview showing final query with substituted values:**
- Collapsible section below parameter inputs
- Header: "SQL Preview" with expand/collapse icon
- Monaco Editor (read-only) for syntax highlighting
- Height: 300px (fixed pixel height)
- Theme: matches main editor theme
- Auto-scroll to top on content change

**Preview update logic:**
- Debounced updates (300ms) as user types or changes parameters
- Use `replaceParametersInSQL` utility for substitution
- Handle missing parameters gracefully (show original placeholder)
- Show parameter count: "X of Y parameters configured"

### 5. Save Complete Query

**Store fully parameterized SQL:**
- On save button click, validate all parameters have values
- Use `replaceParametersInSQL` to generate final SQL
- Call `instanceTemplateService.createTemplate()` with complete SQL
- Save to `instance_templates.sql_query` field (existing column)
- No backend changes required (templates already store complete SQL)
- Success toast: "Template saved with X parameters substituted"
- Close modal and refresh template list

## Out of Scope

### Parameter Validation
- No SQL syntax validation (user responsible to test query)
- No parameter type casting or conversion
- No detection of parameter mismatches (e.g., string in number field)
- Users should test queries in Query Builder before templating

### Parameter History/Versioning
- No tracking of parameter value changes over time
- No comparison between parameter sets
- No rollback to previous parameter configurations
- Future enhancement if needed

### Shared Parameter Libraries
- No global parameter definitions shared across templates
- No parameter presets or saved configurations
- Each template manages its own parameters independently
- Instance mappings are the only shared parameter source

### Parameter Type Conversion/Casting
- No automatic type conversion (string → number, date → timestamp)
- No validation of parameter format (ASIN format, date format)
- No SQL injection protection beyond basic escaping
- Users must ensure parameter values match SQL expectations

## Expected Deliverable

### 1. Instance Template Editor with Parameter Detection

**When user writes SQL with parameters:**
- System detects parameters using existing ParameterDetector
- Blue banner appears: "Detected X parameters - configure values below"
- Parameter input section displays with grouped parameters
- Each parameter shows type badge and appropriate input control

### 2. Auto-Populated ASIN/Campaign Parameters

**When parameters match mappable types:**
- `useInstanceMappings` hook fetches instance mappings on load
- `parameterAutoPopulator` utility pre-fills ASIN/campaign parameters
- Green badge indicates auto-populated values
- Toast notification confirms: "Auto-populated X parameters from instance mappings"
- User can modify values using ParameterSelectorList component

### 3. Manual Entry for Other Parameters

**When parameters don't match mappable types:**
- Text input or date picker appears based on parameter name
- Placeholder guides user: "Enter value for {parameter_name}"
- Real-time validation prevents saving with empty values
- Save button disabled until all parameters filled

### 4. Live SQL Preview

**When user configures parameters:**
- SQL preview panel shows complete query with substituted values
- Preview updates with 300ms debounce as user types
- Monaco Editor provides syntax highlighting (read-only)
- Collapsible to save screen space
- Parameter count indicator: "5 of 5 parameters configured"

### 5. Saved Template with Complete SQL

**When user clicks Save:**
- System validates all parameters have values
- `replaceParametersInSQL` generates final SQL string
- `instanceTemplateService.createTemplate()` saves to database
- `instance_templates.sql_query` contains complete, executable SQL
- Template Execution Wizard can execute without parameter configuration
- Template list refreshes with new template

## Success Metrics

### Usability Metrics
- **Parameter Detection Accuracy**: 95%+ of common parameter formats detected
- **Auto-Population Success Rate**: 90%+ of ASIN/campaign parameters auto-filled
- **Time Savings**: 50% reduction in template creation time (measured in user testing)
- **Preview Usage**: 80%+ of users expand preview before saving

### Technical Metrics
- **Performance**: Parameter detection < 100ms for queries up to 10KB
- **Preview Rendering**: SQL preview updates < 500ms after parameter change
- **Zero API Changes**: No backend modifications required (frontend-only)
- **Component Reuse**: 80%+ of logic reused from existing components

### Adoption Metrics
- **Template Quality**: 30% increase in templates saved with correct parameters
- **Execution Success Rate**: 20% increase in first-time execution success
- **User Satisfaction**: 4.5+ star rating in post-feature survey

## Spec Documentation

- Tasks: @.agent-os/specs/2025-10-16-template-parameter-injection/tasks.md
- Technical Specification: @.agent-os/specs/2025-10-16-template-parameter-injection/sub-specs/technical-spec.md
- API Specification: Not required (no API changes)
