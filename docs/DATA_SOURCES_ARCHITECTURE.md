# AMC Data Sources Architecture

## Overview

The AMC Data Sources section provides comprehensive schema documentation for Amazon Marketing Cloud tables, making them searchable, referenceable, and AI-queryable. This system serves as the foundational knowledge base for query development and optimization.

## System Architecture

### Database Schema

The data sources system uses 6 normalized PostgreSQL tables with JSONB fields for flexibility:

```sql
amc_data_sources          -- Main schema metadata
├── amc_schema_fields     -- Field definitions (1:many)
├── amc_query_examples    -- SQL examples (1:many)
├── amc_schema_sections   -- Documentation sections (1:many)
└── amc_schema_relationships -- Inter-schema relationships (many:many)
    └── amc_field_relationships -- Field-level relationships
```

#### Key Design Decisions

1. **JSONB Storage**: Used for flexible metadata (tags, availability, examples)
2. **Full-Text Search**: PostgreSQL tsvector for efficient searching
3. **Aggregation Thresholds**: Tracked per field for privacy compliance
4. **Version Control**: Semantic versioning for schema updates
5. **RLS Policies**: Read-only access for all users, admin-only writes

### Data Flow Architecture

```
Markdown Files (amc_dataset/) 
    ↓ [Python Parser]
Database (Supabase)
    ↓ [Backend API]
Frontend (React)
    ↓ [User Interface]
Query Builder Integration
```

### API Architecture

RESTful endpoints with consistent patterns:

```
/api/data-sources
├── GET /                     # List with filtering
├── GET /categories           # Unique categories
├── GET /tags                 # Popular tags
├── GET /search-fields        # Cross-schema field search
├── GET /export-ai           # AI-optimized export
└── GET /{schema_id}
    ├── /                    # Schema metadata
    ├── /fields              # Field definitions
    ├── /examples            # Query examples
    ├── /sections            # Documentation
    ├── /relationships       # Schema relationships
    └── /complete           # All data in one call
```

## Frontend Architecture

### Component Hierarchy

```
DataSources (List Page)
├── Search Bar
├── Category Filter
├── Tag Cloud
└── DataSourceCard[]
    └── → DataSourceDetail

DataSourceDetail (Detail Page)
├── Header (name, version, tags)
├── Navigation Tabs
│   ├── Overview (sections)
│   ├── Schema (fields table)
│   ├── Examples (SQL queries)
│   └── Relationships
└── Deep Link Support (#sections)
```

### State Management

- **Server State**: TanStack Query v5 with 10-minute cache
- **URL State**: Search params for filters and deep links
- **Local State**: Expanded sections, copied examples

### Key Features

1. **Search & Discovery**
   - Full-text search across schemas, fields, descriptions
   - Category and tag-based filtering
   - Field search across all schemas

2. **Schema Display**
   - Collapsible field categories
   - Aggregation threshold indicators
   - Data type icons
   - Example values

3. **Query Examples**
   - Syntax highlighting with Monaco Editor
   - Copy to clipboard
   - "Open in Query Builder" with pre-population
   - Category-based organization

4. **Deep Linking**
   - Hash-based section navigation (#overview, #schema, #examples)
   - Auto-scroll to section
   - URL persistence

## Data Import Process

### Schema Parsing

The `import_amc_schemas.py` script:

1. **Reads** markdown files from `amc_dataset/`
2. **Extracts** structured data:
   - Metadata (name, category, tags)
   - Field definitions from tables
   - SQL examples from code blocks
   - Documentation sections
3. **Categorizes** schemas automatically
4. **Generates** semantic tags
5. **Creates** relationships

### Import Pipeline

```python
for schema_file in amc_dataset/*.md:
    1. Parse markdown structure
    2. Extract metadata
    3. Parse field tables (regex)
    4. Extract SQL examples
    5. Identify sections
    6. Insert to database
    7. Create relationships
```

## Integration Points

### Query Builder Integration

```javascript
// Session storage for query draft
sessionStorage.setItem('queryBuilderDraft', {
  name: example.title,
  sql_query: example.sql_query,
  parameters: example.parameters,
  fromDataSource: schema_id
});
navigate('/query-builder/new');
```

### Field Autocomplete (Planned)

```javascript
// Query Builder can reference available fields
const fields = await dataSourceService.getSchemaFields(selectedDataSource);
// Autocomplete suggestions in Monaco Editor
```

### AI Knowledge Base

Export format optimized for LLM consumption:

```json
{
  "version": "1.0",
  "schemas": [{
    "id": "schema_id",
    "semantic_context": ["conversion", "attribution"],
    "key_fields": ["campaign_id", "conversion_id"],
    "metrics": [{"name": "purchases", "type": "LONG"}],
    "dimensions": [{"name": "campaign", "type": "STRING"}],
    "relationships": [{"type": "variant", "target": "schema_id"}]
  }]
}
```

## Schema Categories

Organized into logical groups:

1. **DSP Tables** - Programmatic advertising data
2. **Attribution Tables** - Conversion attribution
3. **Conversion Tables** - Purchase and conversion events
4. **Brand Store Insights** - Store page analytics
5. **Sponsored Ads Tables** - Search advertising
6. **Audience Tables** - Segment definitions
7. **Retail Analytics** - Sales and inventory
8. **Premium Video Content** - Video analytics
9. **Automotive Insights** - Vertical-specific data

## Aggregation Thresholds

Critical for AMC privacy compliance:

- **NONE**: No restrictions
- **LOW**: Standard threshold (10+ users)
- **MEDIUM**: Medium threshold (50+ users)
- **HIGH**: High threshold (100+ users)
- **VERY_HIGH**: Cannot be in SELECT, only in CTEs
- **INTERNAL**: Amazon internal only

## Performance Optimizations

1. **Database**
   - Indexes on search fields
   - JSONB GIN indexes for tags
   - Materialized views for popular queries

2. **API**
   - Batch field insertion (100 per batch)
   - Single query for complete schema
   - Cached categories and tags

3. **Frontend**
   - Virtual scrolling for large field lists
   - Lazy loading of examples
   - Debounced search (300ms)
   - 10-minute cache duration

## Security Considerations

1. **Read-Only Access**: All users can read schemas
2. **Admin Writes**: Only service role can modify
3. **No PII**: Schema documentation only
4. **Rate Limiting**: Applied at API gateway level

## Maintenance

### Adding New Schemas

1. Add markdown file to `amc_dataset/`
2. Run `python scripts/import_amc_schemas.py`
3. Schemas auto-categorized and tagged

### Updating Schemas

1. Modify markdown file
2. Increment version in file
3. Re-run import (updates existing)

### Schema Versioning

- Semantic versioning (MAJOR.MINOR.PATCH)
- Change tracking via updated_at
- Historical versions preserved (planned)

## Future Enhancements

1. **Version History**: Track schema changes over time
2. **Field Lineage**: Track field derivations
3. **Usage Analytics**: Most accessed schemas/fields
4. **Smart Suggestions**: ML-based query recommendations
5. **Collaborative Notes**: User annotations on schemas
6. **Export Templates**: Generate query templates from schemas

## Troubleshooting

### Common Issues

1. **Import Fails**: Check Supabase connection and service role key
2. **Search Not Working**: Verify full-text indexes created
3. **Missing Fields**: Check markdown table format
4. **Wrong Category**: Update category mapping in importer

### Debug Commands

```bash
# Check imported schemas
python -c "from scripts.import_amc_schemas import AMCSchemaImporter; AMCSchemaImporter().run()"

# Test API endpoints
curl http://localhost:8001/api/data-sources

# Verify database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM amc_data_sources;"
```

## Related Documentation

- [AMC Query Template System](./template-library-plan.md)
- [Query Builder Implementation](./QUERY_WORKFLOW_IMPLEMENTATION.md)
- [ID Field Reference](./ID_FIELD_REFERENCE.md)