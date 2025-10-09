import React, { useState, useEffect } from 'react';
import { Calendar, AlertCircle, TrendingUp, ChevronRight } from 'lucide-react';
import { format, subDays, addDays } from 'date-fns';
import type { ScheduleConfig } from '../../types/schedule';

interface DateRangeStepProps {
  config: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
  onNext: () => void;
  onBack: () => void;
}

const WINDOW_PRESETS = [
  { value: 7, label: '7 days', description: 'Weekly' },
  { value: 14, label: '14 days', description: 'Bi-weekly' },
  { value: 30, label: '30 days', description: 'Monthly' },
  { value: 60, label: '60 days', description: 'Bi-monthly' },
  { value: 90, label: '90 days', description: 'Quarterly' },
];

const AMC_DATA_LAG_DAYS = 14;

const DateRangeStep: React.FC<DateRangeStepProps> = ({
  config,
  onChange,
  onNext,
  onBack,
}) => {
  const [customDays, setCustomDays] = useState<string>('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [validationError, setValidationError] = useState<string>('');
  const [dateRangePreviews, setDateRangePreviews] = useState<Array<{
    execution: string;
    startDate: string;
    endDate: string;
  }>>([]);

  // Initialize date range type if not set
  useEffect(() => {
    if (!config.dateRangeType) {
      onChange({ ...config, dateRangeType: 'rolling' });
    }
  }, []);

  // Calculate date range previews
  useEffect(() => {
    if (!config.lookbackDays) {
      setDateRangePreviews([]);
      return;
    }

    const previews = [];
    const today = new Date();
    const lookback = config.lookbackDays;

    // Calculate next 3 executions based on schedule type
    for (let i = 0; i < 3; i++) {
      let executionDate: Date;

      switch (config.type) {
        case 'daily':
          executionDate = addDays(today, i);
          break;
        case 'weekly':
          executionDate = addDays(today, i * 7);
          break;
        case 'monthly':
          executionDate = new Date(today);
          executionDate.setMonth(today.getMonth() + i);
          break;
        case 'interval':
          const interval = config.intervalDays || 1;
          executionDate = addDays(today, i * interval);
          break;
        default:
          executionDate = addDays(today, i);
      }

      // Apply AMC 14-day lag to end date
      const endDate = subDays(executionDate, AMC_DATA_LAG_DAYS);
      const startDate = subDays(endDate, lookback);

      previews.push({
        execution: format(executionDate, 'EEE, MMM d, yyyy'),
        startDate: format(startDate, 'MMM d, yyyy'),
        endDate: format(endDate, 'MMM d, yyyy'),
      });
    }

    setDateRangePreviews(previews);
  }, [config.lookbackDays, config.type, config.intervalDays]);

  const handlePresetSelect = (days: number) => {
    setShowCustomInput(false);
    setCustomDays('');
    setValidationError('');
    onChange({
      ...config,
      lookbackDays: days,
      windowSizeDays: days,
    });
  };

  const handleCustomSelect = () => {
    setShowCustomInput(true);
    if (customDays) {
      const days = parseInt(customDays);
      if (!isNaN(days) && days >= 1 && days <= 365) {
        onChange({
          ...config,
          lookbackDays: days,
          windowSizeDays: days,
        });
      }
    }
  };

  const handleCustomDaysChange = (value: string) => {
    setCustomDays(value);
    const days = parseInt(value);

    if (value && !isNaN(days)) {
      if (days < 1 || days > 365) {
        setValidationError('Window size must be between 1 and 365 days');
      } else {
        setValidationError('');
        onChange({
          ...config,
          lookbackDays: days,
          windowSizeDays: days,
        });
      }
    }
  };

  const handleDateRangeTypeChange = (type: 'rolling' | 'fixed') => {
    onChange({
      ...config,
      dateRangeType: type,
    });
  };

  const handleNext = () => {
    if (!config.lookbackDays || config.lookbackDays < 1) {
      setValidationError('Please select a window size');
      return;
    }

    if (config.lookbackDays > 365) {
      setValidationError('Window size must be between 1 and 365 days');
      return;
    }

    setValidationError('');
    onNext();
  };

  const isPresetSelected = (days: number) => {
    return config.lookbackDays === days && !showCustomInput;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium mb-2">Date Range Configuration</h3>
        <p className="text-gray-600 text-sm">
          Configure how date ranges are calculated for each execution
        </p>
      </div>

      {/* AMC Data Lag Warning */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 mr-3 flex-shrink-0" data-testid="amc-lag-alert" />
          <div className="text-sm">
            <p className="font-medium text-amber-900 mb-1">AMC Data Availability</p>
            <p className="text-amber-800">
              Amazon Marketing Cloud data has a 14-day processing lag. This lag is automatically applied
              to all date calculations, so queries will always use data from 14 days ago minus your selected window.
            </p>
          </div>
        </div>
      </div>

      {/* Date Range Type Toggle */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Date Range Type
        </label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => handleDateRangeTypeChange('rolling')}
            className={`
              p-4 border-2 rounded-lg text-left transition-all
              ${config.dateRangeType === 'rolling'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-center mb-2">
              <TrendingUp className={`w-5 h-5 mr-2 ${config.dateRangeType === 'rolling' ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className="font-medium">Rolling Window</span>
            </div>
            <p className="text-sm text-gray-600">
              Always query the same window size relative to execution date
            </p>
          </button>

          <button
            type="button"
            onClick={() => handleDateRangeTypeChange('fixed')}
            className={`
              p-4 border-2 rounded-lg text-left transition-all
              ${config.dateRangeType === 'fixed'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="flex items-center mb-2">
              <Calendar className={`w-5 h-5 mr-2 ${config.dateRangeType === 'fixed' ? 'text-blue-600' : 'text-gray-400'}`} />
              <span className="font-medium">Fixed Lookback</span>
            </div>
            <p className="text-sm text-gray-600">
              Always query from execution date back N days (accounting for lag)
            </p>
          </button>
        </div>
      </div>

      {/* Window Size Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Window Size
        </label>
        <div className="grid grid-cols-3 gap-3">
          {WINDOW_PRESETS.map((preset) => (
            <button
              key={preset.value}
              type="button"
              onClick={() => handlePresetSelect(preset.value)}
              className={`
                p-3 border-2 rounded-lg text-left transition-all
                ${isPresetSelected(preset.value)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <div className="font-medium text-sm">{preset.label}</div>
              <div className="text-xs text-gray-500 mt-1">{preset.description}</div>
            </button>
          ))}

          {/* Custom Option */}
          <button
            type="button"
            onClick={handleCustomSelect}
            className={`
              p-3 border-2 rounded-lg text-left transition-all
              ${showCustomInput
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
              }
            `}
          >
            <div className="font-medium text-sm">Custom</div>
            <div className="text-xs text-gray-500 mt-1">Specify days</div>
          </button>
        </div>

        {/* Custom Input */}
        {showCustomInput && (
          <div className="mt-3">
            <label htmlFor="custom-days" className="block text-sm font-medium text-gray-700 mb-2">
              Custom days
            </label>
            <input
              id="custom-days"
              type="number"
              min="1"
              max="365"
              value={customDays}
              onChange={(e) => handleCustomDaysChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter number of days (1-365)"
            />
          </div>
        )}
      </div>

      {/* Date Range Preview */}
      {config.lookbackDays && config.lookbackDays > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-sm mb-3 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            Next 3 Executions
          </h4>
          <p className="text-xs text-gray-600 mb-3">
            Date ranges accounting for AMC's 14-day lag (queries run on execution date minus 14 days)
          </p>
          <div className="space-y-2">
            {dateRangePreviews.map((preview, index) => (
              <div
                key={index}
                data-testid={`execution-preview-${index}`}
                className="bg-white p-3 rounded border border-gray-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      Execution {index + 1}: {preview.execution}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      Query range: {preview.startDate} → {preview.endDate}
                      <span className="text-gray-500 ml-1">
                        ({config.lookbackDays}-day window)
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Error */}
      {validationError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-800">{validationError}</p>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-4 border-t">
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default DateRangeStep;
