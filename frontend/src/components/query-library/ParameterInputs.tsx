import { useState, useEffect } from 'react';
import { AlertCircle, Calendar, Hash, Type, ToggleRight, Search, Package } from 'lucide-react';
import { CampaignSelector } from './CampaignSelector';
import { ASINSelector } from './ASINSelector';
import type { ParameterDefinition } from '../../types/queryTemplate';

interface ParameterInputsProps {
  parameter: ParameterDefinition;
  value: any;
  onChange: (value: any) => void;
  instanceId?: string;
}

export default function ParameterInputs({
  parameter,
  value,
  onChange,
  instanceId
}: ParameterInputsProps) {
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  // Validate value when it changes or when field is touched
  useEffect(() => {
    if (touched) {
      validateValue();
    }
  }, [value, touched]);

  const validateValue = () => {
    // Required field validation
    if (parameter.required && !value) {
      setError('This field is required');
      return false;
    }

    // Type-specific validation
    switch (parameter.type) {
      case 'number':
        if (value !== null && value !== undefined) {
          const num = Number(value);
          if (isNaN(num)) {
            setError('Must be a valid number');
            return false;
          }
          if (parameter.validation?.min !== undefined && num < parameter.validation.min) {
            setError(`Value must be at least ${parameter.validation.min}`);
            return false;
          }
          if (parameter.validation?.max !== undefined && num > parameter.validation.max) {
            setError(`Value must be at most ${parameter.validation.max}`);
            return false;
          }
          if (parameter.validation?.min !== undefined && parameter.validation?.max !== undefined) {
            if (num < parameter.validation.min || num > parameter.validation.max) {
              setError(`Value must be between ${parameter.validation.min} and ${parameter.validation.max}`);
              return false;
            }
          }
        }
        break;

      case 'date_range':
        if (value?.start && value?.end) {
          const startDate = new Date(value.start);
          const endDate = new Date(value.end);
          if (endDate < startDate) {
            setError('End date must be after start date');
            return false;
          }
        }
        break;

      case 'pattern':
        if (value && parameter.validation?.pattern) {
          const regex = new RegExp(parameter.validation.pattern);
          if (!regex.test(value)) {
            if (parameter.validation.pattern === '^%.*%$') {
              setError('Pattern must start and end with %');
            } else {
              setError('Invalid pattern format');
            }
            return false;
          }
        }
        break;

      case 'text':
        if (value && parameter.validation?.pattern) {
          const regex = new RegExp(parameter.validation.pattern);
          if (!regex.test(value)) {
            setError('Value does not match required format');
            return false;
          }
        }
        if (value && parameter.validation?.enum?.length) {
          if (!parameter.validation.enum.includes(value)) {
            setError(`Value must be one of: ${parameter.validation.enum.join(', ')}`);
            return false;
          }
        }
        break;
    }

    setError(null);
    return true;
  };

  const handleBlur = () => {
    setTouched(true);
    validateValue();
  };

  const getInputIcon = () => {
    switch (parameter.type) {
      case 'date':
      case 'date_range':
        return <Calendar className="h-4 w-4 text-gray-400" />;
      case 'number':
        return <Hash className="h-4 w-4 text-gray-400" />;
      case 'pattern':
        return <Search className="h-4 w-4 text-gray-400" />;
      case 'asin_list':
        return <Package className="h-4 w-4 text-gray-400" />;
      case 'boolean':
        return <ToggleRight className="h-4 w-4 text-gray-400" />;
      default:
        return <Type className="h-4 w-4 text-gray-400" />;
    }
  };

  const renderInput = () => {
    switch (parameter.type) {
      case 'text':
        return (
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              {getInputIcon()}
            </div>
            <input
              type="text"
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              onBlur={handleBlur}
              placeholder={parameter.defaultValue ? `Default: ${parameter.defaultValue}` : `Enter ${parameter.displayName || parameter.name}`}
              className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                error
                  ? 'border-red-300 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-indigo-500'
              }`}
              aria-label={parameter.displayName || parameter.name}
              aria-required={parameter.required}
              aria-invalid={!!error}
              aria-describedby={error ? `${parameter.name}-error` : undefined}
            />
          </div>
        );

      case 'number':
        return (
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              {getInputIcon()}
            </div>
            <input
              type="number"
              value={value || ''}
              onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
              onBlur={handleBlur}
              min={parameter.validation?.min}
              max={parameter.validation?.max}
              placeholder={parameter.defaultValue !== undefined ? `Default: ${parameter.defaultValue}` : `Enter number`}
              className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                error
                  ? 'border-red-300 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-indigo-500'
              }`}
              aria-label={parameter.displayName || parameter.name}
              aria-required={parameter.required}
              role="spinbutton"
            />
          </div>
        );

      case 'date':
        return (
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              {getInputIcon()}
            </div>
            <input
              type="date"
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              onBlur={handleBlur}
              className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                error
                  ? 'border-red-300 focus:ring-red-500'
                  : 'border-gray-300 focus:ring-indigo-500'
              }`}
              aria-label={`${parameter.displayName || parameter.name} date`}
              aria-required={parameter.required}
            />
          </div>
        );

      case 'date_range':
        return (
          <div className="space-y-2">
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                <Calendar className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="date"
                value={value?.start || ''}
                onChange={(e) => onChange({ ...value, start: e.target.value })}
                onBlur={handleBlur}
                className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                  error
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-indigo-500'
                }`}
                aria-label="Start date"
                aria-required={parameter.required}
              />
            </div>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                <Calendar className="h-4 w-4 text-gray-400" />
              </div>
              <input
                type="date"
                value={value?.end || ''}
                onChange={(e) => onChange({ ...value, end: e.target.value })}
                onBlur={handleBlur}
                className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                  error
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-indigo-500'
                }`}
                aria-label="End date"
                aria-required={parameter.required}
              />
            </div>
          </div>
        );

      case 'campaign_list':
        return (
          <CampaignSelector
            value={value || []}
            onChange={onChange}
            multiple={true}
            placeholder={`Select ${parameter.displayName || 'campaigns'}`}
            className={error ? 'border-red-300' : ''}
            showAll={true}
            valueType="ids"
          />
        );

      case 'asin_list':
        return (
          <ASINSelector
            value={value || []}
            onChange={onChange}
            placeholder={`Select ${parameter.displayName || 'ASINs'}`}
            className={error ? 'border-red-300' : ''}
          />
        );

      case 'pattern':
        return (
          <div className="space-y-1">
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                {getInputIcon()}
              </div>
              <input
                type="text"
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                onBlur={handleBlur}
                placeholder={parameter.defaultValue || '%pattern%'}
                className={`w-full pl-10 pr-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                  error
                    ? 'border-red-300 focus:ring-red-500'
                    : 'border-gray-300 focus:ring-indigo-500'
                }`}
                aria-label={parameter.displayName || parameter.name}
                aria-required={parameter.required}
              />
            </div>
            <p className="text-xs text-gray-500">Use % for wildcards (e.g., %search%)</p>
          </div>
        );

      case 'boolean':
        return (
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={value || false}
              onChange={(e) => onChange(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              aria-label={parameter.displayName || parameter.name}
              role="checkbox"
            />
            <span className="text-sm text-gray-700">
              {parameter.description || parameter.displayName || parameter.name}
            </span>
          </label>
        );

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            onBlur={handleBlur}
            placeholder={`Enter ${parameter.displayName || parameter.name}`}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
              error
                ? 'border-red-300 focus:ring-red-500'
                : 'border-gray-300 focus:ring-indigo-500'
            }`}
            aria-label={parameter.displayName || parameter.name}
            aria-required={parameter.required}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      {/* Label */}
      {parameter.type !== 'boolean' && (
        <label className="block text-sm font-medium text-gray-700">
          {parameter.displayName || parameter.name}
          {parameter.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Description (if not shown elsewhere) */}
      {parameter.description && parameter.type !== 'boolean' && (
        <p className="text-sm text-gray-500">{parameter.description}</p>
      )}

      {/* Input */}
      {renderInput()}

      {/* Error message */}
      {error && touched && (
        <div
          id={`${parameter.name}-error`}
          className="flex items-center space-x-1 text-sm text-red-600"
          role="alert"
        >
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Validation hints */}
      {!error && parameter.validation && (
        <div className="text-xs text-gray-500">
          {parameter.validation.min !== undefined && parameter.validation.max !== undefined && (
            <span>Value between {parameter.validation.min} and {parameter.validation.max}</span>
          )}
          {parameter.validation.enum && (
            <span>Options: {parameter.validation.enum.join(', ')}</span>
          )}
        </div>
      )}
    </div>
  );
}