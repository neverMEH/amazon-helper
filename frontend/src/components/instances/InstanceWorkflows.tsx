import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Clock, PlayCircle, Plus, FileText, Edit2, Trash2, Eye, Tag } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import ExecutionModal from '../workflows/ExecutionModal';
import AMCSyncStatus from '../workflows/AMCSyncStatus';

interface Query {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  status: string;
  sqlQuery: string;
  parameters?: any;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
  lastExecuted?: string;
  executionCount?: number;
  amcWorkflowId?: string;
  isSyncedToAmc?: boolean;
  amcSyncStatus?: string;
  instance?: {
    id: string;
    name: string;
  };
}

interface InstanceWorkflowsProps {
  instanceId: string;
}

export default function InstanceWorkflows({ instanceId }: InstanceWorkflowsProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [executionModal, setExecutionModal] = useState<{ isOpen: boolean; workflowId: string | null }>({
    isOpen: false,
    workflowId: null,
  });
  
  // Fetch all queries and filter by instance
  const { data: allQueries, isLoading } = useQuery<Query[]>({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows');
      return response.data;
    },
  });

  // Filter queries for this specific instance
  const queries = allQueries?.filter(q => 
    q.instance?.id === instanceId
  ) || [];

  // Delete query mutation
  const deleteMutation = useMutation({
    mutationFn: async (queryId: string) => {
      await api.delete(`/workflows/${queryId}`);
    },
    onSuccess: () => {
      toast.success('Query deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: () => {
      toast.error('Failed to delete query');
    }
  });

  const handleExecute = (queryId: string) => {
    setExecutionModal({ isOpen: true, workflowId: queryId });
  };

  const handleDelete = (queryId: string, queryName: string) => {
    if (confirm(`Are you sure you want to delete "${queryName}"?`)) {
      deleteMutation.mutate(queryId);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading workflows...</div>
      </div>
    );
  }

  if (queries.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows for this instance</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new workflow for this instance.
          </p>
          <div className="mt-6 flex justify-center space-x-4">
            <button 
              onClick={() => navigate('/query-builder/new', { state: { instanceId } })}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Workflow
            </button>
            <button 
              onClick={() => navigate('/query-library')}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <FileText className="h-4 w-4 mr-2" />
              Browse Library
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Workflows</h3>
          <div className="flex space-x-2">
            <button 
              onClick={() => navigate('/query-builder/new', { state: { instanceId } })}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4 mr-1" />
              Create Workflow
            </button>
            <button 
              onClick={() => navigate('/query-library')}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <FileText className="h-4 w-4 mr-1" />
              Workflow Library
            </button>
          </div>
        </div>
        <div className="space-y-4">
          {queries.map((query) => (
            <div
              key={query.workflowId}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-900">{query.name}</h3>
                  {query.description && (
                    <p className="mt-1 text-sm text-gray-500">{query.description}</p>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      Created {new Date(query.createdAt).toLocaleDateString()}
                    </span>
                    {query.lastExecuted && (
                      <span className="flex items-center">
                        <PlayCircle className="h-3 w-3 mr-1" />
                        Last run {new Date(query.lastExecuted).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {query.tags && query.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {query.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded"
                        >
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="ml-4 flex items-center space-x-2">
                  <button
                    onClick={() => navigate(`/my-queries/${query.workflowId}`)}
                    className="p-1.5 text-gray-500 hover:text-indigo-600 hover:bg-gray-100 rounded transition-colors"
                    title="View Details"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleExecute(query.workflowId)}
                    className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                    title="Execute Workflow"
                  >
                    <PlayCircle className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => navigate(`/query-builder/edit/${query.workflowId}`)}
                    className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Edit Workflow"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(query.workflowId, query.name)}
                    className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete Query"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              
              {/* AMC Sync Status */}
              {query.workflowId && (
                <div className="mt-4 border-t pt-4">
                  <AMCSyncStatus 
                    workflowId={query.workflowId}
                    initialStatus={{
                      amcWorkflowId: query.amcWorkflowId,
                      isSyncedToAmc: query.isSyncedToAmc,
                      amcSyncStatus: query.amcSyncStatus
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Execution Modal */}
      {executionModal.workflowId && (
        <ExecutionModal
          isOpen={executionModal.isOpen}
          onClose={() => setExecutionModal({ isOpen: false, workflowId: null })}
          workflowId={executionModal.workflowId}
          instanceId={instanceId}
        />
      )}
    </>
  );
}