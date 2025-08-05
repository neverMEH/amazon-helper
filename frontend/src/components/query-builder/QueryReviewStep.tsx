import { useState, useEffect } from 'react';
import { Check, AlertTriangle, Database, Clock, FileText, DollarSign, Info } from 'lucide-react';

interface QueryReviewStepProps {
  state: any;
  setState: (state: any) => void;
  instances: any[];
}

export default function QueryReviewStep({ state, instances }: QueryReviewStepProps) {
  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);
  const [estimatedRuntime, setEstimatedRuntime] = useState<number | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  const selectedInstance = instances.find(i => i.instanceId === state.instanceId || i.id === state.instanceId);

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
    if (selectedInstance?.instanceId?.includes('sandbox')) {
      newWarnings.push('Using sandbox instance. Results may be limited.');
    }
    if (!state.exportSettings.email) {
      newWarnings.push('No email configured. You won\'t receive export notifications.');
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
                <p className="text-sm text-gray-900">
                  {state.exportSettings.name || 'Unnamed Export'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Format</p>
                <p className="text-sm text-gray-900">{state.exportSettings.format}</p>
              </div>
              {state.exportSettings.email && (
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="text-sm text-gray-900">{state.exportSettings.email}</p>
                </div>
              )}
              {state.exportSettings.password && (
                <div className="flex items-center text-xs text-green-600">
                  <Check className="h-3 w-3 mr-1" />
                  Password protected
                </div>
              )}
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
  );
}