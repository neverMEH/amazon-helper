import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Code, Edit2, Trash2, Globe, Lock, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { queryTemplateService } from '../../services/queryTemplateService';
import type { QueryTemplate } from '../../types/queryTemplate';
import { formatDate } from '../../utils/dateUtils';
import QueryTemplateModal from './QueryTemplateModal';
import SQLEditor from '../common/SQLEditor';
import toast from 'react-hot-toast';

export default function QueryTemplates() {
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [expandedTemplates, setExpandedTemplates] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['query-templates', selectedCategory],
    queryFn: () => queryTemplateService.listTemplates(true, selectedCategory || undefined),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ['query-template-categories'],
    queryFn: () => queryTemplateService.getCategories(),
  });

  const deleteMutation = useMutation({
    mutationFn: (templateId: string) => queryTemplateService.deleteTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['query-templates'] });
      toast.success('Template deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete template');
    },
  });

  const handleEdit = (template: QueryTemplate) => {
    setSelectedTemplate(template);
    setIsModalOpen(true);
  };

  const handleCreate = () => {
    setSelectedTemplate(null);
    setIsModalOpen(true);
  };

  const handleDelete = async (templateId: string) => {
    if (confirm('Are you sure you want to delete this template?')) {
      await deleteMutation.mutateAsync(templateId);
    }
  };

  const handleDuplicate = (template: QueryTemplate) => {
    const duplicatedTemplate = {
      ...template,
      name: `${template.name} (Copy)`,
      isOwner: true,
    };
    setSelectedTemplate(duplicatedTemplate);
    setIsModalOpen(true);
  };

  const toggleExpanded = (templateId: string) => {
    setExpandedTemplates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(templateId)) {
        newSet.delete(templateId);
      } else {
        newSet.add(templateId);
      }
      return newSet;
    });
  };

  const handleCopySQL = (sqlTemplate: string) => {
    navigator.clipboard.writeText(sqlTemplate);
    toast.success('SQL query copied to clipboard');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading templates...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Query Templates</h2>
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Template
            </button>
          </div>
          
          {categories.length > 0 && (
            <div className="mt-4">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="block w-full sm:w-64 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-8 px-2"></th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Template
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Visibility
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {templates.map((template) => {
                const isExpanded = expandedTemplates.has(template.templateId);
                return (
                  <>
                    <tr 
                      key={template.templateId} 
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={(e) => {
                        // Don't toggle if clicking on action buttons
                        if (!(e.target as HTMLElement).closest('.action-buttons')) {
                          toggleExpanded(template.templateId);
                        }
                      }}
                    >
                      <td className="px-2 py-4">
                        <button
                          onClick={() => toggleExpanded(template.templateId)}
                          className="p-1 hover:bg-gray-100 rounded"
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4 text-gray-500" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-gray-500" />
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{template.name}</div>
                      {template.description && (
                        <div className="text-sm text-gray-500">{template.description}</div>
                      )}
                      {template.tags.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {template.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                      {Object.keys(template.parametersSchema).length > 0 && (
                        <div className="mt-1">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {Object.keys(template.parametersSchema).length} parameter{Object.keys(template.parametersSchema).length !== 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {template.category}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {template.isPublic ? (
                      <span className="inline-flex items-center text-green-600">
                        <Globe className="h-4 w-4 mr-1" />
                        Public
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-gray-600">
                        <Lock className="h-4 w-4 mr-1" />
                        Private
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {template.usageCount} times
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDate(template.createdAt)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2 action-buttons">
                      <button
                        onClick={() => handleDuplicate(template)}
                        className="text-gray-400 hover:text-gray-600"
                        title="Duplicate template"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      {template.isOwner && (
                        <>
                          <button
                            onClick={() => handleEdit(template)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Edit template"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(template.templateId)}
                            className="text-red-600 hover:text-red-800"
                            title="Delete template"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
                {isExpanded && (
                  <tr className="bg-gray-50 border-t-0">
                    <td colSpan={7} className="px-6 py-6">
                      <div className="space-y-6">
                        {/* SQL Query Section */}
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-medium text-gray-900">SQL Query</h4>
                            <button
                              onClick={() => handleCopySQL(template.sqlTemplate)}
                              className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
                            >
                              <Copy className="h-4 w-4 mr-1" />
                              Copy SQL
                            </button>
                          </div>
                          <SQLEditor
                            value={template.sqlTemplate}
                            onChange={() => {}}
                            height="300px"
                            readOnly
                          />
                          <div className="mt-2 text-sm text-gray-500">
                            {template.sqlTemplate.split('\n').length} lines • {template.sqlTemplate.length} characters
                          </div>
                        </div>

                        {/* Parameters Section */}
                        {Object.keys(template.parametersSchema).length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Parameters</h4>
                            <div className="bg-white rounded-lg border border-gray-200 p-4">
                              <div className="space-y-3">
                                {Object.entries(template.parametersSchema).map(([key, schema]: [string, any]) => (
                                  <div key={key} className="flex items-start">
                                    <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                                      {`{{${key}}}`}
                                    </code>
                                    <div className="ml-4 flex-1">
                                      <div className="text-sm text-gray-700">
                                        Type: <span className="font-medium">{schema.type || 'string'}</span>
                                      </div>
                                      {schema.description && (
                                        <div className="text-sm text-gray-500 mt-1">{schema.description}</div>
                                      )}
                                      {template.defaultParameters[key] !== undefined && (
                                        <div className="text-sm text-gray-500 mt-1">
                                          Default: <code className="bg-gray-100 px-1 rounded">
                                            {JSON.stringify(template.defaultParameters[key])}
                                          </code>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Metadata Section */}
                        <div className="grid grid-cols-2 gap-6">
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Template Information</h4>
                            <dl className="space-y-2">
                              <div>
                                <dt className="text-sm text-gray-500">Template ID</dt>
                                <dd className="text-sm font-mono text-gray-900">{template.templateId}</dd>
                              </div>
                              <div>
                                <dt className="text-sm text-gray-500">Created</dt>
                                <dd className="text-sm text-gray-900">{formatDate(template.createdAt)}</dd>
                              </div>
                              <div>
                                <dt className="text-sm text-gray-500">Last Updated</dt>
                                <dd className="text-sm text-gray-900">{formatDate(template.updatedAt)}</dd>
                              </div>
                              <div>
                                <dt className="text-sm text-gray-500">Usage Count</dt>
                                <dd className="text-sm text-gray-900">{template.usageCount} times</dd>
                              </div>
                            </dl>
                          </div>
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Actions</h4>
                            <div className="space-y-2">
                              <button
                                onClick={() => handleEdit(template)}
                                className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Edit2 className="h-4 w-4 mr-2" />
                                Edit Template
                              </button>
                              <button
                                onClick={() => handleDuplicate(template)}
                                className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                              >
                                <Copy className="h-4 w-4 mr-2" />
                                Duplicate Template
                              </button>
                              {template.isOwner && (
                                <button
                                  onClick={() => handleDelete(template.templateId)}
                                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete Template
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
              );
            })}
            </tbody>
          </table>
          
          {templates.length === 0 && (
            <div className="text-center py-12">
              <Code className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No templates</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating a new query template.
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Template
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <QueryTemplateModal
          template={selectedTemplate}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedTemplate(null);
          }}
          onSuccess={() => {
            setIsModalOpen(false);
            setSelectedTemplate(null);
            queryClient.invalidateQueries({ queryKey: ['query-templates'] });
          }}
        />
      )}
    </div>
  );
}