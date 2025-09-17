import { useState, useEffect, useMemo } from 'react';
import { Clock, Calendar, Database, ChevronLeft, ChevronRight, AlertTriangle, Info } from 'lucide-react';

interface BackfillConfig {
  enabled: boolean;
  periods: number;
  segmentation: 'daily' | 'weekly' | 'monthly';
}

interface ScheduleConfig {
  type: 'once' | 'scheduled' | 'backfill_with_schedule';
  frequency: 'daily' | 'weekly' | 'monthly' | null;
  time: string | null;
  timezone: string;
  dayOfWeek?: number;
  dayOfMonth?: number;
  backfillConfig: BackfillConfig | null;
}

interface LookbackConfig {
  type: 'relative' | 'custom';
  value?: number;
  unit?: 'days' | 'weeks' | 'months';
  startDate?: string;
  endDate?: string;
}

interface ReportScheduleSelectionProps {
  workflowId: string;
  instanceId: string;
  scheduleConfig: ScheduleConfig;
  lookbackConfig: LookbackConfig;
  onNext: () => void;
  onPrevious: () => void;
  onScheduleChange: (config: ScheduleConfig) => void;
}

const TIMEZONES = [
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST/AEDT)' },
];

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

const AMC_MAX_DAYS = 14 * 31; // ~14 months
const PARALLEL_EXECUTIONS = 5;
const EXECUTION_TIME_MINUTES = 2; // Average per execution

export default function ReportScheduleSelection({
  workflowId: _workflowId,
  instanceId: _instanceId,
  scheduleConfig,
  lookbackConfig: _lookbackConfig,
  onNext,
  onPrevious,
  onScheduleChange,
}: ReportScheduleSelectionProps) {
  const [localConfig, setLocalConfig] = useState<ScheduleConfig>(scheduleConfig);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Update local config when props change
  useEffect(() => {
    setLocalConfig(scheduleConfig);
  }, [scheduleConfig]);

  // Calculate backfill duration and progress
  const backfillCalculations = useMemo(() => {
    if (!localConfig.backfillConfig?.enabled) {
      return null;
    }

    const { periods, segmentation } = localConfig.backfillConfig;
    let totalDays = 0;

    switch (segmentation) {
      case 'daily':
        totalDays = periods;
        break;
      case 'weekly':
        totalDays = periods * 7;
        break;
      case 'monthly':
        totalDays = periods * 30;
        break;
    }

    // Calculate batches and time
    const totalBatches = Math.ceil(periods / PARALLEL_EXECUTIONS);
    const estimatedMinutes = totalBatches * EXECUTION_TIME_MINUTES;
    const estimatedHours = Math.round(estimatedMinutes / 60 * 10) / 10;

    return {
      totalDays,
      totalBatches,
      estimatedHours,
      isLarge: periods > 100,
      exceedsLimit: totalDays > AMC_MAX_DAYS,
    };
  }, [localConfig.backfillConfig]);

  // Validation
  useEffect(() => {
    const errors: string[] = [];

    if (localConfig.type === 'scheduled' || localConfig.type === 'backfill_with_schedule') {
      if (!localConfig.frequency) {
        errors.push('Schedule frequency is required');
      }
      if (!localConfig.time) {
        errors.push('Schedule time is required');
      }
      if (localConfig.frequency === 'weekly' && localConfig.dayOfWeek === undefined) {
        errors.push('Day of week is required for weekly schedules');
      }
      if (localConfig.frequency === 'monthly' && localConfig.dayOfMonth === undefined) {
        errors.push('Day of month is required for monthly schedules');
      }
    }

    if (localConfig.type === 'backfill_with_schedule' && localConfig.backfillConfig) {
      if (localConfig.backfillConfig.periods <= 0) {
        errors.push('Backfill periods must be greater than 0');
      }
      if (backfillCalculations?.exceedsLimit) {
        errors.push('Backfill period exceeds AMC\'s 14-month data retention limit');
      }
    }

    setValidationErrors(errors);
  }, [localConfig, backfillCalculations]);

  const handleTypeChange = (type: ScheduleConfig['type']) => {
    const newConfig: ScheduleConfig = {
      ...localConfig,
      type,
    };

    // Set defaults based on type
    if (type === 'scheduled') {
      newConfig.frequency = newConfig.frequency || 'daily';
      newConfig.time = newConfig.time || '09:00';
    } else if (type === 'backfill_with_schedule') {
      newConfig.frequency = newConfig.frequency || 'daily';
      newConfig.time = newConfig.time || '09:00';
      newConfig.backfillConfig = newConfig.backfillConfig || {
        enabled: true,
        periods: 52,
        segmentation: 'weekly',
      };
    }

    setLocalConfig(newConfig);
    onScheduleChange(newConfig);
  };

  const handleFrequencyChange = (frequency: ScheduleConfig['frequency']) => {
    const newConfig = { ...localConfig, frequency };

    // Set defaults for day selection
    if (frequency === 'weekly' && newConfig.dayOfWeek === undefined) {
      newConfig.dayOfWeek = 1; // Monday
    } else if (frequency === 'monthly' && newConfig.dayOfMonth === undefined) {
      newConfig.dayOfMonth = 1;
    }

    setLocalConfig(newConfig);
    onScheduleChange(newConfig);
  };

  const handleBackfillChange = (field: keyof BackfillConfig, value: any) => {
    if (!localConfig.backfillConfig) return;

    const newConfig = {
      ...localConfig,
      backfillConfig: {
        ...localConfig.backfillConfig,
        [field]: value,
      },
    };

    setLocalConfig(newConfig);
    onScheduleChange(newConfig);
  };

  const canProceed = validationErrors.length === 0;

  const getScheduleSummary = () => {
    if (localConfig.type === 'once') {
      return 'Immediate execution';
    }

    const timeStr = localConfig.time || '09:00';
    const timezone = TIMEZONES.find(tz => tz.value === localConfig.timezone)?.label || localConfig.timezone;
    let frequencyStr = '';

    if (localConfig.frequency === 'daily') {
      frequencyStr = `Daily at ${timeStr}`;
    } else if (localConfig.frequency === 'weekly') {
      const day = DAYS_OF_WEEK.find(d => d.value === localConfig.dayOfWeek)?.label || 'Monday';
      frequencyStr = `Weekly on ${day} at ${timeStr}`;
    } else if (localConfig.frequency === 'monthly') {
      frequencyStr = `Monthly on day ${localConfig.dayOfMonth || 1} at ${timeStr}`;
    }

    if (localConfig.type === 'backfill_with_schedule' && backfillCalculations) {
      const { periods, segmentation } = localConfig.backfillConfig!;
      return `${periods} ${segmentation} periods historical, then ${frequencyStr.toLowerCase()} (${timezone})`;
    }

    return `${frequencyStr} (${timezone})`;
  };

  return (
    <div className="space-y-6">
      {/* Schedule Type Selection */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Clock className="h-5 w-5 mr-2" />
          Execution Schedule
        </h3>

        <div className="space-y-3">
          <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="scheduleType"
              value="once"
              checked={localConfig.type === 'once'}
              onChange={() => handleTypeChange('once')}
              className="mt-1 text-blue-600 focus:ring-blue-500"
              aria-label="Run Once"
            />
            <div className="ml-3">
              <div className="font-medium text-gray-900">Run Once</div>
              <div className="text-sm text-gray-500">Execute immediately when submitted</div>
            </div>
          </label>

          <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="scheduleType"
              value="scheduled"
              checked={localConfig.type === 'scheduled'}
              onChange={() => handleTypeChange('scheduled')}
              className="mt-1 text-blue-600 focus:ring-blue-500"
              aria-label="Scheduled"
            />
            <div className="ml-3">
              <div className="font-medium text-gray-900">Scheduled</div>
              <div className="text-sm text-gray-500">Run automatically on a schedule</div>
            </div>
          </label>

          <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
            <input
              type="radio"
              name="scheduleType"
              value="backfill_with_schedule"
              checked={localConfig.type === 'backfill_with_schedule'}
              onChange={() => handleTypeChange('backfill_with_schedule')}
              className="mt-1 text-blue-600 focus:ring-blue-500"
              aria-label="Backfill with Schedule"
            />
            <div className="ml-3">
              <div className="font-medium text-gray-900">Backfill with Schedule</div>
              <div className="text-sm text-gray-500">
                Backfill historical data first, then continue on schedule
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* Schedule Configuration */}
      {(localConfig.type === 'scheduled' || localConfig.type === 'backfill_with_schedule') && (
        <div className="border-t pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4">Schedule Configuration</h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="frequency" className="block text-sm font-medium text-gray-700 mb-1">
                Frequency
              </label>
              <select
                id="frequency"
                value={localConfig.frequency || 'daily'}
                onChange={(e) => handleFrequencyChange(e.target.value as ScheduleConfig['frequency'])}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            <div>
              <label htmlFor="time" className="block text-sm font-medium text-gray-700 mb-1">
                Time
              </label>
              <input
                id="time"
                type="time"
                value={localConfig.time || '09:00'}
                onChange={(e) => {
                  const newConfig = { ...localConfig, time: e.target.value };
                  setLocalConfig(newConfig);
                  onScheduleChange(newConfig);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {localConfig.frequency === 'weekly' && (
              <div>
                <label htmlFor="dayOfWeek" className="block text-sm font-medium text-gray-700 mb-1">
                  Day of Week
                </label>
                <select
                  id="dayOfWeek"
                  value={localConfig.dayOfWeek || 1}
                  onChange={(e) => {
                    const newConfig = { ...localConfig, dayOfWeek: parseInt(e.target.value) };
                    setLocalConfig(newConfig);
                    onScheduleChange(newConfig);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {DAYS_OF_WEEK.map(day => (
                    <option key={day.value} value={day.value}>{day.label}</option>
                  ))}
                </select>
              </div>
            )}

            {localConfig.frequency === 'monthly' && (
              <div>
                <label htmlFor="dayOfMonth" className="block text-sm font-medium text-gray-700 mb-1">
                  Day of Month
                </label>
                <input
                  id="dayOfMonth"
                  type="number"
                  min="1"
                  max="31"
                  value={localConfig.dayOfMonth || 1}
                  onChange={(e) => {
                    const newConfig = { ...localConfig, dayOfMonth: parseInt(e.target.value) };
                    setLocalConfig(newConfig);
                    onScheduleChange(newConfig);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            <div className="col-span-2">
              <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
                Timezone
              </label>
              <select
                id="timezone"
                value={localConfig.timezone}
                onChange={(e) => {
                  const newConfig = { ...localConfig, timezone: e.target.value };
                  setLocalConfig(newConfig);
                  onScheduleChange(newConfig);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {TIMEZONES.map(tz => (
                  <option key={tz.value} value={tz.value}>{tz.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Backfill Configuration */}
      {localConfig.type === 'backfill_with_schedule' && localConfig.backfillConfig && (
        <div className="border-t pt-6">
          <h4 className="text-md font-medium text-gray-900 mb-4 flex items-center">
            <Database className="h-4 w-4 mr-2" />
            Backfill Configuration
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="periods" className="block text-sm font-medium text-gray-700 mb-1">
                Number of Periods
              </label>
              <input
                id="periods"
                type="number"
                min="1"
                max="365"
                value={localConfig.backfillConfig.periods}
                onChange={(e) => handleBackfillChange('periods', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label htmlFor="segmentation" className="block text-sm font-medium text-gray-700 mb-1">
                Segmentation
              </label>
              <select
                id="segmentation"
                value={localConfig.backfillConfig.segmentation}
                onChange={(e) => handleBackfillChange('segmentation', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          {/* Progress Calculation */}
          {backfillCalculations && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-2" />
                <div className="text-sm text-blue-900">
                  <p className="font-medium mb-1">Backfill Summary</p>
                  <ul className="space-y-1 text-blue-700">
                    <li>• {localConfig.backfillConfig.periods} {localConfig.backfillConfig.segmentation} segments</li>
                    <li>• Total period: {backfillCalculations.totalDays} days</li>
                    <li>• Parallel processing: up to {PARALLEL_EXECUTIONS} executions</li>
                    <li>• Estimated completion: {backfillCalculations.estimatedHours < 1
                        ? `${Math.round(backfillCalculations.estimatedHours * 60)} minutes`
                        : `${backfillCalculations.estimatedHours} hours`}</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Warnings */}
          {backfillCalculations?.isLarge && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 mr-2" />
                <div className="text-sm text-yellow-800">
                  <p className="font-medium">Large backfill operation</p>
                  <p className="mt-1">This backfill may take several hours to complete. Progress will be tracked in the dashboard.</p>
                </div>
              </div>
            </div>
          )}

          {backfillCalculations?.exceedsLimit && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 mr-2" />
                <div className="text-sm text-red-800">
                  <p className="font-medium">Exceeds AMC data retention limit</p>
                  <p className="mt-1">The backfill period exceeds AMC's 14-month data retention limit. Please reduce the number of periods.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Schedule Summary */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Schedule Summary</h4>
        <div className="text-sm text-gray-900">
          <div className="flex items-center">
            <Calendar className="h-4 w-4 mr-2 text-gray-500" />
            {localConfig.type === 'once' && 'Run once - Immediate execution'}
            {localConfig.type === 'scheduled' && getScheduleSummary()}
            {localConfig.type === 'backfill_with_schedule' && (
              <div>
                <div>{localConfig.backfillConfig?.periods} {localConfig.backfillConfig?.segmentation} historical</div>
                <div className="text-xs text-gray-600 mt-1">Then {getScheduleSummary().toLowerCase()}</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          {validationErrors.map((error, index) => (
            <p key={index} className="text-sm text-red-600">{error}</p>
          ))}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <button
          onClick={onPrevious}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md
                   text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2
                   focus:ring-offset-2 focus:ring-blue-500"
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous
        </button>

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