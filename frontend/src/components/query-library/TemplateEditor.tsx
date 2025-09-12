import { useState, useEffect } from 'react';
import { Save, X, Wand2, Eye, Code, Settings, Tag, AlertCircle, Check, Info, Sparkles } from 'lucide-react';
import SQLEditor from '../common/SQLEditor';
import { toast } from 'react-hot-toast';
import type { QueryTemplate } from '../../types/queryTemplate';
import { 
  detectParametersWithContext, 
  generatePreviewSQL,
  type ParameterDefinition as AnalyzerParameterDef
} from '../../utils/sqlParameterAnalyzer';
import AsinMultiSelect from './AsinMultiSelect';
import ParameterEditor from '../workflows/ParameterEditor';

interface TemplateEditorProps {
  template?: QueryTemplate;
  onSave: (template: any) => Promise<void>;  // Returns snake_case format for API
  onCancel: () => void;
  isLoading?: boolean;
}

interface ParameterDefinition extends AnalyzerParameterDef {
  userValue?: any;
}

const PARAMETER_TYPES = [
  { value: 'text', label: 'Text', icon: '📝' },
  { value: 'number', label: 'Number', icon: '🔢' },
  { value: 'date', label: 'Date', icon: '📅' },
  { value: 'date_range', label: 'Date Range', icon: '📆' },
  { value: 'asin_list', label: 'ASIN List', icon: '📦' },
  { value: 'campaign_list', label: 'Campaign List', icon: '📊' },
  { value: 'pattern', label: 'Pattern (LIKE)', icon: '🔍' },
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

  // Detect parameters in SQL query with context awareness
  useEffect(() => {
    const detectedParamsWithContext = detectParametersWithContext(formData.sqlTemplate);
    const paramNames = detectedParamsWithContext.map(p => p.name);
    setDetectedParams(paramNames);

    // Update parameters with context-aware detection
    setParameters(prev => {
      const updated: ParameterDefinition[] = [];
      
      // Process each detected parameter
      detectedParamsWithContext.forEach(detectedParam => {
        const existing = prev.find(p => p.name === detectedParam.name);
        if (existing) {
          // Preserve user values and descriptions
          updated.push({
            ...detectedParam,
            description: existing.description,
            userValue: existing.userValue,
            defaultValue: existing.defaultValue,
          });
        } else {
          // Add new parameter
          updated.push(detectedParam);
        }
      });
      
      return updated;
    });
  }, [formData.sqlTemplate]);

  // Handle ASIN selection for asin_list parameters
  const [showAsinModal, setShowAsinModal] = useState<string | null>(null);
  
  const handleAsinSelection = (paramName: string, asins: string[]) => {
    setParameters(prev => prev.map(p => 
      p.name === paramName ? { ...p, userValue: asins } : p
    ));
    setShowAsinModal(null);
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

  // Generate preview SQL using context-aware formatting
  const getPreviewSQL = (): string => {
    return generatePreviewSQL(formData.sqlTemplate, parameters);
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
                              Parameter: {`{{${param.name}}}`}
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
                        
                        {/* Context Information */}
                        {param.sqlContext && (
                          <div className="mt-2 flex items-start space-x-2 p-2 bg-blue-50 rounded text-xs">
                            <Info className="w-3 h-3 text-blue-600 flex-shrink-0 mt-0.5" />
                            <div className="text-blue-800">
                              <span className="font-medium">SQL Context:</span> {param.sqlContext}
                              {param.formatPattern && (
                                <div className="mt-1 text-blue-700">{param.formatPattern}</div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Input fields based on type */}
                        <div className="mt-3">
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Test Value (for preview)
                          </label>
                          
                          {param.type === 'asin_list' ? (
                            <div className="space-y-2">
                              <AsinMultiSelect
                                value={param.userValue || []}
                                onChange={(asins) => updateParameter(index, 'userValue', asins)}
                                placeholder="Select ASINs for testing"
                                maxItems={100}
                                className="text-sm"
                              />
                            </div>
                          ) : param.type === 'pattern' ? (
                            <div>
                              <input
                                type="text"
                                value={param.userValue || ''}
                                onChange={(e) => updateParameter(index, 'userValue', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                                placeholder="Enter pattern (will be wrapped with %...%)"
                              />
                              {param.userValue && (
                                <div className="mt-1 text-xs text-gray-500">
                                  Will be formatted as: <code className="bg-gray-100 px-1 py-0.5 rounded">%{param.userValue}%</code>
                                </div>
                              )}
                            </div>
                          ) : param.type === 'campaign_list' ? (
                            <textarea
                              value={param.userValue || ''}
                              onChange={(e) => updateParameter(index, 'userValue', e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                              placeholder="Enter campaign names/IDs, comma-separated"
                              rows={2}
                            />
                          ) : param.type === 'date' ? (
                            <input
                              type="date"
                              value={param.userValue || ''}
                              onChange={(e) => updateParameter(index, 'userValue', e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            />
                          ) : param.type === 'date_range' ? (
                            <div className="flex items-center space-x-2">
                              <input
                                type="date"
                                value={param.userValue?.start || ''}
                                onChange={(e) => updateParameter(index, 'userValue', {
                                  ...param.userValue,
                                  start: e.target.value
                                })}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                                placeholder="Start date"
                              />
                              <span className="text-gray-500">to</span>
                              <input
                                type="date"
                                value={param.userValue?.end || ''}
                                onChange={(e) => updateParameter(index, 'userValue', {
                                  ...param.userValue,
                                  end: e.target.value
                                })}
                                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                                placeholder="End date"
                              />
                            </div>
                          ) : param.type === 'number' ? (
                            <input
                              type="number"
                              value={param.userValue || ''}
                              onChange={(e) => updateParameter(index, 'userValue', Number(e.target.value))}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                              placeholder="Enter a number"
                            />
                          ) : param.type === 'boolean' ? (
                            <select
                              value={param.userValue || 'true'}
                              onChange={(e) => updateParameter(index, 'userValue', e.target.value === 'true')}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            >
                              <option value="true">True</option>
                              <option value="false">False</option>
                            </select>
                          ) : (
                            <input
                              type="text"
                              value={param.userValue || ''}
                              onChange={(e) => updateParameter(index, 'userValue', e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                              placeholder="Enter value"
                            />
                          )}
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
                  value={getPreviewSQL()}
                  onChange={() => {}}
                  height="400px"
                  readOnly
                />
              </div>

              {parameters.length > 0 && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Parameter Context & Formatting</h3>
                  <div className="space-y-3">
                    {parameters.map(param => (
                      <div key={param.name} className="border-b border-gray-100 pb-2 last:border-0">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-mono text-gray-600">{`{{${param.name}}}`}</span>
                          <span className="text-xs text-gray-500">{param.type}</span>
                        </div>
                        {param.sqlContext && (
                          <div className="text-xs text-gray-600 mb-1">
                            <span className="font-medium">Context:</span> {param.sqlContext}
                          </div>
                        )}
                        {param.formatPattern && (
                          <div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                            {param.formatPattern}
                          </div>
                        )}
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