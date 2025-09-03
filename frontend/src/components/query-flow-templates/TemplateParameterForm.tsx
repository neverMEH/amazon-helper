import React, { useState, useEffect, useCallback } from 'react';
import type { QueryFlowTemplate, ParameterFormValues, TemplateParameter } from '../../types/queryFlowTemplate';
import BaseParameterInput from './parameters/BaseParameterInput';

interface TemplateParameterFormProps {
  template: QueryFlowTemplate;
  values: ParameterFormValues;
  onChange: (values: ParameterFormValues) => void;
  onValidationChange: (isValid: boolean, errors: Record<string, string>) => void;
  disabled?: boolean;
  className?: string;
}

const TemplateParameterForm: React.FC<TemplateParameterFormProps> = ({
  template,
  values,
  onChange,
  onValidationChange,
  disabled = false,
  className = ''
}) => {
  const [parameterErrors, setParameterErrors] = useState<Record<string, string>>({});
  
  // Get sorted parameters by order_index
  const sortedParameters = template.parameters?.sort((a, b) => a.order_index - b.order_index) || [];

  // Check if parameter should be shown based on dependencies
  const isParameterVisible = useCallback((parameter: TemplateParameter): boolean => {
    if (!parameter.dependencies || parameter.dependencies.length === 0) {
      return true;
    }

    // Check if all dependencies are met
    return parameter.dependencies.every(depName => {
      const depValue = values[depName];
      
      // For boolean dependencies, check if true
      if (typeof depValue === 'boolean') {
        return depValue === true;
      }
      
      // For other types, check if value exists and is not empty
      if (Array.isArray(depValue)) {
        return depValue.length > 0;
      }
      
      return depValue != null && depValue !== '';
    });
  }, [values]);

  // Handle parameter value change
  const handleParameterChange = useCallback((paramName: string, value: any) => {
    const newValues = { ...values, [paramName]: value };
    onChange(newValues);
  }, [values, onChange]);

  // Handle parameter error change
  const handleParameterError = useCallback((paramName: string, error: string | null) => {
    setParameterErrors(prev => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[paramName] = error;
      } else {
        delete newErrors[paramName];
      }
      return newErrors;
    });
  }, []);

  // Calculate validation state and notify parent
  useEffect(() => {
    const visibleParameters = sortedParameters.filter(isParameterVisible);
    const requiredParameters = visibleParameters.filter(p => p.required);
    
    // Check for missing required parameters
    const missingRequired = requiredParameters.filter(p => {
      const value = values[p.parameter_name];
      if (Array.isArray(value)) {
        return value.length === 0;
      }
      return value == null || value === '';
    });

    // Build complete error object
    const allErrors: Record<string, string> = { ...parameterErrors };
    
    // Add missing required field errors
    missingRequired.forEach(param => {
      if (!allErrors[param.parameter_name]) {
        allErrors[param.parameter_name] = 'This field is required';
      }
    });

    // Calculate if form is valid
    const isValid = Object.keys(allErrors).length === 0;
    
    onValidationChange(isValid, allErrors);
  }, [values, parameterErrors, sortedParameters, isParameterVisible, onValidationChange]);

  // Set default values when template changes
  useEffect(() => {
    const newValues = { ...values };
    let hasChanges = false;

    sortedParameters.forEach(param => {
      if (param.default_value != null && values[param.parameter_name] == null) {
        newValues[param.parameter_name] = param.default_value;
        hasChanges = true;
      }
    });

    if (hasChanges) {
      onChange(newValues);
    }
  }, [template.id, sortedParameters]);

  if (!template.parameters || template.parameters.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <p>This template has no configurable parameters.</p>
      </div>
    );
  }

  const visibleParameters = sortedParameters.filter(isParameterVisible);

  if (visibleParameters.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <p>No parameters are currently available based on your selections.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">
          Template Parameters
        </h3>
        <p className="text-sm text-blue-700">
          Configure the parameters for "{template.name}". Required fields are marked with an asterisk (*).
        </p>
      </div>

      <div className="space-y-4">
        {visibleParameters.map((parameter) => (
          <div key={parameter.parameter_name} className="space-y-1">
            <BaseParameterInput
              parameter={parameter}
              value={values[parameter.parameter_name]}
              onChange={(value) => handleParameterChange(parameter.parameter_name, value)}
              onError={(error) => handleParameterError(parameter.parameter_name, error)}
              disabled={disabled}
            />
          </div>
        ))}
      </div>

      {/* Parameter dependencies info */}
      {template.parameters.some(p => p.dependencies && p.dependencies.length > 0) && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Parameter Dependencies
          </h4>
          <div className="text-xs text-gray-600 space-y-1">
            {template.parameters
              .filter(p => p.dependencies && p.dependencies.length > 0)
              .map(param => (
                <div key={param.parameter_name}>
                  <span className="font-medium">{param.display_name}</span>
                  {' depends on: '}
                  <span className="italic">
                    {param.dependencies!.map(dep => {
                      const depParam = template.parameters?.find(p => p.parameter_name === dep);
                      return depParam?.display_name || dep;
                    }).join(', ')}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Debug info in development */}
      {process.env.NODE_ENV === 'development' && (
        <details className="bg-gray-100 border border-gray-300 rounded-md">
          <summary className="p-2 cursor-pointer text-sm font-medium text-gray-700">
            Debug: Parameter Values
          </summary>
          <pre className="p-2 text-xs bg-gray-50 overflow-auto">
            {JSON.stringify(values, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

export default TemplateParameterForm;