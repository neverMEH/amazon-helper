import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Play, Copy, Clock, AlertCircle, CheckCircle, Edit2, Code } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  parameters?: any;
  tags?: string[];
  isTemplate?: boolean;
  instance?: {
    id: string;
    name: string;
  };
  createdAt: string;
  lastExecuted?: string;
  status?: string;
}

export default function WorkflowDetail() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Partial<Workflow>>({});
  const [executing, setExecuting] = useState(false);

  const { data: workflow, isLoading } = useQuery<Workflow>({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}/`);
      return response.data;
    },
    onSuccess: (data) => {
      setEditForm({
        name: data.name,
        description: data.description,
        sqlQuery: data.sqlQuery,
        parameters: data.parameters,
        tags: data.tags,
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      const response = await api.put(`/workflows/${workflowId}/`, data);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow updated successfully');
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      toast.error(`Failed to update workflow: ${error.response?.data?.detail || error.message}`);
    },
  });

  const executeMutation = useMutation({
    mutationFn: async (parameters?: any) => {
      const response = await api.post(`/workflows/${workflowId}/execute/`, parameters || {});
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Workflow execution started: ${data.execution_id}`);
      setExecuting(false);
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
    },
    onError: (error: any) => {
      toast.error(`Failed to execute workflow: ${error.response?.data?.detail || error.message}`);
      setExecuting(false);
    },
  });

  const handleSave = () => {
    updateMutation.mutate(editForm);
  };

  const handleExecute = () => {
    setExecuting(true);
    executeMutation.mutate(editForm.parameters || {});
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(workflow?.sqlQuery || '');
    toast.success('SQL query copied to clipboard');
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading workflow...</div>
        </div>
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Workflow not found</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  />
                ) : (
                  workflow.name
                )}
              </h1>
              {workflow.isTemplate && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  Template
                </span>
              )}
              {workflow.status === 'active' ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              )}
            </div>
            <div className="flex items-center space-x-2">
              {!isEditing ? (
                <>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Edit2 className="h-4 w-4 mr-2" />
                    Edit
                  </button>
                  <button
                    onClick={handleExecute}
                    disabled={executing}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
                  >
                    {executing ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Execute
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-6">
          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
            {isEditing ? (
              <textarea
                value={editForm.description || ''}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                rows={3}
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            ) : (
              <p className="text-gray-600">{workflow.description || 'No description provided'}</p>
            )}
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Instance</label>
              <p className="mt-1 text-sm text-gray-900">{workflow.instance?.name || 'No instance assigned'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Executed</label>
              <p className="mt-1 text-sm text-gray-900 flex items-center">
                <Clock className="h-4 w-4 mr-1 text-gray-400" />
                {workflow.lastExecuted ? new Date(workflow.lastExecuted).toLocaleString() : 'Never'}
              </p>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
            {isEditing ? (
              <input
                type="text"
                value={editForm.tags?.join(', ') || ''}
                onChange={(e) => setEditForm({ ...editForm, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                placeholder="Enter tags separated by commas"
                className="w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
              />
            ) : (
              <div className="flex flex-wrap gap-2">
                {workflow.tags && workflow.tags.length > 0 ? (
                  workflow.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {tag}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500 text-sm">No tags</span>
                )}
              </div>
            )}
          </div>

          {/* SQL Query */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">SQL Query</label>
              <button
                onClick={handleCopy}
                className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
              >
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </button>
            </div>
            <div className="relative">
              <Code className="absolute top-3 left-3 h-5 w-5 text-gray-400" />
              {isEditing ? (
                <textarea
                  value={editForm.sqlQuery || ''}
                  onChange={(e) => setEditForm({ ...editForm, sqlQuery: e.target.value })}
                  rows={15}
                  className="w-full pl-10 font-mono text-sm border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  style={{ fontFamily: 'monospace' }}
                />
              ) : (
                <pre className="w-full p-3 pl-10 bg-gray-50 border border-gray-200 rounded-md overflow-x-auto">
                  <code className="text-sm text-gray-800" style={{ fontFamily: 'monospace' }}>
                    {workflow.sqlQuery}
                  </code>
                </pre>
              )}
            </div>
          </div>

          {/* Parameters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Parameters</label>
            {isEditing ? (
              <textarea
                value={JSON.stringify(editForm.parameters || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const params = JSON.parse(e.target.value);
                    setEditForm({ ...editForm, parameters: params });
                  } catch {
                    // Invalid JSON, just update the text
                  }
                }}
                rows={8}
                className="w-full font-mono text-sm border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                style={{ fontFamily: 'monospace' }}
                placeholder="{}"
              />
            ) : (
              <pre className="w-full p-3 bg-gray-50 border border-gray-200 rounded-md overflow-x-auto">
                <code className="text-sm text-gray-800" style={{ fontFamily: 'monospace' }}>
                  {JSON.stringify(workflow.parameters || {}, null, 2)}
                </code>
              </pre>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}