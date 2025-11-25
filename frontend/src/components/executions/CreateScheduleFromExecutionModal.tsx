import { useState, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  X,
  Calendar,
  Clock,
  TrendingUp,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Loader,
  Database,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { format, addDays, subDays } from 'date-fns';
import api from '../../services/api';
import type {
  CreateScheduleFromExecutionModalProps,
  ScheduleWizardState,
  ScheduleFrequency,
  ScheduleCreateFromExecutionPayload,
  ExecutionScheduleData,
} from '../../types/executionSchedule';
import {
  extractExecutionScheduleData,
  getDefaultWizardState,
  TIMEZONE_OPTIONS,
  DAYS_OF_WEEK,
  LOOKBACK_PRESETS,
} from '../../types/executionSchedule';

// AMC has 14-day data processing lag
const AMC_DATA_LAG_DAYS = 14;

/**
 * 4-step wizard for creating a schedule from an execution
 * Pre-populates Snowflake configuration from the source execution
 */
export default function CreateScheduleFromExecutionModal({
  isOpen,
  onClose,
  execution,
  onSuccess,
}: CreateScheduleFromExecutionModalProps) {
  const navigate = useNavigate();

  // Extract execution data for pre-population
  const executionData = useMemo(() => extractExecutionScheduleData(execution), [execution]);

  // Initialize wizard state with pre-populated values
  const [wizardState, setWizardState] = useState<ScheduleWizardState>(() =>
    executionData ? getDefaultWizardState(executionData) : getEmptyWizardState()
  );

  const [currentStep, setCurrentStep] = useState(1);
  const [customLookback, setCustomLookback] = useState(false);

  // Steps definition
  const steps = [
    { id: 1, name: 'Schedule Type', icon: Calendar },
    { id: 2, name: 'Timing', icon: Clock },
    { id: 3, name: 'Date Range', icon: TrendingUp },
    { id: 4, name: 'Review', icon: CheckCircle },
  ];

  // Create schedule mutation
  const createScheduleMutation = useMutation({
    mutationFn: async (payload: ScheduleCreateFromExecutionPayload) => {
      if (!executionData?.workflowId) {
        throw new Error('Workflow ID not found');
      }
      const response = await api.post(
        `/workflows/${executionData.workflowId}/schedules`,
        payload
      );
      return response.data;
    },
    onSuccess: () => {
      toast.success('Schedule created successfully!');
      onClose();
      onSuccess?.();
      navigate('/schedules');
    },
    onError: (error: unknown) => {
      const errorMessage =
        error && typeof error === 'object' && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : 'Failed to create schedule';
      toast.error(errorMessage || 'Failed to create schedule');
    },
  });

  // Handle form submission
  const handleSubmit = () => {
    const payload: ScheduleCreateFromExecutionPayload = {
      preset_type: wizardState.frequency,
      name: wizardState.name,
      description: wizardState.description || undefined,
      timezone: wizardState.timezone,
      execute_time: wizardState.executeTime,
      lookback_days: wizardState.lookbackDays,
      date_range_type: wizardState.dateRangeType,
      snowflake_enabled: wizardState.snowflakeEnabled,
      snowflake_table_name: wizardState.snowflakeEnabled ? wizardState.snowflakeTableName : undefined,
      snowflake_schema_name: wizardState.snowflakeEnabled && wizardState.snowflakeSchemaName
        ? wizardState.snowflakeSchemaName
        : undefined,
      snowflake_strategy: wizardState.snowflakeEnabled ? wizardState.snowflakeStrategy : undefined,
    };

    // Add day of week/month based on frequency
    if (wizardState.frequency === 'weekly' && wizardState.dayOfWeek !== undefined) {
      payload.day_of_week = wizardState.dayOfWeek;
    }
    if (wizardState.frequency === 'monthly' && wizardState.dayOfMonth !== undefined) {
      payload.day_of_month = wizardState.dayOfMonth;
    }

    createScheduleMutation.mutate(payload);
  };

  // Navigation
  const canGoNext = () => {
    switch (currentStep) {
      case 1:
        return !!wizardState.frequency;
      case 2:
        return !!wizardState.executeTime && !!wizardState.timezone;
      case 3:
        return wizardState.lookbackDays > 0 && wizardState.lookbackDays <= 365;
      case 4:
        return !wizardState.snowflakeEnabled || !!wizardState.snowflakeTableName;
      default:
        return false;
    }
  };

  const goNext = () => {
    if (currentStep < 4 && canGoNext()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const goBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Calculate preview dates for date range step
  const previewDates = useMemo(() => {
    const today = new Date();
    const dates: { executionDate: Date; startDate: Date; endDate: Date }[] = [];

    for (let i = 0; i < 3; i++) {
      let executionDate: Date;

      if (wizardState.frequency === 'daily') {
        executionDate = addDays(today, i);
      } else if (wizardState.frequency === 'weekly') {
        executionDate = addDays(today, i * 7);
      } else {
        executionDate = addDays(today, i * 30);
      }

      // Account for AMC data lag
      const endDate = subDays(executionDate, AMC_DATA_LAG_DAYS);
      const startDate = subDays(endDate, wizardState.lookbackDays);

      dates.push({ executionDate, startDate, endDate });
    }

    return dates;
  }, [wizardState.frequency, wizardState.lookbackDays]);

  if (!isOpen) return null;

  // Check if execution has required data
  if (!executionData) {
    return (
      <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
          <div className="flex items-center gap-3 text-red-600 mb-4">
            <AlertTriangle className="h-6 w-6" />
            <h3 className="text-lg font-medium">Cannot Create Schedule</h3>
          </div>
          <p className="text-gray-600 mb-4">
            This execution does not have an associated workflow. A workflow is required to create a schedule.
          </p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Create Schedule from Execution</h2>
            <p className="text-sm text-gray-500 mt-1">
              {executionData.workflowName || 'Unnamed Workflow'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-gray-200">
          <nav className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = step.id < currentStep;

              return (
                <div key={step.id} className="flex items-center">
                  <div
                    className={`flex items-center gap-2 px-3 py-2 rounded-md ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-600'
                        : isCompleted
                        ? 'text-green-600'
                        : 'text-gray-400'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="text-sm font-medium hidden sm:inline">{step.name}</span>
                    <span className="text-sm font-medium sm:hidden">{step.id}</span>
                  </div>
                  {index < steps.length - 1 && (
                    <ChevronRight className="h-4 w-4 text-gray-300 mx-2" />
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {/* Step 1: Schedule Type */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-1">Select Schedule Frequency</h3>
                <p className="text-sm text-gray-500">How often should this query run?</p>
              </div>

              <div className="grid gap-3">
                {(['daily', 'weekly', 'monthly'] as ScheduleFrequency[]).map((freq) => (
                  <label
                    key={freq}
                    className={`relative flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                      wizardState.frequency === freq
                        ? 'border-indigo-500 ring-2 ring-indigo-500 bg-indigo-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="frequency"
                      value={freq}
                      checked={wizardState.frequency === freq}
                      onChange={(e) =>
                        setWizardState((prev) => ({
                          ...prev,
                          frequency: e.target.value as ScheduleFrequency,
                          dayOfWeek: e.target.value === 'weekly' ? 1 : undefined,
                          dayOfMonth: e.target.value === 'monthly' ? 1 : undefined,
                        }))
                      }
                      className="sr-only"
                    />
                    <div className="flex-1">
                      <span className="block text-sm font-medium text-gray-900 capitalize">
                        {freq}
                      </span>
                      <span className="block text-sm text-gray-500 mt-1">
                        {freq === 'daily' && 'Run every day at the scheduled time'}
                        {freq === 'weekly' && 'Run once per week on a specific day'}
                        {freq === 'monthly' && 'Run once per month on a specific date'}
                      </span>
                    </div>
                    {wizardState.frequency === freq && (
                      <CheckCircle className="h-5 w-5 text-indigo-600" />
                    )}
                  </label>
                ))}
              </div>

              {/* Suggested frequency hint */}
              {executionData.dateRange && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex items-start gap-2">
                    <Info className="h-4 w-4 text-blue-600 mt-0.5" />
                    <div className="text-sm text-blue-700">
                      <p>
                        Based on your execution's {executionData.lookbackDays}-day date range,
                        we suggest a <strong>{wizardState.frequency}</strong> schedule.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Timing */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-1">Configure Timing</h3>
                <p className="text-sm text-gray-500">When should this schedule run?</p>
              </div>

              {/* Time of Day */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time of Day
                </label>
                <input
                  type="time"
                  value={wizardState.executeTime}
                  onChange={(e) =>
                    setWizardState((prev) => ({ ...prev, executeTime: e.target.value }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Recommended: 02:00 (off-peak hours for better performance)
                </p>
              </div>

              {/* Timezone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timezone
                </label>
                <select
                  value={wizardState.timezone}
                  onChange={(e) =>
                    setWizardState((prev) => ({ ...prev, timezone: e.target.value }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {TIMEZONE_OPTIONS.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Day of Week (for weekly) */}
              {wizardState.frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Day of Week
                  </label>
                  <select
                    value={wizardState.dayOfWeek ?? 1}
                    onChange={(e) =>
                      setWizardState((prev) => ({
                        ...prev,
                        dayOfWeek: parseInt(e.target.value, 10),
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {DAYS_OF_WEEK.map((day) => (
                      <option key={day.value} value={day.value}>
                        {day.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Day of Month (for monthly) */}
              {wizardState.frequency === 'monthly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Day of Month
                  </label>
                  <select
                    value={wizardState.dayOfMonth ?? 1}
                    onChange={(e) =>
                      setWizardState((prev) => ({
                        ...prev,
                        dayOfMonth: parseInt(e.target.value, 10),
                      }))
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {Array.from({ length: 28 }, (_, i) => i + 1).map((day) => (
                      <option key={day} value={day}>
                        {day}
                        {day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Days 29-31 may be skipped in shorter months
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Date Range */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-1">Configure Date Range</h3>
                <p className="text-sm text-gray-500">
                  Set the rolling window for each execution
                </p>
              </div>

              {/* AMC Data Lag Warning */}
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5" />
                  <div className="text-sm text-amber-700">
                    <p className="font-medium">AMC Data Processing Lag</p>
                    <p className="mt-1">
                      AMC data has a 14-day processing lag. Date ranges are automatically
                      adjusted to account for this.
                    </p>
                  </div>
                </div>
              </div>

              {/* Lookback Presets */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lookback Window
                </label>
                <div className="flex flex-wrap gap-2">
                  {LOOKBACK_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      onClick={() => {
                        setWizardState((prev) => ({ ...prev, lookbackDays: preset.value }));
                        setCustomLookback(false);
                      }}
                      className={`px-3 py-1.5 text-sm rounded-md border ${
                        !customLookback && wizardState.lookbackDays === preset.value
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                          : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => setCustomLookback(true)}
                    className={`px-3 py-1.5 text-sm rounded-md border ${
                      customLookback
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Custom
                  </button>
                </div>

                {/* Custom Input */}
                {customLookback && (
                  <div className="mt-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min={1}
                        max={365}
                        value={wizardState.lookbackDays}
                        onChange={(e) =>
                          setWizardState((prev) => ({
                            ...prev,
                            lookbackDays: parseInt(e.target.value, 10) || 30,
                          }))
                        }
                        className="w-24 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                      />
                      <span className="text-sm text-gray-500">days</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500">Enter a value between 1 and 365</p>
                  </div>
                )}
              </div>

              {/* Pre-calculated from execution hint */}
              {executionData.dateRange && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex items-start gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
                    <div className="text-sm text-green-700">
                      <p>
                        Pre-calculated from your execution's date range:{' '}
                        <strong>{executionData.lookbackDays} days</strong>
                        {executionData.dateRange.start && executionData.dateRange.end && (
                          <span className="text-green-600">
                            {' '}
                            ({executionData.dateRange.start} to {executionData.dateRange.end})
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Date Range Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preview: Next 3 Executions
                </label>
                <div className="bg-gray-50 rounded-md p-3 space-y-2">
                  {previewDates.map((preview, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">
                        {format(preview.executionDate, 'MMM d, yyyy')}
                      </span>
                      <span className="text-gray-700">
                        {format(preview.startDate, 'MMM d')} - {format(preview.endDate, 'MMM d, yyyy')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-medium text-gray-900 mb-1">Review & Configure</h3>
                <p className="text-sm text-gray-500">Review your schedule and configure Snowflake</p>
              </div>

              {/* Schedule Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schedule Name
                </label>
                <input
                  type="text"
                  value={wizardState.name}
                  onChange={(e) =>
                    setWizardState((prev) => ({ ...prev, name: e.target.value }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter a name for this schedule"
                />
              </div>

              {/* Schedule Summary */}
              <div className="bg-gray-50 rounded-md p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Schedule Summary</h4>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Frequency:</dt>
                    <dd className="text-gray-900 capitalize">{wizardState.frequency}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Time:</dt>
                    <dd className="text-gray-900">{wizardState.executeTime}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Timezone:</dt>
                    <dd className="text-gray-900">{wizardState.timezone}</dd>
                  </div>
                  {wizardState.frequency === 'weekly' && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Day:</dt>
                      <dd className="text-gray-900">
                        {DAYS_OF_WEEK.find((d) => d.value === wizardState.dayOfWeek)?.label}
                      </dd>
                    </div>
                  )}
                  {wizardState.frequency === 'monthly' && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Day:</dt>
                      <dd className="text-gray-900">{wizardState.dayOfMonth}</dd>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Lookback:</dt>
                    <dd className="text-gray-900">{wizardState.lookbackDays} days</dd>
                  </div>
                </dl>
              </div>

              {/* Snowflake Configuration */}
              <div className="border border-gray-200 rounded-md p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-blue-600" />
                    <h4 className="text-sm font-medium text-gray-900">Snowflake Upload</h4>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={wizardState.snowflakeEnabled}
                      onChange={(e) =>
                        setWizardState((prev) => ({
                          ...prev,
                          snowflakeEnabled: e.target.checked,
                        }))
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                  </label>
                </div>

                {/* Pre-populated from execution hint */}
                {executionData.snowflakeEnabled && (
                  <div className="mb-4 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                    <div className="flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      <span>Pre-populated from your execution's Snowflake configuration</span>
                    </div>
                  </div>
                )}

                {wizardState.snowflakeEnabled && (
                  <div className="space-y-4">
                    {/* Table Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Table Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={wizardState.snowflakeTableName}
                        onChange={(e) =>
                          setWizardState((prev) => ({
                            ...prev,
                            snowflakeTableName: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="e.g., campaign_metrics"
                      />
                      {executionData.snowflakeTableName && (
                        <p className="mt-1 text-xs text-gray-500">
                          Original execution uploaded to: {executionData.snowflakeTableName}
                        </p>
                      )}
                    </div>

                    {/* Schema Name */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Schema Name (optional)
                      </label>
                      <input
                        type="text"
                        value={wizardState.snowflakeSchemaName}
                        onChange={(e) =>
                          setWizardState((prev) => ({
                            ...prev,
                            snowflakeSchemaName: e.target.value,
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Uses default if empty"
                      />
                    </div>

                    {/* Strategy */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Upload Strategy
                      </label>
                      <select
                        value={wizardState.snowflakeStrategy}
                        onChange={(e) =>
                          setWizardState((prev) => ({
                            ...prev,
                            snowflakeStrategy: e.target.value as 'upsert' | 'append' | 'replace' | 'create_new',
                          }))
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="upsert">Upsert (recommended for schedules)</option>
                        <option value="append">Append</option>
                        <option value="replace">Replace</option>
                        <option value="create_new">Create New Table</option>
                      </select>
                      <p className="mt-1 text-xs text-gray-500">
                        Upsert prevents duplicate data using composite date range keys
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={currentStep === 1 ? onClose : goBack}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {currentStep === 1 ? 'Cancel' : (
              <span className="flex items-center gap-1">
                <ChevronLeft className="h-4 w-4" />
                Back
              </span>
            )}
          </button>

          {currentStep < 4 ? (
            <button
              onClick={goNext}
              disabled={!canGoNext()}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              <span className="flex items-center gap-1">
                Next
                <ChevronRight className="h-4 w-4" />
              </span>
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!canGoNext() || createScheduleMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {createScheduleMutation.isPending ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4" />
                  Create Schedule
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Empty wizard state for error cases
 */
function getEmptyWizardState(): ScheduleWizardState {
  return {
    frequency: 'weekly',
    executeTime: '02:00',
    timezone: 'UTC',
    lookbackDays: 30,
    dateRangeType: 'rolling',
    snowflakeEnabled: false,
    snowflakeTableName: '',
    snowflakeSchemaName: '',
    snowflakeStrategy: 'upsert',
    name: '',
    description: '',
  };
}
