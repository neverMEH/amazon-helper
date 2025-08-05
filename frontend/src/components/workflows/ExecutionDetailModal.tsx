import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, CheckCircle, XCircle, Loader, Clock, AlertCircle, Download, Eye, BarChart, Table, TrendingUp, Database } from 'lucide-react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import EnhancedResultsTable from '../executions/EnhancedResultsTable';
import DataVisualization from '../executions/DataVisualization';
// AI analysis will be integrated later
// import { DataAnalysisService } from '../../services/dataAnalysisService';

interface ExecutionDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  executionId: string;
}

interface ExecutionStatus {
  execution_id: string;
  status: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  row_count?: number;
  triggered_by: string;
}

interface ExecutionDetails {
  execution_id: string;
  workflow_id: string;
  status: string;
  progress: number;
  execution_parameters?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  row_count?: number;
  triggered_by: string;
  output_location?: string;
  size_bytes?: number;
}

interface Results {
  columns: Array<{ name: string; type: string }>;
  rows: any[][];
  total_rows: number;
  sample_size: number;
  execution_details?: {
    query_runtime_seconds?: number;
    data_scanned_gb?: number;
    cost_estimate_usd?: number;
  };
}

export default function ExecutionDetailModal({ isOpen, onClose, executionId }: ExecutionDetailModalProps) {
  const [showResults, setShowResults] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'enhanced' | 'charts' | 'ai'>('enhanced');
  // const analysisService = useMemo(() => new DataAnalysisService(), []);

  // Get execution details
  const { data: execution } = useQuery<ExecutionDetails>({
    queryKey: ['execution-detail', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/detail`);
      return response.data;
    },
    enabled: isOpen && !!executionId,
  });

  // Get execution status
  const { data: status } = useQuery<ExecutionStatus>({
    queryKey: ['execution-status', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/status`);
      return response.data;
    },
    enabled: isOpen && !!executionId,
    refetchInterval: (query) => {
      return query.state.data?.status === 'running' ? 2000 : false;
    },
  });

  // Get results when completed
  const { data: results, isLoading: loadingResults } = useQuery<Results>({
    queryKey: ['execution-results', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/results`);
      return response.data;
    },
    enabled: showResults && status?.status === 'completed',
  });

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
    a.download = `execution_${executionId}_results.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Results downloaded');
  };

  const getStatusIcon = (status?: string) => {
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Execution Details: {executionId}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          {/* Status Section */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-4">Execution Status</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center mb-4">
                {getStatusIcon(status?.status)}
                <span className="ml-2 font-medium capitalize">{status?.status || 'Unknown'}</span>
                {status?.status === 'running' && (
                  <span className="ml-4 text-sm text-gray-600">Progress: {status.progress}%</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Execution ID:</span>
                  <p className="font-mono text-xs mt-1">{executionId}</p>
                </div>
                <div>
                  <span className="text-gray-500">Triggered By:</span>
                  <p>{status?.triggered_by || 'Unknown'}</p>
                </div>
                <div>
                  <span className="text-gray-500">Started:</span>
                  <p>{status?.started_at ? new Date(status.started_at).toLocaleString() : '-'}</p>
                </div>
                <div>
                  <span className="text-gray-500">Completed:</span>
                  <p>{status?.completed_at ? new Date(status.completed_at).toLocaleString() : '-'}</p>
                </div>
                {status?.duration_seconds && (
                  <div>
                    <span className="text-gray-500">Duration:</span>
                    <p>{status.duration_seconds.toFixed(2)}s</p>
                  </div>
                )}
                {status?.row_count !== undefined && (
                  <div>
                    <span className="text-gray-500">Rows:</span>
                    <p>{status.row_count != null ? status.row_count.toLocaleString() : '0'}</p>
                  </div>
                )}
              </div>

              {status?.status === 'running' && (
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

              {status?.error_message && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800">{status.error_message}</p>
                </div>
              )}
            </div>
          </div>

          {/* Parameters Section */}
          {execution?.execution_parameters && Object.keys(execution.execution_parameters).length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-4">Execution Parameters</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(execution.execution_parameters, null, 2)}
                </pre>
              </div>
            </div>
          )}

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
                    <div className="inline-flex rounded-md shadow-sm" role="group">
                      <button
                        onClick={() => setViewMode('enhanced')}
                        className={`px-3 py-1 text-sm font-medium rounded-l-md border ${
                          viewMode === 'enhanced' 
                            ? 'bg-indigo-600 text-white border-indigo-600' 
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <Table className="h-4 w-4 inline mr-1" />
                        Enhanced Table
                      </button>
                      <button
                        onClick={() => setViewMode('charts')}
                        className={`px-3 py-1 text-sm font-medium border-t border-b ${
                          viewMode === 'charts'
                            ? 'bg-indigo-600 text-white border-indigo-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <BarChart className="h-4 w-4 inline mr-1" />
                        Charts
                      </button>
                      <button
                        onClick={() => setViewMode('ai')}
                        className={`px-3 py-1 text-sm font-medium border ${
                          viewMode === 'ai'
                            ? 'bg-indigo-600 text-white border-indigo-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <TrendingUp className="h-4 w-4 inline mr-1" />
                        AI Analysis
                      </button>
                      <button
                        onClick={() => setViewMode('table')}
                        className={`px-3 py-1 text-sm font-medium rounded-r-md border ${
                          viewMode === 'table'
                            ? 'bg-indigo-600 text-white border-indigo-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <Database className="h-4 w-4 inline mr-1" />
                        Raw Data
                      </button>
                    </div>
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
                            <p className="text-purple-900">${results.execution_details.cost_estimate_usd?.toFixed(4) || '0.0000'}</p>
                          </div>
                        </div>
                      )}

                      {(() => {
                        // Transform data for visualization
                        const transformedData = results.rows.map(row => {
                          const obj: any = {};
                          results.columns.forEach((col, idx) => {
                            obj[col.name] = row[idx];
                          });
                          return obj;
                        });

                        // Extract instance and brand info
                        const instanceInfo = undefined; // Will be implemented with proper instance data

                        const brands = execution?.execution_parameters?.brands || 
                                      execution?.execution_parameters?.brand_id ? 
                                      [execution.execution_parameters.brand_id] : [];

                        switch (viewMode) {
                          case 'enhanced':
                            return (
                              <EnhancedResultsTable
                                data={transformedData}
                                instanceInfo={instanceInfo}
                                brands={brands}
                                executionContext={{
                                  workflowName: execution?.workflow_id || '',
                                  executionId: executionId,
                                  startTime: execution?.started_at,
                                  endTime: execution?.completed_at
                                }}
                              />
                            );
                          
                          case 'charts':
                            return (
                              <DataVisualization
                                data={transformedData}
                                columns={results.columns.map(c => c.name)}
                                title="Query Results Visualization"
                                brands={brands}
                              />
                            );
                          
                          case 'ai':
                            // AI analysis will be integrated later
                            return (
                              <div className="bg-gray-50 rounded-lg p-6">
                                <h4 className="text-lg font-medium mb-4">AI-Powered Analysis</h4>
                                <p className="text-sm text-gray-600">AI analysis feature coming soon...</p>
                              </div>
                            );
                          
                          case 'table':
                          default:
                            return (
                              <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                  <thead className="bg-gray-50">
                                    <tr>
                                      {results.columns.map((col) => (
                                        <th
                                          key={col.name}
                                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                                        >
                                          {col.name}
                                        </th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-gray-200">
                                    {results.rows.map((row, idx) => (
                                      <tr key={idx}>
                                        {row.map((cell, cellIdx) => (
                                          <td key={cellIdx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {cell}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            );
                        }
                      })()}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <AlertCircle className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                      <p>No results available</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Output Location */}
          {execution?.output_location && (
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2">Output Location</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <code className="text-sm text-gray-700">{execution.output_location}</code>
                {execution.size_bytes && (
                  <p className="text-sm text-gray-500 mt-1">
                    Size: {(execution.size_bytes / 1024 / 1024).toFixed(2)} MB
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}