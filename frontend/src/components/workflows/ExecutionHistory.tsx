import { useQuery } from '@tanstack/react-query';
import { History, Clock, CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-react';
import api from '../../services/api';

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
  amc_execution_id?: string;
}

interface ExecutionHistoryProps {
  workflowId: string;
}

export default function ExecutionHistory({ workflowId }: ExecutionHistoryProps) {
  const { data: executions, isLoading } = useQuery<Execution[]>({
    queryKey: ['workflow-executions', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}/executions`);
      return response.data;
    },
    // Refetch every 10 seconds to check for updates
    refetchInterval: 10000,
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
      <div className="text-center py-8">
        <Loader className="h-8 w-8 animate-spin mx-auto text-gray-400" />
        <p className="mt-2 text-sm text-gray-500">Loading execution history...</p>
      </div>
    );
  }

  if (!executions || executions.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <History className="h-12 w-12 mx-auto mb-2 text-gray-400" />
        <p>No executions yet</p>
        <p className="text-sm mt-1">Execute this workflow to see the history</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-4">Execution History</h3>
      <div className="overflow-hidden bg-white shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
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
              <tr key={execution.execution_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(execution.status)}
                    <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                      {execution.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {execution.execution_id.slice(0, 8)}...
                  </code>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {execution.started_at ? new Date(execution.started_at).toLocaleString() : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDuration(execution.duration_seconds)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {execution.row_count?.toLocaleString() || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {execution.triggered_by}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {executions.some(e => e.error_message) && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Error Details</h4>
          {executions.filter(e => e.error_message).map((execution) => (
            <div key={execution.execution_id} className="bg-red-50 border border-red-200 rounded-md p-3 mb-2">
              <p className="text-sm text-red-800">
                <strong>Execution {execution.execution_id.slice(0, 8)}:</strong> {execution.error_message}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}