import { useState, useEffect, useCallback } from 'react';
import type { FC, ReactNode } from 'react';
import type { DetectedParameter } from '../../utils/parameterDetection';
import { ASINSelector } from './ASINSelector';
import { DateRangeSelector } from './DateRangeSelector';
import { CampaignSelector } from './CampaignSelector';
import { AlertCircle } from 'lucide-react';

interface UniversalParameterSelectorProps {
  parameter: DetectedParameter;
  instanceId: string;
  brandId: string;
  value: any;
  onChange: (value: any) => void;
  className?: string;
}

/**
 * Container component that renders the appropriate selector based on parameter type
 */
export const UniversalParameterSelector: FC<UniversalParameterSelectorProps> = ({
  parameter,
  instanceId,
  brandId,
  value,
  onChange,
  className = ''
}) => {
  const [error, setError] = useState<string | null>(null);

  // Clear error when parameter changes
  useEffect(() => {
    setError(null);
  }, [parameter]);

  // Handle value change with error handling
  const handleChange = useCallback((newValue: any) => {
    try {
      setError(null);
      onChange(newValue);
    } catch (err) {
      console.error('Error updating parameter value:', err);
      setError('Failed to update parameter value');
    }
  }, [onChange]);

  // Render the appropriate selector based on parameter type
  const renderSelector = (): ReactNode => {
    switch (parameter.type) {
      case 'asin':
        return (
          <ASINSelector
            instanceId={instanceId}
            brandId={brandId}
            value={value}
            onChange={handleChange}
            placeholder={`Select ASINs for ${parameter.name}`}
          />
        );
      
      case 'date':
        return (
          <DateRangeSelector
            value={value}
            onChange={handleChange}
            parameterName={parameter.name}
          />
        );
      
      case 'campaign':
        return (
          <CampaignSelector
            instanceId={instanceId}
            brandId={brandId}
            value={value}
            onChange={handleChange}
            placeholder={`Select campaigns for ${parameter.name}`}
            campaignType={parameter.campaign_type}
            valueType={parameter.value_type}
          />
        );
      
      case 'unknown':
      default:
        return (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-2" />
              <div>
                <p className="text-sm font-medium text-yellow-800">
                  Unknown parameter type
                </p>
                <p className="text-sm text-yellow-700 mt-1">
                  Unable to determine the type for parameter "{parameter.name}". 
                  Please enter the value manually.
                </p>
                <input
                  type="text"
                  value={value || ''}
                  onChange={(e) => handleChange(e.target.value)}
                  className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`Enter value for ${parameter.name}`}
                />
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`universal-parameter-selector ${className}`}>
      <div className="mb-2">
        <label className="block text-sm font-medium text-gray-700">
          {parameter.name}
          <span className="ml-2 text-xs text-gray-500">
            ({parameter.type} parameter)
          </span>
        </label>
        <div className="text-xs text-gray-500 mt-1">
          Placeholder: <code className="bg-gray-100 px-1 rounded">{parameter.placeholder}</code>
        </div>
      </div>
      
      {error && (
        <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
      
      {renderSelector()}
    </div>
  );
};

interface ParameterSelectorListProps {
  parameters: DetectedParameter[];
  values: Record<string, any>;
  instanceId: string;
  brandId: string;
  onChange: (parameterName: string, value: any) => void;
  className?: string;
}

/**
 * Component that renders a list of parameter selectors
 */
export const ParameterSelectorList: FC<ParameterSelectorListProps> = ({
  parameters,
  values,
  instanceId,
  brandId,
  onChange,
  className = ''
}) => {
  if (!parameters.length) {
    return (
      <div className="text-sm text-gray-500 italic">
        No parameters detected in the SQL query
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {parameters.map((param) => (
        <UniversalParameterSelector
          key={param.name}
          parameter={param}
          instanceId={instanceId}
          brandId={brandId}
          value={values[param.name]}
          onChange={(value) => onChange(param.name, value)}
        />
      ))}
    </div>
  );
};