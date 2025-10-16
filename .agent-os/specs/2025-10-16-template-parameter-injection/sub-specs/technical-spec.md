# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-10-16-template-parameter-injection/spec.md

> Created: 2025-10-16
> Version: 1.0.0

## Technical Requirements

### Frontend Architecture

**Component Changes:**
- **Primary File**: `frontend/src/components/instances/InstanceTemplateEditor.tsx`
- **New State Management**:
  ```typescript
  const [detectedParameters, setDetectedParameters] = useState<Parameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [previewSQL, setPreviewSQL] = useState<string>('');
  const [showPreview, setShowPreview] = useState<boolean>(true);
  const [isDetectingParameters, setIsDetectingParameters] = useState<boolean>(false);
  ```

**Reusable Components:**
1. **ParameterDetector** (existing utility)
   - Location: `frontend/src/utils/parameterDetector.ts`
   - Method: `detectParameters(sqlQuery: string): Parameter[]`
   - Formats supported: `{{param}}`, `:param`, `$param`
   - Type detection: asin, campaign, date, text

2. **ParameterSelectorList** (existing component)
   - Location: `frontend/src/components/workflows/ParameterSelectorList.tsx`
   - Props: `parameter`, `value`, `onChange`, `asins`, `campaigns`
   - Features: Add/remove items, clear all, search/filter

3. **useInstanceMappings** (existing hook)
   - Location: `frontend/src/hooks/useInstanceMappings.ts`
   - Returns: `{ mappings, isLoading, error, refetch }`
   - Caches results using TanStack Query (5-minute stale time)

4. **parameterAutoPopulator** (existing utility)
   - Location: `frontend/src/utils/parameterAutoPopulator.ts`
   - Method: `autoPopulateParameters(parameters, mappings): Record<string, any>`
   - Logic: Matches parameter names/types to mapping data

5. **replaceParametersInSQL** (existing utility)
   - Location: `frontend/src/utils/sqlParameterReplacer.ts`
   - Method: `replaceParametersInSQL(sql: string, values: Record<string, any>): string`
   - Handles: Arrays, single values, proper SQL escaping

**New Component Required:**

**ParameterPreviewPanel** (new component to create)
```typescript
// frontend/src/components/templates/ParameterPreviewPanel.tsx
interface ParameterPreviewPanelProps {
  sql: string;
  isVisible: boolean;
  onToggle: () => void;
  parameterCount: number;
  totalParameters: number;
}

export function ParameterPreviewPanel({
  sql,
  isVisible,
  onToggle,
  parameterCount,
  totalParameters
}: ParameterPreviewPanelProps) {
  // Monaco Editor (read-only) with syntax highlighting
  // Collapsible with expand/collapse icon
  // Height: 300px fixed
  // Shows "X of Y parameters configured"
}
```

### Parameter Detection Flow

**1. SQL Editor onChange Event:**
```typescript
const handleSQLChange = (value: string | undefined) => {
  setSqlQuery(value || '');

  // Debounce parameter detection (500ms)
  if (detectionTimeoutRef.current) {
    clearTimeout(detectionTimeoutRef.current);
  }

  detectionTimeoutRef.current = setTimeout(() => {
    detectParametersFromSQL(value || '');
  }, 500);
};
```

**2. Parameter Detection:**
```typescript
const detectParametersFromSQL = (sql: string) => {
  setIsDetectingParameters(true);

  try {
    const detector = new ParameterDetector();
    const params = detector.detectParameters(sql);
    setDetectedParameters(params);

    // Show banner if parameters found
    if (params.length > 0) {
      toast.info(`Detected ${params.length} parameter${params.length > 1 ? 's' : ''} - configure values below`);
    }
  } catch (error) {
    console.error('Parameter detection failed:', error);
    toast.error('Failed to detect parameters');
  } finally {
    setIsDetectingParameters(false);
  }
};
```

**3. Auto-Population:**
```typescript
useEffect(() => {
  if (detectedParameters.length > 0 && mappings && !isLoadingMappings) {
    const autoValues = parameterAutoPopulator.autoPopulateParameters(
      detectedParameters,
      mappings
    );

    if (Object.keys(autoValues).length > 0) {
      setParameterValues(prev => ({
        ...prev,
        ...autoValues
      }));

      toast.success(`Auto-populated ${Object.keys(autoValues).length} parameter${Object.keys(autoValues).length > 1 ? 's' : ''} from instance mappings`);
    }
  }
}, [detectedParameters, mappings, isLoadingMappings]);
```

**4. Preview Update:**
```typescript
useEffect(() => {
  // Debounce preview update (300ms)
  if (previewTimeoutRef.current) {
    clearTimeout(previewTimeoutRef.current);
  }

  previewTimeoutRef.current = setTimeout(() => {
    updatePreview();
  }, 300);
}, [sqlQuery, parameterValues]);

const updatePreview = () => {
  try {
    const preview = replaceParametersInSQL(sqlQuery, parameterValues);
    setPreviewSQL(preview);
  } catch (error) {
    console.error('Preview generation failed:', error);
    setPreviewSQL(sqlQuery); // Fallback to original SQL
  }
};
```

**5. Save with Substituted SQL:**
```typescript
const handleSave = async () => {
  // Validate all parameters have values
  const missingParams = detectedParameters.filter(p =>
    !parameterValues[p.name] ||
    (Array.isArray(parameterValues[p.name]) && parameterValues[p.name].length === 0)
  );

  if (missingParams.length > 0) {
    toast.error(`Please fill ${missingParams.length} required parameter${missingParams.length > 1 ? 's' : ''}`);
    return;
  }

  // Generate final SQL with substituted values
  const finalSQL = replaceParametersInSQL(sqlQuery, parameterValues);

  // Save template with complete SQL
  try {
    await instanceTemplateService.createTemplate(instanceId, {
      name: templateName,
      description: templateDescription,
      sql_query: finalSQL, // Complete SQL, not original with placeholders
      tags: templateTags
    });

    toast.success(`Template saved with ${detectedParameters.length} parameter${detectedParameters.length > 1 ? 's' : ''} substituted`);
    onClose();
  } catch (error) {
    console.error('Failed to save template:', error);
    toast.error('Failed to save template');
  }
};
```

### UI/UX Specifications

**Parameter Section Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ SQL Editor (Monaco)                                         │
│ Height: 400px                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ℹ️ Detected 3 parameters - configure values below          │
│ [Collapse ▼]                                                │
├─────────────────────────────────────────────────────────────┤
│ ASIN Parameters (2)                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ tracked_asins [ASIN] 🟢 Auto-populated                  │ │
│ │ [ParameterSelectorList component]                       │ │
│ │ - B07ZPKN6YR                                            │ │
│ │ - B08L8KC1J9                                            │ │
│ │ [+ Add] [Clear All]                                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Date Parameters (1)                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ start_date [Date]                                       │ │
│ │ [Date Picker Input: 2025-10-01]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SQL Preview (3 of 3 parameters configured) [Expand ▲]      │
├─────────────────────────────────────────────────────────────┤
│ [Monaco Editor - Read Only]                                 │
│ SELECT * FROM dsp_impressions                               │
│ WHERE asin IN ('B07ZPKN6YR', 'B08L8KC1J9')                 │
│ AND date >= '2025-10-01'                                    │
│ Height: 300px                                               │
└─────────────────────────────────────────────────────────────┘

[Cancel] [Save Template] ← Disabled if parameters incomplete
```

**Visual Indicators:**
- **Blue Banner**: Parameter detection notification
- **Green Badge**: Auto-populated parameter indicator
- **Red Border**: Empty required parameter (validation error)
- **Gray Badge**: Manual entry required
- **Spinner**: Loading state for mappings fetch

**Color Scheme:**
- Primary: Blue (#3B82F6) for info banners
- Success: Green (#10B981) for auto-populated badges
- Error: Red (#EF4444) for validation errors
- Neutral: Gray (#6B7280) for manual entry indicators

### Performance Considerations

**Debouncing Strategy:**
```typescript
// Parameter detection: 500ms debounce
// Rationale: Avoid excessive re-detection while typing SQL
const PARAMETER_DETECTION_DEBOUNCE = 500;

// Preview update: 300ms debounce
// Rationale: Balance responsiveness with performance
const PREVIEW_UPDATE_DEBOUNCE = 300;
```

**React Optimization:**
```typescript
// Memoize parameter selector to prevent unnecessary re-renders
const MemoizedParameterSelector = React.memo(ParameterSelectorList);

// Memoize preview panel
const MemoizedPreviewPanel = React.memo(ParameterPreviewPanel);

// Use useMemo for expensive calculations
const parameterCount = useMemo(() => {
  return Object.keys(parameterValues).filter(key => {
    const value = parameterValues[key];
    return value && (!Array.isArray(value) || value.length > 0);
  }).length;
}, [parameterValues]);
```

**Caching Strategy:**
```typescript
// useInstanceMappings already implements TanStack Query caching
// Cache key: ['instance-mappings', instanceId]
// Stale time: 5 minutes
// GC time: 10 minutes

// No additional caching required
```

**Query Size Limits:**
```typescript
// Warn if SQL query exceeds reasonable size
const MAX_SQL_SIZE = 50000; // 50KB
const MAX_PARAMETERS = 100;  // 100 parameters

if (sqlQuery.length > MAX_SQL_SIZE) {
  toast.warning('Large SQL query detected - parameter detection may be slow');
}

if (detectedParameters.length > MAX_PARAMETERS) {
  toast.warning(`Detected ${detectedParameters.length} parameters - consider simplifying query`);
}
```

### Error Handling

**1. Parameter Detection Failures:**
```typescript
try {
  const params = detector.detectParameters(sql);
  setDetectedParameters(params);
} catch (error) {
  console.error('Parameter detection failed:', error);
  toast.error('Failed to detect parameters - showing original SQL');
  setDetectedParameters([]); // Graceful degradation
}
```

**2. Mapping Fetch Failures:**
```typescript
const { mappings, isLoading, error } = useInstanceMappings(instanceId);

if (error) {
  toast.warning('Failed to load instance mappings - manual entry required');
  // Allow user to continue with manual entry
  // Don't block template creation
}
```

**3. Parameter Substitution Failures:**
```typescript
try {
  const preview = replaceParametersInSQL(sqlQuery, parameterValues);
  setPreviewSQL(preview);
} catch (error) {
  console.error('SQL substitution failed:', error);
  toast.error('Failed to generate preview - check parameter values');
  setPreviewSQL(sqlQuery); // Show original SQL as fallback
}
```

**4. Save Validation:**
```typescript
const validateParameters = () => {
  const errors: string[] = [];

  detectedParameters.forEach(param => {
    const value = parameterValues[param.name];

    if (!value) {
      errors.push(`${param.name} is required`);
    } else if (Array.isArray(value) && value.length === 0) {
      errors.push(`${param.name} must have at least one value`);
    }
  });

  if (errors.length > 0) {
    toast.error(`Validation failed:\n${errors.join('\n')}`);
    return false;
  }

  return true;
};
```

**5. Empty Parameter Edge Cases:**
```typescript
// Handle JavaScript empty array truthy issue
const hasValue = (value: any): boolean => {
  if (value === null || value === undefined || value === '') {
    return false;
  }

  if (Array.isArray(value)) {
    return value.length > 0; // Explicitly check length
  }

  return true;
};

// Use in validation
const isValid = detectedParameters.every(p => hasValue(parameterValues[p.name]));
```

## Component Hierarchy

```
InstanceTemplateEditor (modal)
├── Template Name Input
├── Template Description Textarea
├── Tags Input
├── SQL Editor (Monaco - 400px height)
├── Parameter Detection Section (conditional render)
│   ├── Info Banner ("Detected X parameters")
│   ├── Collapse/Expand Button
│   └── Parameter Groups (grouped by type)
│       ├── ASIN Parameters
│       │   └── ParameterSelectorList (for each ASIN param)
│       ├── Campaign Parameters
│       │   └── ParameterSelectorList (for each campaign param)
│       └── Other Parameters
│           └── Text/Date Input (for each other param)
├── ParameterPreviewPanel (new component)
│   ├── Header ("SQL Preview - X of Y parameters configured")
│   ├── Collapse/Expand Button
│   └── Monaco Editor (read-only, 300px height)
└── Action Buttons
    ├── Cancel Button
    └── Save Button (disabled if validation fails)
```

## Data Flow

```
┌─────────────────┐
│ User Types SQL  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Debounced Detection     │ (500ms)
│ ParameterDetector.      │
│ detectParameters()      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Set detectedParameters  │
│ Show Info Banner        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ useInstanceMappings     │
│ Fetch Instance Mappings │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ parameterAutoPopulator. │
│ autoPopulateParameters()│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Set parameterValues     │
│ Show Success Toast      │
│ Render Parameter Inputs │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ User Modifies Values    │
│ (Add/Remove/Edit)       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Debounced Preview       │ (300ms)
│ replaceParametersInSQL()│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Set previewSQL          │
│ Update Preview Panel    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ User Clicks Save        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Validate Parameters     │
│ (All filled?)           │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Generate Final SQL      │
│ replaceParametersInSQL()│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ instanceTemplateService │
│ .createTemplate()       │
│ (Save complete SQL)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Success Toast           │
│ Close Modal             │
│ Refresh Template List   │
└─────────────────────────┘
```

## External Dependencies

**No New Dependencies Required:**
- All utilities already exist in codebase
- ParameterDetector class: `frontend/src/utils/parameterDetector.ts`
- ParameterSelectorList component: `frontend/src/components/workflows/ParameterSelectorList.tsx`
- useInstanceMappings hook: `frontend/src/hooks/useInstanceMappings.ts`
- parameterAutoPopulator utility: `frontend/src/utils/parameterAutoPopulator.ts`
- replaceParametersInSQL utility: `frontend/src/utils/sqlParameterReplacer.ts`
- Monaco Editor: Already used in main SQL editor
- TanStack Query: Already configured for caching

**New Component to Create:**
- `ParameterPreviewPanel.tsx`: Collapsible SQL preview with Monaco Editor (read-only)

## Testing Strategy

**Unit Tests:**
1. Parameter detection with various SQL formats
2. Auto-population logic with mock mappings
3. Parameter validation (empty values, arrays)
4. SQL substitution with edge cases

**Component Tests:**
1. InstanceTemplateEditor renders parameter section when parameters detected
2. Auto-population toast appears with correct count
3. Save button disabled when parameters incomplete
4. Preview updates on parameter value change

**Integration Tests:**
1. Full flow: Detect → Auto-populate → Modify → Preview → Save
2. Error handling: Mapping fetch failure, detection failure
3. Edge cases: Empty arrays, special characters in parameters
4. Performance: Large SQL queries, many parameters

**Manual Testing Checklist:**
- [ ] Type SQL with `{{asin}}` parameter
- [ ] Verify ASIN auto-populates from mappings
- [ ] Add/remove ASINs using ParameterSelectorList
- [ ] Verify preview updates live
- [ ] Save template and verify SQL stored correctly
- [ ] Test with 50+ ASINs (performance check)
- [ ] Test with mixed parameter types (ASIN + date + custom)
- [ ] Test with no mappings available (graceful degradation)
- [ ] Test save validation (empty parameters blocked)
- [ ] Verify Template Execution Wizard works with saved template

## Migration Considerations

**No Database Migration Required:**
- `instance_templates.sql_query` already stores TEXT
- Complete SQL with substituted values fits existing schema
- No new columns or tables needed

**No API Changes Required:**
- `POST /api/instances/{instance_id}/templates` already accepts `sql_query` field
- Backend doesn't validate or process parameters
- Templates stored as-is in database

**Backward Compatibility:**
- Existing templates (without parameters) continue to work
- Feature is additive (doesn't break existing workflows)
- Users can choose to use parameters or not

## Rollout Plan

**Phase 1: Development**
- Implement ParameterPreviewPanel component
- Integrate parameter detection in InstanceTemplateEditor
- Add auto-population logic
- Implement preview update logic
- Add validation before save

**Phase 2: Testing**
- Unit tests for parameter detection/substitution
- Component tests for UI interactions
- Integration tests for full workflow
- Performance testing with large queries

**Phase 3: Deployment**
- Deploy frontend-only changes
- No backend deployment needed
- No database migration required
- Monitor error logs for issues

**Phase 4: Monitoring**
- Track parameter detection success rate
- Monitor template save success rate
- Collect user feedback on usability
- Measure time savings (analytics)
