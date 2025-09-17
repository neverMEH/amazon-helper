import { useState, useEffect, useCallback } from 'react';
import { Calendar, Clock, ChevronRight } from 'lucide-react';
import { format, subDays, subMonths, startOfWeek, endOfWeek, startOfMonth, endOfMonth } from 'date-fns';
import type { DetectedParameter } from '../../utils/parameterDetection';

interface LookbackConfig {
  type: 'relative' | 'custom';
  value?: number;
  unit?: 'days' | 'weeks' | 'months';
  startDate?: string;
  endDate?: string;
}

interface ReportBuilderParametersProps {
  workflowId: string;
  instanceId: string;
  sqlQuery?: string;
  parameters: Record<string, any>;
  lookbackConfig: LookbackConfig;
  detectedParameters?: DetectedParameter[];
  onNext: () => void;
  onParametersChange: (data: {
    parameters: Record<string, any>;
    lookbackConfig: LookbackConfig;
  }) => void;
}

interface PredefinedLookback {
  label: string;
  value: number;
  unit: 'days' | 'weeks' | 'months';
  type: 'relative' | 'lastWeek' | 'lastMonth';
}

const PREDEFINED_LOOKBACKS: PredefinedLookback[] = [
  { label: 'Last 7 Days', value: 7, unit: 'days', type: 'relative' },
  { label: 'Last 14 Days', value: 14, unit: 'days', type: 'relative' },
  { label: 'Last 30 Days', value: 30, unit: 'days', type: 'relative' },
  { label: 'Last Week', value: 1, unit: 'weeks', type: 'lastWeek' },
  { label: 'Last Month', value: 1, unit: 'months', type: 'lastMonth' },
];

const AMC_MAX_MONTHS = 14;
const AMC_MAX_DAYS = AMC_MAX_MONTHS * 31; // Approximate

export default function ReportBuilderParameters({
  workflowId: _workflowId,
  instanceId: _instanceId,
  sqlQuery,
  parameters: initialParameters,
  lookbackConfig: initialLookback,
  detectedParameters = [],
  onNext,
  onParametersChange,
}: ReportBuilderParametersProps) {
  const [parameters, setParameters] = useState(initialParameters);
  const [lookbackConfig, setLookbackConfig] = useState<LookbackConfig>(initialLookback);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // If no detectedParameters provided, infer from parameters keys
  const effectiveDetectedParams = detectedParameters.length > 0
    ? detectedParameters
    : Object.keys(initialParameters).map(key => ({
        name: key,
        type: key.toLowerCase().includes('campaign') ? 'campaigns' as const :
              key.toLowerCase().includes('asin') ? 'asins' as const :
              'string' as const,
        defaultValue: null
      }));

  // Calculate date range from lookback config
  const calculateDateRange = useCallback((config: LookbackConfig): { start: Date; end: Date } => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (config.type === 'custom' && config.startDate && config.endDate) {
      return {
        start: new Date(config.startDate),
        end: new Date(config.endDate),
      };
    }

    // Handle relative lookbacks
    if (config.type === 'relative' && config.value) {
      const endDate = today;
      let startDate = new Date(today);

      switch (config.unit) {
        case 'weeks':
          // For "Last Week", get actual last week dates
          if (config.value === 1) {
            const lastWeek = subDays(today, 7);
            startDate = startOfWeek(lastWeek, { weekStartsOn: 0 }); // Sunday
            return {
              start: startDate,
              end: endOfWeek(lastWeek, { weekStartsOn: 0 }),
            };
          }
          startDate = subDays(today, config.value * 7);
          break;
        case 'months':
          // For "Last Month", get actual last month dates
          if (config.value === 1) {
            const lastMonth = subMonths(today, 1);
            startDate = startOfMonth(lastMonth);
            return {
              start: startDate,
              end: endOfMonth(lastMonth),
            };
          }
          startDate = subMonths(today, config.value);
          break;
        case 'days':
        default:
          startDate = subDays(today, config.value);
      }

      return { start: startDate, end: endDate };
    }

    // Default to last 7 days
    return { start: subDays(today, 7), end: today };
  }, []);

  // Validate lookback configuration
  const validateLookback = useCallback((config: LookbackConfig): string[] => {
    const errors: string[] = [];

    if (config.type === 'custom') {
      if (!config.startDate || !config.endDate) {
        errors.push('Both start and end dates are required for custom range');
        return errors;
      }

      const start = new Date(config.startDate);
      const end = new Date(config.endDate);
      const today = new Date();

      // Check if end date is after start date
      if (end < start) {
        errors.push('End date must be after start date');
      }

      // Check if dates are not in the future
      if (start > today || end > today) {
        errors.push('Dates cannot be in the future');
      }

      // Check AMC data retention limit (14 months)
      const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
      if (daysDiff > AMC_MAX_DAYS) {
        errors.push(`Date range exceeds AMC's 14-month data retention limit`);
      }
    } else if (config.type === 'relative') {
      if (!config.value || !config.unit) {
        errors.push('Lookback period is required');
      } else {
        // Check if relative period exceeds AMC limits
        let days = config.value;
        if (config.unit === 'weeks') days *= 7;
        if (config.unit === 'months') days *= 31;

        if (days > AMC_MAX_DAYS) {
          errors.push(`Lookback period exceeds AMC's 14-month data retention limit`);
        }
      }
    }

    return errors;
  }, []);

  // Handle parameter changes
  const handleParameterChange = (paramName: string, value: any) => {
    const newParams = { ...parameters, [paramName]: value };
    setParameters(newParams);
    onParametersChange({
      parameters: newParams,
      lookbackConfig,
    });
  };

  // Handle lookback button clicks
  const handlePredefinedLookback = (lookback: PredefinedLookback) => {
    let newConfig: LookbackConfig;

    if (lookback.type === 'lastWeek' || lookback.type === 'lastMonth') {
      // These are special cases that should use relative type
      newConfig = {
        type: 'relative',
        value: lookback.value,
        unit: lookback.unit,
      };
    } else {
      newConfig = {
        type: 'relative',
        value: lookback.value,
        unit: lookback.unit,
      };
    }

    setLookbackConfig(newConfig);
    onParametersChange({
      parameters,
      lookbackConfig: newConfig,
    });
  };

  // Handle custom range selection
  const handleCustomRange = () => {
    const today = new Date();
    const lastWeek = subDays(today, 7);
    const newConfig: LookbackConfig = {
      type: 'custom',
      startDate: format(lastWeek, 'yyyy-MM-dd'),
      endDate: format(today, 'yyyy-MM-dd'),
    };

    setLookbackConfig(newConfig);
    onParametersChange({
      parameters,
      lookbackConfig: newConfig,
    });
  };

  // Handle date input changes
  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    const newConfig = {
      ...lookbackConfig,
      [field]: value,
    };

    setLookbackConfig(newConfig);
    onParametersChange({
      parameters,
      lookbackConfig: newConfig,
    });
  };

  // Validate on changes
  useEffect(() => {
    const errors = validateLookback(lookbackConfig);
    setValidationErrors(errors);
  }, [lookbackConfig, validateLookback]);

  // Check if currently selected matches a predefined button
  const isButtonSelected = (lookback: PredefinedLookback) => {
    if (lookbackConfig.type !== 'relative') return false;
    return (
      lookbackConfig.value === lookback.value &&
      lookbackConfig.unit === lookback.unit
    );
  };

  const dateRange = calculateDateRange(lookbackConfig);

  // Handle parameter value changes
  const handleParameterChange = (paramName: string, value: string) => {
    const newParams = {
      ...parameters,
      [paramName]: value
    };
    setParameters(newParams);
    onParametersChange({
      parameters: newParams,
      lookbackConfig
    });
  };

  // Check if all required parameters have values
  // If there are no detected parameters, we can proceed
  const hasParameterValues = effectiveDetectedParams.length === 0 ||
    effectiveDetectedParams.every(param => {
      const value = parameters[param.name];
      return value !== undefined && value !== null && value !== '' &&
             (!Array.isArray(value) || value.length > 0);
    });

  const canProceed = validationErrors.length === 0 && hasParameterValues;

  // Count selected items for display
  // const getParameterDisplay = (value: any): string => {
  //   if (Array.isArray(value)) {
  //     return `${value.length} selected`;
  //   }
  //   if (typeof value === 'object' && value !== null) {
  //     return 'Configured';
  //   }
  //   return String(value);
  // };

  return (
    <div className="space-y-6">
      {/* SQL Query Display */}
      {sqlQuery && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">SQL Query</h3>
          <div className="bg-gray-50 rounded-lg p-4 overflow-auto max-h-64">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">{sqlQuery}</pre>
          </div>
        </div>
      )}

      {/* Lookback Window Selection */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
          <Calendar className="h-5 w-5 mr-2" />
          Lookback Window
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Select the time period for your report data
        </p>

        {/* Predefined Buttons */}
        <div className="flex flex-wrap gap-2 mb-4">
          {PREDEFINED_LOOKBACKS.map((lookback) => (
            <button
              key={lookback.label}
              onClick={() => handlePredefinedLookback(lookback)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                isButtonSelected(lookback)
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {lookback.label}
            </button>
          ))}
          <button
            onClick={handleCustomRange}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              lookbackConfig.type === 'custom'
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Custom Range
          </button>
        </div>

        {/* Custom Date Range Inputs */}
        {lookbackConfig.type === 'custom' && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                id="start-date"
                type="date"
                value={lookbackConfig.startDate || ''}
                onChange={(e) => handleDateChange('startDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                id="end-date"
                type="date"
                value={lookbackConfig.endDate || ''}
                onChange={(e) => handleDateChange('endDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        )}

        {/* Date Range Preview */}
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center text-sm text-blue-900">
            <Clock className="h-4 w-4 mr-2" />
            <span className="font-medium">Date Range:</span>
            <span className="ml-2">
              {format(dateRange.start, 'MMM dd, yyyy')} to {format(dateRange.end, 'MMM dd, yyyy')}
            </span>
          </div>
        </div>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
            {validationErrors.map((error, index) => (
              <p key={index} className="text-sm text-red-600">{error}</p>
            ))}
          </div>
        )}
      </div>

      {/* Query Parameters */}
      {effectiveDetectedParams.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Query Parameters</h3>
          <div className="space-y-4">
            {effectiveDetectedParams.map((param) => {
              const value = parameters[param.name] || '';

              // Create a label for the parameter
              const paramLabel = param.name.toLowerCase().includes('campaign') ? 'Campaigns' :
                                param.name.toLowerCase().includes('asin') ? 'ASINs' :
                                param.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

              const inputId = `param-input-${param.name}`;

              return (
                <div key={param.name} className="border border-gray-200 rounded-lg p-4">
                  <div className="mb-2">
                    <label
                      htmlFor={inputId}
                      className="block text-sm font-medium text-gray-700"
                    >
                      {paramLabel} <span className="text-gray-500">({`{{${param.name}}}`})</span>
                    </label>
                  </div>

                  {/* Input field based on parameter type */}
                  {param.type === 'date' ? (
                    <input
                      id={inputId}
                      type="date"
                      value={value}
                      onChange={(e) => handleParameterChange(param.name, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : param.type === 'campaigns' || param.type === 'asins' ? (
                    <textarea
                      id={inputId}
                      value={value}
                      onChange={(e) => handleParameterChange(param.name, e.target.value)}
                      placeholder={param.type === 'asins' ?
                        "Enter ASINs (comma-separated or one per line)" :
                        "Enter campaign IDs or names (comma-separated or one per line)"}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      rows={3}
                    />
                  ) : (
                    <input
                      id={inputId}
                      type="text"
                      value={value}
                      onChange={(e) => handleParameterChange(param.name, e.target.value)}
                      placeholder={`Enter ${paramLabel.toLowerCase()}`}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  )}

                  {/* Show current value */}
                  {value && (
                    <p className="mt-1 text-xs text-gray-500">
                      Current value: {value}
                    </p>
                  )}

                  {/* For now, keeping the button for compatibility */}
                  <button
                    id={`param-button-${param.name}`}
                    type="button"
                    style={{ display: 'none' }}
                    onClick={() => {
                      // In a real implementation, this would open a modal or dropdown
                      // For now, just toggle a simple test value
                      if (param.name.toLowerCase().includes('campaign')) {
                        handleParameterChange(param.name, ['test-campaign']);
                      } else if (param.name.toLowerCase().includes('asin')) {
                        handleParameterChange(param.name, ['B001TEST']);
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label={param.name.toLowerCase().includes('campaign') ? 'select campaigns' :
                               param.name.toLowerCase().includes('asin') ? 'select asins' :
                               `select ${param.name}`}
                  >
                    {hasValue && Array.isArray(parameters[param.name]) && parameters[param.name].length > 0
                      ? `${parameters[param.name].length} selected`
                      : `Select ${paramLabel.toLowerCase()}`}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-end pt-4 border-t">
        <button
          onClick={onNext}
          disabled={!canProceed}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md
                    shadow-sm text-white transition-colors ${
            canProceed
              ? 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              : 'bg-gray-400 cursor-not-allowed'
          }`}
        >
          Next
          <ChevronRight className="ml-2 h-4 w-4" />
        </button>
      </div>
    </div>
  );
}