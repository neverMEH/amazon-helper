import { useState, useEffect } from 'react';
import { Save, X, Wand2, Eye, Code, Settings, Tag, AlertCircle, Check } from 'lucide-react';
import SQLEditor from '../common/SQLEditor';
import { toast } from 'react-hot-toast';
import type { QueryTemplate } from '../../types/queryTemplate';

interface TemplateEditorProps {
  template?: QueryTemplate;
  onSave: (template: any) => Promise<void>;  // Returns snake_case format for API
  onCancel: () => void;
  isLoading?: boolean;
}

interface ParameterDefinition {
  name: string;
  type: 'text' | 'number' | 'date' | 'date_range' | 'asin_list' | 'campaign_list' | 'boolean';
  required: boolean;
  defaultValue?: any;
  description?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    enum?: string[];
  };
}

const PARAMETER_TYPES = [
  { value: 'text', label: 'Text', icon: '📝' },
  { value: 'number', label: 'Number', icon: '🔢' },
  { value: 'date', label: 'Date', icon: '📅' },
  { value: 'date_range', label: 'Date Range', icon: '📆' },
  { value: 'asin_list', label: 'ASIN List', icon: '📦' },
  { value: 'campaign_list', label: 'Campaign List', icon: '📊' },
  { value: 'boolean', label: 'Boolean', icon: '✓' },
];

const CATEGORIES = [
  'Campaign Performance',
  'Audience Analysis', 
  'Attribution',
  'Conversion',
  'Custom',
];

export default function TemplateEditor({ template, onSave, onCancel, isLoading }: TemplateEditorProps) {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    description: template?.description || '',
    category: template?.category || 'Custom',
    tags: template?.tags || [],
    sqlTemplate: template?.sqlTemplate || '',
    isPublic: template?.isPublic ?? true,
  });

  const [parameters, setParameters] = useState<ParameterDefinition[]>([]);
  const [detectedParams, setDetectedParams] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<'editor' | 'preview' | 'settings'>('editor');
  const [isSaving, setIsSaving] = useState(false);

  // Detect parameters in SQL query
  useEffect(() => {
    const paramPattern = /\{\{(\w+)\}\}/g;
    const matches = formData.sqlTemplate.matchAll(paramPattern) as IterableIterator<RegExpMatchArray>;
    const params = Array.from(new Set(Array.from(matches, m => m[1])));
    setDetectedParams(params);

    // Auto-add new detected parameters
    params.forEach(paramName => {
      if (!parameters.find(p => p.name === paramName)) {
        setParameters(prev => [...prev, {
          name: paramName,
          type: guessParameterType(paramName),
          required: true,
          description: '',
        }]);
      }
    });

    // Remove parameters that are no longer in the query
    setParameters(prev => prev.filter(p => params.includes(p.name)));
  }, [formData.sqlTemplate]);

  // Guess parameter type based on name
  const guessParameterType = (name: string): ParameterDefinition['type'] => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('date') || lowerName.includes('time')) return 'date';
    if (lowerName.includes('start') && lowerName.includes('end')) return 'date_range';
    if (lowerName.includes('asin')) return 'asin_list';
    if (lowerName.includes('campaign')) return 'campaign_list';
    if (lowerName.includes('count') || lowerName.includes('number') || lowerName.includes('limit')) return 'number';
    if (lowerName.includes('enabled') || lowerName.includes('active') || lowerName.includes('is_')) return 'boolean';
    return 'text';
  };

  // Update parameter definition
  const updateParameter = (index: number, field: keyof ParameterDefinition, value: any) => {
    setParameters(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  // Add tag
  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  // Remove tag
  const removeTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag),
    }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    }

    if (!formData.sqlTemplate.trim()) {
      newErrors.sqlTemplate = 'SQL query is required';
    }

    // AMC is a read-only environment, so we don't need to check for dangerous SQL
    // Comments (--), CTEs (WITH), and VALUES clauses are all perfectly safe
    // Removing overly aggressive validation that was blocking legitimate queries

    // Validate parameters
    parameters.forEach((param, index) => {
      if (!param.description?.trim()) {
        newErrors[`param_${index}`] = 'Parameter description is required';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = async () => {
    if (!validateForm()) {
      toast.error('Please fix the errors before saving');
      return;
    }

    setIsSaving(true);
    try {
      // Convert to snake_case for API
      const templateData: any = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        tags: formData.tags,
        sql_template: formData.sqlTemplate,
        is_public: formData.isPublic,
        parameters_schema: parameters.reduce((acc, param) => {
          acc[param.name] = {
            type: param.type,
            required: param.required,
            default_value: param.defaultValue,
            description: param.description,
            validation: param.validation,
          };
          return acc;
        }, {} as Record<string, any>),
        default_parameters: parameters.reduce((acc, param) => {
          if (param.defaultValue !== undefined) {
            acc[param.name] = param.defaultValue;
          }
          return acc;
        }, {} as Record<string, any>),
      };

      await onSave(templateData);
      toast.success('Template saved successfully');
    } catch (error) {
      console.error('Failed to save template:', error);
      toast.error('Failed to save template');
    } finally {
      setIsSaving(false);
    }
  };

  // Generate preview SQL with sample values
  const generatePreviewSQL = (): string => {
    let previewSQL = formData.sqlTemplate;
    
    parameters.forEach(param => {
      const sampleValue = getSampleValue(param);
      previewSQL = previewSQL.replace(
        new RegExp(`\\{\\{${param.name}\\}\\}`, 'g'),
        sampleValue
      );
    });

    return previewSQL;
  };

  // Get sample value for parameter type
  const getSampleValue = (param: ParameterDefinition): string => {
    switch (param.type) {
      case 'date':
        return "'2024-01-15'";
      case 'date_range':
        return "'2024-01-01' AND '2024-01-31'";
      case 'asin_list':
        return "('B001234567', 'B002345678', 'B003456789')";
      case 'campaign_list':
        return "('Campaign 1', 'Campaign 2')";
      case 'number':
        return '100';
      case 'boolean':
        return 'true';
      default:
        return "'sample_value'";
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">
            {template ? 'Edit Template' : 'Create New Template'}
          </h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-4 flex space-x-4 border-b">
          <button
            onClick={() => setActiveTab('editor')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'editor'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Code className="w-4 h-4" />
              <span>SQL Editor</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'preview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Eye className="w-4 h-4" />
              <span>Preview</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'editor' && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className={`w-full px-3 py-2 border rounded-lg ${
                      errors.name ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="e.g., Campaign Performance Analysis"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    {CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Describe what this template does..."
                />
              </div>

              {/* SQL Editor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SQL Query *
                </label>
                <div className={`border rounded-lg ${errors.sqlTemplate ? 'border-red-500' : 'border-gray-300'}`}>
                  <SQLEditor
                    value={formData.sqlTemplate}
                    onChange={(value) => setFormData(prev => ({ ...prev, sqlTemplate: value || '' }))}
                    height="300px"
                  />
                </div>
                {errors.sqlTemplate && (
                  <p className="mt-1 text-sm text-red-600">{errors.sqlTemplate}</p>
                )}
              </div>

              {/* Detected Parameters */}
              {detectedParams.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-gray-700">
                      Detected Parameters ({detectedParams.length})
                    </h3>
                    <div className="flex items-center text-xs text-gray-500">
                      <Wand2 className="w-3 h-3 mr-1" />
                      Auto-detected from SQL
                    </div>
                  </div>
                  <div className="space-y-3">
                    {parameters.map((param, index) => (
                      <div key={param.name} className="border border-gray-200 rounded-lg p-4">
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              Parameter: {param.name}
                            </label>
                            <select
                              value={param.type}
                              onChange={(e) => updateParameter(index, 'type', e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              {PARAMETER_TYPES.map(type => (
                                <option key={type.value} value={type.value}>
                                  {type.icon} {type.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="col-span-2">
                            <label className="block text-xs font-medium text-gray-600 mb-1">
                              Description *
                            </label>
                            <input
                              type="text"
                              value={param.description || ''}
                              onChange={(e) => updateParameter(index, 'description', e.target.value)}
                              className={`w-full px-2 py-1 text-sm border rounded ${
                                errors[`param_${index}`] ? 'border-red-500' : 'border-gray-300'
                              }`}
                              placeholder="Describe this parameter..."
                            />
                          </div>
                        </div>
                        <div className="mt-2 flex items-center space-x-4">
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={param.required}
                              onChange={(e) => updateParameter(index, 'required', e.target.checked)}
                              className="mr-2"
                            />
                            Required
                          </label>
                          {param.type === 'number' && (
                            <div className="flex items-center space-x-2 text-sm">
                              <input
                                type="number"
                                placeholder="Min"
                                className="w-20 px-2 py-1 border border-gray-300 rounded"
                                onChange={(e) => updateParameter(index, 'validation', {
                                  ...param.validation,
                                  min: e.target.value ? Number(e.target.value) : undefined,
                                })}
                              />
                              <span>-</span>
                              <input
                                type="number"
                                placeholder="Max"
                                className="w-20 px-2 py-1 border border-gray-300 rounded"
                                onChange={(e) => updateParameter(index, 'validation', {
                                  ...param.validation,
                                  max: e.target.value ? Number(e.target.value) : undefined,
                                })}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">Preview Mode</p>
                    <p className="mt-1">
                      This shows how your SQL will look with sample parameter values.
                      Actual values will be provided when the template is used.
                    </p>
                  </div>
                </div>
              </div>

              <div className="border border-gray-300 rounded-lg">
                <SQLEditor
                  value={generatePreviewSQL()}
                  onChange={() => {}}
                  height="400px"
                  readOnly
                />
              </div>

              {parameters.length > 0 && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Sample Parameter Values</h3>
                  <div className="space-y-2">
                    {parameters.map(param => (
                      <div key={param.name} className="flex justify-between text-sm">
                        <span className="font-mono text-gray-600">{`{{${param.name}}}`}</span>
                        <span className="text-gray-900">{getSampleValue(param)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                    placeholder="Add a tag..."
                  />
                  <button
                    onClick={addTag}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {formData.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                    >
                      <Tag className="w-3 h-3 mr-1" />
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="ml-2 hover:text-blue-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              {/* Visibility */}
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.isPublic}
                    onChange={(e) => setFormData(prev => ({ ...prev, isPublic: e.target.checked }))}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Make this template public
                  </span>
                </label>
                <p className="mt-1 text-sm text-gray-500 ml-6">
                  Public templates can be used by all users in your organization
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-between items-center">
          <div className="flex items-center text-sm text-gray-600">
            {detectedParams.length > 0 && (
              <>
                <Check className="w-4 h-4 text-green-600 mr-1" />
                {detectedParams.length} parameter{detectedParams.length !== 1 ? 's' : ''} detected
              </>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              disabled={isSaving}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Template</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}