import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Play, Loader, CheckCircle, XCircle, Download, Eye, BarChart } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import JSONEditor from '../common/JSONEditor';
import ResultsVisualization from './ResultsVisualization';

interface ExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflow: {
    workflowId: string;
    name: string;
    parameters?: any;
  };
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

export default function ExecutionModal({ isOpen, onClose, workflow }: ExecutionModalProps) {
  const queryClient = useQueryClient();
  const [parameters, setParameters] = useState(workflow.parameters || {});
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [showVisualization, setShowVisualization] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setParameters(workflow.parameters || {});
      setExecutionId(null);
      setShowResults(false);
      setShowVisualization(false);
    }
  }, [isOpen, workflow.parameters]);

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: async (params: any) => {
      const response = await api.post(`/workflows/${workflow.workflowId}/execute`, params);
      return response.data;
    },
    onSuccess: (data) => {
      setExecutionId(data.execution_id);
      toast.success('Workflow execution started');
      queryClient.invalidateQueries({ queryKey: ['workflow-executions', workflow.workflowId] });
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
    refetchInterval: (query) => {
      // Stop polling if completed or failed
      return query.data?.status === 'running' || query.data?.status === 'pending' ? 2000 : false;
    },
  });

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
    executeMutation.mutate(parameters);
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
    a.download = `${workflow.name.replace(/\s+/g, '_')}_results_${executionId}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Results downloaded');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Execute Workflow: {workflow.name}</h2>
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
              <div>
                <h3 className="text-lg font-medium mb-2">Parameters</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Configure the parameters for this execution. These will be substituted in the SQL query.
                </p>
                <JSONEditor
                  value={parameters}
                  onChange={setParameters}
                  height="200px"
                />
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleExecute}
                  disabled={executeMutation.isPending}
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
                        <span className="text-gray-500">Execution ID:</span>
                        <p className="font-mono text-xs mt-1">{status.execution_id}</p>
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
                          <p>{status.row_count.toLocaleString()}</p>
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

                    {status.error_message && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                        <p className="text-sm text-red-800">{status.error_message}</p>
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
                                Showing first 100 of {results.total_rows.toLocaleString()} rows
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