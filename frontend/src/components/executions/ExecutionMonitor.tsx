import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Database, 
  ExternalLink,
  Eye,
  EyeOff
} from 'lucide-react';

interface ExecutionMonitorProps {
  instanceId?: string;
  workflowId?: string;
  refreshInterval?: number; // seconds
  showDiagnostics?: boolean;
}

interface ExecutionStatus {
  internal_execution_id: string;
  amc_execution_id?: string;
  status: string;
  progress: number;
  started_at: string;
  completed_at?: string;
  workflow_name?: string;
  error_message?: string;
  duration_seconds?: number;
  row_count?: number;
}

interface CrossReferenceResults {
  matched: Array<{
    internal_execution_id: string;
    amc_execution_id: string;
    workflow_name: string;
    database_status: string;
    amc_status: string;
    started_at: string;
  }>;
  database_only: Array<{
    internal_execution_id: string;
    amc_execution_id?: string;
    workflow_name: string;
    status: string;
    started_at: string;
  }>;
  amc_only: Array<{
    amc_execution_id: string;
    workflow_id?: string;
    amc_status: string;
    created_time?: string;
  }>;
  missing_amc_ids: Array<{
    internal_execution_id: string;
    workflow_name: string;
    status: string;
    started_at: string;
  }>;
}

interface ExecutionMonitorData {
  workflow_id?: string;
  workflow_name?: string;
  instance_id?: string;
  running_executions: ExecutionStatus[];
  recent_executions: ExecutionStatus[];
  missing_amc_ids: ExecutionStatus[];
  execution_summary: {
    pending: number;
    running: number;
    completed: number;
    failed: number;
    missing_amc_id: number;
  };
  diagnostics: {
    has_running_executions: boolean;
    has_missing_amc_ids: boolean;
    recommendations: Array<{
      type: string;
      message: string;
      action: string;
    }>;
  };
}

interface CrossReferenceData {
  success: boolean;
  instance_id: string;
  database_executions_count: number;
  amc_executions_count: number;
  cross_reference_results: CrossReferenceResults;
  summary: {
    matched_executions: number;
    database_only: number;
    amc_only: number;
    missing_amc_ids: number;
  };
}

const ExecutionMonitor: React.FC<ExecutionMonitorProps> = ({
  instanceId,
  workflowId,
  refreshInterval = 5,
  showDiagnostics = true
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Query for workflow execution status (if workflowId provided)
  const { 
    data: workflowData, 
    isLoading: workflowLoading,
    error: workflowError,
    refetch: refetchWorkflow
  } = useQuery<ExecutionMonitorData>({
    queryKey: ['workflow-execution-status', workflowId],
    queryFn: async () => {
      const response = await axios.get(`/api/workflows/${workflowId}/execution-status`);
      return response.data;
    },
    enabled: !!workflowId,
    refetchInterval: refreshInterval * 1000,
    gcTime: 30000,
    staleTime: 0
  });

  // Query for cross-reference data (if instanceId provided)
  const { 
    data: crossRefData, 
    isLoading: crossRefLoading,
    error: crossRefError,
    refetch: refetchCrossRef
  } = useQuery<CrossReferenceData>({
    queryKey: ['execution-cross-reference', instanceId],
    queryFn: async () => {
      const response = await axios.get(`/api/workflows/executions/cross-reference?instance_id=${instanceId}`);
      return response.data;
    },
    enabled: !!instanceId,
    refetchInterval: refreshInterval * 1000,
    gcTime: 30000,
    staleTime: 0
  });

  // Update last refresh time when data changes
  useEffect(() => {
    if (workflowData || crossRefData) {
      setLastRefresh(new Date());
    }
  }, [workflowData, crossRefData]);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': case 'succeeded': return 'text-green-600 bg-green-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'failed': case 'cancelled': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const manualRefresh = async () => {
    if (workflowId) await refetchWorkflow();
    if (instanceId) await refetchCrossRef();
  };

  const isLoading = workflowLoading || crossRefLoading;
  const hasError = workflowError || crossRefError;

  return (
    <div className="bg-white border rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center space-x-2">
          <Database className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold">Execution Monitor</h3>
          {isLoading && <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />}
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1 text-gray-600 hover:text-gray-800"
            title={showDetails ? 'Hide details' : 'Show details'}
          >
            {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
          <button
            onClick={manualRefresh}
            disabled={isLoading}
            className="p-1 text-gray-600 hover:text-gray-800 disabled:opacity-50"
            title="Refresh now"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Error State */}
      {hasError && (
        <div className="p-4 bg-red-50 border-l-4 border-red-400">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-800">
              Failed to load execution data: {(workflowError as any)?.message || (crossRefError as any)?.message}
            </span>
          </div>
        </div>
      )}

      {/* Workflow Execution Status */}
      {workflowData && (
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900">{workflowData.workflow_name}</h4>
            <div className="text-sm text-gray-500">
              {workflowData.running_executions.length} running • {workflowData.recent_executions.length} total
            </div>
          </div>

          {/* Running Executions */}
          {workflowData.running_executions.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-sm font-medium text-gray-700 flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                Running Executions ({workflowData.running_executions.length})
              </h5>
              {workflowData.running_executions.map((exec) => (
                <div key={exec.internal_execution_id} className="p-3 bg-blue-50 border border-blue-200 rounded">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(exec.status)}`}>
                          {exec.status}
                        </span>
                        <span className="text-sm font-mono text-gray-600">
                          {exec.internal_execution_id.substring(0, 8)}...
                        </span>
                        {exec.amc_execution_id ? (
                          <span className="text-xs text-green-600">✓ AMC ID</span>
                        ) : (
                          <span className="text-xs text-red-600">⚠ No AMC ID</span>
                        )}
                      </div>
                      {showDetails && (
                        <div className="text-xs text-gray-500 space-y-1">
                          <div>Internal ID: {exec.internal_execution_id}</div>
                          {exec.amc_execution_id && <div>AMC ID: {exec.amc_execution_id}</div>}
                          <div>Started: {formatTimestamp(exec.started_at)}</div>
                          {exec.error_message && (
                            <div className="text-red-600">Error: {exec.error_message}</div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{exec.progress}%</div>
                      <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${exec.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Missing AMC IDs */}
          {workflowData.missing_amc_ids.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-sm font-medium text-red-700 flex items-center">
                <AlertTriangle className="w-4 h-4 mr-1" />
                Missing AMC IDs ({workflowData.missing_amc_ids.length})
              </h5>
              {workflowData.missing_amc_ids.slice(0, showDetails ? undefined : 3).map((exec) => (
                <div key={exec.internal_execution_id} className="p-2 bg-red-50 border border-red-200 rounded text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-gray-600">
                      {exec.internal_execution_id.substring(0, 8)}...
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(exec.status)}`}>
                      {exec.status}
                    </span>
                  </div>
                </div>
              ))}
              {!showDetails && workflowData.missing_amc_ids.length > 3 && (
                <div className="text-xs text-gray-500 text-center">
                  +{workflowData.missing_amc_ids.length - 3} more
                </div>
              )}
            </div>
          )}

          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
            <div className="text-center p-2 bg-yellow-50 rounded">
              <div className="font-medium text-yellow-800">{workflowData.execution_summary.pending}</div>
              <div className="text-yellow-600">Pending</div>
            </div>
            <div className="text-center p-2 bg-blue-50 rounded">
              <div className="font-medium text-blue-800">{workflowData.execution_summary.running}</div>
              <div className="text-blue-600">Running</div>
            </div>
            <div className="text-center p-2 bg-green-50 rounded">
              <div className="font-medium text-green-800">{workflowData.execution_summary.completed}</div>
              <div className="text-green-600">Completed</div>
            </div>
            <div className="text-center p-2 bg-red-50 rounded">
              <div className="font-medium text-red-800">{workflowData.execution_summary.failed}</div>
              <div className="text-red-600">Failed</div>
            </div>
            <div className="text-center p-2 bg-orange-50 rounded">
              <div className="font-medium text-orange-800">{workflowData.execution_summary.missing_amc_id}</div>
              <div className="text-orange-600">No AMC ID</div>
            </div>
          </div>

          {/* Diagnostics and Recommendations */}
          {showDiagnostics && workflowData.diagnostics.recommendations.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-sm font-medium text-gray-700 flex items-center">
                <CheckCircle className="w-4 h-4 mr-1" />
                Recommendations
              </h5>
              {workflowData.diagnostics.recommendations.map((rec, index) => (
                <div key={index} className="p-3 bg-blue-50 border-l-4 border-blue-400">
                  <div className="text-sm font-medium text-blue-800">{rec.message}</div>
                  <div className="text-xs text-blue-600 mt-1">{rec.action}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Cross-Reference Data */}
      {crossRefData && (
        <div className="p-4 border-t space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900">Instance Cross-Reference</h4>
            <div className="text-sm text-gray-500">
              {crossRefData.database_executions_count} DB • {crossRefData.amc_executions_count} AMC
            </div>
          </div>

          {/* Cross-Reference Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
            <div className="text-center p-2 bg-green-50 rounded">
              <div className="font-medium text-green-800">{crossRefData.summary.matched_executions}</div>
              <div className="text-green-600">Matched</div>
            </div>
            <div className="text-center p-2 bg-yellow-50 rounded">
              <div className="font-medium text-yellow-800">{crossRefData.summary.database_only}</div>
              <div className="text-yellow-600">DB Only</div>
            </div>
            <div className="text-center p-2 bg-blue-50 rounded">
              <div className="font-medium text-blue-800">{crossRefData.summary.amc_only}</div>
              <div className="text-blue-600">AMC Only</div>
            </div>
            <div className="text-center p-2 bg-red-50 rounded">
              <div className="font-medium text-red-800">{crossRefData.summary.missing_amc_ids}</div>
              <div className="text-red-600">Missing IDs</div>
            </div>
          </div>

          {/* Details */}
          {showDetails && (
            <div className="space-y-3">
              {/* Database Only Executions */}
              {crossRefData.cross_reference_results.database_only.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-yellow-700 mb-2">
                    In Database but Not in AMC ({crossRefData.cross_reference_results.database_only.length})
                  </h6>
                  <div className="space-y-1">
                    {crossRefData.cross_reference_results.database_only.map((exec, index) => (
                      <div key={index} className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                        <div className="flex justify-between">
                          <span className="font-mono">{exec.internal_execution_id.substring(0, 8)}...</span>
                          <span className={`px-1 py-0.5 rounded text-xs ${getStatusColor(exec.status)}`}>
                            {exec.status}
                          </span>
                        </div>
                        <div className="text-gray-600 mt-1">{exec.workflow_name}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AMC Only Executions */}
              {crossRefData.cross_reference_results.amc_only.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-blue-700 mb-2">
                    In AMC but Not in Database ({crossRefData.cross_reference_results.amc_only.length})
                  </h6>
                  <div className="space-y-1">
                    {crossRefData.cross_reference_results.amc_only.map((exec, index) => (
                      <div key={index} className="p-2 bg-blue-50 border border-blue-200 rounded text-xs">
                        <div className="flex justify-between">
                          <span className="font-mono">{exec.amc_execution_id.substring(0, 8)}...</span>
                          <span className={`px-1 py-0.5 rounded text-xs ${getStatusColor(exec.amc_status)}`}>
                            {exec.amc_status}
                          </span>
                        </div>
                        {exec.workflow_id && (
                          <div className="text-gray-600 mt-1">Workflow: {exec.workflow_id}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* No Data State */}
      {!isLoading && !hasError && !workflowData && !crossRefData && (
        <div className="p-8 text-center text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No execution data to monitor.</p>
          <p className="text-sm mt-1">Provide a workflowId or instanceId to start monitoring.</p>
        </div>
      )}
    </div>
  );
};

export default ExecutionMonitor;