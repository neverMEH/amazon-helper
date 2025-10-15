/**
 * Instance Templates List Component
 *
 * Displays and manages SQL templates for a specific AMC instance.
 * Provides CRUD operations and "Use Template" functionality.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  FileText,
  Edit2,
  Trash2,
  PlayCircle,
  Tag,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { instanceTemplateService } from '../../services/instanceTemplateService';
import InstanceTemplateEditor from './InstanceTemplateEditor';
import type { InstanceTemplate } from '../../types/instanceTemplate';

interface InstanceTemplatesProps {
  instanceId: string;
}

export default function InstanceTemplates({ instanceId }: InstanceTemplatesProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showEditor, setShowEditor] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<InstanceTemplate | undefined>();
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Fetch templates
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['instance-templates', instanceId],
    queryFn: () => instanceTemplateService.listTemplates(instanceId),
    enabled: !!instanceId,
  });

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (data: {
      name: string;
      description?: string;
      sql_query: string;
      tags?: string[];
    }) => {
      if (selectedTemplate) {
        return instanceTemplateService.updateTemplate(
          instanceId,
          selectedTemplate.templateId,
          data
        );
      } else {
        return instanceTemplateService.createTemplate(instanceId, data);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instance-templates', instanceId] });
      setShowEditor(false);
      setSelectedTemplate(undefined);
      toast.success(
        selectedTemplate ? 'Template updated successfully' : 'Template created successfully'
      );
    },
    onError: (error: any) => {
      console.error('Failed to save template:', error);
      const errorMessage = error?.response?.data?.detail || 'Failed to save template';
      toast.error(errorMessage);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (templateId: string) =>
      instanceTemplateService.deleteTemplate(instanceId, templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instance-templates', instanceId] });
      setDeleteConfirm(null);
      toast.success('Template deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete template');
    },
  });

  // Handlers
  const handleCreateNew = () => {
    setSelectedTemplate(undefined);
    setShowEditor(true);
  };

  const handleEdit = (template: InstanceTemplate) => {
    setSelectedTemplate(template);
    setShowEditor(true);
  };

  const handleDelete = (templateId: string) => {
    setDeleteConfirm(templateId);
  };

  const confirmDelete = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm);
    }
  };

  const handleUseTemplate = async (template: InstanceTemplate) => {
    try {
      // Increment usage count
      await instanceTemplateService.useTemplate(instanceId, template.templateId);

      // Navigate to query builder with pre-filled SQL
      navigate('/query-builder/new', {
        state: {
          instanceId,
          sqlQuery: template.sqlQuery,
          templateName: template.name,
        },
      });
    } catch (error) {
      console.error('Failed to use template:', error);
      toast.error('Failed to use template');
    }
  };

  const handleSave = async (data: {
    name: string;
    description?: string;
    sql_query: string;
    tags?: string[];
  }) => {
    await saveMutation.mutateAsync(data);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading templates...</div>
      </div>
    );
  }

  // Empty state
  if (templates.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a template to save frequently-used SQL queries.
          </p>
          <div className="mt-6">
            <button
              onClick={handleCreateNew}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Template
            </button>
          </div>
        </div>

        {/* Editor Modal */}
        {showEditor && (
          <InstanceTemplateEditor
            instanceId={instanceId}
            template={selectedTemplate}
            onSave={handleSave}
            onCancel={() => {
              setShowEditor(false);
              setSelectedTemplate(undefined);
            }}
            isLoading={saveMutation.isPending}
          />
        )}
      </div>
    );
  }

  // Template list view
  return (
    <>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Templates</h3>
            <p className="text-sm text-gray-600">
              {templates.length} {templates.length === 1 ? 'template' : 'templates'}
            </p>
          </div>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Template
          </button>
        </div>

        {/* Template Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((template) => (
            <TemplateCard
              key={template.templateId}
              template={template}
              onUse={() => handleUseTemplate(template)}
              onEdit={() => handleEdit(template)}
              onDelete={() => handleDelete(template.templateId)}
            />
          ))}
        </div>
      </div>

      {/* Editor Modal */}
      {showEditor && (
        <InstanceTemplateEditor
          instanceId={instanceId}
          template={selectedTemplate}
          onSave={handleSave}
          onCancel={() => {
            setShowEditor(false);
            setSelectedTemplate(undefined);
          }}
          isLoading={saveMutation.isPending}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <AlertCircle className="h-6 w-6 text-red-600 mr-3" />
              <h3 className="text-lg font-semibold">Delete Template</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this template? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Template Card Component
interface TemplateCardProps {
  template: InstanceTemplate;
  onUse: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function TemplateCard({ template, onUse, onEdit, onDelete }: TemplateCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 flex-1">
          {template.name}
        </h4>
      </div>

      {template.description && (
        <p className="text-xs text-gray-600 mb-3 line-clamp-2">{template.description}</p>
      )}

      {/* Tags */}
      {template.tags && template.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {template.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
            >
              <Tag className="h-3 w-3 mr-1" />
              {tag}
            </span>
          ))}
          {template.tags.length > 3 && (
            <span className="text-xs text-gray-500">+{template.tags.length - 3} more</span>
          )}
        </div>
      )}

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <div className="flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          <span>{template.usageCount || 0} uses</span>
        </div>
        <span>{new Date(template.createdAt).toLocaleDateString()}</span>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onUse}
          className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50"
        >
          <PlayCircle className="h-4 w-4 mr-2" />
          Use Template
        </button>
        <button
          onClick={onEdit}
          className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
          aria-label="Edit template"
        >
          <Edit2 className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          className="p-2 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
          aria-label="Delete template"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
