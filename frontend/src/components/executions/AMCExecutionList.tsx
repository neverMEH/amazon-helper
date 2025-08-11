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
  Server
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

interface Instance {
  id: string;
  instanceId: string;
  name: string;
  region: string;
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
  
  // Fetch all instances if we need to show instance badges
  const { data: instances } = useQuery<Instance[]>({
    queryKey: ['amc-instances'],
    queryFn: async () => {
      const response = await api.get('/instances');
      return response.data;
    },
    enabled: showInstanceBadge || !instanceId,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch executions based on context (instance-specific or all)
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['amc-executions', instanceId, workflowId],
    enabled: tokenStatus?.hasValidToken === true, // Only fetch if we have valid tokens
    queryFn: async () => {
      if (instanceId) {
        // Instance-specific executions
        return amcExecutionService.listExecutions(instanceId);
      } else if (instances && instances.length > 0) {
        // Limit parallel requests to prevent overwhelming the backend
        const BATCH_SIZE = 5; // Process 5 instances at a time
        const allExecutions = [];
        
        for (let i = 0; i < instances.length; i += BATCH_SIZE) {
          const batch = instances.slice(i, i + BATCH_SIZE);
          const batchResults = await Promise.all(
            batch.map(async (instance) => {
              try {
                const result = await amcExecutionService.listExecutions(instance.instanceId);
                // Add instance info to each execution
                return result.executions.map(exec => ({
                  ...exec,
                  instanceInfo: {
                    id: instance.instanceId,
                    name: instance.name,
                    region: instance.region
                  }
                }));
              } catch (error) {
                console.error(`Failed to fetch executions for instance ${instance.instanceId}:`, error);
                return [];
              }
            })
          );
          allExecutions.push(...batchResults);
        }
        
        // Flatten and sort by date
        const flatExecutions = allExecutions.flat().sort((a, b) => {
          const dateA = new Date(a.createdAt || a.startTime || 0).getTime();
          const dateB = new Date(b.createdAt || b.startTime || 0).getTime();
          return dateB - dateA;
        });
        
        return { executions: flatExecutions };
      }
      return { executions: [] };
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
      executions = executions.filter(exec => 
        exec.workflowId === workflowId || 
        exec.workflowName?.toLowerCase().includes(workflowId.toLowerCase())
      );
    }
    
    // Filter by status
    if (statusFilter !== 'all') {
      executions = executions.filter(exec => exec.status === statusFilter);
    }
    
    // Filter by instance
    if (instanceFilter !== 'all' && !instanceId) {
      executions = executions.filter(exec => 
        (exec as any).instanceInfo?.id === instanceFilter
      );
    }
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      executions = executions.filter(exec => 
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
    const statuses = new Set(data?.executions?.map(exec => exec.status) || []);
    return Array.from(statuses);
  }, [data?.executions]);

  // Get unique instances for filter
  const uniqueInstances = useMemo(() => {
    if (instanceId) return [];
    const instanceMap = new Map();
    data?.executions?.forEach(exec => {
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
        </h3>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </button>
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
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>
                  {getStatusText(status)}
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
                {uniqueInstances.map(instance => (
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
            {filteredExecutions.map((execution) => {
              const execWithInstance = execution as any;
              return (
                <li key={execution.workflowExecutionId}>
                  <button
                    onClick={() => setSelectedExecutionId(execution.workflowExecutionId)}
                    className="w-full px-4 py-4 sm:px-6 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition duration-150"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center flex-1">
                        {getStatusIcon(execution.status)}
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
          instanceId={instanceId || ((filteredExecutions.find(e => e.workflowExecutionId === selectedExecutionId) as any)?.instanceInfo?.id)}
          executionId={selectedExecutionId}
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
        />
      )}
    </div>
  );
}