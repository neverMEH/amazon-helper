/**
 * Instance Template Editor Modal
 *
 * Modal for creating/editing SQL templates with parameter detection and auto-population.
 * Detects SQL parameters, auto-populates ASINs/campaigns from instance mappings,
 * and provides a preview of the final SQL.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Save, X, Tag, AlertCircle, Wand2, Link } from 'lucide-react';
import SQLEditor from '../common/SQLEditor';
import { toast } from 'react-hot-toast';
import { ParameterDetector } from '../parameter-detection';
import type { DetectedParameter } from '../../utils/parameterDetection';
import { useInstanceMappings } from '../../hooks/useInstanceMappings';
import { autoPopulateParameters, extractParameterValues } from '../../utils/parameterAutoPopulator';
import { replaceParametersInSQL } from '../../utils/sqlParameterizer';
import ParameterPreviewPanel from './ParameterPreviewPanel';
import type { InstanceTemplate } from '../../types/instanceTemplate';

interface InstanceTemplateEditorProps {
  template?: InstanceTemplate;
  instanceId: string;
  onSave: (template: {
    name: string;
    description?: string;
    sql_query: string;
    tags?: string[];
  }) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function InstanceTemplateEditor({
  template,
  instanceId,
  onSave,
  onCancel,
  isLoading,
}: InstanceTemplateEditorProps) {
  const [formData, setFormData] = useState({
    name: template?.name || '',
    description: template?.description || '',
    sqlQuery: template?.sqlQuery || '',
    tags: template?.tags || [],
  });

  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  // Parameter detection state
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [hasAutoPopulated, setHasAutoPopulated] = useState(false);

  // SQL Preview state
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // Fetch instance mappings for auto-population
  const { data: instanceMappings, isLoading: loadingMappings } = useInstanceMappings(instanceId);

  // Generate SQL preview with parameters substituted
  const previewSQL = useMemo(() => {
    if (!formData.sqlQuery || detectedParameters.length === 0) {
      return formData.sqlQuery;
    }

    try {
      return replaceParametersInSQL(formData.sqlQuery, parameterValues);
    } catch (error) {
      console.error('Error replacing parameters:', error);
      return formData.sqlQuery;
    }
  }, [formData.sqlQuery, parameterValues, detectedParameters.length]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    } else if (formData.name.length > 255) {
      newErrors.name = 'Template name must be 255 characters or less';
    }

    if (!formData.sqlQuery.trim()) {
      newErrors.sqlQuery = 'SQL query is required';
    }

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
      // Use preview SQL (with parameters replaced) if we have parameters and values
      const sqlToSave = detectedParameters.length > 0 && Object.keys(parameterValues).length > 0
        ? previewSQL
        : formData.sqlQuery.trim();

      await onSave({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        sql_query: sqlToSave,
        tags: formData.tags.length > 0 ? formData.tags : undefined,
      });
      toast.success('Template saved successfully');
    } catch (error: any) {
      console.error('Failed to save template:', error);
      const errorMessage = error?.response?.data?.detail || 'Failed to save template';
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  // Add tag
  const addTag = () => {
    const trimmedTag = tagInput.trim();
    if (trimmedTag && !formData.tags.includes(trimmedTag)) {
      setFormData((prev) => ({
        ...prev,
        tags: [...prev.tags, trimmedTag],
      }));
      setTagInput('');
    }
  };

  // Remove tag
  const removeTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.filter((t) => t !== tag),
    }));
  };

  // Handle Enter key in tag input
  const handleTagKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  // Handle detected parameters
  const handleParametersDetected = useCallback((params: DetectedParameter[]) => {
    setDetectedParameters(params);

    // Initialize values for new parameters
    const newValues: Record<string, any> = {};
    params.forEach(param => {
      if (!(param.name in parameterValues)) {
        newValues[param.name] = '';
      }
    });

    if (Object.keys(newValues).length > 0) {
      setParameterValues(prev => ({ ...prev, ...newValues }));
    }
  }, [parameterValues]);

  // Handle parameter value change
  const handleParameterChange = useCallback((parameterName: string, value: any) => {
    setParameterValues(prev => ({
      ...prev,
      [parameterName]: value
    }));
  }, []);

  // Auto-populate parameters from instance mappings
  useEffect(() => {
    if (instanceMappings && detectedParameters.length > 0 && instanceId && !hasAutoPopulated) {
      // Map parameter names based on detected parameter types
      const parameterNameMap: { brands?: string; asins?: string; campaigns?: string } = {};

      detectedParameters.forEach(param => {
        const lowerName = param.name.toLowerCase();
        if (param.type === 'asin' || lowerName.includes('asin') || lowerName.includes('tracked')) {
          parameterNameMap.asins = param.name;
        } else if (param.type === 'campaign' || lowerName.includes('campaign')) {
          parameterNameMap.campaigns = param.name;
        } else if (lowerName.includes('brand')) {
          parameterNameMap.brands = param.name;
        }
      });

      // Only auto-populate if we have mappings and relevant parameters
      if (Object.keys(parameterNameMap).length > 0) {
        const autoPopulated = autoPopulateParameters(instanceMappings, parameterValues, parameterNameMap);
        const newValues = extractParameterValues(autoPopulated);

        // Check if any values were actually auto-populated
        const hasNewValues = Object.keys(parameterNameMap).some(key => {
          const paramName = parameterNameMap[key as keyof typeof parameterNameMap];
          return paramName && newValues[paramName] && (!parameterValues[paramName] ||
            (Array.isArray(newValues[paramName]) && newValues[paramName].length > 0));
        });

        if (hasNewValues) {
          setParameterValues(newValues);
          setHasAutoPopulated(true);
          toast.success('Parameters auto-populated from instance mappings', { icon: '🔗' });
        }
      }
    }
  }, [instanceMappings, detectedParameters, instanceId, hasAutoPopulated, parameterValues]);

  // Reset auto-populate flag when instance changes
  useEffect(() => {
    setHasAutoPopulated(false);
  }, [instanceId]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">
              {template ? 'Edit Template' : 'Create New Template'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Save SQL queries for quick reuse in this instance
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          {/* Template Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, name: e.target.value }))
              }
              className={`w-full px-3 py-2 border rounded-lg ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              } focus:ring-2 focus:ring-blue-500 focus:border-transparent`}
              placeholder="e.g., Weekly Campaign Performance"
              maxLength={255}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.name}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              {formData.name.length}/255 characters
            </p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="Describe what this template does..."
            />
          </div>

          {/* SQL Editor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SQL Query *
            </label>
            <div
              className={`border rounded-lg ${
                errors.sqlQuery ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <SQLEditor
                value={formData.sqlQuery}
                onChange={(value) =>
                  setFormData((prev) => ({ ...prev, sqlQuery: value || '' }))
                }
                height="400px"
              />
            </div>
            {errors.sqlQuery && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.sqlQuery}
              </p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              💡 Tip: Use parameters like{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">
                {'{{start_date}}'}
              </code>
              , <code className="bg-gray-100 px-1 py-0.5 rounded">:date</code>, or{' '}
              <code className="bg-gray-100 px-1 py-0.5 rounded">$param</code>
              {' '}— ASINs and campaigns will auto-populate!
            </p>
          </div>

          {/* Parameter Detection (invisible component) */}
          {formData.sqlQuery && (
            <ParameterDetector
              sqlQuery={formData.sqlQuery}
              onParametersDetected={handleParametersDetected}
              debounceMs={500}
            />
          )}

          {/* Parameter Detection UI */}
          {detectedParameters.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start mb-3">
                <Wand2 className="h-5 w-5 text-blue-600 mt-0.5 mr-2" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">
                    Detected {detectedParameters.length} parameter{detectedParameters.length !== 1 ? 's' : ''}
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    Fill in the parameter values below. ASINs and campaigns will auto-populate from instance mappings.
                  </p>
                </div>
                {hasAutoPopulated && instanceMappings && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 rounded-md text-xs font-medium">
                    <Link className="h-3 w-3" />
                    Auto-populated
                  </div>
                )}
              </div>

              {loadingMappings && (
                <div className="mb-3 text-xs text-blue-600 flex items-center gap-2">
                  <div className="animate-spin h-3 w-3 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  Loading instance mappings...
                </div>
              )}

              {/* Parameter Inputs */}
              <div className="space-y-3">
                {detectedParameters.map((param) => (
                  <div key={param.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {param.name}
                      <span className="ml-2 text-xs text-gray-500">
                        ({param.type})
                      </span>
                    </label>
                    {param.type === 'date' ? (
                      <input
                        type="date"
                        value={parameterValues[param.name] || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder={`Enter ${param.name}`}
                      />
                    ) : param.type === 'asin' || param.type === 'campaign' ? (
                      <textarea
                        value={
                          Array.isArray(parameterValues[param.name])
                            ? parameterValues[param.name].join(', ')
                            : parameterValues[param.name] || ''
                        }
                        onChange={(e) => {
                          const value = e.target.value;
                          // Convert comma-separated string to array
                          const arrayValue = value.split(',').map(v => v.trim()).filter(Boolean);
                          handleParameterChange(param.name, arrayValue);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        rows={3}
                        placeholder={`Enter ${param.name} (comma-separated)`}
                      />
                    ) : (
                      <input
                        type="text"
                        value={parameterValues[param.name] || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder={`Enter ${param.name}`}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SQL Preview Panel */}
          {detectedParameters.length > 0 && (
            <ParameterPreviewPanel
              sqlQuery={previewSQL}
              isOpen={isPreviewOpen}
              onToggle={() => setIsPreviewOpen(!isPreviewOpen)}
            />
          )}

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags (Optional)
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={handleTagKeyPress}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Add a tag..."
              />
              <button
                onClick={addTag}
                type="button"
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Add
              </button>
            </div>
            {formData.tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {formData.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    <Tag className="w-3 h-3 mr-1" />
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      type="button"
                      className="ml-2 hover:text-blue-600"
                      aria-label={`Remove ${tag} tag`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end space-x-3">
          <button
            onClick={onCancel}
            type="button"
            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            type="button"
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
  );
}
