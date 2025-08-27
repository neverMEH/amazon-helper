# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-27-asin-management-page/spec.md

## Technical Requirements

### Frontend Implementation

- **React Component Structure**: Create new `ASINManagement` component following patterns from `CampaignsOptimized.tsx`
- **Data Grid**: Use TanStack Table v8 with virtual scrolling for performance with large datasets (10,000+ rows)
- **State Management**: TanStack Query v5 for server state with aggressive caching strategy
- **Filtering UI**: Multi-select dropdown for brands using existing brand selector patterns, text search with 300ms debounce
- **CSV Import**: Client-side parsing with Papa Parse library, validation before backend submission
- **Parameter Integration**: Modal component that can be invoked from QueryConfigurationStep with callback for selected ASINs
- **Performance**: Implement pagination (100 rows default), virtual scrolling for large datasets, memoization of expensive filters

### Backend Implementation

- **Service Layer**: Create `ASINService` extending `DatabaseService` with connection retry pattern
- **Data Validation**: Pydantic models for ASIN data structure with field validation
- **Bulk Operations**: Batch insert with conflict resolution (ON CONFLICT DO UPDATE)
- **Query Optimization**: Create compound indexes on (brand, marketplace), (asin), and text search index on title
- **Caching Strategy**: In-memory cache for brand list, frequently accessed ASINs
- **API Response**: Paginated responses with total count, filter metadata

### Integration Points

- **Query Builder Integration**: Modify `QueryConfigurationStep` to include "Select ASINs" button for ASIN-type parameters
- **Parameter Population**: Update parameter field to accept array of ASINs, format as comma-separated or JSON array
- **Brand Service**: Reuse existing brand fetching logic from instance_brands table
- **Authentication**: Use existing auth patterns, all endpoints require user authentication
- **Permissions**: ASINs are user-agnostic (shared across all users in the organization)

### UI/UX Specifications

- **Table Columns**: ASIN (sortable), Title (searchable), Brand (filterable), Marketplace, Last Updated
- **Row Actions**: View details (expandable row), Copy ASIN, Add to query (when in selection mode)
- **Bulk Actions**: Select all visible, Select all filtered, Clear selection
- **Import Feedback**: Progress bar for large imports, validation error display, success/failure summary
- **Responsive Design**: Mobile-friendly with horizontal scroll on small screens
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### Performance Criteria

- **Initial Load**: < 500ms for first 100 rows
- **Filter Response**: < 200ms for client-side filtering
- **Search Response**: < 300ms for server-side search
- **Import Speed**: Process 10,000 ASINs in < 10 seconds
- **Memory Usage**: Maintain < 100MB browser memory with 10,000 rows loaded