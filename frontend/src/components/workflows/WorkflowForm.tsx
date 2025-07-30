import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Save, Play, Calendar } from 'lucide-react';
import { toast } from 'react-hot-toast';
import QueryEditor from './QueryEditor';
import api from '../../services/api';

interface WorkflowFormProps {
  onClose: () => void;
  workflowId?: string;
  templateId?: string;
}

interface Instance {
  id: string;
  instanceId: string;
  instanceName: string;
  accountName: string;
  isActive: boolean;
}

interface QueryTemplate {
  template_id: string;
  name: string;
  description: string;
  sql_template: string;
  default_parameters: any;
  tags: string[];
}

export default function WorkflowForm({ onClose, workflowId, templateId }: WorkflowFormProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    instance_id: '',
    sql_query: '',
    parameters: {},
    tags: [] as string[],
  });
  const [detectedParams, setDetectedParams] = useState<string[]>([]);

  // Fetch instances
  const { data: instances } = useQuery<Instance[]>({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances/');
      return response.data;
    },
  });

  // Fetch templates
  const { data: templates } = useQuery<QueryTemplate[]>({
    queryKey: ['query-templates'],
    queryFn: async () => {
      const response = await api.get('/queries/templates/');
      return response.data;
    },
  });

  // Fetch existing workflow if editing
  const { data: workflow } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}`);
      return response.data;
    },
    enabled: !!workflowId,
  });

  useEffect(() => {
    if (workflow) {
      setFormData({
        name: workflow.name,
        description: workflow.description || '',
        instance_id: workflow.instance?.id || '',
        sql_query: workflow.sql_query,
        parameters: workflow.parameters || {},
        tags: workflow.tags || [],
      });
    } else if (templateId && templates) {
      const template = templates.find(t => t.template_id === templateId);
      if (template) {
        setFormData(prev => ({
          ...prev,
          name: template.name,
          description: template.description || '',
          sql_query: template.sql_template,
          parameters: template.default_parameters || {},
          tags: template.tags || [],
        }));
      }
    }
  }, [workflow, templateId, templates]);

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post('/workflows/', data);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow created successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create workflow');
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.put(`/workflows/${workflowId}`, data);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow updated successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update workflow');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || !formData.instance_id || !formData.sql_query) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Prepare parameters based on detected params
    const defaultParams: any = {};
    detectedParams.forEach(param => {
      if (!formData.parameters[param]) {
        // Set default values based on parameter name
        if (param.includes('date') || param.includes('start') || param.includes('end')) {
          defaultParams[param] = new Date().toISOString().split('T')[0];
        } else if (param.includes('days') || param.includes('window')) {
          defaultParams[param] = 30;
        } else {
          defaultParams[param] = '';
        }
      }
    });

    const finalData = {
      ...formData,
      parameters: { ...defaultParams, ...formData.parameters },
    };

    if (workflowId) {
      updateMutation.mutate(finalData);
    } else {
      createMutation.mutate(finalData);
    }
  };

  const handleTagAdd = (tag: string) => {
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({ ...prev, tags: [...prev.tags, tag] }));
    }
  };

  const handleTagRemove = (tag: string) => {
    setFormData(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tag) }));
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            {workflowId ? 'Edit Workflow' : 'Create New Workflow'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Basic Information */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Workflow Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="e.g., Customer Journey Analysis"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Describe what this workflow does..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                AMC Instance *
              </label>
              <select
                value={formData.instance_id}
                onChange={(e) => setFormData(prev => ({ ...prev, instance_id: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                required
              >
                <option value="">Select an instance</option>
                {instances?.filter(i => i.isActive).map(instance => (
                  <option key={instance.instanceId} value={instance.instanceId}>
                    {instance.instanceName} ({instance.accountName})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* SQL Query Editor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              SQL Query *
            </label>
            <QueryEditor
              value={formData.sql_query}
              onChange={(value) => setFormData(prev => ({ ...prev, sql_query: value }))}
              onParametersDetected={setDetectedParams}
              height="400px"
            />
            {detectedParams.length > 0 && (
              <div className="mt-2 text-sm text-gray-600">
                Detected parameters: {detectedParams.map(p => (
                  <span key={p} className="inline-flex items-center px-2 py-1 mr-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                    {`{{${p}}}`}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {formData.tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleTagRemove(tag)}
                    className="ml-1 text-indigo-600 hover:text-indigo-900"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <input
              type="text"
              placeholder="Add tag and press Enter"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleTagAdd((e.target as HTMLInputElement).value);
                  (e.target as HTMLInputElement).value = '';
                }
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>
        </form>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={createMutation.isPending || updateMutation.isPending}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4 mr-2" />
            {workflowId ? 'Update' : 'Create'} Workflow
          </button>
        </div>
      </div>
    </div>
  );
}