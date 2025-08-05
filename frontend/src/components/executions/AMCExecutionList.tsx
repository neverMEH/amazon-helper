import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon, 
  ExclamationCircleIcon,
  ChevronRightIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
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
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'FAILED':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'CANCELLED':
        return <ExclamationCircleIcon className="h-5 w-5 text-gray-500" />;
      case 'RUNNING':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'PENDING':
      default:
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
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
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
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
          <ArrowPathIcon className="h-4 w-4 mr-1" />
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
                    <div className="flex items-center">
                      {getStatusIcon(execution.status)}
                      <div className="ml-4 text-left">
                        <p className="text-sm font-medium text-gray-900">
                          {execution.workflowName || 'Ad Hoc Query'}
                        </p>
                        <p className="text-xs text-gray-500">
                          ID: {execution.workflowExecutionId}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className="text-right mr-4">
                        <p className="text-sm text-gray-900">
                          {getStatusText(execution.status)}
                        </p>
                        <p className="text-xs text-gray-500">
                          Started: {formatDate(execution.startTime)}
                        </p>
                        {execution.endTime && (
                          <p className="text-xs text-gray-500">
                            Ended: {formatDate(execution.endTime)}
                          </p>
                        )}
                      </div>
                      <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                  {execution.triggeredBy && (
                    <div className="mt-2 text-xs text-gray-500 text-left">
                      Triggered by: {execution.triggeredBy}
                    </div>
                  )}
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