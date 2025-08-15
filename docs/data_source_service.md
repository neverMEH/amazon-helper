# data_source_service.py

## Purpose
Manages AMC schema documentation and field definitions. Provides comprehensive catalog of available AMC data sources with field-level metadata, examples, and filtering capabilities for query development.

## Dependencies
### External Dependencies
- json: builtin - JSON parsing for Supabase array fields
- datetime: builtin - Timestamp handling
- logging: builtin - Service logging

### Internal Dependencies
- db_service.py: Inherits from DatabaseService (SupabaseService)
- Database tables: amc_data_sources, schema_fields

## Exports
### Classes
- `DataSourceService`: Main service class inheriting from SupabaseService

### Functions
- `list_data_sources()`: List schemas with filtering and pagination
- `get_data_source_by_schema_id()`: Get specific schema by AMC schema ID
- `search_data_sources()`: Full-text search across schemas
- `get_schema_fields()`: Get field definitions for a schema
- `get_data_source_categories()`: List available categories
- `get_all_tags()`: Get unique tags across all schemas
- `compare_data_sources()`: Side-by-side schema comparison
- `parse_json_fields()`: Handle Supabase JSON array parsing

## Usage Examples
```python
# Initialize service
service = DataSourceService()

# List all data sources with filtering
sources = await service.list_data_sources(
    category="Advertising",
    search="attribution",
    tags=["conversion"],
    limit=50
)

# Get specific schema
schema = await service.get_data_source_by_schema_id("amazon_attributed_events_by_conversion_time")

# Search across schemas
results = await service.search_data_sources("user engagement")

# Get field definitions
fields = await service.get_schema_fields("amazon_attributed_events_by_conversion_time")

# Compare multiple schemas
comparison = await service.compare_data_sources([
    "amazon_attributed_events_by_conversion_time",
    "amazon_attributed_events_by_traffic_time"
])
```

## Relationships
### Used By
- frontend/src/pages/DataSources.tsx: Schema listing and browsing
- frontend/src/pages/DataSourceDetail.tsx: Detailed schema view
- frontend/src/components/data-sources/: All data source components
- amc_manager/api/supabase/data_sources.py: API endpoints
- Query Builder: Schema field assistance

### Uses
- db_service.py: Database connectivity and query execution
- amc_data_sources table: Schema metadata storage
- schema_fields table: Field definitions and types

## Side Effects
- Database queries to Supabase PostgreSQL
- JSON parsing for array fields from Supabase
- Caching of schema metadata (in-memory)
- Search index utilization for full-text search

## Testing Considerations
### Key Scenarios
- JSON array parsing from Supabase (tags, data_sources fields)
- Full-text search functionality
- Category filtering accuracy
- Tag-based filtering with JSONB containment
- Field relationship mapping
- Pagination and offset handling

### Edge Cases
- Empty search results
- Invalid schema IDs
- Malformed JSON in array fields
- Missing field definitions
- Schema version conflicts
- Large schema comparison operations

### Mocking Requirements
- Mock Supabase responses with correct JSON array formatting
- Field definition mocks with proper type information
- Search result mocks with relevance scoring

## Performance Notes
### Optimizations
- Database indexes on frequently searched fields
- JSON field parsing caching
- Paginated results to prevent large data loads
- Selective field loading based on requirements

### Bottlenecks
- Full-text search on large schema sets
- JSON array parsing for tags and categories
- Field relationship computation
- Large schema comparison operations

### Monitoring Points
- Search query performance
- JSON parsing efficiency
- Cache hit rates
- Database connection usage

## Critical Implementation Patterns

### JSON Field Parsing from Supabase
```python
def parse_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Supabase JSON array returns properly"""
    # Supabase returns JSON arrays as strings, need to parse
    if isinstance(data.get('tags'), str):
        try:
            data['tags'] = json.loads(data['tags'])
        except json.JSONDecodeError:
            data['tags'] = []
    
    if isinstance(data.get('data_sources'), str):
        try:
            data['data_sources'] = json.loads(data['data_sources'])
        except json.JSONDecodeError:
            data['data_sources'] = []
    
    return data
```

### Tag-Based Filtering with JSONB
```python
def list_data_sources(self, tags: Optional[List[str]] = None, ...):
    """Use JSONB containment for tag filtering"""
    if tags:
        # Use PostgreSQL JSONB containment operator
        query = query.contains('tags', json.dumps(tags))
    
    # Execute query and parse results
    result = query.limit(limit).offset(offset).execute()
    
    # Parse JSON fields for each result
    for item in result.data:
        item = self.parse_json_fields(item)
```

### Full-Text Search Implementation
```python
def search_data_sources(self, search_term: str) -> List[Dict[str, Any]]:
    """Full-text search across multiple fields"""
    query = (
        self.client.table('amc_data_sources')
        .select('*')
        .or_(
            f"name.ilike.%{search_term}%,"
            f"description.ilike.%{search_term}%,"
            f"category.ilike.%{search_term}%"
        )
    )
    
    result = query.execute()
    return [self.parse_json_fields(item) for item in result.data]
```

### Schema Field Relationships
```python
def get_schema_fields(self, schema_id: str) -> List[Dict[str, Any]]:
    """Get field definitions with proper type information"""
    query = (
        self.client.table('schema_fields')
        .select('*, amc_data_sources(name, category)')
        .eq('schema_id', schema_id)
        .order('field_order', desc=False)
    )
    
    result = query.execute()
    
    # Enhance field data with computed properties
    for field in result.data:
        field['is_required'] = field.get('nullable', True) is False
        field['display_type'] = self._format_field_type(field['data_type'])
```

## Database Schema Integration

### amc_data_sources Table
```sql
CREATE TABLE amc_data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tags JSONB DEFAULT '[]',
    example_queries JSONB DEFAULT '[]',
    last_updated TIMESTAMP DEFAULT NOW()
);
```

### schema_fields Table
```sql
CREATE TABLE schema_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id TEXT REFERENCES amc_data_sources(schema_id),
    field_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    nullable BOOLEAN DEFAULT TRUE,
    description TEXT,
    field_order INTEGER,
    example_values JSONB DEFAULT '[]'
);
```

## AMC Schema Categories

### Standard Categories
- **Advertising**: Campaign, ad group, keyword performance
- **Attribution**: Conversion tracking and attribution modeling
- **Audience**: User behavior and segmentation
- **Product**: Product catalog and performance
- **Custom**: User-defined schemas and views

### Tag Classification
- **Data Type**: events, metrics, dimensions
- **Frequency**: daily, hourly, real-time
- **Source**: Amazon DSP, Amazon Marketing Cloud, Third-party
- **Use Case**: reporting, optimization, analysis

## Advanced Filtering Features

### Multi-Criteria Filtering
```python
def advanced_filter(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Support complex filtering with AND/OR conditions"""
    query = self.client.table('amc_data_sources').select('*')
    
    # Category filter
    if filters.get('categories'):
        query = query.in_('category', filters['categories'])
    
    # Tag intersection (all tags must match)
    if filters.get('required_tags'):
        for tag in filters['required_tags']:
            query = query.contains('tags', json.dumps([tag]))
    
    # Date range filter
    if filters.get('updated_after'):
        query = query.gte('last_updated', filters['updated_after'])
```

### Field-Level Search
```python
def search_fields(self, field_search: str) -> List[Dict[str, Any]]:
    """Search within field definitions"""
    query = (
        self.client.table('schema_fields')
        .select('*, amc_data_sources(name, category)')
        .or_(
            f"field_name.ilike.%{field_search}%,"
            f"description.ilike.%{field_search}%"
        )
    )
    
    return query.execute().data
```

## Error Handling Strategies

### JSON Parsing Errors
```python
def safe_json_parse(self, data: str, field_name: str) -> List[Any]:
    """Safely parse JSON fields with fallback"""
    try:
        return json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON field {field_name}: {data}")
        return []
```

### Schema Not Found
```python
def get_data_source_by_schema_id(self, schema_id: str) -> Optional[Dict[str, Any]]:
    """Get schema with existence validation"""
    result = (
        self.client.table('amc_data_sources')
        .select('*')
        .eq('schema_id', schema_id)
        .execute()
    )
    
    if not result.data:
        logger.warning(f"Schema not found: {schema_id}")
        return None
    
    return self.parse_json_fields(result.data[0])
```

## Integration with Frontend

### React Query Keys
```typescript
// Consistent query keys for caching
['dataSources', { category, search, tags, page }]
['dataSource', schemaId]
['schemaFields', schemaId]
['dataSourceCategories']
```

### API Response Format
```typescript
interface DataSource {
    id: string;
    schema_id: string;
    name: string;
    description?: string;
    category: string;
    tags: string[];
    example_queries: ExampleQuery[];
    field_count: number;
    last_updated: string;
}
```

## Recent Updates

### 2025-08-15 Changes
- Fixed JSON field parsing for Supabase array returns
- Enhanced search functionality with field-level search
- Improved error handling for missing schemas
- Added schema comparison functionality
- Cleaned up empty sections in DataSourceDetail display

### Performance Improvements
- Added database indexes for search performance
- Optimized JSON parsing with caching
- Reduced query complexity for large result sets

## Configuration Options

### Search Configuration
- `SEARCH_LIMIT`: Maximum search results (default: 100)
- `FUZZY_SEARCH_THRESHOLD`: Similarity threshold for fuzzy matching
- `CACHE_TTL`: Cache time-to-live for schema data

### Feature Flags
- `ENABLE_FIELD_SEARCH`: Enable field-level search
- `ENABLE_SCHEMA_COMPARISON`: Enable schema comparison features
- `USE_FULL_TEXT_INDEX`: Use PostgreSQL full-text search index

## Known Issues & Workarounds

### Supabase JSON Array Parsing
- Supabase returns JSON arrays as strings in some cases
- Always use `parse_json_fields()` after query execution
- Type checking before JSON parsing prevents errors

### Large Schema Handling
- Schemas with many fields can slow rendering
- Implement pagination for field lists
- Consider field grouping for better UX

### Search Relevance
- Basic ILIKE search may not provide optimal relevance
- Consider implementing full-text search with ranking
- Add search result highlighting