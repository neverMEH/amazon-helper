import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Download, RefreshCw, AlertCircle, CheckCircle, Clock, Loader2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';

interface ExecutionResultsProps {
  executionId: string;
  onClose: () => void;
}

interface ExecutionStatus {
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  row_count?: number;
  triggered_by: string;
  amc_execution_id?: string;
}

interface ExecutionResult {
  columns: Array<{
    name: string;
    type: string;
  }>;
  rows: any[][];
  total_rows: number;
  sample_size: number;
  execution_details: {
    query_runtime_seconds: number;
    data_scanned_gb: number;
    cost_estimate_usd: number;
  };
}

export default function ExecutionResults({ executionId, onClose }: ExecutionResultsProps) {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch execution status
  const { data: status } = useQuery<ExecutionStatus>({
    queryKey: ['execution-status', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/status`);
      return response.data;
    },
    refetchInterval: (query) => {
      const data = query.state.data;
      if (autoRefresh && data && (data.status === 'running' || data.status === 'pending')) {
        return 2000;
      }
      return false;
    },
  });

  // Fetch execution results (only if completed)
  const { data: results, isLoading: resultsLoading } = useQuery<ExecutionResult>({
    queryKey: ['execution-results', executionId],
    queryFn: async () => {
      const response = await api.get(`/workflows/executions/${executionId}/results`);
      return response.data;
    },
    enabled: status?.status === 'completed',
  });

  // Stop auto-refresh when component unmounts or execution completes
  useEffect(() => {
    if (status?.status === 'completed' || status?.status === 'failed') {
      setAutoRefresh(false);
    }
  }, [status?.status]);

  const handleDownloadResults = async () => {
    try {
      const response = await api.get(`/workflows/executions/${executionId}/results?format=csv`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `execution_${executionId}_results.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Results downloaded successfully');
    } catch (error) {
      toast.error('Failed to download results');
    }
  };

  const getStatusIcon = () => {
    switch (status?.status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status?.status) {
      case 'pending':
        return 'Pending';
      case 'running':
        return 'Running';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  // const formatBytes = (bytes: number) => {
  //   if (bytes < 1024) return `${bytes} B`;
  //   if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  //   if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  //   return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
  // };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-medium text-gray-900">
              Execution Results
            </h3>
            {getStatusIcon()}
            <span className={`text-sm font-medium ${
              status?.status === 'completed' ? 'text-green-600' :
              status?.status === 'failed' ? 'text-red-600' :
              status?.status === 'running' ? 'text-blue-600' :
              'text-yellow-600'
            }`}>
              {getStatusText()}
            </span>
            {status?.progress !== undefined && status.progress > 0 && status.progress < 100 && (
              <span className="text-sm text-gray-500">
                ({status.progress}%)
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {(status?.status === 'pending' || status?.status === 'running') && (
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-2 rounded-md ${
                  autoRefresh
                    ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
              >
                <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
              </button>
            )}
            {status?.status === 'completed' && results && (
              <button
                onClick={handleDownloadResults}
                className="p-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                title="Download results as CSV"
              >
                <Download className="h-4 w-4" />
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Execution Details */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Execution ID</p>
              <p className="font-mono text-sm">{executionId}</p>
              {status?.amc_execution_id && (
                <>
                  <p className="text-sm text-gray-500 mt-2">AMC Execution ID</p>
                  <p className="font-mono text-sm">{status.amc_execution_id}</p>
                </>
              )}
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Duration</p>
              <p className="text-lg font-medium">{formatDuration(status?.duration_seconds)}</p>
              {status?.started_at && (
                <p className="text-xs text-gray-500 mt-1">
                  Started: {new Date(status.started_at).toLocaleString()}
                </p>
              )}
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Triggered By</p>
              <p className="text-lg font-medium capitalize">{status?.triggered_by || 'Unknown'}</p>
              {status?.row_count !== undefined && (
                <p className="text-xs text-gray-500 mt-1">
                  Rows: {status.row_count != null ? status.row_count.toLocaleString() : '0'}
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {status?.status === 'failed' && status.error_message && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Execution Failed</h3>
                  <p className="mt-2 text-sm text-red-700">{status.error_message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Results Table */}
          {status?.status === 'completed' && results && (
            <>
              {/* Query Statistics */}
              <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-blue-600">Query Runtime</p>
                  <p className="text-lg font-medium text-blue-900">
                    {formatDuration(results.execution_details?.query_runtime_seconds)}
                  </p>
                </div>
                
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-sm text-green-600">Data Scanned</p>
                  <p className="text-lg font-medium text-green-900">
                    {results.execution_details?.data_scanned_gb?.toFixed(2) || '0'} GB
                  </p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-4">
                  <p className="text-sm text-purple-600">Estimated Cost</p>
                  <p className="text-lg font-medium text-purple-900">
                    ${results.execution_details?.cost_estimate_usd?.toFixed(4) || '0.00'}
                  </p>
                </div>
              </div>

              {/* Results Summary */}
              <div className="mb-4 flex items-center justify-between">
                <h4 className="text-lg font-medium text-gray-900">
                  Query Results
                </h4>
                <p className="text-sm text-gray-500">
                  Showing {results.sample_size} of {results.total_rows != null ? results.total_rows.toLocaleString() : '0'} rows
                </p>
              </div>

              {/* Results Table */}
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {results.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          {column.name}
                          <span className="ml-1 text-gray-400 normal-case">
                            ({column.type})
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50">
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                          >
                            {cell === null ? (
                              <span className="text-gray-400 italic">NULL</span>
                            ) : (
                              String(cell)
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {results.total_rows > results.sample_size && (
                <p className="mt-4 text-sm text-gray-500 text-center">
                  Download the full results to see all {results.total_rows != null ? results.total_rows.toLocaleString() : '0'} rows
                </p>
              )}
            </>
          )}

          {/* Loading State for Results */}
          {status?.status === 'completed' && resultsLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 text-gray-400 animate-spin" />
              <span className="ml-2 text-gray-500">Loading results...</span>
            </div>
          )}

          {/* Running State */}
          {(status?.status === 'pending' || status?.status === 'running') && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-12 w-12 text-blue-500 animate-spin mb-4" />
              <p className="text-lg text-gray-700 mb-2">
                {status.status === 'pending' ? 'Preparing execution...' : 'Executing query...'}
              </p>
              {status.progress > 0 && (
                <div className="w-full max-w-xs">
                  <div className="bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${status.progress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 text-center mt-2">
                    {status.progress}% complete
                  </p>
                </div>
              )}
              <p className="text-sm text-gray-500 mt-4">
                This may take a few minutes depending on the query complexity
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}