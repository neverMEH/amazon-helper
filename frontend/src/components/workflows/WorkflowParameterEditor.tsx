import { useState, useEffect, useCallback } from 'react';
import { Wand2, Settings } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { ParameterDetector, ParameterSelectorList } from '../parameter-detection';
import type { DetectedParameter } from '../../utils/parameterDetection';
import api from '../../services/api';

interface WorkflowParameterEditorProps {
  sqlQuery: string;
  instanceId: string;
  parameters: Record<string, any>;
  onChange: (parameters: Record<string, any>) => void;
  className?: string;
}

/**
 * Enhanced parameter editor that integrates automatic parameter detection
 * with contextual selectors for ASINs, dates, and campaigns
 */
export default function WorkflowParameterEditor({
  sqlQuery,
  instanceId,
  parameters,
  onChange,
  className = ''
}: WorkflowParameterEditorProps) {
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>(parameters || {});
  const [isAutoDetectEnabled, setIsAutoDetectEnabled] = useState(true);
  const [showManualEdit, setShowManualEdit] = useState(false);

  // Fetch instance details to get brand information
  const { data: instance } = useQuery({
    queryKey: ['instance', instanceId],
    queryFn: async () => {
      const response = await api.get(`/instances/${instanceId}`);
      return response.data;
    },
    enabled: !!instanceId,
    staleTime: 5 * 60 * 1000
  });

  // Get brand tag from instance's brands array
  const brandId = instance?.brands?.[0]?.brandTag || instance?.brands?.[0]?.brand_tag || '';

  // Handle detected parameters
  const handleParametersDetected = useCallback((params: DetectedParameter[]) => {
    setDetectedParameters(params);
    
    // Initialize values for new parameters
    const newValues: Record<string, any> = {};
    params.forEach(param => {
      if (!(param.name in parameterValues)) {
        newValues[param.name] = '';
      }
    });
    
    if (Object.keys(newValues).length > 0) {
      const updated = { ...parameterValues, ...newValues };
      setParameterValues(updated);
      onChange(updated);
    }
  }, [parameterValues, onChange]);

  // Handle parameter value change
  const handleParameterChange = useCallback((parameterName: string, value: any) => {
    const updated = {
      ...parameterValues,
      [parameterName]: value
    };
    setParameterValues(updated);
    onChange(updated);
  }, [parameterValues, onChange]);

  // Handle manual parameter editing
  const handleManualParameterChange = useCallback((key: string, value: string) => {
    handleParameterChange(key, value);
  }, [handleParameterChange]);

  // Initialize parameter values from props
  useEffect(() => {
    if (parameters && Object.keys(parameters).length > 0) {
      setParameterValues(parameters);
    }
  }, [parameters]);

  // Toggle between auto-detect and manual modes
  const toggleAutoDetect = () => {
    setIsAutoDetectEnabled(!isAutoDetectEnabled);
    if (!isAutoDetectEnabled) {
      setShowManualEdit(false);
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Query Parameters</h3>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={toggleAutoDetect}
            className={`flex items-center px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              isAutoDetectEnabled
                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Wand2 className="h-4 w-4 mr-1.5" />
            {isAutoDetectEnabled ? 'Auto-detect ON' : 'Auto-detect OFF'}
          </button>
          
          {!isAutoDetectEnabled && (
            <button
              type="button"
              onClick={() => setShowManualEdit(!showManualEdit)}
              className="flex items-center px-3 py-1.5 text-sm font-medium bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
            >
              <Settings className="h-4 w-4 mr-1.5" />
              Manual Edit
            </button>
          )}
        </div>
      </div>

      {/* Parameter Detection (invisible component) */}
      {isAutoDetectEnabled && sqlQuery && (
        <ParameterDetector
          sqlQuery={sqlQuery}
          onParametersDetected={handleParametersDetected}
          debounceMs={500}
        />
      )}

      {/* Auto-detected Parameters with Smart Selectors */}
      {isAutoDetectEnabled && detectedParameters.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start mb-3">
            <Wand2 className="h-5 w-5 text-blue-600 mt-0.5 mr-2" />
            <div>
              <p className="text-sm font-medium text-blue-900">
                Auto-detected {detectedParameters.length} parameter{detectedParameters.length !== 1 ? 's' : ''}
              </p>
              <p className="text-xs text-blue-700 mt-1">
                Select values from all available options
              </p>
            </div>
          </div>
          
          <ParameterSelectorList
            parameters={detectedParameters}
            values={parameterValues}
            instanceId={instanceId}
            brandId={brandId}
            onChange={handleParameterChange}
            showAll={true}
            className="mt-4"
          />
        </div>
      )}


      {/* Manual Parameter Editing */}
      {(!isAutoDetectEnabled || showManualEdit) && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="mb-3">
            <p className="text-sm font-medium text-gray-700">Manual Parameter Entry</p>
            <p className="text-xs text-gray-500 mt-1">
              Enter parameter values directly
            </p>
          </div>
          
          {Object.keys(parameterValues).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(parameterValues).map(([key, value]) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {key}
                  </label>
                  <input
                    type="text"
                    value={value || ''}
                    onChange={(e) => handleManualParameterChange(key, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder={`Enter value for ${key}`}
                  />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">
              No parameters found in the query
            </p>
          )}
        </div>
      )}

      {/* No parameters detected message */}
      {isAutoDetectEnabled && detectedParameters.length === 0 && sqlQuery && (
        <div className="text-sm text-gray-500 italic">
          No parameters detected in the SQL query
        </div>
      )}

      {/* Usage hint */}
      {detectedParameters.length > 0 && (
        <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
          <p className="font-medium mb-1">Supported parameter formats:</p>
          <ul className="list-disc list-inside space-y-0.5 text-gray-600">
            <li>Mustache brackets: {'{{parameter_name}}'}</li>
            <li>Colon prefix: :parameter_name</li>
            <li>Dollar sign prefix: $parameter_name</li>
          </ul>
        </div>
      )}
    </div>
  );
}