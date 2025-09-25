import { useState, useEffect, useCallback } from 'react';
import type { FC, ReactNode } from 'react';
import type { DetectedParameter } from '../../utils/parameterDetection';
import { ASINSelector } from './ASINSelector';
import { DateRangeSelector } from './DateRangeSelector';
import { AlertCircle } from 'lucide-react';

interface UniversalParameterSelectorProps {
  parameter: DetectedParameter;
  instanceId?: string;  // Now optional
  brandId?: string;  // Now optional
  value: any;
  onChange: (value: any) => void;
  showAll?: boolean;  // Show all items without filtering
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
  showAll = true,  // Default to showing all items
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
            showAll={showAll}
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
        // For campaign parameters, use a pattern input for LIKE queries
        // This allows wildcards like %brand% to filter campaigns
        return (
          <div className="space-y-1">
            <input
              type="text"
              value={value || ''}
              onChange={(e) => handleChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder={`Enter campaign pattern (e.g., %brand% for LIKE queries)`}
            />
            <p className="text-xs text-gray-500">
              Use % for wildcard matching (e.g., %Nike% matches all campaigns with "Nike" in the name)
            </p>
          </div>
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
  instanceId?: string;  // Now optional
  brandId?: string;  // Now optional
  onChange: (parameterName: string, value: any) => void;
  showAll?: boolean;  // Show all items without filtering
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
  showAll = true,  // Default to showing all items
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
          showAll={showAll}
        />
      ))}
    </div>
  );
};