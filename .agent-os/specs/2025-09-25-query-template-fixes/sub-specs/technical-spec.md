# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-25-query-template-fixes/spec.md

> Created: 2025-09-25
> Version: 1.0.0

## Technical Requirements

### 1. CampaignSelector Integration in TemplateEditor

**Current Issue**: TemplateEditor.tsx uses a basic textarea for campaign_list parameters instead of the existing CampaignSelector component.

**Files to Modify**:
- `frontend/src/components/query-library/TemplateEditor.tsx`

**Implementation Details**:
- Import CampaignSelector from `../parameter-detection/CampaignSelector.tsx`
- In the parameter rendering section (lines ~400-500), detect when `param.type === 'campaign_list'`
- Replace the textarea with CampaignSelector component
- Pass required props: `value`, `onChange`, `multiple={true}`, `valueType="ids"`
- Handle the onChange to update parameter preview values correctly
- The CampaignSelector expects optional instanceId and brandId - these should be passed from user context if available

**Code Changes**:
```typescript
// Add import
import CampaignSelector from '../parameter-detection/CampaignSelector';

// Replace textarea rendering for campaign_list
{param.type === 'campaign_list' ? (
  <CampaignSelector
    value={param.previewValue || ''}
    onChange={(value) => updateParameter(param.name, { previewValue: value })}
    multiple={true}
    valueType="ids"
    placeholder="Select campaigns..."
  />
) : (
  // existing textarea code
)}
```

### 2. Persistent Template Name Header

**Current Issue**: Template name is only visible in the Editor tab and disappears when switching to Preview or Settings tabs.

**Files to Modify**:
- `frontend/src/components/query-library/TemplateEditor.tsx`

**Implementation Details**:
- Move the template name input outside of the tab content area
- Create a persistent header section above the tabs
- Ensure the name field is always visible and editable
- Update the component structure to have header -> tabs -> content layout

**UI Structure**:
```
[Template Header - Always Visible]
  - Template Name Input
  - Save/Cancel buttons
[Tab Navigation]
  - Editor | Preview | Settings
[Tab Content Area]
  - Current tab content
```

### 3. Parameter State Persistence Fix

**Current Issue**: Parameter metadata (description, required, previewValue) not properly persisting when saved to database.

**Files to Modify**:
- `frontend/src/components/query-library/TemplateEditor.tsx`
- `frontend/src/services/queryTemplateService.ts`

**Implementation Details**:
- Ensure `updateParameter` function updates all parameter properties
- Verify the parameters_schema JSON structure includes all fields
- Check that the backend properly stores and retrieves the full parameter schema
- Add validation to ensure required parameter fields are preserved

**Parameter Schema Structure**:
```typescript
interface ParameterSchema {
  [key: string]: {
    type: string;
    description?: string;
    required?: boolean;
    previewValue?: any;
    defaultValue?: any;
    validation?: {
      min?: number;
      max?: number;
      pattern?: string;
    };
  }
}
```

### 4. Report Builder Integration

**Current Issue**: Report Builder (ReportBuilder.tsx) has its own template system (TemplateGrid) that doesn't connect to Query Library templates.

**Files to Modify**:
- `frontend/src/pages/ReportBuilder.tsx`
- `frontend/src/components/report-builder/TemplateGrid.tsx`

**Implementation Details**:
- Add a new tab or section in Report Builder for "Query Library Templates"
- Fetch templates from queryTemplateService
- Display templates in a grid or list format
- Add "Use Template" action that opens parameter configuration modal
- Apply configured template SQL to the Report Builder's SQL editor

**Integration Points**:
```typescript
// In ReportBuilder.tsx
import { queryTemplateService } from '../services/queryTemplateService';

// Add state for templates
const [templates, setTemplates] = useState([]);

// Fetch templates on mount
useEffect(() => {
  queryTemplateService.list({ isPublic: true })
    .then(setTemplates)
    .catch(console.error);
}, []);

// Add template selection handler
const applyTemplate = async (template, parameters) => {
  const sql = await queryTemplateService.buildQuery(template.id, parameters);
  setSqlQuery(sql); // Update Report Builder's SQL
};
```

### 5. Enhanced Parameter Input Components

**Current Issue**: Parameter inputs lack proper validation and user-friendly interfaces for different types.

**Files to Modify**:
- `frontend/src/components/query-library/TemplateEditor.tsx`
- Create new file: `frontend/src/components/query-library/ParameterInputs.tsx`

**Implementation Details**:
- Create specialized input components for each parameter type
- Add validation based on parameter constraints
- Provide better UI feedback for required fields
- Support all parameter types detected by sqlParameterAnalyzer

**Component Mapping**:
```typescript
const ParameterInputs = {
  text: TextInput,
  number: NumberInput,
  date: DatePicker,
  date_range: DateRangePicker,
  asin_list: AsinMultiSelect,
  campaign_list: CampaignSelector,
  pattern: PatternInput,
  boolean: BooleanToggle
};
```

## Approach

### Development Strategy
1. **Incremental Implementation**: Implement fixes one by one to avoid breaking existing functionality
2. **Component Reuse**: Leverage existing components (CampaignSelector, AsinMultiSelect) rather than creating new ones
3. **Backward Compatibility**: Ensure changes don't break existing templates or workflows
4. **User Experience Focus**: Prioritize intuitive UI and clear feedback for parameter configuration

### Implementation Order
1. Fix CampaignSelector integration (highest impact, lowest risk)
2. Implement persistent template header (UI improvement)
3. Fix parameter state persistence (data integrity)
4. Add Report Builder integration (feature expansion)
5. Enhance parameter input components (polish)

### Error Handling
- Graceful degradation when CampaignSelector API calls fail
- Validation feedback for invalid parameter values
- Recovery mechanisms for corrupted parameter schemas
- Clear error messages for template application failures

## External Dependencies

### Frontend Dependencies
- Existing CampaignSelector component (`frontend/src/components/parameter-detection/CampaignSelector.tsx`)
- AsinMultiSelect component for ASIN parameters
- Date picker components for date/date_range parameters
- React Hook Form for form validation (if not already used)
- Monaco Editor for SQL syntax highlighting

### Backend Dependencies
- Query Template Service API endpoints
- Campaign API for CampaignSelector data
- Parameter validation utilities
- SQL query building service

### Database Dependencies
- No schema changes required
- Existing `query_templates` table structure supports enhanced parameter schemas
- Parameter metadata stored in `parameters_schema` JSON column

## Performance Considerations

- CampaignSelector makes API calls - implement caching to avoid repeated fetches
- Template list in Report Builder should use pagination or virtualization for large lists
- Parameter validation should be debounced to avoid excessive re-renders
- SQL query building should be optimized for complex parameter substitution

## Testing Requirements

### Unit Tests
- Parameter type detection and validation
- Template name persistence across tab switches
- Parameter schema serialization/deserialization
- SQL query building with various parameter combinations

### Integration Tests
- CampaignSelector integration with various campaign configurations
- Template application in Report Builder
- Parameter state persistence through save/load cycles
- Cross-component data flow validation

### User Acceptance Tests
- Template creation workflow end-to-end
- Parameter configuration user experience
- Template application in different contexts
- Error handling and recovery scenarios

### Edge Cases
- Empty campaigns list
- Invalid parameter values
- Network errors during campaign loading
- Corrupted parameter schemas
- Large parameter sets (performance)

## Migration Considerations

### Data Migration
- No database schema changes required
- Existing templates will continue to work unchanged
- Parameter schemas are backward compatible
- No data migration scripts needed

### User Impact
- Improved UI experience with no breaking changes
- Existing templates remain functional
- Users can gradually adopt enhanced parameter features
- No training required for basic functionality

### Rollback Strategy
- Changes are additive and can be easily reverted
- Component-level rollback possible
- Database changes are non-destructive
- Feature flags can control new functionality rollout