import React, { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';
import type { BaseParameterInputProps, DateRangeValue } from '../../../types/queryFlowTemplate';

const DateRangeParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<DateRangeValue>(
    value || { start: '', end: '', preset: '' }
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalValue(value || { start: '', end: '', preset: '' });
  }, [value]);

  const calculatePresetDates = (preset: string): DateRangeValue => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    switch (preset) {
      case 'last_7_days':
        const start7 = new Date(today);
        start7.setDate(start7.getDate() - 7);
        return {
          start: start7.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          preset
        };
      
      case 'last_14_days':
        const start14 = new Date(today);
        start14.setDate(start14.getDate() - 14);
        return {
          start: start14.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          preset
        };
      
      case 'last_30_days':
        const start30 = new Date(today);
        start30.setDate(start30.getDate() - 30);
        return {
          start: start30.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          preset
        };
      
      case 'last_month':
        const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
        const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        return {
          start: lastMonthStart.toISOString().split('T')[0],
          end: lastMonthEnd.toISOString().split('T')[0],
          preset
        };
      
      case 'this_month':
        const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        return {
          start: thisMonthStart.toISOString().split('T')[0],
          end: yesterday.toISOString().split('T')[0],
          preset
        };
      
      case 'last_quarter':
        const currentQuarter = Math.floor(today.getMonth() / 3);
        const lastQuarter = currentQuarter === 0 ? 3 : currentQuarter - 1;
        const lastQuarterYear = currentQuarter === 0 ? today.getFullYear() - 1 : today.getFullYear();
        const lastQuarterStart = new Date(lastQuarterYear, lastQuarter * 3, 1);
        const lastQuarterEnd = new Date(lastQuarterYear, (lastQuarter + 1) * 3, 0);
        return {
          start: lastQuarterStart.toISOString().split('T')[0],
          end: lastQuarterEnd.toISOString().split('T')[0],
          preset
        };
      
      default:
        return localValue;
    }
  };

  const validateDateRange = (range: DateRangeValue): boolean => {
    if (!range.start || !range.end) {
      if (parameter.required) {
        setError('Both start and end dates are required');
        onError?.('Both start and end dates are required');
        return false;
      }
      setError(null);
      onError?.(null);
      return true;
    }

    const startDate = new Date(range.start);
    const endDate = new Date(range.end);

    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
      setError('Invalid date format');
      onError?.('Invalid date format');
      return false;
    }

    if (startDate > endDate) {
      setError('Start date must be before end date');
      onError?.('Start date must be before end date');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check min days
    if (rules.min_days) {
      const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      if (daysDiff < rules.min_days) {
        const error = `Date range must be at least ${rules.min_days} days`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    // Check max days
    if (rules.max_days) {
      const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      if (daysDiff > rules.max_days) {
        const error = `Date range must not exceed ${rules.max_days} days`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    // Check future dates
    if (rules.allow_future === false) {
      const now = new Date();
      if (startDate > now || endDate > now) {
        setError('Future dates are not allowed');
        onError?.('Future dates are not allowed');
        return false;
      }
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = { ...localValue, start: e.target.value, preset: '' };
    setLocalValue(newValue);
    
    if (validateDateRange(newValue)) {
      onChange(newValue);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = { ...localValue, end: e.target.value, preset: '' };
    setLocalValue(newValue);
    
    if (validateDateRange(newValue)) {
      onChange(newValue);
    }
  };

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const preset = e.target.value;
    if (!preset) {
      const newValue = { start: '', end: '', preset: '' };
      setLocalValue(newValue);
      onChange(newValue);
      return;
    }

    const newValue = calculatePresetDates(preset);
    setLocalValue(newValue);
    
    if (validateDateRange(newValue)) {
      onChange(newValue);
    }
  };

  const handleBlur = () => {
    validateDateRange(localValue);
  };

  // Get constraints for date inputs
  const getInputConstraints = () => {
    const constraints: any = {};
    
    if (parameter.validation_rules.allow_future === false) {
      const today = new Date().toISOString().split('T')[0];
      constraints.max = today;
    }
    
    return constraints;
  };

  const presets = parameter.ui_config.presets || [
    { label: 'Last 7 days', value: 'last_7_days' },
    { label: 'Last 14 days', value: 'last_14_days' },
    { label: 'Last 30 days', value: 'last_30_days' },
    { label: 'Last month', value: 'last_month' },
    { label: 'This month', value: 'this_month' },
    { label: 'Last quarter', value: 'last_quarter' }
  ];

  return (
    <div className={`space-y-2 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {parameter.ui_config.show_presets !== false && (
        <div className="mb-2">
          <select
            value={localValue.preset || ''}
            onChange={handlePresetChange}
            disabled={disabled}
            className={`
              block w-full px-3 py-2
              border rounded-md shadow-sm
              focus:ring-indigo-500 focus:border-indigo-500
              ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              border-gray-300
            `}
          >
            <option value="">Custom date range</option>
            {presets.map(preset => (
              <option key={preset.value} value={preset.value}>
                {preset.label}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Start Date</label>
          <div className="relative">
            <input
              type="date"
              value={localValue.start}
              onChange={handleStartChange}
              onBlur={handleBlur}
              disabled={disabled}
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
        </div>

        <div>
          <label className="block text-xs text-gray-600 mb-1">End Date</label>
          <div className="relative">
            <input
              type="date"
              value={localValue.end}
              onChange={handleEndChange}
              onBlur={handleBlur}
              disabled={disabled}
              min={localValue.start}
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

export default DateRangeParameter;