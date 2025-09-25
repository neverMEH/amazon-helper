import { useState, useMemo } from 'react';
import { Search, Filter, ChevronRight, Clock, CheckCircle, XCircle, AlertCircle, Play, Database, Calendar, User } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';

interface Execution {
  workflowExecutionId: string;
  workflowId: string;
  workflowName: string;
  status: string;
  startTime: string;
  endTime?: string;
  sqlQuery?: string;
  triggeredBy: string;
  amcExecutionId?: string;
  rowCount?: number;
  errorMessage?: string;
  instanceInfo?: {
    id: string;
    name: string;
  };
  isStoredLocally: boolean;
  execution_id?: string; // Add this for compatibility
  instance_id?: string; // Add this for compatibility
}

interface ExecutionsGridProps {
  onSelect?: (execution: Execution) => void;
}

const statusIcons: Record<string, any> = {
  SUCCEEDED: CheckCircle,
  COMPLETED: CheckCircle,
  FAILED: XCircle,
  RUNNING: Play,
  PENDING: Clock,
  CANCELLED: XCircle,
};

const statusColors: Record<string, string> = {
  SUCCEEDED: 'bg-green-100 text-green-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  RUNNING: 'bg-blue-100 text-blue-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  CANCELLED: 'bg-gray-100 text-gray-800',
};

export default function ExecutionsGrid({ onSelect }: ExecutionsGridProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedInstance, setSelectedInstance] = useState<string>('');

  // Fetch all executions
  const { data: executionsData, isLoading, error, refetch } = useQuery({
    queryKey: ['all-executions'],
    queryFn: async () => {
      const response = await api.get('/amc-executions/all/stored', {
        params: { limit: 100 }
      });
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const executions: Execution[] = executionsData?.executions || [];

  // Extract unique values for filters
  const statuses = useMemo(() => {
    const statusSet = new Set(executions.map(e => e.status).filter(Boolean));
    return Array.from(statusSet).sort();
  }, [executions]);

  const instances = useMemo(() => {
    const instanceSet = new Set(
      executions
        .map(e => e.instanceInfo?.name)
        .filter(Boolean)
    );
    return Array.from(instanceSet).sort();
  }, [executions]);

  // Filter executions
  const filteredExecutions = useMemo(() => {
    return executions.filter(execution => {
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        const matchesSearch =
          execution.workflowName.toLowerCase().includes(search) ||
          execution.workflowExecutionId.toLowerCase().includes(search) ||
          execution.instanceInfo?.name.toLowerCase().includes(search);

        if (!matchesSearch) return false;
      }

      // Status filter
      if (selectedStatus && execution.status !== selectedStatus) {
        return false;
      }

      // Instance filter
      if (selectedInstance && execution.instanceInfo?.name !== selectedInstance) {
        return false;
      }

      return true;
    });
  }, [executions, searchTerm, selectedStatus, selectedInstance]);

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedStatus('');
    setSelectedInstance('');
  };

  const hasActiveFilters = searchTerm || selectedStatus || selectedInstance;

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getDuration = (startTime: string, endTime?: string) => {
    if (!startTime) return 'N/A';
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) return `${durationSeconds}s`;
    if (durationSeconds < 3600) return `${Math.floor(durationSeconds / 60)}m ${durationSeconds % 60}s`;
    return `${Math.floor(durationSeconds / 3600)}h ${Math.floor((durationSeconds % 3600) / 60)}m`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading executions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Error loading executions: {(error as Error).message}</p>
        <button
          onClick={() => refetch()}
          className="mt-2 text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Search */}
          <div className="lg:col-span-2">
            <label htmlFor="search" className="sr-only">Search executions</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                id="search"
                placeholder="Search executions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label htmlFor="status" className="sr-only">Status</label>
            <select
              id="status"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              {statuses.map(status => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          {/* Instance Filter */}
          <div>
            <label htmlFor="instance" className="sr-only">Instance</label>
            <select
              id="instance"
              value={selectedInstance}
              onChange={(e) => setSelectedInstance(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Instances</option>
              {instances.map(instance => (
                <option key={instance} value={instance}>
                  {instance}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active filters indicator */}
        {hasActiveFilters && (
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {filteredExecutions.length} of {executions.length} executions
            </span>
            <button
              onClick={clearFilters}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {/* Executions Grid */}
      {filteredExecutions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Filter className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No executions found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {executions.length === 0 
              ? "No executions have been run yet. Create a report to see executions here."
              : "Try adjusting your search or filters"
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filteredExecutions.map((execution) => {
            const StatusIcon = statusIcons[execution.status] || AlertCircle;
            const statusColor = statusColors[execution.status] || 'bg-gray-100 text-gray-800';

            return (
              <div
                key={execution.workflowExecutionId}
                role="button"
                tabIndex={0}
                onClick={() => onSelect?.(execution)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect?.(execution);
                  }
                }}
                className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-4 border border-gray-200
                         hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-shrink-0">
                    <Database className="h-8 w-8 text-indigo-600" />
                  </div>
                  <div className="flex items-center space-x-2">
                    <StatusIcon className="h-4 w-4 text-gray-400" />
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-gray-900 mb-1 line-clamp-2">
                  {execution.workflowName || 'Unnamed Execution'}
                </h3>

                <div className="space-y-2 mb-3">
                  <div className="flex items-center text-xs text-gray-500">
                    <Calendar className="h-3 w-3 mr-1" />
                    {formatDate(execution.startTime)}
                  </div>
                  
                  {execution.instanceInfo && (
                    <div className="flex items-center text-xs text-gray-500">
                      <User className="h-3 w-3 mr-1" />
                      {execution.instanceInfo.name}
                    </div>
                  )}

                  <div className="flex items-center text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    {getDuration(execution.startTime, execution.endTime)}
                  </div>
                </div>

                <div className="flex flex-wrap gap-1">
                  {/* Status Badge */}
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusColor}`}>
                    {execution.status}
                  </span>

                  {/* Trigger Badge */}
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {execution.triggeredBy}
                  </span>

                  {/* Row Count */}
                  {execution.rowCount && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                      {execution.rowCount.toLocaleString()} rows
                    </span>
                  )}
                </div>

                {/* Error Message */}
                {execution.errorMessage && (
                  <div className="mt-2 text-xs text-red-600 line-clamp-2">
                    {execution.errorMessage}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
