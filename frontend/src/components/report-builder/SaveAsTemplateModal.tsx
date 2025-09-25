import { useState } from 'react';
import { X, Save, FileText, Tag, Globe, Lock } from 'lucide-react';
import { queryTemplateService } from '../../services/queryTemplateService';
import toast from 'react-hot-toast';

interface SaveAsTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  execution: {
    workflowName: string;
    sqlQuery?: string;
    workflowId?: string;
  };
  onSuccess?: (templateId: string) => void;
}

export default function SaveAsTemplateModal({
  isOpen,
  onClose,
  execution,
  onSuccess
}: SaveAsTemplateModalProps) {
  const [templateName, setTemplateName] = useState(execution.workflowName || 'New Template');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Custom Queries');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const categories = [
    'Campaign Analysis',
    'Product Performance',
    'Budget Optimization',
    'Audience Insights',
    'Creative Analysis',
    'Sales Attribution',
    'Custom Queries'
  ];

  if (!isOpen) return null;

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSave = async () => {
    if (!templateName.trim()) {
      toast.error('Please provide a template name');
      return;
    }

    if (!execution.sqlQuery) {
      toast.error('No SQL query found in the execution');
      return;
    }

    setIsSaving(true);
    try {
      let response;

      // Always use the direct create method since we have the SQL query
      // The createFromWorkflow method requires the workflow to exist in the database
      // which may not be the case for ad-hoc executions
      const templatePayload = {
        name: templateName,
        description: description || '',
        category,
        tags,
        is_public: isPublic,
        sql_template: execution.sqlQuery,
        parameters_schema: {},
        default_parameters: {}
      };

      console.log('Creating template with payload:', templatePayload);
      response = await queryTemplateService.createTemplate(templatePayload);

      console.log('Template created successfully:', response);

      if (!response || !response.templateId) {
        throw new Error('Template was created but no ID was returned');
      }

      toast.success(`Template "${templateName}" saved successfully!`);
      onSuccess?.(response.templateId);
      onClose();
    } catch (error: any) {
      console.error('=== Template save failed ===');
      console.error('Full error object:', error);
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);

      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
        console.error('Response data:', error.response.data);
        console.error('Response config:', error.response.config);
      }

      // Extract error message from various possible locations
      let errorMessage = 'Failed to save template';

      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
        console.log('Error from detail:', errorMessage);
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
        console.log('Error from message:', errorMessage);
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
        console.log('Error from error:', errorMessage);
      } else if (error.message && error.message !== 'Request failed with status code 422') {
        errorMessage = error.message;
        console.log('Error from error.message:', errorMessage);
      }

      // Show more descriptive error for validation errors
      if (error.response?.status === 422) {
        console.log('422 Validation Error detected');
        const validationErrors = error.response?.data?.detail;
        console.log('Validation errors:', validationErrors);

        if (Array.isArray(validationErrors)) {
          errorMessage = 'Validation error: ' + validationErrors.map((e: any) => {
            console.log('Validation error item:', e);
            return e.msg || e.message || JSON.stringify(e);
          }).join(', ');
        } else if (typeof validationErrors === 'string') {
          errorMessage = validationErrors;
        } else if (validationErrors && typeof validationErrors === 'object') {
          errorMessage = 'Validation error: ' + JSON.stringify(validationErrors);
        } else {
          errorMessage = 'Please check all required fields are filled correctly';
        }
      }

      console.log('Final error message to display:', errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <FileText className="h-6 w-6 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">Save as Template</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Template Name */}
          <div>
            <label htmlFor="template-name" className="block text-sm font-medium text-gray-700 mb-2">
              Template Name *
            </label>
            <input
              id="template-name"
              type="text"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter a descriptive name for your template"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="template-description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="template-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Describe what this template does and when to use it"
            />
          </div>

          {/* Category */}
          <div>
            <label htmlFor="template-category" className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              id="template-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            <div className="flex items-center space-x-2 mb-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter a tag and press Enter"
              />
              <button
                onClick={handleAddTag}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <Tag className="h-4 w-4" />
              </button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-indigo-600 hover:text-indigo-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Visibility */}
          <div>
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <span className="flex items-center text-sm text-gray-700">
                {isPublic ? (
                  <>
                    <Globe className="h-4 w-4 mr-1 text-green-600" />
                    Make this template public (visible to all users)
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4 mr-1 text-gray-400" />
                    Keep this template private (only visible to you)
                  </>
                )}
              </span>
            </label>
          </div>

          {/* SQL Preview */}
          {execution.sqlQuery && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SQL Query Preview
              </label>
              <div className="bg-gray-50 rounded-md p-3 overflow-x-auto">
                <pre className="text-xs text-gray-600 font-mono">
                  {execution.sqlQuery.substring(0, 500)}
                  {execution.sqlQuery.length > 500 && '...'}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || !templateName.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? 'Saving...' : 'Save Template'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}