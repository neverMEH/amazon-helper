import { useState, useEffect, useCallback, useMemo } from 'react';
import type { FC } from 'react';
import { Calendar, Hash, List, Type, Code, AlertCircle, Info } from 'lucide-react';
import { ASINSelector } from './ASINSelector';
import { CampaignSelector } from './CampaignSelector';
import { DateRangeSelector } from './DateRangeSelector';
import type { ParameterDefinition } from '../../utils/sqlParameterAnalyzer';

interface EnhancedParameterSelectorProps {
  parameter: ParameterDefinition;
  instanceId?: string;
  value: any;
  onChange: (value: any) => void;
  className?: string;
}

/**
 * Enhanced parameter selector with context-aware input types
 */
export const EnhancedParameterSelector: FC<EnhancedParameterSelectorProps> = ({
  parameter,
  instanceId,
  value,
  onChange,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState(value);
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Debounced onChange for text inputs
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value && parameter.type === 'text') {
        onChange(localValue);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [localValue, value, onChange, parameter.type]);

  // Get icon based on parameter type
  const getIcon = () => {
    switch (parameter.type) {
      case 'date':
      case 'date_range':
        return <Calendar className="h-4 w-4 text-gray-400" />;
      case 'number':
        return <Hash className="h-4 w-4 text-gray-400" />;
      case 'asin_list':
      case 'campaign_list':
        return <List className="h-4 w-4 text-gray-400" />;
      case 'pattern':
        return <Code className="h-4 w-4 text-gray-400" />;
      case 'boolean':
        return <Type className="h-4 w-4 text-gray-400" />;
      default:
        return <Type className="h-4 w-4 text-gray-400" />;
    }
  };

  // Render appropriate input based on type and context
  const renderInput = () => {
    switch (parameter.type) {
      case 'asin_list':
        return (
          <ASINSelector
            instanceId={instanceId}
            value={value}
            onChange={onChange}
            placeholder={`Select ASINs${parameter.required ? ' (required)' : ''}`}
            showAll={true}
          />
        );

      case 'campaign_list':
        return (
          <CampaignSelector
            instanceId={instanceId!}
            value={value}
            onChange={onChange}
            placeholder={`Select campaigns${parameter.required ? ' (required)' : ''}`}
            multiple={true}
          />
        );

      case 'date':
        if (parameter.name.toLowerCase().includes('start') ||
            parameter.name.toLowerCase().includes('end')) {
          return (
            <input
              type="date"
              value={localValue || ''}
              onChange={(e) => {
                setLocalValue(e.target.value);
                onChange(e.target.value);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              required={parameter.required}
            />
          );
        }
        return (
          <DateRangeSelector
            value={value}
            onChange={onChange}
            parameterName={parameter.name}
          />
        );

      case 'date_range':
        return (
          <DateRangeSelector
            value={value}
            onChange={onChange}
            parameterName={parameter.name}
          />
        );

      case 'number':
        return (
          <div className="relative">
            <input
              type="number"
              value={localValue || ''}
              onChange={(e) => {
                const val = e.target.value ? Number(e.target.value) : '';
                setLocalValue(val);
                onChange(val);
              }}
              min={parameter.validation?.min}
              max={parameter.validation?.max}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              placeholder={parameter.defaultValue?.toString() || 'Enter number'}
              required={parameter.required}
            />
            {parameter.validation && (
              <div className="text-xs text-gray-500 mt-1">
                {parameter.validation.min !== undefined && `Min: ${parameter.validation.min}`}
                {parameter.validation.min !== undefined && parameter.validation.max !== undefined && ' • '}
                {parameter.validation.max !== undefined && `Max: ${parameter.validation.max}`}
              </div>
            )}
          </div>
        );

      case 'pattern':
        return (
          <div className="space-y-1">
            <div className="relative">
              <input
                type="text"
                value={localValue || ''}
                onChange={(e) => setLocalValue(e.target.value)}
                onBlur={() => onChange(localValue)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                placeholder={parameter.sqlContext === 'LIKE' ? 'e.g., %search_term%' : 'Enter pattern'}
                required={parameter.required}
              />
              {parameter.sqlContext === 'LIKE' && (
                <div className="absolute right-2 top-2">
                  <button
                    type="button"
                    onClick={() => setShowHint(!showHint)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Info className="h-4 w-4" />
                  </button>
                </div>
              )}
            </div>
            {showHint && parameter.sqlContext === 'LIKE' && (
              <div className="bg-blue-50 border border-blue-200 rounded p-2 text-xs">
                <p className="font-medium text-blue-900 mb-1">Pattern Matching:</p>
                <ul className="space-y-1 text-blue-800">
                  <li>• Use % for any characters (e.g., %brand%)</li>
                  <li>• Use _ for single character (e.g., B_AND)</li>
                  <li>• Leave empty for exact match</li>
                </ul>
              </div>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="true"
                checked={localValue === true || localValue === 'true'}
                onChange={() => {
                  onChange(true);
                  setLocalValue(true);
                }}
                className="mr-2 text-indigo-600 focus:ring-indigo-500"
              />
              <span>True</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="false"
                checked={localValue === false || localValue === 'false'}
                onChange={() => {
                  onChange(false);
                  setLocalValue(false);
                }}
                className="mr-2 text-indigo-600 focus:ring-indigo-500"
              />
              <span>False</span>
            </label>
          </div>
        );

      default:
        // Handle list type with comma-separated input
        if (parameter.sqlContext === 'IN' || parameter.sqlContext === 'VALUES') {
          return (
            <div className="space-y-1">
              <textarea
                value={Array.isArray(localValue) ? localValue.join(', ') : localValue || ''}
                onChange={(e) => {
                  const values = e.target.value.split(',').map(v => v.trim()).filter(v => v);
                  setLocalValue(values);
                  onChange(values);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter comma-separated values"
                rows={3}
                required={parameter.required}
              />
              <p className="text-xs text-gray-500">
                Separate multiple values with commas
              </p>
            </div>
          );
        }

        // Default text input
        return (
          <input
            type="text"
            value={localValue || ''}
            onChange={(e) => setLocalValue(e.target.value)}
            onBlur={() => onChange(localValue)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            placeholder={parameter.description || `Enter ${parameter.name}`}
            required={parameter.required}
          />
        );
    }
  };

  // Format the parameter name for display
  const formatName = (name: string) => {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          <span className="flex items-center gap-2">
            {getIcon()}
            {formatName(parameter.name)}
            {parameter.required && <span className="text-red-500">*</span>}
          </span>
        </label>
        {parameter.sqlContext && (
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {parameter.sqlContext}
          </span>
        )}
      </div>

      {parameter.description && (
        <p className="text-sm text-gray-600">{parameter.description}</p>
      )}

      {renderInput()}

      {parameter.formatPattern && (
        <div className="flex items-start gap-1 mt-1">
          <AlertCircle className="h-3 w-3 text-gray-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-gray-500">{parameter.formatPattern}</p>
        </div>
      )}
    </div>
  );
};