import React from 'react';
import { CheckCircle, Calendar, Clock, Bell, Settings, AlertCircle } from 'lucide-react';
import type { ScheduleConfig } from '../../types/schedule';
import { scheduleService } from '../../services/scheduleService';

interface ReviewStepProps {
  config: ScheduleConfig;
  workflowName: string;
  onComplete: () => void;
  onBack: () => void;
  isLoading: boolean;
}

const ReviewStep: React.FC<ReviewStepProps> = ({
  config,
  workflowName,
  onComplete,
  onBack,
  isLoading,
}) => {
  const getScheduleDescription = () => {
    switch (config.type) {
      case 'daily':
        return `Daily at ${config.executeTime}`;
      case 'interval':
        return config.intervalDays === 1
          ? `Daily at ${config.executeTime}`
          : `Every ${config.intervalDays} days at ${config.executeTime}`;
      case 'weekly':
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        return `Every ${days[config.dayOfWeek || 1]} at ${config.executeTime}`;
      case 'monthly':
        if (config.monthlyType === 'last') {
          return `Last day of month at ${config.executeTime}`;
        } else if (config.monthlyType === 'firstBusiness') {
          return `First business day of month at ${config.executeTime}`;
        } else if (config.monthlyType === 'lastBusiness') {
          return `Last business day of month at ${config.executeTime}`;
        } else {
          const day = config.dayOfMonth || 1;
          return `Monthly on the ${day}${day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'} at ${config.executeTime}`;
        }
      case 'custom':
        return config.cronExpression || 'Custom schedule';
      default:
        return 'Unknown schedule';
    }
  };

  const getCronExpression = () => {
    if (config.type === 'custom') {
      return config.cronExpression;
    }
    return scheduleService.generateCronExpression(config);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">Review Schedule</h3>
        <p className="text-gray-600 text-sm">
          Please review your schedule configuration before creating
        </p>
      </div>

      {/* Workflow Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Workflow</h4>
        <p className="text-gray-900 font-medium">{workflowName}</p>
      </div>

      {/* Schedule Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <Calendar className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-medium text-blue-900 mb-1">Schedule</h4>
            <p className="text-blue-800 font-medium">{getScheduleDescription()}</p>
            <p className="text-xs text-blue-600 mt-1">Timezone: {config.timezone}</p>
          </div>
        </div>
      </div>

      {/* Configuration Details */}
      <div className="space-y-4">
        {/* CRON Expression */}
        <div className="flex items-center justify-between py-2 border-b">
          <span className="text-sm text-gray-600">
            <Settings className="w-4 h-4 inline mr-2" />
            CRON Expression
          </span>
          <span className="text-sm font-mono text-gray-900">{getCronExpression()}</span>
        </div>

        {/* Data Lookback */}
        <div className="flex items-center justify-between py-2 border-b">
          <span className="text-sm text-gray-600">
            <Clock className="w-4 h-4 inline mr-2" />
            Data Lookback Period
          </span>
          <span className="text-sm text-gray-900">
            {config.type === 'interval' && config.intervalDays
              ? `${config.intervalDays} days`
              : config.type === 'weekly'
              ? '7 days'
              : config.type === 'monthly'
              ? '30 days'
              : '1 day'}
          </span>
        </div>

        {/* Notifications */}
        <div className="flex items-center justify-between py-2 border-b">
          <span className="text-sm text-gray-600">
            <Bell className="w-4 h-4 inline mr-2" />
            Notifications
          </span>
          <span className="text-sm text-gray-900">
            {config.notifications.onSuccess && config.notifications.onFailure
              ? 'On success and failure'
              : config.notifications.onSuccess
              ? 'On success only'
              : config.notifications.onFailure
              ? 'On failure only'
              : 'Disabled'}
          </span>
        </div>

        {/* Email */}
        {config.notifications.email && (
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">Email</span>
            <span className="text-sm text-gray-900">{config.notifications.email}</span>
          </div>
        )}

        {/* Auto-pause */}
        {config.autoPauseOnFailure && (
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">
              <AlertCircle className="w-4 h-4 inline mr-2 text-yellow-600" />
              Auto-pause
            </span>
            <span className="text-sm text-gray-900">After 3 consecutive failures</span>
          </div>
        )}

        {/* Cost Limit */}
        {config.costLimit && (
          <div className="flex items-center justify-between py-2 border-b">
            <span className="text-sm text-gray-600">Cost Limit</span>
            <span className="text-sm text-gray-900">${config.costLimit.toFixed(2)}</span>
          </div>
        )}
      </div>

      {/* Custom Parameters */}
      {Object.keys(config.parameters).length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Custom Parameters</h4>
          <pre className="bg-gray-50 rounded-lg p-3 text-xs font-mono text-gray-700 overflow-x-auto">
            {JSON.stringify(config.parameters, null, 2)}
          </pre>
        </div>
      )}

      {/* Info Message */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start">
          <CheckCircle className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-green-800">
            Your schedule will be created and activated immediately. The first execution will occur
            at the next scheduled time based on your configuration.
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Back
        </button>
        <button
          onClick={onComplete}
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Creating...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4 mr-2" />
              Create Schedule
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ReviewStep;