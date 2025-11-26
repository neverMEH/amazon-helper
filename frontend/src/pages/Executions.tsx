import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  RefreshCw,
  Search,
  Filter,
  Server,
  Cloud,
  Loader,
  Database,
  Upload,
  AlertTriangle,
  X,
  Activity
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { amcExecutionService } from '../services/amcExecutionService';
import type { AMCExecution } from '../types/amcExecution';
import AMCExecutionDetail from '../components/executions/AMCExecutionDetail';
import api from '../services/api';

interface InstanceInfo {
  id: string;
  name: string;
  brands?: string[];
}

export default function Executions() {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedInstance, setSelectedInstance] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch all executions
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['amc-executions-all'],
    queryFn: async () => {
      try {
        const response = await api.get('/amc-executions/all/stored', {
          params: { limit: 100 }
        });
        return response.data;
      } catch (error) {
        console.error('Failed to fetch all stored executions:', error);
        return { executions: [] };
      }
    },
  });

  // Smart polling: only poll when there are pending/running executions
  const hasPendingExecutions = useMemo(() => {
    const executions = data?.executions || [];
    return executions.some((exec: any) =>
      ['RUNNING', 'PENDING', 'IN_QUEUE', 'CREATED'].includes(exec.status)
    );
  }, [data?.executions]);

  // Use a separate query for polling
  useQuery({
    queryKey: ['amc-executions-poll'],
    queryFn: () => refetch(),
    refetchInterval: hasPendingExecutions ? 15000 : false,
    enabled: hasPendingExecutions,
  });

  // Extract unique instances for tabs
  const uniqueInstances = useMemo(() => {
    const instanceMap = new Map<string, InstanceInfo>();
    data?.executions?.forEach((exec: any) => {
      const info = exec.instanceInfo;
      if (info?.id) {
        if (!instanceMap.has(info.id)) {
          instanceMap.set(info.id, {
            id: info.id,
            name: info.name || info.id,
            brands: info.brands || [],
          });
        }
      }
    });
    return Array.from(instanceMap.values()).sort((a, b) =>
      a.name.localeCompare(b.name)
    );
  }, [data?.executions]);

  // Filter executions based on search, status, and selected instance
  const filteredExecutions = useMemo(() => {
    let executions = data?.executions || [];

    // Filter by selected instance
    if (selectedInstance) {
      executions = executions.filter((exec: any) =>
        exec.instanceInfo?.id === selectedInstance
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      executions = executions.filter((exec: any) => exec.status === statusFilter);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      executions = executions.filter((exec: any) =>
        exec.workflowName?.toLowerCase().includes(query) ||
        exec.workflowExecutionId.toLowerCase().includes(query) ||
        exec.workflowDescription?.toLowerCase().includes(query) ||
        exec.triggeredBy?.toLowerCase().includes(query) ||
        exec.instanceInfo?.name?.toLowerCase().includes(query) ||
        exec.instanceInfo?.brands?.some((b: string) => b.toLowerCase().includes(query))
      );
    }

    return executions;
  }, [data?.executions, selectedInstance, statusFilter, searchQuery]);

  // Get unique statuses for filter
  const uniqueStatuses = useMemo(() => {
    const statuses = new Set(data?.executions?.map((exec: any) => exec.status) || []);
    return Array.from(statuses);
  }, [data?.executions]);

  // Get execution count per instance
  const getInstanceExecutionCount = (instanceId: string) => {
    return data?.executions?.filter((e: any) => e.instanceInfo?.id === instanceId).length || 0;
  };

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

  const getSnowflakeBadge = (execution: any) => {
    const enabled = execution.snowflakeEnabled || execution.snowflake_enabled;
    const status = execution.snowflakeStatus || execution.snowflake_status;
    const attemptCount = execution.snowflakeAttemptCount || execution.snowflake_attempt_count || 0;

    if (!enabled) return null;

    switch (status) {
      case 'uploaded':
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800" title="Snowflake upload completed">
            <Database className="h-3 w-3 mr-1" />
            Uploaded
          </span>
        );
      case 'uploading':
      case 'pending':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800" title="Snowflake upload in progress">
            <Upload className="h-3 w-3 mr-1 animate-pulse" />
            Uploading
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800" title={`Snowflake upload failed (${attemptCount}/3 attempts)`}>
            <AlertTriangle className="h-3 w-3 mr-1" />
            Upload Failed {attemptCount > 0 ? `(${attemptCount}/3)` : ''}
          </span>
        );
      case 'skipped':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600" title="Snowflake upload skipped (no config)">
            <Database className="h-3 w-3 mr-1" />
            Skipped
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800" title="Snowflake upload pending">
            <Clock className="h-3 w-3 mr-1" />
            Pending Upload
          </span>
        );
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const refreshResult = await amcExecutionService.refreshAllExecutions();

      if (refreshResult.success) {
        if (refreshResult.updated > 0) {
          toast.success(`Updated ${refreshResult.updated} execution status${refreshResult.updated > 1 ? 'es' : ''}`);
        } else if (refreshResult.refreshed > 0) {
          toast.success(`Checked ${refreshResult.refreshed} execution${refreshResult.refreshed > 1 ? 's' : ''}, all up to date`);
        } else {
          toast.success('No pending executions to refresh');
        }
      }

      await refetch();
    } catch (error) {
      console.error('Failed to refresh executions:', error);
      toast.error('Failed to refresh execution statuses');
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center py-16">
          <div className="flex items-center gap-3 text-gray-500">
            <Loader className="w-5 h-5 animate-spin" />
            Loading executions...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-600">Failed to load AMC executions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">All Executions</h1>
          <p className="text-gray-600 mt-1">View and manage AMC workflow executions across all instances</p>
        </div>
        <div className="flex items-center gap-3">
          {hasPendingExecutions && (
            <span className="flex items-center text-xs text-green-600 bg-green-50 px-2 py-1 rounded-md">
              <Activity className="w-3 h-3 mr-1 animate-pulse" />
              Auto-refreshing
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh execution statuses"
          >
            {isRefreshing ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-4 flex flex-col sm:flex-row gap-4">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search executions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pl-10 pr-8 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Statuses</option>
              {uniqueStatuses.map((status: any) => (
                <option key={status} value={status}>
                  {getStatusText(status as AMCExecution['status'])}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Instance Tabs */}
      {uniqueInstances.length > 0 && (
        <div className="mb-6 overflow-x-auto">
          <div className="flex items-center space-x-2 pb-2">
            <button
              onClick={() => setSelectedInstance(null)}
              className={`flex items-center px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                selectedInstance === null
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Database className="w-3.5 h-3.5 mr-1.5" />
              All Instances
              <span className={`ml-1.5 px-1.5 py-0.5 rounded text-xs ${
                selectedInstance === null ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                {data?.executions?.length || 0}
              </span>
            </button>
            {uniqueInstances.map((instance) => {
              const execCount = getInstanceExecutionCount(instance.id);

              return (
                <button
                  key={instance.id}
                  onClick={() => setSelectedInstance(instance.id)}
                  className={`flex items-center px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                    selectedInstance === instance.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {instance.name}
                  {instance.brands && instance.brands.length > 0 && (
                    <span className={`ml-1.5 text-xs ${
                      selectedInstance === instance.id ? 'text-blue-200' : 'text-gray-500'
                    }`}>
                      ({instance.brands.slice(0, 2).join(', ')}{instance.brands.length > 2 ? '...' : ''})
                    </span>
                  )}
                  <span className={`ml-1.5 px-1.5 py-0.5 rounded text-xs ${
                    selectedInstance === instance.id
                      ? 'bg-blue-500'
                      : 'bg-gray-200'
                  }`}>
                    {execCount}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Results count */}
      {filteredExecutions.length !== data?.executions?.length && (
        <p className="text-sm text-gray-500 mb-4">
          Showing {filteredExecutions.length} of {data?.executions?.length} executions
        </p>
      )}

      {/* Executions List */}
      {filteredExecutions.length === 0 ? (
        <div className="text-center py-12">
          {searchQuery || statusFilter !== 'all' || selectedInstance ? (
            <>
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No matching executions</h3>
              <p className="text-gray-600 mb-4">Try adjusting your search or filter criteria</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('all');
                  setSelectedInstance(null);
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                <X className="w-4 h-4 mr-2" />
                Clear Filters
              </button>
            </>
          ) : (
            <>
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No executions yet</h3>
              <p className="text-gray-600">
                Run a template from an instance to see executions here.
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {filteredExecutions.map((execution: any) => (
              <li key={execution.workflowExecutionId}>
                <button
                  onClick={() => setSelectedExecutionId(execution.workflowExecutionId)}
                  className="w-full px-4 py-4 sm:px-6 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center flex-1">
                      {getStatusIcon(execution.status as AMCExecution['status'])}
                      <div className="ml-4 text-left flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-medium text-gray-900">
                            {execution.workflowName || 'Ad Hoc Query'}
                          </p>
                          {execution.sqlQuery && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {getQueryType(execution.sqlQuery)}
                            </span>
                          )}
                          {execution.instanceInfo && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                              <Server className="h-3 w-3 mr-1" />
                              {execution.instanceInfo.name}
                            </span>
                          )}
                          {getSnowflakeBadge(execution)}
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

      {/* Execution Detail Modal */}
      {selectedExecutionId && (
        <AMCExecutionDetail
          instanceId={filteredExecutions.find((e: any) => e.workflowExecutionId === selectedExecutionId)?.instanceInfo?.id}
          executionId={selectedExecutionId}
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
          onRerunSuccess={(newExecutionId) => {
            setSelectedExecutionId(newExecutionId);
          }}
        />
      )}
    </div>
  );
}
