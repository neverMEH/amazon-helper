# Query Library Redesign - Implementation Plan

## Overview
Transform the query library into a comprehensive, standalone feature that serves as the central hub for query templates with sophisticated parameter handling, seamless integration with workflows/collections/schedules, and automatic report generation.

## Phase 1: Database Schema Enhancement

### 1.1 Enhanced query_templates table
- Add `report_config` JSONB field for dashboard configuration
- Add `version` integer for version control
- Add `parent_template_id` for template forking
- Add `execution_count` for usage analytics

### 1.2 New table: query_template_parameters
```sql
CREATE TABLE query_template_parameters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID REFERENCES query_templates(id) ON DELETE CASCADE,
  parameter_name TEXT NOT NULL,
  parameter_type TEXT NOT NULL, -- asin_list, campaign_list, date_range, etc.
  display_name TEXT NOT NULL,
  description TEXT,
  required BOOLEAN DEFAULT true,
  default_value JSONB,
  validation_rules JSONB, -- min/max, pattern, allowed values
  ui_config JSONB, -- component type, placeholder, help text
  display_order INTEGER,
  group_name TEXT, -- for UI grouping
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(template_id, parameter_name)
);
```

### 1.3 New table: query_template_reports
```sql
CREATE TABLE query_template_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID REFERENCES query_templates(id) ON DELETE CASCADE,
  report_name TEXT NOT NULL,
  dashboard_config JSONB, -- widget layouts and types
  field_mappings JSONB, -- maps query results to widgets
  default_filters JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

### 1.4 New table: query_template_instances
```sql
CREATE TABLE query_template_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id UUID REFERENCES query_templates(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  instance_name TEXT NOT NULL,
  saved_parameters JSONB,
  is_favorite BOOLEAN DEFAULT false,
  last_executed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Phase 2: Backend Services

### 2.1 Enhanced QueryTemplateService
```python
class QueryTemplateService(DatabaseService):
    async def create_template(self, template_data: dict) -> dict:
        """Create new query template with parameters"""
        
    async def fork_template(self, template_id: str, user_id: str) -> dict:
        """Fork existing template for customization"""
        
    async def update_template_version(self, template_id: str, changes: dict) -> dict:
        """Create new version of template"""
        
    async def share_template(self, template_id: str, is_public: bool) -> dict:
        """Share template publicly or privately"""
```

### 2.2 New TemplateParameterService
```python
class TemplateParameterService(DatabaseService):
    async def detect_parameters(self, sql: str) -> List[dict]:
        """Auto-detect parameters from SQL"""
        
    async def infer_parameter_type(self, param_name: str, context: str) -> str:
        """Infer parameter type from name and SQL context"""
        
    async def validate_parameter_value(self, param_type: str, value: Any) -> bool:
        """Validate parameter value against type rules"""
        
    async def bulk_process_asins(self, asin_text: str) -> List[str]:
        """Process bulk ASIN paste (60+ items)"""
```

### 2.3 New TemplateReportService
```python
class TemplateReportService(DatabaseService):
    async def generate_dashboard(self, template_id: str, execution_results: dict) -> dict:
        """Generate dashboard from template execution"""
        
    async def map_results_to_widgets(self, results: dict, mappings: dict) -> dict:
        """Map query results to dashboard widgets"""
        
    async def schedule_report(self, template_id: str, schedule: dict) -> dict:
        """Schedule automated report generation"""
        
    async def export_report(self, report_id: str, format: str) -> bytes:
        """Export report to PDF/Excel"""
```

### 2.4 Enhanced ParameterEngine
New parameter types to support:
- `asin_list`: Multi-select with bulk paste support
- `campaign_filter`: Wildcard pattern matching
- `date_expression`: Dynamic date calculations (TODAY()-7)
- `threshold_numeric`: Min/max validated numbers
- `percentage`: 0-100 percentage values
- `enum_select`: Predefined option lists

## Phase 3: Frontend Components

### 3.1 Query Library Page (/query-library)
```typescript
interface QueryLibraryPage {
  templateGallery: TemplateCard[];
  categories: string[];
  searchBar: SearchComponent;
  filters: FilterPanel;
  quickActions: ['Use', 'Fork', 'Share', 'Preview'];
}
```

### 3.2 Template Editor Component
```typescript
interface TemplateEditor {
  sqlEditor: MonacoEditor;
  parameterPanel: ParameterBuilder;
  testRunner: TestExecutor;
  resultPreview: ResultViewer;
  reportBuilder: ReportDesigner;
}
```

### 3.3 Parameter Input Components

#### ASIN Multi-Select Component
```typescript
interface AsinMultiSelect {
  bulkPasteMode: boolean;
  searchMode: boolean;
  validationPattern: RegExp; // B[0-9A-Z]{9}
  maxItems: number; // Support 60+ items
  deduplicate: boolean;
}
```

#### Campaign Selector Component
```typescript
interface CampaignSelector {
  dataSource: 'user_campaigns' | 'all_campaigns';
  multiSelect: boolean;
  wildcardSupport: boolean; // %pattern%
  searchable: boolean;
}
```

#### Date Range Picker Component
```typescript
interface DateRangePicker {
  presets: ['Last 7 days', 'Last 30 days', 'Last 90 days', 'Custom'];
  dynamicExpressions: boolean; // TODAY(), LAST_WEEK()
  amcBuiltinSupport: boolean; // BUILT_IN_PARAMETER support
}
```

### 3.4 Report Builder Interface
```typescript
interface ReportBuilder {
  widgetPalette: WidgetType[];
  layoutGrid: DragDropGrid;
  fieldMapper: FieldMappingUI;
  previewPane: LivePreview;
}
```

## Phase 4: Integration Points

### 4.1 Workflow Integration
```typescript
// New workflow creation flow
interface WorkflowFromTemplate {
  templateSelector: TemplatePickerModal;
  parameterForm: DynamicParameterForm;
  sqlPreview: SQLPreviewWithSubstitution;
  saveOptions: WorkflowSaveOptions;
}
```

### 4.2 Collection Integration
```typescript
// Collection with template support
interface CollectionFromTemplate {
  template: QueryTemplate;
  batchParameters: BatchParameterGenerator;
  weekOverrides: WeekSpecificParameters;
}
```

### 4.3 Schedule Integration
```typescript
// Schedule with dynamic parameters
interface ScheduleWithTemplate {
  template: QueryTemplate;
  dynamicParameters: RuntimeParameterExpressions;
  executionConfig: ScheduleConfiguration;
}
```

## Phase 5: Example Implementation - Marketing Funnel Template

### Template Definition
```json
{
  "template_id": "tpl_marketing_funnel",
  "name": "Complete Marketing Funnel Analysis",
  "description": "Analyze customer journey from awareness to conversion",
  "category": "attribution",
  "parameters": [
    {
      "name": "brand_asins",
      "type": "asin_list",
      "display_name": "Brand ASINs",
      "description": "List of ASINs to analyze (supports 60+ items)",
      "required": true,
      "ui_config": {
        "component": "AsinMultiSelect",
        "bulkPaste": true,
        "placeholder": "Paste ASINs here, one per line"
      }
    },
    {
      "name": "brand_filter",
      "type": "campaign_filter",
      "display_name": "Campaign Name Filter",
      "description": "Filter campaigns by name pattern",
      "default_value": "%Supergoop%",
      "ui_config": {
        "component": "TextInput",
        "wildcardHint": true
      }
    },
    {
      "name": "date_range",
      "type": "date_range",
      "display_name": "Analysis Period",
      "required": true,
      "ui_config": {
        "component": "DateRangePicker",
        "presets": true
      }
    },
    {
      "name": "min_users_threshold",
      "type": "threshold_numeric",
      "display_name": "Minimum Users Threshold",
      "default_value": 100,
      "validation_rules": {
        "min": 0,
        "max": 10000
      }
    }
  ]
}
```

### Dashboard Configuration
```json
{
  "widgets": [
    {
      "type": "funnel",
      "title": "Marketing Funnel",
      "data_mapping": {
        "stages": ["awareness_users", "consideration_users", "conversion_users"],
        "labels": ["Awareness", "Consideration", "Conversion"]
      }
    },
    {
      "type": "metric_card",
      "title": "Overall Conversion Rate",
      "data_mapping": {
        "value": "overall_conversion_rate",
        "format": "percentage"
      }
    },
    {
      "type": "bar_chart",
      "title": "Campaign Performance",
      "data_mapping": {
        "x": "campaign",
        "y": "roas",
        "color": "ad_product_type"
      }
    },
    {
      "type": "line_chart",
      "title": "ROAS Trend",
      "data_mapping": {
        "x": "date",
        "y": "roas",
        "series": "campaign"
      }
    }
  ]
}
```

## Phase 6: Migration Strategy

### 6.1 Data Migration Steps
1. Backup existing query_templates table
2. Add new columns to query_templates
3. Create new parameter tables
4. Auto-detect parameters in existing templates
5. Generate parameter definitions from detection
6. Create default UI configurations

### 6.2 Backward Compatibility
```python
class TemplateCompatibilityLayer:
    def convert_legacy_template(self, old_template: dict) -> dict:
        """Convert old template format to new format"""
        
    def detect_legacy_parameters(self, sql: str) -> List[dict]:
        """Detect parameters in legacy SQL"""
        
    def generate_parameter_schema(self, parameters: List[dict]) -> dict:
        """Generate JSON schema from detected parameters"""
```

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1-2  | Database | Schema updates, migration scripts |
| 3-4  | Backend Services | Parameter service, Template service |
| 5-6  | Query Library UI | Main page, template gallery |
| 7-8  | Parameter System | Input components, validation |
| 9-10 | Integration | Workflow/Collection/Schedule integration |
| 11-12 | Dashboard | Report builder, auto-generation |
| 13-14 | Testing | E2E testing, migration, documentation |

## Key Performance Indicators

1. **Template Reuse Rate**: % of workflows created from templates
2. **Parameter Input Time**: Average time to fill parameters
3. **Dashboard Generation Success**: % of successful auto-generations
4. **User Adoption**: % of users using query library
5. **Template Sharing**: Number of shared templates

## Technical Considerations

### Security
- SQL injection prevention at multiple layers
- Parameter validation and sanitization
- Template permission management
- Audit logging for template usage

### Performance
- Template caching for frequently used queries
- Lazy loading for large parameter lists
- Indexed parameter search
- Optimized dashboard generation

### Scalability
- Support for 100+ parameters per template
- Bulk operations for large ASIN lists
- Concurrent template executions
- Distributed report generation

## Success Criteria

1. **User Experience**
   - Non-technical users can execute complex queries
   - Parameter input is intuitive and error-free
   - Dashboard generation requires no manual configuration

2. **Developer Experience**
   - Templates are easily maintainable
   - New parameter types can be added without schema changes
   - Integration points are well-documented

3. **Business Value**
   - 50% reduction in query creation time
   - 75% of common queries available as templates
   - 90% of reports auto-generated from templates

## Conclusion

This redesign transforms the query library from a simple template storage system into a comprehensive query management platform that serves as the foundation for all data analysis workflows in RecomAMP. The phased approach ensures continuous value delivery while building toward the complete vision.