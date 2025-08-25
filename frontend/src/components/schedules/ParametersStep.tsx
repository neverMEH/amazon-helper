import React from 'react';
import { Bell, Mail, DollarSign, AlertTriangle } from 'lucide-react';
import type { ScheduleConfig } from '../../types/schedule';

interface ParametersStepProps {
  config: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
  onNext: () => void;
  onBack: () => void;
}

const ParametersStep: React.FC<ParametersStepProps> = ({ config, onChange, onNext, onBack }) => {
  const handleNotificationChange = (field: string, value: any) => {
    onChange({
      ...config,
      notifications: {
        ...config.notifications,
        [field]: value,
      },
    });
  };


  const getDefaultLookbackDays = () => {
    if (config.type === 'interval' && config.intervalDays) {
      return config.intervalDays;
    }
    if (config.type === 'weekly') {
      return 7;
    }
    if (config.type === 'monthly') {
      return 30;
    }
    return 1; // Daily
  };

  const handleLookbackChange = (value: string) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue > 0) {
      onChange({
        ...config,
        lookbackDays: numValue,
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">Configure Parameters</h3>
        <p className="text-gray-600 text-sm">
          Set default parameters and notification preferences for scheduled runs
        </p>
      </div>

      {/* Dynamic Parameters */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Query Parameters</h4>
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Lookback Period
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="number"
                value={config.lookbackDays || getDefaultLookbackDays()}
                onChange={(e) => handleLookbackChange(e.target.value)}
                min="1"
                max="365"
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white w-24 focus:ring-blue-500 focus:border-blue-500"
              />
              <span className="text-sm text-gray-600">days</span>
              <button
                type="button"
                onClick={() => onChange({ ...config, lookbackDays: undefined })}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Reset to default ({getDefaultLookbackDays()})
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Adjust how many days of data to include in each scheduled execution. 
              Default is based on your schedule frequency.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Custom Parameters (Optional)
            </label>
            <textarea
              placeholder='{"aggregation": "daily", "filter": "campaign_type=SD"}'
              value={JSON.stringify(config.parameters, null, 2)}
              onChange={(e) => {
                try {
                  const params = JSON.parse(e.target.value);
                  onChange({ ...config, parameters: params });
                } catch {
                  // Invalid JSON, don't update
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
              rows={3}
            />
            <p className="text-xs text-gray-500 mt-1">
              JSON format. These will be merged with dynamic date parameters.
            </p>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          <Bell className="w-4 h-4 inline mr-2" />
          Notifications
        </h4>
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.notifications.onSuccess}
              onChange={(e) => handleNotificationChange('onSuccess', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">Notify on successful execution</span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={config.notifications.onFailure}
              onChange={(e) => handleNotificationChange('onFailure', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <span className="ml-2 text-sm text-gray-700">Notify on failed execution</span>
          </label>

          {(config.notifications.onSuccess || config.notifications.onFailure) && (
            <div className="ml-6 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="w-4 h-4 inline mr-2" />
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="your@email.com"
                  value={config.notifications.email || ''}
                  onChange={(e) => handleNotificationChange('email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Settings */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Advanced Settings</h4>
        <div className="space-y-3">
          <div>
            <label className="flex items-center justify-between">
              <span className="text-sm text-gray-700">
                <AlertTriangle className="w-4 h-4 inline mr-2 text-yellow-600" />
                Auto-pause on consecutive failures
              </span>
              <input
                type="checkbox"
                checked={config.autoPauseOnFailure ?? false}
                onChange={(e) => onChange({ ...config, autoPauseOnFailure: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </label>
            <p className="text-xs text-gray-500 mt-1 ml-6">
              Automatically pause the schedule after 3 consecutive failures
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <DollarSign className="w-4 h-4 inline mr-2" />
              Cost Limit (Optional)
            </label>
            <div className="flex items-center space-x-2">
              <span className="text-gray-500">$</span>
              <input
                type="number"
                placeholder="100.00"
                value={config.costLimit || ''}
                onChange={(e) => onChange({ ...config, costLimit: parseFloat(e.target.value) || undefined })}
                className="px-3 py-2 border border-gray-300 rounded-lg w-32"
                step="0.01"
              />
              <span className="text-sm text-gray-600">per execution</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={onNext}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Continue
        </button>
      </div>
    </div>
  );
};

export default ParametersStep;