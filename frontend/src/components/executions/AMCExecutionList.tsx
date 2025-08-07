import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { amcExecutionService } from '../../services/amcExecutionService';
import type { AMCExecution } from '../../types/amcExecution';
import AMCExecutionDetail from './AMCExecutionDetail';

interface Props {
  instanceId: string;
}

export default function AMCExecutionList({ instanceId }: Props) {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['amc-executions', instanceId],
    queryFn: () => amcExecutionService.listExecutions(instanceId),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: !!instanceId
  });

  const getStatusIcon = (status: AMCExecution['status']) => {
    switch (status) {
      case 'SUCCEEDED':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'FAILED':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'CANCELLED':
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
      case 'RUNNING':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'PENDING':
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status: AMCExecution['status']) => {
    switch (status) {
      case 'SUCCEEDED':
        return 'Completed';
      case 'FAILED':
        return 'Failed';
      case 'CANCELLED':
        return 'Cancelled';
      case 'RUNNING':
        return 'Running';
      case 'PENDING':
      default:
        return 'Pending';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getQueryType = (sqlQuery?: string) => {
    if (!sqlQuery) return null;
    const query = sqlQuery.toLowerCase();
    if (query.includes('conversion') || query.includes('path')) return 'Attribution';
    if (query.includes('campaign')) return 'Campaign';
    if (query.includes('audience') || query.includes('segment')) return 'Audience';
    if (query.includes('overlap')) return 'Overlap';
    if (query.includes('performance')) return 'Performance';
    return 'Analysis';
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-sm text-red-600">Failed to load AMC executions</p>
      </div>
    );
  }

  const executions = data?.executions || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">AMC Execution History</h3>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </button>
      </div>

      {executions.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-8 text-center">
          <p className="text-gray-500">No executions found for this instance</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {executions.map((execution) => (
              <li key={execution.workflowExecutionId}>
                <button
                  onClick={() => setSelectedExecutionId(execution.workflowExecutionId)}
                  className="w-full px-4 py-4 sm:px-6 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      {getStatusIcon(execution.status)}
                      <div className="ml-4 text-left flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-gray-900">
                            {execution.workflowName || 'Ad Hoc Query'}
                          </p>
                          {execution.sqlQuery && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {getQueryType(execution.sqlQuery)}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          ID: {execution.workflowExecutionId}
                        </p>
                        {execution.workflowDescription && (
                          <p className="text-xs text-gray-600 mt-1 line-clamp-1">
                            {execution.workflowDescription}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className="text-right mr-4">
                        <p className="text-sm text-gray-900">
                          {getStatusText(execution.status)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {execution.createdAt ? 
                            `Created: ${formatDate(execution.createdAt)}` :
                            `Started: ${formatDate(execution.startTime)}`
                          }
                        </p>
                        {execution.completedAt && (
                          <p className="text-xs text-gray-500">
                            Completed: {formatDate(execution.completedAt)}
                          </p>
                        )}
                        {execution.durationSeconds && (
                          <p className="text-xs text-gray-600 font-medium">
                            Duration: {formatDuration(execution.durationSeconds)}
                          </p>
                        )}
                        {execution.rowCount !== undefined && execution.rowCount !== null && (
                          <p className="text-xs text-gray-600">
                            Rows: {execution.rowCount.toLocaleString()}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 text-left">
                    {execution.triggeredBy && (
                      <span>Triggered by: {execution.triggeredBy}</span>
                    )}
                    {execution.executionParameters && Object.keys(execution.executionParameters).length > 0 && (
                      <span>Parameters: {Object.keys(execution.executionParameters).length}</span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {selectedExecutionId && (
        <AMCExecutionDetail
          instanceId={instanceId}
          executionId={selectedExecutionId}
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
        />
      )}
    </div>
  );
}