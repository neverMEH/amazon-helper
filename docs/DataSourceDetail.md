# DataSourceDetail.tsx

## Purpose
Comprehensive AMC schema detail page providing complete documentation view with two-panel layout, table of contents navigation, field explorer, and example query integration. Serves as the primary interface for understanding AMC data sources.

## Dependencies
### External Dependencies
- react: 18.2.0+ - Core React hooks (useState, useEffect, useRef, useMemo)
- react-router-dom: 6.0+ - Navigation (useParams, useNavigate)
- @tanstack/react-query: 4.0+ - Data fetching and caching
- lucide-react: 0.400+ - Icon components

### Internal Dependencies
- ../services/dataSourceService: API service for schema data
- ../components/common/SQLEditor: Monaco-based SQL editor
- ../components/data-sources/TableOfContents: Scroll-synced navigation
- ../components/data-sources/FieldExplorer: Advanced field browser
- ../types/dataSource: TypeScript type definitions

## Exports
### Default Export
- `DataSourceDetail`: Main component for schema detail display

## Usage Examples
```tsx
// Route integration
<Route path="/data-sources/:schemaId" element={<DataSourceDetail />} />

// Direct navigation
navigate(`/data-sources/${schema.schema_id}`);

// Query key for React Query
queryKey: ['dataSource', schemaId]
```

## Relationships
### Used By
- frontend/src/App.tsx: Route configuration
- frontend/src/pages/DataSources.tsx: Navigation from list view
- Command palette search results

### Uses
- dataSourceService.getCompleteSchema(): Fetch detailed schema
- TableOfContents: Section navigation
- FieldExplorer: Field browsing and search
- SQLEditor: Example query display
- SessionStorage: Query builder integration

## Side Effects
- URL parameter parsing for schema ID
- Local storage for UI state persistence
- Session storage for query builder communication
- Scroll position tracking for TOC sync
- Copy to clipboard operations

## Testing Considerations
### Key Scenarios
- Schema loading states (loading, success, error)
- URL parameter handling and validation
- Table of contents scroll synchronization
- Field explorer filtering and search
- Example query copy functionality
- Navigation to query builder with pre-filled data

### Edge Cases
- Invalid schema IDs in URL
- Missing schema fields or sections
- Large schemas with many fields
- Network failures during loading
- Malformed example queries
- Browser without clipboard API support

### Mocking Requirements
- Mock dataSourceService responses
- Schema data with complete field definitions
- Example queries with various complexities
- Navigation mock for router integration

## Performance Notes
### Optimizations
- useMemo for computed values (TOC items, filtered fields)
- React Query caching for schema data
- Lazy rendering of large field lists
- Debounced search input
- Efficient scroll event handling

### Bottlenecks
- Large schemas with hundreds of fields
- Complex example queries in Monaco Editor
- Frequent scroll events for TOC sync
- JSON parsing of large schema objects

### Monitoring Points
- Schema load times
- Field search performance
- Scroll event frequency
- Memory usage with large schemas

## Component Architecture

### State Management
```tsx
interface ComponentState {
  activeSection: string;           // Current TOC section
  copiedExample: string | null;    // Recently copied example ID
  fieldSearch: string;             // Field search query
  expandedSections: Set<string>;   // Expanded field categories
}
```

### Two-Panel Layout
```tsx
<div className="flex h-full">
  {/* Left Panel - Table of Contents */}
  <div className="w-64 border-r bg-gray-50">
    <TableOfContents
      sections={tocSections}
      activeSection={activeSection}
      onSectionClick={handleSectionClick}
    />
  </div>
  
  {/* Right Panel - Content */}
  <div className="flex-1 overflow-auto" ref={contentRef}>
    {/* Content sections */}
  </div>
</div>
```

### Query Builder Integration
```tsx
const handleUseInQueryBuilder = (example: QueryExample) => {
  // Store example data in session storage
  sessionStorage.setItem('queryBuilderDraft', JSON.stringify({
    sql_query: example.sql_query,
    name: example.name,
    description: example.description,
    parameters: example.parameters || {}
  }));
  
  // Navigate to query builder
  navigate('/query-builder');
};
```

## Critical Implementation Patterns

### Scroll-Synced Table of Contents
```tsx
useEffect(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
        }
      });
    },
    {
      threshold: 0.5,
      rootMargin: '-10% 0px -70% 0px'
    }
  );

  // Observe all section elements
  const sections = contentRef.current?.querySelectorAll('[data-section]');
  sections?.forEach(section => observer.observe(section));

  return () => observer.disconnect();
}, [schema]);
```

### React Query Integration
```tsx
const { data: schema, isLoading, error } = useQuery<CompleteSchema>({
  queryKey: ['dataSource', schemaId],
  queryFn: async () => {
    if (!schemaId) throw new Error('Schema ID required');
    return await dataSourceService.getCompleteSchema(schemaId);
  },
  enabled: !!schemaId,
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
});
```

### Copy to Clipboard with Feedback
```tsx
const handleCopyExample = async (example: QueryExample) => {
  try {
    await navigator.clipboard.writeText(example.sql_query);
    setCopiedExample(example.id);
    
    // Reset feedback after delay
    setTimeout(() => setCopiedExample(null), 2000);
  } catch (error) {
    console.error('Failed to copy:', error);
    // Fallback for browsers without clipboard API
    fallbackCopy(example.sql_query);
  }
};
```

### Memoized TOC Generation
```tsx
const tocSections = useMemo(() => {
  if (!schema) return [];
  
  const sections = [
    { id: 'overview', title: 'Overview', level: 1 },
    { id: 'fields', title: 'Fields', level: 1 },
  ];
  
  // Add field category sections
  const categories = groupFieldsByCategory(schema.fields);
  categories.forEach(category => {
    sections.push({
      id: `fields-${category.toLowerCase()}`,
      title: category,
      level: 2
    });
  });
  
  // Add example sections
  if (schema.examples?.length > 0) {
    sections.push({ id: 'examples', title: 'Examples', level: 1 });
  }
  
  return sections;
}, [schema]);
```

## UI Component Integration

### Field Explorer Integration
```tsx
<FieldExplorer
  fields={schema.fields}
  searchTerm={fieldSearch}
  onFieldSelect={handleFieldSelect}
  categories={fieldCategories}
  expandedCategories={expandedSections}
  onCategoryToggle={handleCategoryToggle}
/>
```

### SQL Editor for Examples
```tsx
<SQLEditor
  value={example.sql_query}
  readOnly={true}
  height="300px"
  language="sql"
  theme="vs-light"
  options={{
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    lineNumbers: 'on',
    wordWrap: 'on'
  }}
/>
```

## Error Handling Strategies

### Schema Loading Errors
```tsx
if (error) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Schema Not Found
        </h3>
        <p className="text-gray-600 mb-4">
          The requested schema could not be loaded.
        </p>
        <button
          onClick={() => navigate('/data-sources')}
          className="btn btn-primary"
        >
          Back to Data Sources
        </button>
      </div>
    </div>
  );
}
```

### Navigation Error Handling
```tsx
useEffect(() => {
  // Validate schema ID format
  if (schemaId && !isValidSchemaId(schemaId)) {
    console.error('Invalid schema ID format:', schemaId);
    navigate('/data-sources', { replace: true });
  }
}, [schemaId, navigate]);
```

## Accessibility Features

### Keyboard Navigation
```tsx
const handleKeyDown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowUp':
    case 'ArrowDown':
      // Navigate TOC sections
      event.preventDefault();
      navigateTOC(event.key === 'ArrowUp' ? -1 : 1);
      break;
    case 'Enter':
      // Activate focused section
      if (document.activeElement?.id) {
        setActiveSection(document.activeElement.id);
      }
      break;
  }
};
```

### Screen Reader Support
```tsx
<section 
  id="overview" 
  data-section="overview"
  aria-labelledby="overview-heading"
  role="region"
>
  <h2 id="overview-heading" className="sr-only">
    Schema Overview
  </h2>
  {/* Content */}
</section>
```

## Mobile Responsiveness

### Responsive Layout
```tsx
const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

// Toggle TOC visibility on mobile
const [showTOC, setShowTOC] = useState(!isMobile);

// Responsive class names
const containerClasses = cn(
  'flex h-full',
  isMobile ? 'flex-col' : 'flex-row'
);
```

## Recent Updates

### 2025-08-15 Changes
- Merged DataSourceDetailV2 features into main component
- Added two-panel layout with persistent TOC
- Integrated FieldExplorer for advanced field browsing
- Enhanced query builder integration via session storage
- Improved error handling for missing schemas
- Cleaned up empty sections display

### Performance Improvements
- Optimized intersection observer for TOC sync
- Added React Query caching with appropriate TTL
- Memoized expensive computations
- Reduced re-renders with stable callbacks

## Integration Notes

### With DataSources List
- Seamless navigation from list to detail
- Breadcrumb navigation support
- Back button functionality

### With Query Builder
- Session storage communication
- Pre-filled example queries
- Parameter extraction

### With Search/Command Palette
- Direct navigation to specific schemas
- Search result integration
- Deep linking support

## Configuration Options

### Display Configuration
```tsx
interface DisplayConfig {
  showTOC: boolean;
  tocPosition: 'left' | 'right';
  defaultExpandedSections: string[];
  maxFieldsPerCategory: number;
  enableFieldSearch: boolean;
}
```

### Feature Flags
- `ENABLE_FIELD_EXPLORER`: Toggle field explorer
- `ENABLE_QUERY_BUILDER_INTEGRATION`: Query builder links
- `SHOW_EXAMPLE_ACTIONS`: Copy/use example buttons

## Known Issues & Workarounds

### Monaco Editor Height Issues
- Monaco requires explicit pixel heights
- Fails in flex containers without min-height
- Workaround: Use fixed heights for examples

### Large Schema Performance
- Schemas with 100+ fields can slow rendering
- Implement virtual scrolling for large field lists
- Consider field pagination or grouping

### Session Storage Limitations
- Limited storage size for complex examples
- Clear data after successful navigation
- Fallback to URL parameters for simple cases