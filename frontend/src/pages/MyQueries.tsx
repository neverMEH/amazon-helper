import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
  Search, 
  Play, 
  Edit2, 
  Trash2, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Calendar,
  Cloud,
  CloudOff
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../services/api';
import { formatDistanceToNow } from 'date-fns';

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  status: string;
  instance?: {
    id: string;
    instanceId: string;
    instanceName: string;
  };
  parameters?: any;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
  lastExecutedAt?: string;
  executionCount?: number;
  amcWorkflowId?: string;
  isSyncedToAmc?: boolean;
  amcSyncStatus?: string;
}

export default function MyQueries() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string | null>(null);

  // Fetch workflows
  const { data: workflows = [], isLoading } = useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows');
      return response.data;
    }
  });

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      await api.delete(`/workflows/${workflowId}`);
    },
    onSuccess: () => {
      toast.success('Query deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: () => {
      toast.error('Failed to delete query');
    }
  });

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      const response = await api.post(`/workflows/${workflowId}/execute`);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Query execution started');
      // Navigate to execution details if needed
    },
    onError: () => {
      toast.error('Failed to execute query');
    }
  });

  // Filter workflows
  const filteredWorkflows = workflows.filter(workflow => {
    if (searchQuery && !workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !workflow.description?.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (filterStatus && workflow.status !== filterStatus) {
      return false;
    }
    return true;
  });

  const handleEdit = (workflowId: string) => {
    navigate(`/query-builder/edit/${workflowId}`);
  };

  const handleExecute = async (workflowId: string) => {
    await executeMutation.mutateAsync(workflowId);
  };

  const handleDelete = async (workflowId: string) => {
    if (confirm('Are you sure you want to delete this query?')) {
      await deleteMutation.mutateAsync(workflowId);
    }
  };

  const handleSchedule = () => {
    // TODO: Open schedule modal
    toast('Schedule feature coming soon', {
      icon: 'ℹ️'
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'draft':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'archived':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getSyncIcon = (workflow: Workflow) => {
    if (workflow.isSyncedToAmc) {
      return (
        <span title="Synced to AMC">
          <Cloud className="h-4 w-4 text-blue-500" />
        </span>
      );
    }
    return (
      <span title="Not synced to AMC">
        <CloudOff className="h-4 w-4 text-gray-400" />
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Queries</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage and execute your saved AMC queries
            </p>
          </div>
          <button
            onClick={() => navigate('/query-builder/new')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Query
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search queries..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilterStatus(null)}
            className={`px-3 py-2 text-sm rounded-md ${
              !filterStatus ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterStatus('active')}
            className={`px-3 py-2 text-sm rounded-md ${
              filterStatus === 'active' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilterStatus('draft')}
            className={`px-3 py-2 text-sm rounded-md ${
              filterStatus === 'draft' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Draft
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading queries...</div>
        </div>
      )}

      {/* Queries Table */}
      {!isLoading && filteredWorkflows.length > 0 && (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Query Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Run
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sync
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredWorkflows.map((workflow) => (
                <tr key={workflow.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {workflow.name}
                      </div>
                      {workflow.description && (
                        <div className="text-xs text-gray-500 truncate max-w-xs">
                          {workflow.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {workflow.instance?.instanceName || '-'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {workflow.instance?.instanceId}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(workflow.status)}
                      <span className="ml-2 text-sm text-gray-900 capitalize">
                        {workflow.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.lastExecutedAt ? (
                      <div className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatDistanceToNow(new Date(workflow.lastExecutedAt), { addSuffix: true })}
                      </div>
                    ) : (
                      'Never'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getSyncIcon(workflow)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handleExecute(workflow.workflowId)}
                        disabled={executeMutation.isPending}
                        className="text-blue-600 hover:text-blue-900"
                        title="Execute"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(workflow.workflowId)}
                        className="text-gray-600 hover:text-gray-900"
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleSchedule()}
                        className="text-gray-600 hover:text-gray-900"
                        title="Schedule"
                      >
                        <Calendar className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(workflow.workflowId)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-900"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredWorkflows.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No queries found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery
              ? 'Try adjusting your search criteria'
              : 'Get started by creating your first query'}
          </p>
          <div className="mt-6">
            <button
              onClick={() => navigate('/query-builder/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create New Query
            </button>
          </div>
        </div>
      )}
    </div>
  );
}