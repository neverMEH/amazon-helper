import { useState, useMemo } from 'react';
import {
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  Edit2, Check, AlertTriangle, Info, Code,
  Calendar, Clock, Database, DollarSign, FileText
} from 'lucide-react';
import { format, subDays, parseISO } from 'date-fns';
import SQLEditor from '../common/SQLEditor';

interface LookbackConfig {
  type: 'relative' | 'custom';
  value?: number;
  unit?: 'days' | 'weeks' | 'months';
  startDate?: string;
  endDate?: string;
}

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

interface EstimatedCost {
  dataScanned: string;
  estimatedCost: string;
  queryComplexity: 'Low' | 'Medium' | 'High';
}

interface ReportReviewStepProps {
  workflowId: string;
  workflowName: string;
  instanceId: string;
  instanceName: string;
  sqlQuery: string;
  parameters: Record<string, any>;
  lookbackConfig: LookbackConfig;
  scheduleConfig: ScheduleConfig;
  estimatedCost: EstimatedCost | null;
  validationWarnings?: string[];
  onNext: () => void;
  onPrevious: () => void;
  onEdit: (section: 'parameters' | 'lookback' | 'schedule') => void;
}

const TIMEZONE_LABELS: Record<string, string> = {
  'America/Los_Angeles': 'Pacific Time',
  'America/Denver': 'Mountain Time',
  'America/Chicago': 'Central Time',
  'America/New_York': 'Eastern Time',
  'Europe/London': 'London',
  'Europe/Paris': 'Paris',
  'Asia/Tokyo': 'Tokyo',
  'Australia/Sydney': 'Sydney',
};

const DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export default function ReportReviewStep({
  workflowId,
  workflowName,
  instanceId,
  instanceName,
  sqlQuery,
  parameters,
  lookbackConfig,
  scheduleConfig,
  estimatedCost,
  validationWarnings = [],
  onNext,
  onPrevious,
  onEdit,
}: ReportReviewStepProps) {
  const [showQueryPreview, setShowQueryPreview] = useState(true);
  const [showParameterDetails, setShowParameterDetails] = useState(false);

  // Calculate date range from lookback config
  const dateRange = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (lookbackConfig.type === 'custom' && lookbackConfig.startDate && lookbackConfig.endDate) {
      return {
        start: parseISO(lookbackConfig.startDate),
        end: parseISO(lookbackConfig.endDate),
      };
    }

    if (lookbackConfig.type === 'relative' && lookbackConfig.value) {
      let days = lookbackConfig.value;
      if (lookbackConfig.unit === 'weeks') days *= 7;
      if (lookbackConfig.unit === 'months') days *= 30;

      return {
        start: subDays(today, days),
        end: today,
      };
    }

    return { start: subDays(today, 7), end: today };
  }, [lookbackConfig]);

  // Process SQL with parameter injection for preview
  const processedSQL = useMemo(() => {
    let sql = sqlQuery;

    // Add campaign filter if campaigns parameter exists
    if (parameters.campaigns && Array.isArray(parameters.campaigns) && parameters.campaigns.length > 0) {
      const campaignValues = parameters.campaigns.map(c => `'${c}'`).join(', ');
      const campaignCTE = `WITH campaign_filter AS (
  SELECT * FROM (VALUES ${campaignValues}) AS t(campaign_id)
)
`;
      sql = campaignCTE + sql;
    }

    // Add ASIN filter if asins parameter exists
    if (parameters.asins && Array.isArray(parameters.asins) && parameters.asins.length > 0) {
      const asinValues = parameters.asins.map(a => `'${a}'`).join(', ');
      const asinCTE = `WITH asin_filter AS (
  SELECT * FROM (VALUES ${asinValues}) AS t(asin)
)
`;
      sql = asinCTE + sql;
    }

    // Replace date placeholders
    sql = sql.replace(/\{\{start_date\}\}/g, format(dateRange.start, 'yyyy-MM-dd'));
    sql = sql.replace(/\{\{end_date\}\}/g, format(dateRange.end, 'yyyy-MM-dd'));

    return sql;
  }, [sqlQuery, parameters, dateRange]);

  // Format lookback display
  const formatLookback = () => {
    if (lookbackConfig.type === 'relative') {
      return `Last ${lookbackConfig.value} ${lookbackConfig.unit}`;
    }
    return `${format(dateRange.start, 'MMM dd, yyyy')} to ${format(dateRange.end, 'MMM dd, yyyy')}`;
  };

  // Format schedule display
  const formatSchedule = () => {
    if (scheduleConfig.type === 'once') {
      return 'Run once - Immediate execution';
    }

    const time = scheduleConfig.time || '09:00';
    const timezone = TIMEZONE_LABELS[scheduleConfig.timezone] || scheduleConfig.timezone;
    let schedule = '';

    if (scheduleConfig.frequency === 'daily') {
      schedule = `Daily at ${time}`;
    } else if (scheduleConfig.frequency === 'weekly') {
      const day = DAYS_OF_WEEK[scheduleConfig.dayOfWeek || 1];
      schedule = `Weekly on ${day} at ${time}`;
    } else if (scheduleConfig.frequency === 'monthly') {
      schedule = `Monthly on day ${scheduleConfig.dayOfMonth || 1} at ${time}`;
    }

    if (scheduleConfig.type === 'backfill_with_schedule' && scheduleConfig.backfillConfig) {
      const { periods, segmentation } = scheduleConfig.backfillConfig;
      const totalDays = segmentation === 'daily' ? periods :
                       segmentation === 'weekly' ? periods * 7 :
                       periods * 30;
      return (
        <>
          <div>{periods} {segmentation} segments ({totalDays} days historical)</div>
          <div className="text-sm text-gray-600 mt-1">Then {schedule.toLowerCase()} ({timezone})</div>
        </>
      );
    }

    return `${schedule} (${timezone})`;
  };

  const isHighCost = estimatedCost && parseFloat(estimatedCost.estimatedCost.replace('$', '')) > 10;
  const hasLargeBackfill = scheduleConfig.backfillConfig && scheduleConfig.backfillConfig.periods > 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2 flex items-center">
          <FileText className="h-5 w-5 mr-2" />
          Review Configuration
        </h3>
        <p className="text-sm text-gray-500">
          Review all settings before submitting your report configuration
        </p>
      </div>

      {/* Validation Status */}
      <div className={`p-4 rounded-lg flex items-start ${
        validationWarnings.length > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'
      }`}>
        {validationWarnings.length > 0 ? (
          <>
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
            <div>
              <p className="text-sm font-medium text-yellow-800">Validation Warnings</p>
              <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                {validationWarnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          </>
        ) : (
          <>
            <Check className="h-5 w-5 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-green-800">All checks passed</p>
              <p className="text-sm text-green-700">Your configuration is ready for submission</p>
            </div>
          </>
        )}
      </div>

      {/* Configuration Summary Card */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">Configuration Summary</h4>

        <div className="space-y-4">
          {/* Workflow Info */}
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-600">Report</p>
              <p className="font-medium text-gray-900">{workflowName}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Instance</p>
              <p className="font-medium text-gray-900">{instanceName}</p>
            </div>
          </div>

          {/* Lookback */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <p className="text-sm text-gray-600 flex items-center mb-1">
                  <Calendar className="h-4 w-4 mr-1" />
                  Lookback Window
                </p>
                <p className="font-medium text-gray-900">{formatLookback()}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Date Range: {format(dateRange.start, 'MMM dd, yyyy')} to {format(dateRange.end, 'MMM dd, yyyy')}
                </p>
              </div>
              <button
                data-testid="edit-lookback"
                onClick={() => onEdit('lookback')}
                className="text-blue-600 hover:text-blue-700 p-1"
                aria-label="Edit lookback"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Schedule */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <p className="text-sm text-gray-600 flex items-center mb-1">
                  <Clock className="h-4 w-4 mr-1" />
                  Schedule
                </p>
                <div className="font-medium text-gray-900">{formatSchedule()}</div>
              </div>
              <button
                data-testid="edit-schedule"
                onClick={() => onEdit('schedule')}
                className="text-blue-600 hover:text-blue-700 p-1"
                aria-label="Edit schedule"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Parameters */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <p className="text-sm text-gray-600 flex items-center mb-1">
                  <Database className="h-4 w-4 mr-1" />
                  Parameters
                </p>
                {Object.keys(parameters).length === 0 ? (
                  <p className="text-sm text-gray-500 italic">No parameters configured</p>
                ) : (
                  <div>
                    {Object.entries(parameters).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm mt-1">
                        <span className="text-gray-600 capitalize">{key}:</span>
                        <span className="font-medium text-gray-900">
                          {Array.isArray(value) ? `${value.length} selected` : value}
                        </span>
                      </div>
                    ))}
                    {Object.keys(parameters).length > 0 && (
                      <button
                        onClick={() => setShowParameterDetails(!showParameterDetails)}
                        className="text-xs text-blue-600 hover:text-blue-700 mt-2 flex items-center"
                        aria-label="Show details"
                      >
                        {showParameterDetails ? (
                          <>Hide details <ChevronUp className="h-3 w-3 ml-1" /></>
                        ) : (
                          <>Show details <ChevronDown className="h-3 w-3 ml-1" /></>
                        )}
                      </button>
                    )}
                    {showParameterDetails && (
                      <div className="mt-2 p-2 bg-white rounded text-xs space-y-1">
                        {Object.entries(parameters).map(([key, value]) => (
                          <div key={key}>
                            <p className="font-medium text-gray-700">{key}:</p>
                            <p className="text-gray-600 ml-2">
                              {Array.isArray(value) ? value.join(', ') : value}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <button
                data-testid="edit-parameters"
                onClick={() => onEdit('parameters')}
                className="text-blue-600 hover:text-blue-700 p-1"
                aria-label="Edit parameters"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* SQL Query Preview */}
      <div className="border rounded-lg">
        <button
          onClick={() => setShowQueryPreview(!showQueryPreview)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
          aria-label="Query Preview"
        >
          <div className="flex items-center">
            <Code className="h-5 w-5 text-gray-600 mr-2" />
            <span className="text-sm font-medium text-gray-900">Query Preview</span>
          </div>
          {showQueryPreview ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </button>

        {showQueryPreview && (
          <div className="border-t p-4">
            <div className="mb-2 flex items-center text-xs text-gray-500">
              <Info className="h-3 w-3 mr-1" />
              Preview shows the SQL query with injected parameters
            </div>
            <SQLEditor
              value={processedSQL}
              onChange={() => {}}
              height="300px"
              readOnly={true}
            />
            {parameters.campaigns && (
              <p className="text-xs text-gray-500 mt-2">
                Campaign filters will be injected as WITH clause
              </p>
            )}
          </div>
        )}
      </div>

      {/* Cost Estimation */}
      <div className={`border rounded-lg p-4 ${isHighCost ? 'border-yellow-300 bg-yellow-50' : ''}`}>
        <div className="flex items-start">
          <DollarSign className={`h-5 w-5 mr-3 mt-0.5 ${isHighCost ? 'text-yellow-600' : 'text-gray-600'}`} />
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900 mb-2">Cost Estimation</p>
            {estimatedCost ? (
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Data Scanned:</span>
                  <span className="font-medium">{estimatedCost.dataScanned}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Estimated Cost:</span>
                  <span className="font-medium">{estimatedCost.estimatedCost}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Query Complexity:</span>
                  <span className={`font-medium ${
                    estimatedCost.queryComplexity === 'High' ? 'text-red-600' :
                    estimatedCost.queryComplexity === 'Medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>{estimatedCost.queryComplexity}</span>
                </div>
                {isHighCost && (
                  <div className="mt-2 p-2 bg-yellow-100 rounded text-xs text-yellow-800">
                    <p className="font-medium">High cost query</p>
                    <p>AMC charges may apply for large data scans</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500 italic">Cost estimation unavailable</p>
            )}
          </div>
        </div>
      </div>

      {/* Warnings for large operations */}
      {hasLargeBackfill && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
            <div>
              <p className="text-sm font-medium text-yellow-800">Large backfill operation</p>
              <p className="text-sm text-yellow-700 mt-1">
                This operation will process {scheduleConfig.backfillConfig?.periods} periods and may take several hours to complete.
                You will be able to monitor progress in the dashboard.
              </p>
            </div>
          </div>
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
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md
                   shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2
                   focus:ring-offset-2 focus:ring-blue-500"
        >
          Continue to Submit
          <ChevronRight className="ml-2 h-4 w-4" />
        </button>
      </div>
    </div>
  );
}