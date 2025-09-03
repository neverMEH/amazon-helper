import React, { useState, useEffect } from 'react';
import { Hash } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const NumberParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<string>(value?.toString() || '');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalValue(value?.toString() || '');
  }, [value]);

  const validateNumber = (str: string): boolean => {
    if (!str && parameter.required) {
      setError('This field is required');
      onError?.('This field is required');
      return false;
    }

    if (!str) {
      setError(null);
      onError?.(null);
      return true;
    }

    const num = parseFloat(str);
    
    if (isNaN(num)) {
      setError('Must be a valid number');
      onError?.('Must be a valid number');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check if integer is required
    if (rules.type === 'integer' && !Number.isInteger(num)) {
      setError('Must be a whole number');
      onError?.('Must be a whole number');
      return false;
    }

    // Check min value
    if (rules.min_value !== undefined && num < rules.min_value) {
      const error = `Must be at least ${rules.min_value}`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check max value
    if (rules.max_value !== undefined && num > rules.max_value) {
      const error = `Must not exceed ${rules.max_value}`;
      setError(error);
      onError?.(error);
      return false;
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    
    if (validateNumber(newValue)) {
      const num = parseFloat(newValue);
      if (!isNaN(num)) {
        onChange(num);
      } else if (newValue === '') {
        onChange(null);
      }
    }
  };

  const handleBlur = () => {
    validateNumber(localValue);
  };

  // Get input constraints
  const getInputProps = () => {
    const props: any = {
      type: 'number'
    };

    if (parameter.validation_rules.min_value !== undefined) {
      props.min = parameter.validation_rules.min_value;
    }

    if (parameter.validation_rules.max_value !== undefined) {
      props.max = parameter.validation_rules.max_value;
    }

    if (parameter.validation_rules.type === 'integer') {
      props.step = 1;
    } else {
      props.step = 'any';
    }

    return props;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        <input
          value={localValue}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          required={parameter.required}
          placeholder={parameter.ui_config.placeholder}
          className={`
            block w-full px-3 py-2 pr-10
            border rounded-md shadow-sm
            focus:ring-indigo-500 focus:border-indigo-500
            ${error ? 'border-red-300' : 'border-gray-300'}
            ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
          `}
          {...getInputProps()}
        />
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <Hash className="h-4 w-4 text-gray-400" />
        </div>
      </div>

      {parameter.ui_config.help_text && !error && (
        <p className="text-xs text-gray-500">
          {parameter.ui_config.help_text}
        </p>
      )}

      {error && (
        <p className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
};

export default NumberParameter;