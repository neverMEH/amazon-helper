# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-09-03-query-flow-templates/spec.md

> Created: 2025-09-03
> Version: 1.0.0

## Technical Requirements

### Backend Architecture
- Extend existing FastAPI backend with new template management endpoints
- Implement parameter substitution engine with type validation
- Create template execution service with parameter injection
- Add chart configuration management system
- Integrate with existing AMC workflow execution pipeline

### Frontend Architecture
- Develop React components for parameter selection UI
- Implement dynamic form generation based on template parameter definitions
- Create chart rendering system using recharts with custom configurations
- Build template browser with search, filtering, and categorization
- Integrate with existing TanStack Query caching system

### Parameter System
- Type-safe parameter definitions (string, number, date, array, boolean)
- Parameter validation and sanitization
- Support for parameter dependencies and conditional visibility
- Integration with existing campaign and ASIN selection components
- Default value computation and smart suggestions

### Template Engine
- SQL template parsing with parameter placeholder replacement
- Template versioning and backward compatibility
- Template validation and testing framework
- Performance optimization for large parameter sets
- Template execution history and caching

## Approach

### Phase 1: Core Template System
1. **Database Schema Implementation**: Create new tables for templates, parameters, and chart configurations
2. **Backend API Development**: Implement template CRUD operations and parameter management
3. **Template Engine**: Build SQL parameter substitution system with validation
4. **Basic Frontend Components**: Create template browser and parameter selection UI

### Phase 2: Parameter UI System
1. **Dynamic Form Generation**: Build React components that render based on parameter definitions
2. **Parameter Type Components**: Create specialized inputs for dates, campaigns, ASINs, etc.
3. **Validation System**: Implement client-side and server-side parameter validation
4. **Integration Testing**: Ensure compatibility with existing campaign/ASIN selection systems

### Phase 3: Visualization Framework
1. **Chart Configuration System**: Implement template-specific chart definitions
2. **Chart Rendering Components**: Build flexible chart components using recharts
3. **Data Transformation Layer**: Create system to transform query results for chart consumption
4. **Interactive Features**: Add drill-down, filtering, and export capabilities

### Phase 4: Template Library & Migration
1. **Template Library UI**: Complete browser interface with search, filtering, and favorites
2. **Sample Templates**: Implement initial set of proven templates
3. **Migration System**: Create path from existing query library to new template system
4. **Performance Optimization**: Optimize for large datasets and complex templates

### Implementation Details

#### Parameter Substitution Engine
```python
class ParameterEngine:
    def substitute_parameters(self, sql_template: str, parameters: Dict[str, Any]) -> str:
        # Handle different parameter types
        # Validate parameter values against definitions
        # Perform SQL injection prevention
        # Support array parameters for IN clauses
        pass
```

#### Template Definition Schema
```typescript
interface QueryTemplate {
  template_id: string;
  name: string;
  description: string;
  category: string;
  sql_template: string;
  parameters: ParameterDefinition[];
  chart_configs: ChartConfiguration[];
  tags: string[];
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_runtime: number;
}
```

#### Chart Configuration System
```typescript
interface ChartConfiguration {
  chart_id: string;
  chart_type: 'line' | 'bar' | 'pie' | 'table' | 'scatter';
  title: string;
  data_mapping: DataMapping;
  styling: ChartStyling;
  interactions: InteractionConfig;
}
```

## External Dependencies

### New Dependencies
- **recharts**: Chart rendering library for custom visualizations
- **react-hook-form**: Enhanced form handling for parameter inputs
- **yup**: Schema validation for parameter definitions
- **sql-formatter**: SQL template formatting and parsing

### Enhanced Existing Dependencies
- **TanStack Query**: Extended for template caching and parameter state management
- **Monaco Editor**: Integration for template authoring (admin feature)
- **Tailwind CSS**: Extended with chart-specific styling utilities

### Integration Points
- **AMC Workflow System**: Template execution through existing workflow pipeline
- **Campaign/ASIN Selection**: Reuse existing selection components as parameter inputs
- **Authentication System**: Template access control using existing user management
- **Database Layer**: Extension of existing Supabase schema and services