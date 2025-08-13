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
  Cloud
} from 'lucide-react';
import { amcExecutionService } from '../../services/amcExecutionService';
import type { AMCExecution } from '../../types/amcExecution';
import AMCExecutionDetail from './AMCExecutionDetail';
import api from '../../services/api';

interface Props {
  instanceId?: string;  // Optional - if not provided, shows all executions
  workflowId?: string;  // Optional - if provided, shows executions for specific workflow
  showInstanceBadge?: boolean; // Show instance name as a badge
}

export default function AMCExecutionList({ instanceId, workflowId, showInstanceBadge = false }: Props) {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [instanceFilter, setInstanceFilter] = useState<string>('all');
  
  // Check token status first
  const { data: tokenStatus } = useQuery({
    queryKey: ['token-status'],
    queryFn: async () => {
      const response = await api.get('/auth/token-status');
      return response.data;
    },
    staleTime: 60 * 1000, // Check every minute
  });
  

  // Fetch executions based on context (instance-specific or all)
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['amc-executions', instanceId, workflowId],
    // No longer require tokens for fetching from database
    queryFn: async () => {
      if (instanceId) {
        // Instance-specific executions - fetch from stored data first
        try {
          const response = await api.get(`/amc-executions/stored/${instanceId}`, {
            params: { limit: 50, sync_if_empty: false }
          });
          return response.data;
        } catch (error) {
          console.error(`Failed to fetch stored executions for instance ${instanceId}:`, error);
          // Fallback to AMC API if stored fetch fails and we have tokens
          if (tokenStatus?.hasValidToken) {
            return amcExecutionService.listExecutions(instanceId);
          }
          return { executions: [] };
        }
      } else {
        // Fetch all executions from database in a single efficient call
        try {
          const response = await api.get('/amc-executions/all/stored', {
            params: { limit: 100 }
          });
          return response.data;
        } catch (error) {
          console.error('Failed to fetch all stored executions:', error);
          return { executions: [] };
        }
      }
    },
    refetchInterval: 30000
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

  // Filter and search executions
  const filteredExecutions = useMemo(() => {
    let executions = data?.executions || [];
    
    // Filter by workflow if specified
    if (workflowId) {
      executions = executions.filter((exec: any) => 
        exec.workflowId === workflowId || 
        exec.workflowName?.toLowerCase().includes(workflowId.toLowerCase())
      );
    }
    
    // Filter by status
    if (statusFilter !== 'all') {
      executions = executions.filter((exec: any) => exec.status === statusFilter);
    }
    
    // Filter by instance
    if (instanceFilter !== 'all' && !instanceId) {
      executions = executions.filter((exec: any) => 
        (exec as any).instanceInfo?.id === instanceFilter
      );
    }
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      executions = executions.filter((exec: any) => 
        exec.workflowName?.toLowerCase().includes(query) ||
        exec.workflowExecutionId.toLowerCase().includes(query) ||
        exec.workflowDescription?.toLowerCase().includes(query) ||
        exec.triggeredBy?.toLowerCase().includes(query)
      );
    }
    
    return executions;
  }, [data?.executions, workflowId, statusFilter, instanceFilter, searchQuery, instanceId]);

  // Get unique statuses for filter
  const uniqueStatuses = useMemo(() => {
    const statuses = new Set(data?.executions?.map((exec: any) => exec.status) || []);
    return Array.from(statuses);
  }, [data?.executions]);

  // Get unique instances for filter
  const uniqueInstances = useMemo(() => {
    if (instanceId) return [];
    const instanceMap = new Map();
    data?.executions?.forEach((exec: any) => {
      const info = (exec as any).instanceInfo;
      if (info) {
        instanceMap.set(info.id, info);
      }
    });
    return Array.from(instanceMap.values());
  }, [data?.executions, instanceId]);

  // Check if we're missing tokens
  if (tokenStatus?.requiresAuthentication) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-yellow-800">Authentication Required</p>
            <p className="text-sm text-yellow-700 mt-1">
              Please authenticate with Amazon Advertising API in your profile settings to view AMC executions.
            </p>
          </div>
        </div>
      </div>
    );
  }
  
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

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h3 className="text-lg font-medium text-gray-900">
          {instanceId ? 'AMC Execution History' : 'All AMC Executions'}
          {data?.source && (
            <span className="ml-2 text-xs text-gray-500">
              (from {data.source})
            </span>
          )}
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </button>
          {tokenStatus?.hasValidToken && instanceId && (
            <button
              onClick={async () => {
                try {
                  // Force sync from AMC API
                  await api.get(`/amc-executions/${instanceId}`, {
                    params: { limit: 50 }
                  });
                  // Refetch to get updated data
                  refetch();
                } catch (error) {
                  console.error('Failed to sync from AMC:', error);
                }
              }}
              className="inline-flex items-center px-3 py-1.5 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              title="Sync latest data from AMC API"
            >
              <Cloud className="h-4 w-4 mr-1" />
              Sync from AMC
            </button>
          )}
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by workflow name, ID, or user..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        
        <div className="flex gap-2">
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
          
          {!instanceId && uniqueInstances.length > 0 && (
            <div className="relative">
              <Server className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <select
                value={instanceFilter}
                onChange={(e) => setInstanceFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Instances</option>
                {uniqueInstances.map((instance: any) => (
                  <option key={instance.id} value={instance.id}>
                    {instance.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Results count */}
      {filteredExecutions.length !== data?.executions?.length && (
        <p className="text-sm text-gray-500">
          Showing {filteredExecutions.length} of {data?.executions?.length} executions
        </p>
      )}

      {filteredExecutions.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-8 text-center">
          <p className="text-gray-500">
            {searchQuery || statusFilter !== 'all' || instanceFilter !== 'all' 
              ? 'No executions match your filters'
              : 'No executions found'
            }
          </p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {filteredExecutions.map((execution: any) => {
              const execWithInstance = execution as any;
              return (
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
                            {(showInstanceBadge || !instanceId) && execWithInstance.instanceInfo && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                <Server className="h-3 w-3 mr-1" />
                                {execWithInstance.instanceInfo.name}
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
              );
            })}
          </ul>
        </div>
      )}

      {selectedExecutionId && (
        <AMCExecutionDetail
          instanceId={instanceId || ((filteredExecutions.find((e: any) => e.workflowExecutionId === selectedExecutionId) as any)?.instanceInfo?.id)}
          executionId={selectedExecutionId}
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
          onRerunSuccess={(newExecutionId) => {
            // Directly switch to new execution without closing
            // The transition state in AMCExecutionDetail handles the smooth transition
            setSelectedExecutionId(newExecutionId);
          }}
        />
      )}
    </div>
  );
}