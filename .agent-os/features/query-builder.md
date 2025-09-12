# Query Builder System

## Overview

The query builder system provides a sophisticated SQL editing environment with Monaco Editor, parameter substitution, syntax highlighting, and integrated AMC schema awareness. It enables users to build complex AMC queries with dynamic parameters and real-time validation.

## Key Components

### Backend Services
- `amc_manager/services/workflow_service.py` - Query processing and parameter substitution
- `amc_manager/services/amc_schema_service.py` - Schema metadata management
- `amc_manager/api/supabase/workflows.py` - Query CRUD operations

### Frontend Components
- `frontend/src/components/SQLEditor.tsx` - Monaco-based SQL editor
- `frontend/src/components/QueryBuilder.tsx` - Query building interface
- `frontend/src/components/ParameterForm.tsx` - Parameter input interface
- `frontend/src/components/SchemaExplorer.tsx` - AMC schema browser
- `frontend/src/components/query-library/CampaignSelector.tsx` - Enhanced campaign selector (2025-09-12)
- `frontend/src/components/query-library/DateRangePicker.tsx` - Advanced date range picker (2025-09-12)

### Database Tables
- `workflows` - SQL query storage
- `amc_data_sources` - AMC schema documentation
- `amc_schema_fields` - Field metadata and descriptions
- `query_templates` - Pre-built query library

## Technical Implementation

### Monaco Editor Integration
```typescript
// SQLEditor.tsx - Advanced SQL editor
import Editor from '@monaco-editor/react';

interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  height?: string;
  readOnly?: boolean;
  onValidate?: (markers: any[]) => void;
}

const SQLEditor: React.FC<SQLEditorProps> = ({ 
  value, 
  onChange, 
  height = "400px",  // CRITICAL: Must use pixel heights
  readOnly = false,
  onValidate 
}) => {
  const handleEditorDidMount = (editor: any, monaco: any) => {
    // Configure SQL language features
    monaco.languages.setLanguageConfiguration('sql', {
      comments: {
        lineComment: '--',
        blockComment: ['/*', '*/']
      },
      brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')']
      ],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ]
    });

    // Add AMC-specific keywords
    monaco.languages.setMonarchTokensProvider('sql', {
      keywords: [
        'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',
        'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN',
        'SUM', 'COUNT', 'AVG', 'MAX', 'MIN',
        // AMC-specific functions
        'DATEADD', 'DATEDIFF', 'EXTRACT',
        'LISTAGG', 'ROW_NUMBER', 'RANK'
      ],
      // AMC table names as special tokens
      tables: [
        'dsp_campaign_data', 'dsp_impression_data', 'dsp_click_data',
        'amazon_attributed_events_by_conversion_time',
        'amazon_attributed_events_by_traffic_time'
      ]
    });

    // Parameter highlighting
    editor.onDidChangeModelContent(() => {
      const model = editor.getModel();
      const content = model.getValue();
      
      // Highlight {{parameter}} syntax
      const parameterRegex = /\{\{[\w_]+\}\}/g;
      const decorations = [];
      let match;
      
      while ((match = parameterRegex.exec(content)) !== null) {
        const startPos = model.getPositionAt(match.index);
        const endPos = model.getPositionAt(match.index + match[0].length);
        
        decorations.push({
          range: new monaco.Range(
            startPos.lineNumber,
            startPos.column,
            endPos.lineNumber,
            endPos.column
          ),
          options: {
            className: 'parameter-highlight',
            hoverMessage: { value: `Parameter: ${match[0]}` }
          }
        });
      }
      
      editor.deltaDecorations([], decorations);
    });
  };

  return (
    <Editor
      height={height}
      defaultLanguage="sql"
      theme="vs-dark"
      value={value}
      onChange={onChange}
      onMount={handleEditorDidMount}
      onValidate={onValidate}
      options={{
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        fontSize: 14,
        lineNumbers: 'on',
        wordWrap: 'on',
        readOnly,
        folding: true,
        bracketMatching: 'always',
        autoIndent: 'full',
      }}
    />
  );
};
```

### Parameter Substitution System
```python
# workflow_service.py - Parameter processing
class ParameterProcessor:
    def __init__(self):
        self.parameter_patterns = {
            'campaign_ids': r'\{\{campaign_ids\}\}',
            'asin_list': r'\{\{asin_list\}\}',
            'start_date': r'\{\{start_date\}\}',
            'end_date': r'\{\{end_date\}\}',
            'limit': r'\{\{limit\}\}'
        }
    
    def substitute_parameters(self, sql_query: str, parameters: Dict[str, Any]) -> str:
        """Replace parameter placeholders with actual values"""
        substituted_query = sql_query
        
        for param_name, pattern in self.parameter_patterns.items():
            if param_name in parameters:
                value = self.format_parameter_value(param_name, parameters[param_name])
                substituted_query = re.sub(pattern, value, substituted_query)
        
        return substituted_query
    
    def format_parameter_value(self, param_name: str, value: Any) -> str:
        """Format parameter value for SQL injection"""
        if param_name in ['campaign_ids', 'asin_list']:
            # Handle list parameters
            if isinstance(value, (list, tuple)):
                # Format as SQL IN clause values
                formatted_values = [f"'{str(v)}'" for v in value]
                return ', '.join(formatted_values)
            else:
                return f"'{str(value)}'"
        
        elif param_name in ['start_date', 'end_date']:
            # Handle date parameters
            if isinstance(value, str):
                # Ensure proper date format for AMC
                return f"'{value}'"
            elif hasattr(value, 'strftime'):
                # Convert datetime to AMC format (no timezone)
                return f"'{value.strftime('%Y-%m-%dT%H:%M:%S')}'"
        
        elif param_name == 'limit':
            # Handle numeric parameters
            return str(int(value)) if value else '100'
        
        else:
            # Default string parameter
            return f"'{str(value)}'"
    
    def extract_parameters(self, sql_query: str) -> List[str]:
        """Extract parameter names from SQL query"""
        parameter_pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(parameter_pattern, sql_query)
        return list(set(matches))  # Remove duplicates
```

### Schema Integration
```python
# amc_schema_service.py - Schema metadata management
class AMCSchemaService:
    async def get_data_sources(self) -> List[dict]:
        """Get available AMC data sources"""
        sources = self.db.table('amc_data_sources')\
            .select('*')\
            .eq('is_active', True)\
            .order('category, name')\
            .execute()
        
        return sources.data
    
    async def get_table_fields(self, table_name: str) -> List[dict]:
        """Get field metadata for specific table"""
        fields = self.db.table('amc_schema_fields')\
            .select('*')\
            .eq('table_name', table_name)\
            .order('field_name')\
            .execute()
        
        return fields.data
    
    async def search_schema(self, query: str) -> dict:
        """Search schema for tables and fields matching query"""
        # Search tables
        tables = self.db.table('amc_data_sources')\
            .select('*')\
            .ilike('name', f'%{query}%')\
            .execute()
        
        # Search fields
        fields = self.db.table('amc_schema_fields')\
            .select('*, amc_data_sources(name)')\
            .or_(f'field_name.ilike.%{query}%,description.ilike.%{query}%')\
            .execute()
        
        return {
            'tables': tables.data,
            'fields': fields.data
        }
```

## Advanced Query Features

### Query Validation
```typescript
// QueryBuilder.tsx - Client-side validation
const validateQuery = (sql: string, parameters: Record<string, any>) => {
  const errors: string[] = [];
  
  // Check for required parameters
  const paramMatches = sql.match(/\{\{(\w+)\}\}/g) || [];
  const requiredParams = paramMatches.map(match => match.slice(2, -2));
  
  for (const param of requiredParams) {
    if (!parameters[param] || parameters[param] === '') {
      errors.push(`Missing value for parameter: ${param}`);
    }
  }
  
  // Check for common SQL issues
  if (!sql.trim().toLowerCase().startsWith('select')) {
    errors.push('Query must start with SELECT');
  }
  
  if (!sql.toLowerCase().includes('from')) {
    errors.push('Query must include FROM clause');
  }
  
  // AMC-specific validations
  if (sql.toLowerCase().includes('delete') || sql.toLowerCase().includes('update')) {
    errors.push('Only SELECT queries are allowed');
  }
  
  return errors;
};
```

### Query Preview System
```python
# Preview query with substituted parameters
async def preview_query(self, workflow_id: str, parameters: Dict[str, Any]) -> dict:
    """Generate preview of query with parameters substituted"""
    workflow = await self.get_workflow(workflow_id)
    
    # Extract and validate parameters
    required_params = self.parameter_processor.extract_parameters(workflow['sql_query'])
    missing_params = [param for param in required_params if param not in parameters]
    
    if missing_params:
        return {
            'success': False,
            'error': f'Missing parameters: {", ".join(missing_params)}',
            'required_parameters': required_params
        }
    
    # Substitute parameters
    preview_sql = self.parameter_processor.substitute_parameters(
        workflow['sql_query'], 
        parameters
    )
    
    return {
        'success': True,
        'preview_sql': preview_sql,
        'original_sql': workflow['sql_query'],
        'parameters_used': parameters
    }
```

## Parameter Management

### Dynamic Parameter Form
```typescript
// ParameterForm.tsx - Dynamic parameter input
interface ParameterFormProps {
  parameters: string[];
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  campaigns?: Campaign[];
  asins?: ASIN[];
}

const ParameterForm: React.FC<ParameterFormProps> = ({ 
  parameters, 
  values, 
  onChange,
  campaigns = [],
  asins = []
}) => {
  const renderParameterInput = (paramName: string) => {
    switch (paramName) {
      case 'campaign_ids':
        return (
          <CampaignSelector
            value={values[paramName] || []}
            onChange={(selected) => onChange({ ...values, [paramName]: selected })}
            campaigns={campaigns}
            multiple
          />
        );
      
      case 'asin_list':
        return (
          <ASINSelector
            value={values[paramName] || []}
            onChange={(selected) => onChange({ ...values, [paramName]: selected })}
            asins={asins}
            multiple
          />
        );
      
      case 'start_date':
      case 'end_date':
        return (
          <input
            type="datetime-local"
            value={values[paramName] || ''}
            onChange={(e) => onChange({ ...values, [paramName]: e.target.value })}
            className="form-input"
          />
        );
      
      case 'limit':
        return (
          <input
            type="number"
            value={values[paramName] || 100}
            onChange={(e) => onChange({ ...values, [paramName]: parseInt(e.target.value) })}
            className="form-input"
            min="1"
            max="10000"
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={values[paramName] || ''}
            onChange={(e) => onChange({ ...values, [paramName]: e.target.value })}
            className="form-input"
          />
        );
    }
  };

  return (
    <div className="space-y-4">
      {parameters.map((param) => (
        <div key={param} className="form-group">
          <label className="form-label">
            {param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </label>
          {renderParameterInput(param)}
        </div>
      ))}
    </div>
  );
};
```

### Enhanced Campaign and ASIN Integration (2025-09-12)

#### Advanced CampaignSelector Component
```typescript
// Enhanced campaign selection with wildcard pattern support
const CampaignSelector: React.FC<CampaignSelectorProps> = ({
  instanceId,
  brandId,
  value,
  onChange,
  placeholder = 'Select campaigns or use wildcards...',
  multiple = true,
  campaignType,
  valueType = 'ids',
  showAll = false,
  className = '',
  enableWildcards = true,
  maxSelections
}) => {
  // Key Features:
  // - Wildcard pattern support: Brand_*, *_2025, *Holiday*
  // - Bulk selection with "Select All Matching" functionality
  // - Real-time search and filtering
  // - Campaign type badges (SP, SB, SD, DSP)
  // - Maximum selection limits with clear feedback
  // - Pattern match visualization with count indicators
  
  // Wildcard pattern matching
  const wildcardToRegex = (pattern: string): RegExp => {
    const escaped = pattern
      .replace(/[.+?^${}()|[\]\\]/g, '\\$&')  // Escape special regex characters
      .replace(/\*/g, '.*');  // Replace * with .*
    return new RegExp(`^${escaped}$`, 'i');  // Case insensitive
  };
  
  // Visual pattern management with active pattern display
  const PatternDisplay = () => (
    <div className="p-2 border-b bg-gray-50">
      <div className="text-xs text-gray-600 mb-1">
        Active Patterns ({wildcardMatchCount} matches):
      </div>
      <div className="flex flex-wrap gap-1">
        {Array.from(wildcardPatterns).map(pattern => (
          <span key={pattern} className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
            <Asterisk className="h-3 w-3 mr-1" />
            {pattern}
            <button onClick={() => handleRemoveWildcardPattern(pattern)}>
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
};
```

#### Advanced DateRangePicker Component
```typescript
// Advanced date range picker with presets and dynamic expressions
const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  showAmcWarning = false,
  supportDynamic = false
}) => {
  // Key Features:
  // - Static date selection with calendar interface
  // - Preset date ranges (Last 7 days, This month, Last quarter)
  // - Dynamic date expressions (today - 7 days, start of month)
  // - AMC 14-day lookback automatic adjustment
  // - Expression validation with real-time preview
  
  // Dynamic date expression resolution
  function resolveDynamicExpression(expr: string): Date | null {
    const normalized = expr.toLowerCase().trim();
    const now = new Date();
    
    // Simple expressions
    if (normalized === 'today') return now;
    if (normalized === 'start of month') return startOfMonth(now);
    if (normalized === 'end of quarter') return endOfQuarter(now);
    
    // Complex expressions with math
    const mathRegex = /^(today|start of month|end of quarter)\s*([\+\-])\s*(\d+)\s*(days?|months?)$/i;
    const match = normalized.match(mathRegex);
    
    if (match) {
      const [, base, operator, amount, unit] = match;
      let baseDate = resolveDynamicExpression(base);
      if (!baseDate) return null;
      
      const num = parseInt(amount);
      const isAdd = operator === '+';
      
      if (unit.startsWith('day')) {
        return isAdd ? addDays(baseDate, num) : subDays(baseDate, num);
      }
    }
    
    return null;
  }
  
  // AMC-aware preset configuration
  const presets = [
    {
      label: 'Last 7 days',
      getValue: () => ({
        startDate: subDays(showAmcWarning ? amcCutoffDate : today, 7),
        endDate: showAmcWarning ? amcCutoffDate : today
      }),
      adjustForAmc: true
    },
    // ... additional presets
  ];
};
```

## Data Flow

1. **Query Composition**: User writes SQL in Monaco Editor
2. **Parameter Detection**: System extracts {{parameter}} placeholders
3. **Parameter Input**: Dynamic form generated for required parameters
4. **Query Preview**: Real-time preview with substituted parameters
5. **Validation**: Client and server-side validation
6. **Execution**: Processed query sent to AMC API

## Error Handling and Validation

### SQL Syntax Validation
```python
def validate_sql_syntax(sql_query: str) -> List[str]:
    """Basic SQL syntax validation"""
    errors = []
    
    # Check for balanced parentheses
    if sql_query.count('(') != sql_query.count(')'):
        errors.append("Unbalanced parentheses in query")
    
    # Check for required keywords
    sql_lower = sql_query.lower()
    if not re.search(r'\bselect\b', sql_lower):
        errors.append("Query must contain SELECT keyword")
    
    if not re.search(r'\bfrom\b', sql_lower):
        errors.append("Query must contain FROM keyword")
    
    # Check for dangerous operations
    dangerous_keywords = ['delete', 'update', 'insert', 'drop', 'create', 'alter']
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', sql_lower):
            errors.append(f"Keyword '{keyword.upper()}' is not allowed")
    
    return errors
```

### Parameter Validation
```python
def validate_parameters(parameters: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate parameter values"""
    errors = {}
    
    # Validate campaign_ids
    if 'campaign_ids' in parameters:
        campaign_ids = parameters['campaign_ids']
        if isinstance(campaign_ids, list) and len(campaign_ids) > 100:
            errors['campaign_ids'] = ['Too many campaign IDs (max 100)']
    
    # Validate date parameters
    for date_param in ['start_date', 'end_date']:
        if date_param in parameters:
            date_value = parameters[date_param]
            try:
                if isinstance(date_value, str):
                    datetime.fromisoformat(date_value)
            except ValueError:
                errors[date_param] = ['Invalid date format']
    
    # Validate date range
    if 'start_date' in parameters and 'end_date' in parameters:
        try:
            start = datetime.fromisoformat(parameters['start_date'])
            end = datetime.fromisoformat(parameters['end_date'])
            if start >= end:
                errors['date_range'] = ['Start date must be before end date']
        except (ValueError, TypeError):
            pass  # Individual date validation will catch format errors
    
    return errors
```

## Interconnections

### With Workflow System
- Queries stored as workflow definitions
- Parameter substitution during execution
- Results linked to query execution

### With Campaign Management
- Campaign IDs available as parameter options
- Campaign filtering in query builder
- Campaign metadata integration

### With Schema Service
- Real-time schema browsing
- Field descriptions and data types
- Table relationship information

### With Template System
- Pre-built queries as starting points
- Template-specific parameter configurations
- Common query patterns

## Performance Optimization

### Editor Performance
```typescript
// Optimize Monaco Editor for large queries
const editorOptions = {
  // Disable expensive features for large files
  folding: sql.length < 10000,
  wordBasedSuggestions: sql.length < 5000,
  
  // Optimize rendering
  renderLineHighlight: 'gutter',
  renderIndentGuides: false,
  
  // Limit suggestions
  suggest: {
    maxVisibleSuggestions: 20
  }
};
```

### Parameter Caching
```typescript
// Cache parameter values across sessions
const useParameterCache = () => {
  const saveParameters = (workflowId: string, parameters: Record<string, any>) => {
    localStorage.setItem(`params_${workflowId}`, JSON.stringify(parameters));
  };
  
  const loadParameters = (workflowId: string) => {
    const saved = localStorage.getItem(`params_${workflowId}`);
    return saved ? JSON.parse(saved) : {};
  };
  
  return { saveParameters, loadParameters };
};
```

## Testing Considerations

### Editor Testing
```typescript
// Test SQL editor functionality
describe('SQLEditor', () => {
  it('highlights parameters correctly', () => {
    const sql = 'SELECT * FROM table WHERE id = {{campaign_ids}}';
    // Test parameter highlighting
  });
  
  it('validates SQL syntax', () => {
    const invalidSQL = 'SELCT * FORM table';
    // Test syntax validation
  });
});
```

### Parameter Testing
```python
def test_parameter_substitution():
    processor = ParameterProcessor()
    sql = 'SELECT * FROM campaigns WHERE id IN ({{campaign_ids}})'
    params = {'campaign_ids': ['123', '456']}
    
    result = processor.substitute_parameters(sql, params)
    expected = "SELECT * FROM campaigns WHERE id IN ('123', '456')"
    
    assert result == expected
```