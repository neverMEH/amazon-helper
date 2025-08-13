import { useState, useEffect, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Play, Loader, CheckCircle, XCircle, Download, Eye, BarChart, Code, Search } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import JSONEditor from '../common/JSONEditor';
import ParameterEditor from './ParameterEditor';
import ResultsVisualization from './ResultsVisualization';
import ExecutionErrorDetails from '../executions/ExecutionErrorDetails';
import DateRangeSelector from '../common/DateRangeSelector';

interface ExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflow?: {
    workflowId: string;
    name: string;
    parameters?: any;
  };
  workflowId?: string;
  instanceId?: string;
}

interface ExecutionStatus {
  execution_id: string;
  status: string;
  progress: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  row_count?: number;
  amc_execution_id?: string;
}

interface ExecutionResult {
  columns: Array<{ name: string; type: string }>;
  rows: any[][];
  total_rows: number;
  execution_details?: {
    query_runtime_seconds: number;
    data_scanned_gb: number;
    cost_estimate_usd: number;
  };
}

export default function ExecutionModal({ isOpen, onClose, workflow, workflowId: propWorkflowId, instanceId }: ExecutionModalProps) {
  const queryClient = useQueryClient();
  const actualWorkflowId = workflow?.workflowId || propWorkflowId;
  
  // Fetch workflow details if only workflowId is provided
  const { data: fetchedWorkflow, isLoading: loadingWorkflow } = useQuery({
    queryKey: ['workflow', actualWorkflowId],
    queryFn: async () => {
      try {
        const response = await api.get(`/workflows/${actualWorkflowId}`);
        return response.data;
      } catch (error: any) {
        // If workflow not found in database (e.g., synced AMC workflow), create a minimal workflow object
        if (error?.response?.status === 404) {
          return {
            workflowId: actualWorkflowId,
            name: actualWorkflowId,
            parameters: {}
          };
        }
        throw error;
      }
    },
    enabled: !!actualWorkflowId && !workflow,
  });
  
  const workflowData = workflow || fetchedWorkflow;
  const [parameters, setParameters] = useState(workflowData?.parameters || {});
  // Use the workflow's tied instance or pre-fill from prop
  const workflowInstanceId = workflowData?.instance?.id || instanceId;
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | undefined>(workflowInstanceId);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showVisualization, setShowVisualization] = useState(false);
  const [useAdvancedEditor, setUseAdvancedEditor] = useState(false);
  const [instanceSearchQuery, setInstanceSearchQuery] = useState('');
  const [showInstanceDropdown, setShowInstanceDropdown] = useState(false);
  const [dateRange, setDateRange] = useState<{ startDate: string; endDate: string; preset?: string }>({
    startDate: '',
    endDate: '',
    preset: '30'
  });
  
  // Fetch available instances for the user
  const { data: instances } = useQuery({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances');
      return response.data;
    },
    enabled: isOpen, // Always fetch to show instance details
  });

  // Update selected instance when workflow data changes
  useEffect(() => {
    if (workflowData?.instance?.id) {
      setSelectedInstanceId(workflowData.instance.id);
    }
  }, [workflowData]);

  // Filter instances based on search query
  const filteredInstances = useMemo(() => {
    if (!instances) return [];
    if (!instanceSearchQuery) return instances;
    
    const query = instanceSearchQuery.toLowerCase();
    return instances.filter((instance: any) => 
      instance.instanceName?.toLowerCase().includes(query) ||
      instance.instanceId?.toLowerCase().includes(query) ||
      instance.accountName?.toLowerCase().includes(query) ||
      instance.region?.toLowerCase().includes(query)
    );
  }, [instances, instanceSearchQuery]);

  // Get selected instance details
  const selectedInstance = useMemo(() => {
    if (!selectedInstanceId || !instances) return null;
    return instances.find((i: any) => i.instanceId === selectedInstanceId);
  }, [selectedInstanceId, instances]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen && workflowData) {
      setParameters(workflowData.parameters || {});
      setExecutionId(null);
      setShowResults(false);
      setShowVisualization(false);
    }
  }, [isOpen, workflowData]);

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: async (params: any) => {
      const requestData = selectedInstanceId ? { ...params, instance_id: selectedInstanceId } : params;
      const response = await api.post(`/workflows/${actualWorkflowId}/execute`, requestData);
      return response.data;
    },
    onSuccess: (data) => {
      setExecutionId(data.execution_id);
      toast.success('Workflow execution started');
      queryClient.invalidateQueries({ queryKey: ['workflow-executions', actualWorkflowId] });
    },
    onError: (error: any) => {
      toast.error(`Execution failed: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Poll execution status
  const { data: status } = useQuery<ExecutionStatus>({
    queryKey: ['execution-status', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/status`);
      return response.data;
    },
    enabled: !!executionId,
    refetchInterval: 10000, // Poll every 10 seconds
  });
  
  // Stop polling when execution is complete
  useEffect(() => {
    if (status && (status.status === 'completed' || status.status === 'failed')) {
      queryClient.invalidateQueries({ queryKey: ['execution-status', executionId] });
    }
  }, [status, executionId, queryClient]);

  // Fetch results
  const { data: results, isLoading: loadingResults } = useQuery<ExecutionResult>({
    queryKey: ['execution-results', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/results`);
      return response.data;
    },
    enabled: !!executionId && status?.status === 'completed' && showResults,
  });

  const handleExecute = () => {
    if (!instanceId && !selectedInstanceId) {
      toast.error('Please select an instance to execute the workflow on');
      return;
    }
    
    if (!dateRange.startDate || !dateRange.endDate) {
      toast.error('Please select a date range for the query');
      return;
    }
    
    // Merge date range parameters with existing parameters
    const executionParams = {
      ...parameters,
      start_date: dateRange.startDate,
      end_date: dateRange.endDate,
      date_range_preset: dateRange.preset,
      // Also add common AMC date parameters
      startDate: dateRange.startDate,
      endDate: dateRange.endDate
    };
    
    executeMutation.mutate(executionParams);
  };

  const handleDownloadResults = async () => {
    if (!results) return;

    // Convert results to CSV
    const headers = results.columns.map(col => col.name).join(',');
    const rows = results.rows.map(row => row.map(cell => 
      typeof cell === 'string' && cell.includes(',') ? `"${cell}"` : cell
    ).join(',')).join('\n');
    
    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(workflowData?.name || 'workflow').replace(/\s+/g, '_')}_results_${executionId}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Results downloaded');
  };

  if (!isOpen) return null;
  
  // Show loading state while fetching workflow
  if (loadingWorkflow) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6">
          <Loader className="h-8 w-8 animate-spin mx-auto text-gray-400" />
          <p className="mt-2 text-sm text-gray-500">Loading workflow...</p>
        </div>
      </div>
    );
  }
  
  if (!workflowData) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Execute Workflow: {workflowData.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          {!executionId ? (
            // Pre-execution: Parameter configuration
            <div className="space-y-6">
              {/* Instance Display - Show tied instance */}
              {(workflowData?.instance || instanceId) ? (
                <div>
                  <h3 className="text-lg font-medium mb-2">Target Instance</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    This workflow will be executed on its configured instance.
                  </p>
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
                    <p className="text-sm font-medium text-gray-900">
                      {selectedInstance?.instanceName || workflowData?.instance?.name || 'Loading...'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      ID: {selectedInstanceId || workflowData?.instance?.id}
                    </p>
                  </div>
                </div>
              ) : !instanceId && (
                <div>
                  <h3 className="text-lg font-medium mb-2">Target Instance</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    ⚠️ No instance configured for this workflow. Please copy the workflow and select an instance.
                  </p>
                  {instances && instances.length > 0 ? (
                    <div className="relative">
                      {/* Search Input */}
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Search className="h-4 w-4 text-gray-400" />
                        </div>
                        <input
                          type="text"
                          value={selectedInstance ? `${selectedInstance.instanceName} (${selectedInstance.instanceId})` : instanceSearchQuery}
                          onChange={(e) => {
                            setInstanceSearchQuery(e.target.value);
                            setSelectedInstanceId(undefined);
                            setShowInstanceDropdown(true);
                          }}
                          onFocus={() => setShowInstanceDropdown(true)}
                          placeholder="Search for an instance by name, ID, or account..."
                          className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        />
                        {selectedInstanceId && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedInstanceId(undefined);
                              setInstanceSearchQuery('');
                              setShowInstanceDropdown(true);
                            }}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center"
                          >
                            <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                          </button>
                        )}
                      </div>

                      {/* Dropdown List */}
                      {showInstanceDropdown && !selectedInstanceId && (
                        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
                          {filteredInstances.length > 0 ? (
                            filteredInstances.map((instance: any) => (
                              <button
                                key={instance.instanceId}
                                type="button"
                                onClick={() => {
                                  setSelectedInstanceId(instance.instanceId);
                                  setInstanceSearchQuery('');
                                  setShowInstanceDropdown(false);
                                }}
                                className="w-full text-left px-3 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm font-medium text-gray-900">
                                      {instance.instanceName}
                                    </p>
                                    <p className="text-xs text-gray-500">
                                      ID: {instance.instanceId} • {instance.accountName}
                                      {instance.region && ` • ${instance.region}`}
                                    </p>
                                  </div>
                                  {instance.brands && instance.brands.length > 0 && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                      {instance.brands.length} {instance.brands.length === 1 ? 'brand' : 'brands'}
                                    </span>
                                  )}
                                </div>
                              </button>
                            ))
                          ) : (
                            <div className="px-3 py-2 text-sm text-gray-500">
                              No instances found matching "{instanceSearchQuery}"
                            </div>
                          )}
                        </div>
                      )}

                      {/* Click outside to close dropdown */}
                      {showInstanceDropdown && (
                        <div
                          className="fixed inset-0 z-0"
                          onClick={() => setShowInstanceDropdown(false)}
                        />
                      )}
                    </div>
                  ) : (
                    <div className="mt-1 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <p className="text-sm text-yellow-800">No AMC instances available. Please ensure you have access to at least one AMC instance.</p>
                    </div>
                  )}
                </div>
              )}
              {/* Date Range Selector */}
              <DateRangeSelector
                value={dateRange}
                onChange={setDateRange}
                className="mb-4"
              />

              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium">Parameters</h3>
                  <button
                    type="button"
                    onClick={() => setUseAdvancedEditor(!useAdvancedEditor)}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium rounded text-gray-600 hover:text-gray-900"
                  >
                    <Code className="h-3 w-3 mr-1" />
                    {useAdvancedEditor ? 'Simple Editor' : 'Advanced Editor'}
                  </button>
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Configure the parameters for this execution. These will be substituted in the SQL query.
                </p>
                {useAdvancedEditor ? (
                  <JSONEditor
                    value={parameters}
                    onChange={setParameters}
                    height="200px"
                  />
                ) : (
                  <ParameterEditor
                    parameters={parameters}
                    onChange={setParameters}
                    schema={workflowData?.parameterSchema}
                  />
                )}
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleExecute}
                  disabled={executeMutation.isPending || (!instanceId && !selectedInstanceId)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
                >
                  {executeMutation.isPending ? (
                    <>
                      <Loader className="h-4 w-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Execute Workflow
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            // Post-execution: Status and results
            <div className="space-y-6">
              {/* Status Section */}
              <div>
                <h3 className="text-lg font-medium mb-4">Execution Status</h3>
                {status && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      {status.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      ) : status.status === 'failed' ? (
                        <XCircle className="h-5 w-5 text-red-500 mr-2" />
                      ) : (
                        <Loader className="h-5 w-5 text-blue-500 mr-2 animate-spin" />
                      )}
                      <span className="font-medium capitalize">{status.status}</span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Internal Execution ID:</span>
                        <p className="font-mono text-xs mt-1">{status.execution_id}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">AMC Execution ID:</span>
                        {status.amc_execution_id ? (
                          <p className="font-mono text-xs mt-1 text-green-700">{status.amc_execution_id}</p>
                        ) : (
                          <p className="text-xs mt-1 text-orange-600 italic">Not available yet</p>
                        )}
                      </div>
                      <div>
                        <span className="text-gray-500">Started:</span>
                        <p>{new Date(status.started_at).toLocaleString()}</p>
                      </div>
                      {status.completed_at && (
                        <div>
                          <span className="text-gray-500">Completed:</span>
                          <p>{new Date(status.completed_at).toLocaleString()}</p>
                        </div>
                      )}
                      {status.row_count !== undefined && (
                        <div>
                          <span className="text-gray-500">Rows:</span>
                          <p>{status.row_count?.toLocaleString() || '0'}</p>
                        </div>
                      )}
                    </div>

                    {status.status === 'running' && (
                      <div className="mt-4">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{status.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${status.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Display detailed error information for failed executions */}
                    {status.error_message && (
                      <div className="mt-4">
                        <ExecutionErrorDetails 
                          errorMessage={status.error_message}
                          status={status.status}
                        />
                      </div>
                    )}

                    {status.amc_execution_id && (
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                        <p className="text-xs text-blue-700">
                          <strong>Tip:</strong> Use the AMC Execution ID to find this execution in the Amazon Marketing Cloud console.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Results Section */}
              {status?.status === 'completed' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium">Results</h3>
                    <div className="space-x-2">
                      {!showResults && (
                        <button
                          onClick={() => setShowResults(true)}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Results
                        </button>
                      )}
                      {showResults && results && (
                        <button
                          onClick={() => setShowVisualization(!showVisualization)}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <BarChart className="h-4 w-4 mr-2" />
                          {showVisualization ? 'Show Table' : 'Show Insights'}
                        </button>
                      )}
                      <button
                        onClick={handleDownloadResults}
                        disabled={!results}
                        className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download CSV
                      </button>
                    </div>
                  </div>

                  {showResults && (
                    <>
                      {loadingResults ? (
                        <div className="text-center py-8">
                          <Loader className="h-8 w-8 animate-spin mx-auto text-gray-400" />
                          <p className="mt-2 text-sm text-gray-500">Loading results...</p>
                        </div>
                      ) : results ? (
                        <div>
                          {results.execution_details && (
                            <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                              <div className="bg-blue-50 p-3 rounded">
                                <p className="text-blue-600 font-medium">Runtime</p>
                                <p className="text-blue-900">{results.execution_details.query_runtime_seconds}s</p>
                              </div>
                              <div className="bg-green-50 p-3 rounded">
                                <p className="text-green-600 font-medium">Data Scanned</p>
                                <p className="text-green-900">{results.execution_details.data_scanned_gb} GB</p>
                              </div>
                              <div className="bg-purple-50 p-3 rounded">
                                <p className="text-purple-600 font-medium">Est. Cost</p>
                                <p className="text-purple-900">${results.execution_details.cost_estimate_usd.toFixed(4)}</p>
                              </div>
                            </div>
                          )}

                          {showVisualization ? (
                            <ResultsVisualization columns={results.columns} rows={results.rows} />
                          ) : (
                            <div className="border rounded-lg overflow-hidden">
                            <div className="overflow-x-auto">
                              <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                  <tr>
                                    {results.columns.map((col, idx) => (
                                      <th
                                        key={idx}
                                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                      >
                                        {col.name}
                                        <span className="ml-1 text-gray-400 normal-case">({col.type})</span>
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                  {results.rows.slice(0, 100).map((row, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50">
                                      {row.map((cell, cellIdx) => (
                                        <td key={cellIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                          {cell === null ? <span className="text-gray-400">null</span> : String(cell)}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {results.total_rows > 100 && (
                              <div className="bg-gray-50 px-6 py-3 text-sm text-gray-600">
                                Showing first 100 of {results.total_rows?.toLocaleString() || '0'} rows
                              </div>
                            )}
                          </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          No results available
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}