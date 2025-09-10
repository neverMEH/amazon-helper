# Query Templates System

## Overview

The Query Templates system provides a library of pre-built, tested AMC queries that users can customize and execute. It accelerates query development by offering proven patterns, parameter configurations, and documentation for common Amazon Marketing Cloud use cases.

## Key Components

### Backend Services
- `amc_manager/services/query_template_service.py` - Template management
- `amc_manager/services/template_instantiation_service.py` - Template to workflow conversion
- `amc_manager/api/supabase/query_templates.py` - Template API endpoints

### Frontend Components
- `frontend/src/pages/QueryTemplates.tsx` - Template library interface
- `frontend/src/components/TemplateCard.tsx` - Template preview and actions
- `frontend/src/components/TemplateCustomizer.tsx` - Parameter customization
- `frontend/src/components/TemplatePreview.tsx` - Query preview before creation

### Database Tables
- `query_templates` - Template definitions and metadata
- `template_categories` - Organization structure
- `template_usage_stats` - Usage tracking and analytics
- `workflows` - Created from templates (references template_id)

## Template Data Model

### Template Structure
```python
# query_templates table schema
class QueryTemplate:
    id: UUID                    # Template identifier
    name: str                  # Template name
    description: str           # Detailed description
    category: str              # Template category
    
    # Template Content
    sql_template: str          # SQL with parameter placeholders
    parameters: dict           # Parameter definitions and defaults
    
    # Template Metadata
    tags: List[str]           # Searchable tags
    difficulty_level: str     # BEGINNER, INTERMEDIATE, ADVANCED
    estimated_runtime: str    # Expected execution time
    
    # Usage Analytics
    usage_count: int          # Times instantiated
    rating: float             # Average user rating
    last_used_at: datetime    # Last instantiation time
    
    # Authoring Information
    author_id: UUID           # Template creator
    is_official: bool         # Official Amazon template
    is_public: bool           # Available to all users
    
    # Documentation
    documentation: str        # Extended documentation
    example_results: dict     # Sample output description
    use_cases: List[str]     # Common use cases
    
    # Validation
    last_tested_at: datetime  # Last validation test
    test_status: str          # PASSED, FAILED, PENDING
    
    # Audit Fields
    created_at: datetime
    updated_at: datetime
```

### Parameter Definition Schema
```python
# Parameter configuration within templates
class ParameterDefinition:
    name: str                 # Parameter name (matches {{name}} in SQL)
    type: str                # campaign_ids, asin_list, date, text, number
    label: str               # Human-readable label
    description: str         # Parameter explanation
    
    # Validation Rules
    required: bool           # Whether parameter is required
    default_value: Any       # Default value if any
    validation_rules: dict   # Min/max, format validation
    
    # UI Configuration
    input_type: str          # select, multiselect, text, date, number
    options: List[str]       # For select inputs
    placeholder: str         # Input placeholder text
    
    # Help and Context
    tooltip: str            # Help tooltip
    examples: List[str]     # Example values
```

## Template Creation and Management

### Template Service Implementation
```python
# query_template_service.py
class QueryTemplateService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.parameter_validator = ParameterValidator()
    
    async def create_template(self, template_data: dict, author_id: str) -> dict:
        """Create new query template"""
        
        # Validate template structure
        validation_errors = await self.validate_template(template_data)
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Template validation failed: {validation_errors}"
            )
        
        # Create template record
        template = self.db.table('query_templates').insert({
            'name': template_data['name'],
            'description': template_data['description'],
            'category': template_data['category'],
            'sql_template': template_data['sql_template'],
            'parameters': template_data.get('parameters', {}),
            'tags': template_data.get('tags', []),
            'difficulty_level': template_data.get('difficulty_level', 'BEGINNER'),
            'estimated_runtime': template_data.get('estimated_runtime', 'Under 5 minutes'),
            'documentation': template_data.get('documentation'),
            'example_results': template_data.get('example_results'),
            'use_cases': template_data.get('use_cases', []),
            'author_id': author_id,
            'is_official': template_data.get('is_official', False),
            'is_public': template_data.get('is_public', True),
            'usage_count': 0,
            'test_status': 'PENDING',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).execute()
        
        template_id = template.data[0]['id']
        
        # Schedule validation test
        await self.schedule_template_validation(template_id)
        
        return template.data[0]
    
    async def validate_template(self, template_data: dict) -> List[str]:
        """Validate template structure and SQL"""
        errors = []
        
        # Required fields validation
        required_fields = ['name', 'description', 'category', 'sql_template']
        for field in required_fields:
            if not template_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # SQL template validation
        sql_template = template_data.get('sql_template', '')
        if sql_template:
            # Check for basic SQL structure
            if not sql_template.strip().lower().startswith('select'):
                errors.append("SQL template must start with SELECT")
            
            # Validate parameter placeholders
            parameter_errors = self.validate_sql_parameters(
                sql_template, 
                template_data.get('parameters', {})
            )
            errors.extend(parameter_errors)
        
        # Parameter definition validation
        parameters = template_data.get('parameters', {})
        if parameters:
            param_errors = self.validate_parameter_definitions(parameters)
            errors.extend(param_errors)
        
        return errors
    
    def validate_sql_parameters(self, sql: str, parameter_definitions: dict) -> List[str]:
        """Validate that SQL parameters match definitions"""
        errors = []
        
        # Extract parameters from SQL
        import re
        sql_params = set(re.findall(r'\{\{(\w+)\}\}', sql))
        defined_params = set(parameter_definitions.keys())
        
        # Check for missing definitions
        missing_definitions = sql_params - defined_params
        if missing_definitions:
            errors.append(f"Missing parameter definitions: {', '.join(missing_definitions)}")
        
        # Check for unused definitions
        unused_definitions = defined_params - sql_params
        if unused_definitions:
            errors.append(f"Unused parameter definitions: {', '.join(unused_definitions)}")
        
        return errors
    
    def validate_parameter_definitions(self, parameters: dict) -> List[str]:
        """Validate parameter definition structure"""
        errors = []
        
        required_param_fields = ['type', 'label', 'description']
        
        for param_name, param_def in parameters.items():
            if not isinstance(param_def, dict):
                errors.append(f"Parameter '{param_name}' must be an object")
                continue
            
            # Check required fields
            for field in required_param_fields:
                if not param_def.get(field):
                    errors.append(f"Parameter '{param_name}' missing required field: {field}")
            
            # Validate parameter type
            valid_types = ['campaign_ids', 'asin_list', 'date', 'text', 'number', 'boolean']
            param_type = param_def.get('type')
            if param_type not in valid_types:
                errors.append(f"Parameter '{param_name}' has invalid type: {param_type}")
        
        return errors

async def get_templates_by_category(self, category: str = None, 
                                  difficulty: str = None,
                                  tags: List[str] = None) -> List[dict]:
    """Get templates with filtering"""
    
    query = self.db.table('query_templates')\
        .select('*')\
        .eq('is_public', True)\
        .order('usage_count', desc=True)
    
    # Apply filters
    if category:
        query = query.eq('category', category)
    
    if difficulty:
        query = query.eq('difficulty_level', difficulty)
    
    if tags:
        # PostgreSQL array overlap operator
        query = query.overlaps('tags', tags)
    
    result = query.execute()
    return result.data
```

### Template Instantiation Service
```python
# template_instantiation_service.py
class TemplateInstantiationService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.workflow_service = WorkflowService()
    
    async def instantiate_template(self, template_id: str, user_id: str, 
                                 instance_id: str, customization: dict) -> dict:
        """Create workflow from template with user customizations"""
        
        # Get template
        template = self.db.table('query_templates')\
            .select('*')\
            .eq('id', template_id)\
            .execute()
        
        if not template.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_data = template.data[0]
        
        # Validate user's parameter values
        parameter_errors = await self.validate_user_parameters(
            template_data['parameters'], 
            customization.get('parameters', {})
        )
        
        if parameter_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Parameter validation failed: {parameter_errors}"
            )
        
        # Generate SQL with user parameters
        sql_query = await self.substitute_template_parameters(
            template_data['sql_template'],
            customization.get('parameters', {}),
            template_data['parameters']
        )
        
        # Create workflow from template
        workflow_data = {
            'name': customization.get('name', f"{template_data['name']} - {datetime.utcnow().strftime('%Y-%m-%d')}"),
            'description': customization.get('description', f"Created from template: {template_data['name']}"),
            'sql_query': sql_query,
            'parameters': customization.get('parameters', {}),
            'template_id': template_id,
            'tags': template_data.get('tags', []) + customization.get('additional_tags', [])
        }
        
        # Create workflow
        workflow = await self.workflow_service.create_workflow(
            workflow_data, user_id, instance_id
        )
        
        # Update template usage statistics
        await self.update_template_usage(template_id)
        
        return workflow
    
    async def validate_user_parameters(self, template_params: dict, 
                                     user_values: dict) -> List[str]:
        """Validate user-provided parameter values against template definitions"""
        errors = []
        
        for param_name, param_def in template_params.items():
            user_value = user_values.get(param_name)
            
            # Check required parameters
            if param_def.get('required', False) and not user_value:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            if not user_value:
                continue  # Skip validation for optional empty parameters
            
            # Type-specific validation
            param_type = param_def.get('type')
            
            if param_type == 'campaign_ids':
                if not isinstance(user_value, list) or not all(isinstance(x, str) for x in user_value):
                    errors.append(f"Parameter '{param_name}' must be a list of campaign IDs")
            
            elif param_type == 'asin_list':
                if not isinstance(user_value, list) or not all(isinstance(x, str) for x in user_value):
                    errors.append(f"Parameter '{param_name}' must be a list of ASINs")
                
                # Validate ASIN format
                asin_pattern = re.compile(r'^B[0-9A-Z]{9}$')
                invalid_asins = [asin for asin in user_value if not asin_pattern.match(asin)]
                if invalid_asins:
                    errors.append(f"Invalid ASINs in '{param_name}': {', '.join(invalid_asins)}")
            
            elif param_type == 'date':
                try:
                    datetime.fromisoformat(str(user_value))
                except ValueError:
                    errors.append(f"Parameter '{param_name}' must be a valid date")
            
            elif param_type == 'number':
                if not isinstance(user_value, (int, float)):
                    errors.append(f"Parameter '{param_name}' must be a number")
                
                # Check min/max constraints
                validation_rules = param_def.get('validation_rules', {})
                if 'min' in validation_rules and user_value < validation_rules['min']:
                    errors.append(f"Parameter '{param_name}' must be at least {validation_rules['min']}")
                if 'max' in validation_rules and user_value > validation_rules['max']:
                    errors.append(f"Parameter '{param_name}' must be at most {validation_rules['max']}")
        
        return errors
    
    async def substitute_template_parameters(self, sql_template: str, 
                                           user_values: dict, 
                                           param_definitions: dict) -> str:
        """Substitute template parameters with user values or defaults"""
        
        result_sql = sql_template
        
        for param_name, param_def in param_definitions.items():
            placeholder = f"{{{{{param_name}}}}}"
            
            # Get user value or default
            user_value = user_values.get(param_name)
            if user_value is None:
                user_value = param_def.get('default_value')
            
            if user_value is not None:
                # Format value based on parameter type
                formatted_value = self.format_parameter_value(
                    param_def.get('type'), 
                    user_value
                )
                result_sql = result_sql.replace(placeholder, formatted_value)
        
        return result_sql
    
    def format_parameter_value(self, param_type: str, value: Any) -> str:
        """Format parameter value for SQL substitution"""
        if param_type in ['campaign_ids', 'asin_list']:
            if isinstance(value, list):
                formatted_values = [f"'{str(v)}'" for v in value]
                return ', '.join(formatted_values)
            else:
                return f"'{str(value)}'"
        
        elif param_type == 'date':
            if isinstance(value, str):
                return f"'{value}'"
            elif hasattr(value, 'strftime'):
                return f"'{value.strftime('%Y-%m-%dT%H:%M:%S')}'"
        
        elif param_type in ['number', 'boolean']:
            return str(value)
        
        else:  # text and other types
            return f"'{str(value)}'"
```

## Frontend Template Interface

### Template Library Component
```typescript
// QueryTemplates.tsx - Template library interface
const QueryTemplates: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  
  const { data: templates, isLoading } = useQuery({
    queryKey: ['query-templates', selectedCategory, selectedDifficulty, selectedTags, searchTerm],
    queryFn: () => queryTemplateService.list({
      category: selectedCategory || undefined,
      difficulty: selectedDifficulty || undefined,
      tags: selectedTags.length > 0 ? selectedTags : undefined,
      search: searchTerm || undefined
    })
  });
  
  const { data: categories } = useQuery({
    queryKey: ['template-categories'],
    queryFn: () => queryTemplateService.getCategories()
  });
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Query Templates</h1>
        <p className="text-lg text-gray-600 mt-2">
          Pre-built AMC queries for common use cases. Customize and create workflows instantly.
        </p>
      </div>
      
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Templates
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or description..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Categories</option>
              {categories?.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
          
          {/* Difficulty Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty
            </label>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="">All Levels</option>
              <option value="BEGINNER">Beginner</option>
              <option value="INTERMEDIATE">Intermediate</option>
              <option value="ADVANCED">Advanced</option>
            </select>
          </div>
          
          {/* Tags Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            <TagSelector
              selectedTags={selectedTags}
              onChange={setSelectedTags}
            />
          </div>
        </div>
      </div>
      
      {/* Template Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <TemplateCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates?.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onCustomize={(template) => {
                // Open customization modal
                setCustomizationModal({ open: true, template });
              }}
            />
          ))}
        </div>
      )}
      
      {templates?.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No templates found
          </h3>
          <p className="text-gray-500">
            Try adjusting your filters or search terms.
          </p>
        </div>
      )}
    </div>
  );
};
```

### Template Customization Modal
```typescript
// TemplateCustomizer.tsx - Parameter customization interface
interface TemplateCustomizerProps {
  template: QueryTemplate;
  onSave: (customization: TemplateCustomization) => void;
  onCancel: () => void;
}

const TemplateCustomizer: React.FC<TemplateCustomizerProps> = ({ 
  template, 
  onSave, 
  onCancel 
}) => {
  const [workflowName, setWorkflowName] = useState(`${template.name} - ${new Date().toLocaleDateString()}`);
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  
  const { data: instances } = useQuery({
    queryKey: ['amc-instances'],
    queryFn: () => instanceService.list({ active: true })
  });
  
  // Initialize parameter values with defaults
  useEffect(() => {
    const defaults: Record<string, any> = {};
    
    Object.entries(template.parameters || {}).forEach(([paramName, paramDef]) => {
      if (paramDef.default_value !== undefined) {
        defaults[paramName] = paramDef.default_value;
      }
    });
    
    setParameterValues(defaults);
  }, [template]);
  
  const handleParameterChange = (paramName: string, value: any) => {
    setParameterValues(prev => ({
      ...prev,
      [paramName]: value
    }));
  };
  
  const validateAndSave = () => {
    // Validate required parameters
    const missingParams: string[] = [];
    
    Object.entries(template.parameters || {}).forEach(([paramName, paramDef]) => {
      if (paramDef.required && !parameterValues[paramName]) {
        missingParams.push(paramName);
      }
    });
    
    if (missingParams.length > 0) {
      alert(`Please provide values for required parameters: ${missingParams.join(', ')}`);
      return;
    }
    
    if (!selectedInstance) {
      alert('Please select an AMC instance');
      return;
    }
    
    // Save customization
    onSave({
      name: workflowName,
      description: workflowDescription,
      instance_id: selectedInstance,
      parameters: parameterValues
    });
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">Customize Template: {template.name}</h2>
          <p className="text-gray-600 mt-1">{template.description}</p>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Workflow Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Workflow Name
              </label>
              <input
                type="text"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AMC Instance
              </label>
              <select
                value={selectedInstance}
                onChange={(e) => setSelectedInstance(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">Select Instance</option>
                {instances?.map((instance) => (
                  <option key={instance.id} value={instance.id}>
                    {instance.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <textarea
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          {/* Parameter Configuration */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Parameters
            </h3>
            
            <div className="space-y-4">
              {Object.entries(template.parameters || {}).map(([paramName, paramDef]) => (
                <ParameterInput
                  key={paramName}
                  parameterName={paramName}
                  definition={paramDef}
                  value={parameterValues[paramName]}
                  onChange={(value) => handleParameterChange(paramName, value)}
                />
              ))}
            </div>
          </div>
          
          {/* Query Preview */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Query Preview
            </h3>
            <TemplateQueryPreview
              template={template}
              parameterValues={parameterValues}
            />
          </div>
        </div>
        
        <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={validateAndSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Workflow
          </button>
        </div>
      </div>
    </div>
  );
};
```

## Template Categories and Organization

### Category Management
```python
TEMPLATE_CATEGORIES = {
    'Attribution': {
        'description': 'Cross-channel attribution analysis',
        'icon': '🎯',
        'subcategories': ['First-Touch', 'Last-Touch', 'Multi-Touch', 'Time-Decay']
    },
    'Performance Analysis': {
        'description': 'Campaign and ad performance metrics',
        'icon': '📊',
        'subcategories': ['Campaign Analysis', 'Audience Insights', 'Creative Performance']
    },
    'Audience Building': {
        'description': 'Audience creation and analysis',
        'icon': '👥',
        'subcategories': ['Look-alike', 'Behavioral', 'Demographic']
    },
    'Incrementality': {
        'description': 'Incremental lift and impact measurement',
        'icon': '📈',
        'subcategories': ['Brand Studies', 'Holdout Analysis', 'Lift Measurement']
    },
    'Cross-Channel': {
        'description': 'Multi-touchpoint customer journey analysis',
        'icon': '🔄',
        'subcategories': ['Journey Mapping', 'Channel Comparison', 'Overlap Analysis']
    },
    'Optimization': {
        'description': 'Campaign and budget optimization queries',
        'icon': '⚡',
        'subcategories': ['Budget Allocation', 'Frequency Capping', 'Bid Optimization']
    }
}
```

### Template Tagging System
```python
# Standardized tags for better discoverability
TEMPLATE_TAGS = {
    # Data Sources
    'dsp_data': 'Uses DSP campaign data',
    'search_data': 'Uses Amazon search data', 
    'attribution_data': 'Uses attribution events',
    
    # Use Cases
    'brand_awareness': 'Brand awareness campaigns',
    'conversion_optimization': 'Conversion optimization',
    'audience_analysis': 'Audience insights',
    'competitive_analysis': 'Competitive intelligence',
    
    # Complexity
    'joins_required': 'Multiple table joins',
    'advanced_sql': 'Advanced SQL concepts',
    'beginner_friendly': 'Good for beginners',
    
    # Business Objectives
    'roi_analysis': 'Return on investment',
    'customer_lifetime_value': 'CLV analysis',
    'market_share': 'Market share insights'
}
```

## Template Testing and Validation

### Automated Template Testing
```python
async def validate_template_execution(template_id: str) -> dict:
    """Test template execution with sample data"""
    
    template = await self.get_template(template_id)
    
    # Generate sample parameter values
    sample_params = await self.generate_sample_parameters(template['parameters'])
    
    try:
        # Create temporary workflow
        temp_workflow = await self.instantiate_template(
            template_id,
            'system', # System user for testing
            'test-instance',
            {'parameters': sample_params}
        )
        
        # Execute with dry run
        execution_result = await self.workflow_service.validate_workflow(temp_workflow['id'])
        
        # Update test status
        self.db.table('query_templates')\
            .update({
                'test_status': 'PASSED' if execution_result['valid'] else 'FAILED',
                'last_tested_at': datetime.utcnow().isoformat()
            })\
            .eq('id', template_id)\
            .execute()
        
        return {
            'template_id': template_id,
            'test_passed': execution_result['valid'],
            'error_message': execution_result.get('error'),
            'tested_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Mark test as failed
        self.db.table('query_templates')\
            .update({
                'test_status': 'FAILED',
                'last_tested_at': datetime.utcnow().isoformat()
            })\
            .eq('id', template_id)\
            .execute()
        
        return {
            'template_id': template_id,
            'test_passed': False,
            'error_message': str(e)
        }
```

## Analytics and Usage Tracking

### Template Analytics
```python
async def get_template_analytics(self, date_range: dict = None) -> dict:
    """Get comprehensive template usage analytics"""
    
    if not date_range:
        date_range = {
            'start': (datetime.utcnow() - timedelta(days=30)).isoformat(),
            'end': datetime.utcnow().isoformat()
        }
    
    # Most used templates
    popular_templates = self.db.table('query_templates')\
        .select('id, name, usage_count, category')\
        .order('usage_count', desc=True)\
        .limit(10)\
        .execute()
    
    # Category usage distribution
    category_stats = self.db.rpc('get_template_category_stats', date_range).execute()
    
    # User adoption rates
    adoption_stats = self.db.rpc('get_template_adoption_stats', date_range).execute()
    
    # Template effectiveness (based on workflow execution success rates)
    effectiveness_stats = self.db.rpc('get_template_effectiveness', date_range).execute()
    
    return {
        'popular_templates': popular_templates.data,
        'category_distribution': category_stats.data,
        'adoption_rates': adoption_stats.data,
        'effectiveness_metrics': effectiveness_stats.data,
        'total_templates': len(popular_templates.data),
        'date_range': date_range
    }
```