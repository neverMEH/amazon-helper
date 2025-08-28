import { useState, useEffect, useCallback, useMemo } from 'react';
import { ChevronDown, ChevronUp, Info, AlertCircle, Wand2 } from 'lucide-react';
import InstanceSelector from './InstanceSelector';
import { ParameterDetector, ParameterSelectorList } from '../parameter-detection';
import type { DetectedParameter } from '../../utils/parameterDetection';

interface QueryConfigurationStepEnhancedProps {
  state: any;
  setState: (state: any) => void;
  instances: any[];
  onNavigateToStep?: (step: number) => void;
  currentStep?: number;
}

const TIMEZONES = [
  { value: 'UTC', label: '-00:00 UTC' },
  { value: 'America/New_York', label: '-05:00 EST' },
  { value: 'America/Chicago', label: '-06:00 CST' },
  { value: 'America/Denver', label: '-07:00 MST' },
  { value: 'America/Los_Angeles', label: '-08:00 PST' },
  { value: 'Europe/London', label: '+00:00 GMT' },
  { value: 'Europe/Paris', label: '+01:00 CET' },
  { value: 'Asia/Tokyo', label: '+09:00 JST' },
  { value: 'Australia/Sydney', label: '+10:00 AEST' }
];

export default function QueryConfigurationStepEnhanced({ 
  state, 
  setState, 
  instances 
}: QueryConfigurationStepEnhancedProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [isAutoDetectEnabled, setIsAutoDetectEnabled] = useState(true);

  // Get selected instance details
  const selectedInstance = useMemo(() => {
    return instances?.find(inst => inst.id === state.instanceId);
  }, [instances, state.instanceId]);

  // Get brand ID from selected instance (assuming instances have brand info)
  const brandId = useMemo(() => {
    // This assumes the instance has brand information
    // You may need to adjust based on your data structure
    return selectedInstance?.brandId || selectedInstance?.brand_id || '';
  }, [selectedInstance]);

  const handleInstanceChange = (instanceId: string) => {
    setState((prev: any) => ({ ...prev, instanceId }));
  };

  const handleTimezoneChange = (timezone: string) => {
    setState((prev: any) => ({ ...prev, timezone }));
  };

  const handleAdvancedOptionChange = (option: string, value: boolean) => {
    setState((prev: any) => ({
      ...prev,
      advancedOptions: {
        ...prev.advancedOptions,
        [option]: value
      }
    }));
  };

  const handleExportSettingChange = (field: string, value: string) => {
    setState((prev: any) => ({
      ...prev,
      exportSettings: {
        ...prev.exportSettings,
        [field]: value
      }
    }));
  };

  // Auto-generate export name
  const generateExportName = useCallback(() => {
    const queryName = state.name || 'Query';
    const instanceName = selectedInstance?.instanceName || selectedInstance?.name || 'Instance';
    
    // Get date range from parameters
    const startDate = parameterValues?.start_date || parameterValues?.startDate || '';
    const endDate = parameterValues?.end_date || parameterValues?.endDate || '';
    const dateRange = startDate && endDate ? `${startDate} to ${endDate}` : 'Date Range';
    
    // Format current date and time
    const now = new Date();
    const dateTimeRan = now.toISOString().split('T')[0] + '_' + 
                       now.toTimeString().split(' ')[0].replace(/:/g, '-');
    
    return `${queryName} - ${instanceName} - ${dateRange} - ${dateTimeRan}`;
  }, [state.name, selectedInstance, parameterValues]);

  // Update export name when parameters change
  useEffect(() => {
    if (state.exportSettings && !state.exportSettings.name) {
      handleExportSettingChange('name', generateExportName());
    }
  }, [parameterValues, generateExportName]);

  // Handle detected parameters
  const handleParametersDetected = useCallback((parameters: DetectedParameter[]) => {
    setDetectedParameters(parameters);
    
    // Initialize parameter values for new parameters
    const newValues: Record<string, any> = {};
    parameters.forEach(param => {
      if (!parameterValues[param.name]) {
        newValues[param.name] = '';
      }
    });
    
    if (Object.keys(newValues).length > 0) {
      setParameterValues(prev => ({ ...prev, ...newValues }));
    }
  }, [parameterValues]);

  // Handle parameter value changes
  const handleParameterChange = useCallback((parameterName: string, value: any) => {
    setParameterValues(prev => ({
      ...prev,
      [parameterName]: value
    }));
    
    // Update state with parameter values
    setState((prev: any) => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [parameterName]: value
      }
    }));
  }, [setState]);

  // Initialize parameter values from state
  useEffect(() => {
    if (state.parameters && Object.keys(state.parameters).length > 0) {
      setParameterValues(state.parameters);
    }
  }, [state.parameters]);

  return (
    <div className="space-y-8">
      {/* Instance Selection */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Select Instance</h3>
        <InstanceSelector
          instanceId={state.instanceId}
          onChange={handleInstanceChange}
          instances={instances}
        />
        {!state.instanceId && (
          <p className="mt-2 text-sm text-red-600">
            <AlertCircle className="inline h-4 w-4 mr-1" />
            Please select an AMC instance to continue
          </p>
        )}
      </div>

      {/* Query Name and Description */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Query Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={state.name}
            onChange={(e) => setState((prev: any) => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter a descriptive name for your query"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={state.description}
            onChange={(e) => setState((prev: any) => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            placeholder="Describe what this query does (optional)"
          />
        </div>
      </div>

      {/* Parameter Detection and Selection */}
      {state.sqlQuery && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Query Parameters</h3>
            <button
              type="button"
              onClick={() => setIsAutoDetectEnabled(!isAutoDetectEnabled)}
              className={`flex items-center px-3 py-1 text-sm rounded-md transition-colors ${
                isAutoDetectEnabled
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Wand2 className="h-4 w-4 mr-1" />
              {isAutoDetectEnabled ? 'Auto-detect ON' : 'Auto-detect OFF'}
            </button>
          </div>

          {/* Parameter Detector (invisible, logic only) */}
          {isAutoDetectEnabled && (
            <ParameterDetector
              sqlQuery={state.sqlQuery}
              onParametersDetected={handleParametersDetected}
              debounceMs={500}
            />
          )}

          {/* Parameter Selectors */}
          {state.instanceId && brandId ? (
            <ParameterSelectorList
              parameters={detectedParameters}
              values={parameterValues}
              instanceId={state.instanceId}
              brandId={brandId}
              onChange={handleParameterChange}
            />
          ) : (
            state.instanceId && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">
                  <AlertCircle className="inline h-4 w-4 mr-1" />
                  Select an instance with a brand to enable parameter selection
                </p>
              </div>
            )
          )}

          {/* Manual parameter editing fallback */}
          {!isAutoDetectEnabled && Object.keys(state.parameters || {}).length > 0 && (
            <div className="space-y-3">
              {Object.entries(state.parameters).map(([key, value]) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {key}
                  </label>
                  <input
                    type="text"
                    value={value as string}
                    onChange={(e) => handleParameterChange(key, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder={`Enter value for ${key}`}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Timezone Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Timezone
        </label>
        <select
          value={state.timezone}
          onChange={(e) => handleTimezoneChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          {TIMEZONES.map(tz => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
      </div>

      {/* Advanced Options */}
      <div>
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4 mr-1" />
          ) : (
            <ChevronDown className="h-4 w-4 mr-1" />
          )}
          Advanced Options
        </button>
        
        {showAdvanced && (
          <div className="mt-4 space-y-3 pl-4 border-l-2 border-gray-200">
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={state.advancedOptions.ignoreDataGaps}
                onChange={(e) => handleAdvancedOptionChange('ignoreDataGaps', e.target.checked)}
                className="mt-1 mr-3"
              />
              <div>
                <span className="text-sm font-medium">Ignore Data Gaps</span>
                <p className="text-xs text-gray-500 mt-1">
                  Continue processing even if some data is missing
                </p>
              </div>
            </label>
            
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={state.advancedOptions.appendThresholdColumns}
                onChange={(e) => handleAdvancedOptionChange('appendThresholdColumns', e.target.checked)}
                className="mt-1 mr-3"
              />
              <div>
                <span className="text-sm font-medium">Append Threshold Columns</span>
                <p className="text-xs text-gray-500 mt-1">
                  Include threshold information in the output
                </p>
              </div>
            </label>
          </div>
        )}
      </div>

      {/* Export Settings */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Export Settings</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Export Name
            <button
              type="button"
              onClick={() => handleExportSettingChange('name', generateExportName())}
              className="ml-2 text-xs text-blue-600 hover:text-blue-700"
            >
              Auto-generate
            </button>
          </label>
          <input
            type="text"
            value={state.exportSettings.name}
            onChange={(e) => handleExportSettingChange('name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter export name"
          />
          <p className="mt-1 text-xs text-gray-500">
            <Info className="inline h-3 w-3 mr-1" />
            This name will be used for the exported data file
          </p>
        </div>
      </div>
    </div>
  );
}