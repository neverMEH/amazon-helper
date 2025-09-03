import React, { useState, useEffect } from 'react';
import { Type } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const StringParameter: React.FC<BaseParameterInputProps> = ({
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

  const validateString = (str: string): boolean => {
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

    const rules = parameter.validation_rules;

    // Check min length
    if (rules.min_length && str.length < rules.min_length) {
      const error = `Must be at least ${rules.min_length} characters`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check max length
    if (rules.max_length && str.length > rules.max_length) {
      const error = `Must not exceed ${rules.max_length} characters`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check pattern
    if (rules.pattern) {
      const regex = new RegExp(rules.pattern);
      if (!regex.test(str)) {
        const error = 'Invalid format';
        setError(error);
        onError?.(error);
        return false;
      }
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    
    if (validateString(newValue)) {
      onChange(newValue);
    }
  };

  const handleBlur = () => {
    validateString(localValue);
  };

  // Determine if multiline based on max_length or ui_config
  const isMultiline = parameter.ui_config.multiline || 
    (parameter.validation_rules.max_length && parameter.validation_rules.max_length > 100);

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      <div className="relative">
        {isMultiline ? (
          <textarea
            value={localValue}
            onChange={handleChange}
            onBlur={handleBlur}
            disabled={disabled}
            required={parameter.required}
            placeholder={parameter.ui_config.placeholder}
            rows={4}
            maxLength={parameter.validation_rules.max_length}
            className={`
              block w-full px-3 py-2
              border rounded-md shadow-sm resize-vertical
              focus:ring-indigo-500 focus:border-indigo-500
              ${error ? 'border-red-300' : 'border-gray-300'}
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
            `}
          />
        ) : (
          <input
            type="text"
            value={localValue}
            onChange={handleChange}
            onBlur={handleBlur}
            disabled={disabled}
            required={parameter.required}
            placeholder={parameter.ui_config.placeholder}
            maxLength={parameter.validation_rules.max_length}
            className={`
              block w-full px-3 py-2 pr-10
              border rounded-md shadow-sm
              focus:ring-indigo-500 focus:border-indigo-500
              ${error ? 'border-red-300' : 'border-gray-300'}
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
            `}
          />
        )}
        
        {!isMultiline && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <Type className="h-4 w-4 text-gray-400" />
          </div>
        )}
      </div>

      {/* Character counter for long text */}
      {parameter.validation_rules.max_length && localValue && (
        <div className="text-xs text-gray-500 text-right">
          {localValue.length} / {parameter.validation_rules.max_length}
        </div>
      )}

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

export default StringParameter;