import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Save, Play, Copy, Clock, AlertCircle, CheckCircle, Edit2, Code, Settings, History, Zap, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import SQLEditor from '../common/SQLEditor';
import JSONEditor from '../common/JSONEditor';
import ExecutionHistory from './ExecutionHistory';
import ExecutionModal from './ExecutionModal';
import AMCSyncStatus from './AMCSyncStatus';

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  parameters?: Record<string, unknown>;
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

type TabType = 'query' | 'parameters' | 'executions';

export default function WorkflowDetail() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const instanceId = searchParams.get('instanceId') || undefined;
  const location = window.location.pathname;
  const isEditRoute = location.endsWith('/edit');
  const [isEditing, setIsEditing] = useState(isEditRoute);
  const [editForm, setEditForm] = useState<Partial<Workflow>>({});
  const [activeTab, setActiveTab] = useState<TabType>('query');
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [showQuickEditModal, setShowQuickEditModal] = useState(false);
  const [quickEditSQL, setQuickEditSQL] = useState('');
  const [isTestingQuickEdit, setIsTestingQuickEdit] = useState(false);

  const { data: workflow, isLoading, error } = useQuery<Workflow>({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}`);
      return response.data;
    },
  });

  // Update form when workflow data changes
  useEffect(() => {
    if (workflow) {
      setEditForm({
        name: workflow.name,
        description: workflow.description,
        sqlQuery: workflow.sqlQuery,
        parameters: workflow.parameters,
        tags: workflow.tags,
      });
    }
  }, [workflow]);

  const updateMutation = useMutation({
    mutationFn: async (data: Partial<Workflow>) => {
      // Map to snake_case for the API
      const payload = {
        name: data.name,
        description: data.description,
        sql_query: data.sqlQuery,
        parameters: data.parameters,
        tags: data.tags,
      };
      const response = await api.put(`/workflows/${workflowId}`, payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Workflow updated successfully');
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: unknown) => {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? `Failed to update workflow: ${(error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Unknown error'}`
        : 'Failed to update workflow';
      toast.error(errorMessage);
    },
  });

  const handleExecute = () => {
    setShowExecutionModal(true);
  };

  const handleSave = () => {
    updateMutation.mutate(editForm);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(workflow?.sqlQuery || '');
    toast.success('SQL query copied to clipboard');
  };

  // Quick Edit test execution mutation
  const testExecutionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/workflows/execute', {
        workflow_id: workflowId,
        instance_id: workflow?.instance?.id || instanceId,
        sql_query_override: quickEditSQL,
        execution_parameters: workflow?.parameters || {}
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Test execution started successfully');
      setIsTestingQuickEdit(false);
      // Could open execution modal to show results
      setShowExecutionModal(true);
    },
    onError: (error: unknown) => {
      const errorMessage = error && typeof error === 'object' && 'response' in error
        ? `Test execution failed: ${(error as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Unknown error'}`
        : 'Test execution failed';
      toast.error(errorMessage);
      setIsTestingQuickEdit(false);
    }
  });

  const handleQuickEditSave = async () => {
    try {
      await updateMutation.mutateAsync({ ...workflow, sqlQuery: quickEditSQL });
      setShowQuickEditModal(false);
      toast.success('Query updated successfully');
    } catch {
      // Error handled by mutation
    }
  };

  const handleQuickEditTest = () => {
    setIsTestingQuickEdit(true);
    testExecutionMutation.mutate();
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

  if (error) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-red-500">
            Error loading workflow: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
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
                    onClick={() => {
                      setQuickEditSQL(workflow.sqlQuery);
                      setShowQuickEditModal(true);
                    }}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Quick Edit
                  </button>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Edit2 className="h-4 w-4 mr-2" />
                    Full Edit
                  </button>
                  <button
                    onClick={handleExecute}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Play className="h-4 w-4 mr-2" />
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

          {/* AMC Sync Status */}
          {!isEditing && workflow.instance && (
            <AMCSyncStatus workflowId={workflow.workflowId} />
          )}

          {/* Tabs */}
          <div>
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('query')}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'query'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Code className="h-4 w-4 mr-2" />
                  SQL Query
                </button>
                <button
                  onClick={() => setActiveTab('parameters')}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'parameters'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Parameters
                </button>
                <button
                  onClick={() => setActiveTab('executions')}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'executions'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <History className="h-4 w-4 mr-2" />
                  Executions
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="mt-4">
              {activeTab === 'query' && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-gray-700">SQL Query</h3>
                    {!isEditing && (
                      <button
                        onClick={handleCopy}
                        className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
                      >
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </button>
                    )}
                  </div>
                  {isEditing ? (
                    <div>
                      <SQLEditor
                        value={editForm.sqlQuery || ''}
                        onChange={(value) => setEditForm({ ...editForm, sqlQuery: value })}
                        height="500px"
                      />
                    </div>
                  ) : (
                    <div>
                      <SQLEditor
                        value={workflow.sqlQuery || ''}
                        onChange={() => {}}
                        height="500px"
                        readOnly
                      />
                    </div>
                  )}
                  {workflow.sqlQuery && (
                    <div className="mt-2 text-sm text-gray-500">
                      {workflow.sqlQuery.split('\n').length} lines • {workflow.sqlQuery.length} characters
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'parameters' && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Parameters</h3>
                  <p className="text-xs text-gray-500 mb-4">
                    Define default parameters for your query. Use {'{{parameter_name}}'} in your SQL to reference them.
                  </p>
                  {isEditing ? (
                    <JSONEditor
                      value={editForm.parameters || {}}
                      onChange={(value) => setEditForm({ ...editForm, parameters: value })}
                      height="300px"
                    />
                  ) : (
                    <JSONEditor
                      value={workflow.parameters || {}}
                      onChange={() => {}}
                      height="300px"
                      readOnly
                    />
                  )}
                </div>
              )}

              {activeTab === 'executions' && (
                <ExecutionHistory workflowId={workflowId!} instanceId={instanceId} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Execution Modal */}
      {workflow && (
        <ExecutionModal
          isOpen={showExecutionModal}
          onClose={() => setShowExecutionModal(false)}
          workflow={workflow}
          instanceId={instanceId}
        />
      )}

      {/* Quick Edit Modal */}
      {showQuickEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-[90vw] max-w-6xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
              <div>
                <h2 className="text-xl font-semibold">Quick SQL Edit</h2>
                <p className="text-sm text-gray-600 mt-1">Make quick changes to your SQL query and test them immediately</p>
              </div>
              <button
                onClick={() => setShowQuickEditModal(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="flex-1 p-6 min-h-0 overflow-hidden">
              <div className="h-full border border-gray-200 rounded-lg">
                <SQLEditor
                  value={quickEditSQL}
                  onChange={setQuickEditSQL}
                  height="400px"
                />
              </div>
            </div>

            <div className="px-6 pb-6 flex-shrink-0">
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Instance:</span> {workflow?.instance?.name || 'Not configured'}
                </div>
                
                <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setShowQuickEditModal(false)}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleQuickEditTest}
                      disabled={isTestingQuickEdit || !workflow?.instance}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                    >
                      {isTestingQuickEdit ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-700 mr-2"></div>
                          Testing...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Test & Execute
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleQuickEditSave}
                      disabled={updateMutation.isPending}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
                    >
                      {updateMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          Save Changes
                        </>
                      )}
                    </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}