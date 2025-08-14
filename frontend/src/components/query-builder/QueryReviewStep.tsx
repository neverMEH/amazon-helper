import { useState, useEffect } from 'react';
import { AlertTriangle, Database, Clock, FileText, DollarSign, Info, Play, Loader, CheckCircle, Eye } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import ExecutionErrorDetails from '../executions/ExecutionErrorDetails';
import AMCExecutionDetail from '../executions/AMCExecutionDetail';

interface QueryReviewStepProps {
  state: any;
  setState: (state: any) => void;
  instances: any[];
}

export default function QueryReviewStep({ state, instances }: QueryReviewStepProps) {
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [estimatedRuntime, setEstimatedRuntime] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionStatus, setExecutionStatus] = useState<'idle' | 'executing' | 'completed' | 'failed'>('idle');
  const [showExecutionDetail, setShowExecutionDetail] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);

  const selectedInstance = instances.find(i => i.instanceId === state.instanceId || i.id === state.instanceId);

  // Test execution mutation
  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!state.instanceId || !state.sqlQuery) {
        throw new Error('Instance and SQL query are required');
      }

      // First, save the workflow if needed
      const workflowPayload = {
        name: state.name || `Test Query - ${new Date().toISOString()}`,
        description: state.description || 'Test execution from Query Builder',
        instance_id: state.instanceId,
        sql_query: state.sqlQuery,
        parameters: state.parameters,
        is_draft: true
      };

      // Create or update workflow
      const workflowResponse = await api.post('/workflows/', workflowPayload);
      const workflowId = workflowResponse.data.workflow_id || workflowResponse.data.id;

      // Execute the workflow
      const executePayload = {
        workflow_id: workflowId,
        instance_id: state.instanceId,
        execution_parameters: state.parameters
      };

      const response = await api.post('/workflows/execute', executePayload);
      return response.data;
    },
    onSuccess: (data) => {
      setExecutionResult(data);
      setExecutionId(data.execution_id);
      setExecutionStatus('completed');
      toast.success('Query executed successfully');
    },
    onError: (error: any) => {
      console.error('Execution error:', error);
      const errorData = error.response?.data || error;
      
      // Log the error structure for debugging
      console.log('Error response data:', errorData);
      
      // Extract error message for toast
      const errorMessage = errorData.detail || errorData.error || errorData.message || 'Query execution failed';
      
      // If the error is in the detail field (from HTTPException), extract it
      let processedError = errorData;
      if (errorData.detail && typeof errorData.detail === 'string') {
        // Check if detail contains structured error information
        if (errorData.detail.includes('unable to compile') || errorData.detail.includes('SQL query was invalid')) {
          processedError = {
            error: errorData.detail,
            errorDetails: {
              failureReason: 'SQL Query Compilation Failed',
              errorMessage: errorData.detail,
              queryValidation: errorData.detail
            }
          };
        } else {
          processedError = {
            error: errorData.detail
          };
        }
      }
      
      setExecutionResult(processedError);
      setExecutionStatus('failed');
      toast.error(errorMessage);
    }
  });

  const handleTestExecution = () => {
    setExecutionStatus('executing');
    setExecutionResult(null);
    executeMutation.mutate();
  };

  useEffect(() => {
    // Simulate cost and runtime estimation
    const queryLength = state.sqlQuery.length;
    const hasJoins = state.sqlQuery.toLowerCase().includes('join');
    const hasAggregations = state.sqlQuery.toLowerCase().includes('group by');
    
    // Simple estimation logic
    const baseCost = 0.001;
    const costMultiplier = hasJoins ? 2 : 1;
    const aggMultiplier = hasAggregations ? 1.5 : 1;
    const estimatedCost = baseCost * costMultiplier * aggMultiplier * (queryLength / 100);
    setEstimatedCost(Math.round(estimatedCost * 1000) / 1000);

    // Runtime estimation (in seconds)
    const baseRuntime = 10;
    const runtimeMultiplier = hasJoins ? 3 : 1;
    const aggRuntimeMultiplier = hasAggregations ? 2 : 1;
    const estimatedTime = baseRuntime * runtimeMultiplier * aggRuntimeMultiplier;
    setEstimatedRuntime(estimatedTime);

    // Generate warnings
    const newWarnings = [];
    if (!state.name) {
      newWarnings.push('Query name is not set. Consider adding a descriptive name.');
    }
    if (Object.keys(state.parameters).length > 5) {
      newWarnings.push('Query has many parameters. Ensure all values are correct.');
    }
    setWarnings(newWarnings);
  }, [state, selectedInstance]);

  // Replace parameters in SQL for preview
  const getPreviewSQL = () => {
    let previewSQL = state.sqlQuery;
    Object.entries(state.parameters).forEach(([param, value]) => {
      const regex = new RegExp(`\\{\\{${param}\\}\\}`, 'g');
      if (Array.isArray(value)) {
        previewSQL = previewSQL.replace(regex, `(${value.map(v => `'${v}'`).join(', ')})`);
      } else if (typeof value === 'string') {
        previewSQL = previewSQL.replace(regex, `'${value}'`);
      } else {
        previewSQL = previewSQL.replace(regex, String(value));
      }
    });
    return previewSQL;
  };

  const formatRuntime = (seconds: number) => {
    if (seconds < 60) return `${seconds} seconds`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <>
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Review & Execute</h2>
        <p className="text-sm text-gray-600">
          Review your query configuration before execution. Make sure all settings are correct.
        </p>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 mb-2">Warnings</h3>
              <ul className="text-sm text-yellow-700 space-y-1">
                {warnings.map((warning, index) => (
                  <li key={index} className="flex items-start">
                    <span className="block w-1.5 h-1.5 rounded-full bg-yellow-600 mt-1.5 mr-2 flex-shrink-0" />
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Summary - Left Column */}
        <div className="lg:col-span-1 space-y-4">
          {/* Instance Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <Database className="h-4 w-4 text-gray-500 mr-2" />
              <h3 className="text-sm font-semibold text-gray-900">Instance</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {selectedInstance?.instanceName || 'Not selected'}
                </p>
                <p className="text-xs text-gray-500">
                  {selectedInstance?.instanceId}
                </p>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-500">Region</p>
                <p className="text-sm text-gray-900">{selectedInstance?.region || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Timezone</p>
                <p className="text-sm text-gray-900">{state.timezone}</p>
              </div>
            </div>
          </div>

          {/* Export Settings Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <FileText className="h-4 w-4 text-gray-500 mr-2" />
              <h3 className="text-sm font-semibold text-gray-900">Export Settings</h3>
            </div>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-500">Export Name</p>
                <p className="text-sm text-gray-900 break-all">
                  {state.exportSettings.name || 'Auto-generated on execution'}
                </p>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-400">
                  All formats (CSV, Parquet, JSON) are available
                </p>
              </div>
            </div>
          </div>

          {/* Estimates Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center mb-3">
              <Info className="h-4 w-4 text-gray-500 mr-2" />
              <h3 className="text-sm font-semibold text-gray-900">Estimates</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <DollarSign className="h-3 w-3 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Estimated Cost</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  ${estimatedCost?.toFixed(3) || '0.001'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Clock className="h-3 w-3 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Estimated Runtime</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {estimatedRuntime ? formatRuntime(estimatedRuntime) : '10 seconds'}
                </span>
              </div>
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-400">
                  * Estimates based on query complexity
                </p>
              </div>
            </div>
          </div>

          {/* Test Execution Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-semibold text-gray-900">Test Execution</h3>
                <p className="text-xs text-gray-500 mt-1">Run a test to validate your query</p>
              </div>
              <button
                onClick={handleTestExecution}
                disabled={executionStatus === 'executing' || !state.instanceId || !state.sqlQuery}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {executionStatus === 'executing' ? (
                  <>
                    <Loader className="h-3 w-3 mr-1 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3 mr-1" />
                    Test Execute
                  </>
                )}
              </button>
            </div>

            {/* Execution Status Display */}
            {executionStatus !== 'idle' && (
              <div className="mt-3">
                {executionStatus === 'executing' && (
                  <div className="flex items-center text-blue-600">
                    <Loader className="h-4 w-4 mr-2 animate-spin" />
                    <span className="text-sm">Query is being executed...</span>
                  </div>
                )}

                {executionStatus === 'completed' && executionResult && (
                  <div>
                    <div className="flex items-center text-green-600 mb-2">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      <span className="text-sm font-medium">Execution successful</span>
                    </div>
                    {executionId && (
                      <button
                        onClick={() => setShowExecutionDetail(true)}
                        className="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        <Eye className="h-3 w-3 mr-1" />
                        View Results
                      </button>
                    )}
                  </div>
                )}

                {executionStatus === 'failed' && executionResult && (
                  <ExecutionErrorDetails
                    errorMessage={executionResult.error || executionResult.message || 'Query execution failed'}
                    errorDetails={executionResult.errorDetails}
                    status="failed"
                    sqlQuery={state.sqlQuery}
                    executionId={executionId || undefined}
                    instanceName={selectedInstance?.instance_name}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* SQL Preview - Right Column */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-200 rounded-lg h-full flex flex-col">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900">Final SQL Query</h3>
              <p className="text-xs text-gray-500 mt-1">
                Parameters have been substituted with their values
              </p>
            </div>
            
            {/* Parameters Summary */}
            {Object.keys(state.parameters).length > 0 && (
              <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                <h4 className="text-xs font-medium text-gray-700 mb-2">Parameter Values:</h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(state.parameters).map(([param, value]) => (
                    <div key={param} className="flex items-center text-xs">
                      <span className="font-mono text-gray-600">{`{{${param}}}`}</span>
                      <span className="mx-1">→</span>
                      <span className="font-medium text-gray-900 truncate">
                        {Array.isArray(value) ? value.join(', ') : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex-1 p-4 overflow-auto">
              <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap">
                {getPreviewSQL()}
              </pre>
            </div>

            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-4">
                  <span>{state.sqlQuery.split('\n').length} lines</span>
                  <span>{state.sqlQuery.length} characters</span>
                  <span>{Object.keys(state.parameters).length} parameters</span>
                </div>
                {state.advancedOptions.ignoreDataGaps && (
                  <span className="text-blue-600">• Ignoring data gaps</span>
                )}
                {state.advancedOptions.appendThresholdColumns && (
                  <span className="text-blue-600">• Threshold columns enabled</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Summary */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-blue-900 mb-1">Ready to Execute</h3>
            <p className="text-sm text-blue-700">
              Your query is configured and ready to run. Click "Execute Query" to start the execution.
              You will be redirected to the execution monitoring page where you can track progress in real-time.
            </p>
          </div>
        </div>
      </div>
    </div>

    {/* Execution Detail Modal */}
    {showExecutionDetail && executionId && state.instanceId && (
      <AMCExecutionDetail
        instanceId={state.instanceId}
        executionId={executionId}
        isOpen={showExecutionDetail}
        onClose={() => setShowExecutionDetail(false)}
      />
    )}
  </>
  );
}