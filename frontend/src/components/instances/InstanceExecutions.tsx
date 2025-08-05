import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { History, Clock, CheckCircle, XCircle, Loader, AlertCircle, ExternalLink, Play, Settings } from 'lucide-react';
import api from '../../services/api';
import ExecutionDetailModal from '../workflows/ExecutionDetailModal';
import ExecutionModal from '../workflows/ExecutionModal';
import AMCExecutionList from '../executions/AMCExecutionList';

interface Execution {
  execution_id: string;
  status: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  row_count?: number;
  triggered_by: string;
  workflow_name?: string;
  workflow_id?: string;
}

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  isTemplate: boolean;
}

interface InstanceExecutionsProps {
  instanceId: string;
}

export default function InstanceExecutions({ instanceId }: InstanceExecutionsProps) {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<{ workflowId: string; name: string } | null>(null);
  const [activeTab, setActiveTab] = useState<'local' | 'amc'>('local');
  
  // Fetch ALL workflows (including templates) for execution
  const { data: allWorkflows } = useQuery<Workflow[]>({
    queryKey: ['all-workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows');
      return response.data;
    },
  });

  // Fetch executions for ALL workflows, then filter by instance
  // This approach is needed because template workflows can be executed on any instance
  const { data: executions, isLoading } = useQuery<Execution[]>({
    queryKey: ['instance-executions', instanceId],
    queryFn: async () => {
      if (!allWorkflows || allWorkflows.length === 0) return [];
      
      // Fetch executions for each workflow with instance filter
      const allExecutions = await Promise.all(
        allWorkflows.map(async (workflow) => {
          try {
            // Pass instance_id to filter executions by instance
            const response = await api.get(`/workflows/${workflow.workflowId}/executions`, {
              params: { instance_id: instanceId }
            });
            // Add workflow info to each execution
            return response.data.map((exec: Execution) => ({
              ...exec,
              workflow_name: workflow.name,
              workflow_id: workflow.workflowId
            }));
          } catch (error) {
            console.error(`Error fetching executions for workflow ${workflow.workflowId}:`, error);
            return [];
          }
        })
      );
      
      // Flatten and sort by start date (most recent first)
      return allExecutions
        .flat()
        .sort((a, b) => {
          if (!a.started_at || !b.started_at) return 0;
          return new Date(b.started_at).getTime() - new Date(a.started_at).getTime();
        });
    },
    enabled: !!allWorkflows && allWorkflows.length > 0,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <Loader className="h-8 w-8 animate-spin mx-auto text-gray-400" />
          <p className="mt-2 text-sm text-gray-500">Loading execution history...</p>
        </div>
      </div>
    );
  }

  const hasWorkflows = allWorkflows && allWorkflows.length > 0;
  const hasExecutions = executions && executions.length > 0;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Execution History</h2>
          <p className="mt-1 text-sm text-gray-500">
            View all workflow executions for this AMC instance
          </p>
        </div>
        {hasWorkflows && activeTab === 'local' && (
          <button
            onClick={() => {
              // Pick the first workflow as default for execution
              const firstWorkflow = allWorkflows[0];
              setSelectedWorkflow({
                workflowId: firstWorkflow.workflowId,
                name: firstWorkflow.name
              });
            }}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <Play className="h-4 w-4 mr-2" />
            Execute Workflow
          </button>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-4" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('local')}
            className={`${
              activeTab === 'local'
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-gray-500 hover:text-gray-700'
            } px-3 py-2 font-medium text-sm rounded-md`}
          >
            Local Executions
          </button>
          <button
            onClick={() => setActiveTab('amc')}
            className={`${
              activeTab === 'amc'
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-gray-500 hover:text-gray-700'
            } px-3 py-2 font-medium text-sm rounded-md`}
          >
            AMC Executions
          </button>
        </nav>
      </div>

      {activeTab === 'amc' ? (
        <AMCExecutionList instanceId={instanceId} />
      ) : !hasWorkflows ? (
        <div className="text-center py-8 text-gray-500">
          <Settings className="h-12 w-12 mx-auto mb-2 text-gray-400" />
          <p>No workflows configured for this instance</p>
          <p className="text-sm mt-1">Create a workflow to start executing queries</p>
        </div>
      ) : !hasExecutions ? (
        <div className="text-center py-8 text-gray-500">
          <History className="h-12 w-12 mx-auto mb-2 text-gray-400" />
          <p>No executions yet</p>
          <p className="text-sm mt-1">Execute a workflow to see the history</p>
        </div>
      ) : (
        <div className="overflow-hidden bg-white shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table className="min-w-full divide-y divide-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Workflow
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Execution ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rows
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Triggered By
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {executions.map((execution) => (
                <tr 
                  key={execution.execution_id} 
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedExecutionId(execution.execution_id)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(execution.status)}
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                        {execution.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {execution.workflow_name || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {execution.execution_id.slice(0, 8)}...
                      </code>
                      <ExternalLink className="h-3 w-3 ml-2 text-gray-400" />
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {execution.started_at ? new Date(execution.started_at).toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDuration(execution.duration_seconds)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {execution.row_count != null ? execution.row_count.toLocaleString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {execution.triggered_by}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Execution Detail Modal */}
      {selectedExecutionId && (
        <ExecutionDetailModal
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
          executionId={selectedExecutionId}
        />
      )}

      {/* Execution Modal for running new workflows */}
      {selectedWorkflow && (
        <ExecutionModal
          isOpen={!!selectedWorkflow}
          onClose={() => setSelectedWorkflow(null)}
          workflow={selectedWorkflow}
          instanceId={instanceId}
        />
      )}
    </div>
  );
}