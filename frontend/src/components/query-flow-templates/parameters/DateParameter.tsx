import React, { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const DateParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<string>(value || '');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  const validateDate = (dateStr: string): boolean => {
    if (!dateStr && parameter.required) {
      setError('This field is required');
      onError?.('This field is required');
      return false;
    }

    if (!dateStr) {
      setError(null);
      onError?.(null);
      return true;
    }

    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      setError('Invalid date format');
      onError?.('Invalid date format');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check min date
    if (rules.min) {
      const minDate = new Date(rules.min);
      if (date < minDate) {
        const error = `Date must be after ${minDate.toLocaleDateString()}`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    // Check max date
    if (rules.max) {
      const maxDate = new Date(rules.max);
      if (date > maxDate) {
        const error = `Date must be before ${maxDate.toLocaleDateString()}`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    // Check future dates
    if (rules.allow_future === false && date > new Date()) {
      const error = 'Future dates are not allowed';
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
    
    if (validateDate(newValue)) {
      onChange(newValue);
    }
  };

  const handleBlur = () => {
    validateDate(localValue);
  };

  // Calculate min/max for HTML input
  const getInputConstraints = () => {
    const constraints: any = {};
    
    if (parameter.validation_rules.min) {
      constraints.min = parameter.validation_rules.min;
    }
    
    if (parameter.validation_rules.max) {
      constraints.max = parameter.validation_rules.max;
    }
    
    if (parameter.validation_rules.allow_future === false) {
      const today = new Date().toISOString().split('T')[0];
      if (!constraints.max || constraints.max > today) {
        constraints.max = today;
      }
    }
    
    return constraints;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        <input
          type="date"
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
          {...getInputConstraints()}
        />
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <Calendar className="h-4 w-4 text-gray-400" />
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

export default DateParameter;