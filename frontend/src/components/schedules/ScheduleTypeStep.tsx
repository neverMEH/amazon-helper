import React from 'react';
import { Calendar, Clock, Settings, TrendingUp, CalendarDays, Briefcase } from 'lucide-react';
import type { ScheduleConfig, SchedulePreset } from '../../types/schedule';

interface ScheduleTypeStepProps {
  config: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
  onNext: () => void;
}

const presets: SchedulePreset[] = [
  {
    id: 'daily',
    name: 'Daily',
    description: 'Run every day at the same time',
    icon: Calendar,
    type: 'daily',
  },
  {
    id: 'interval',
    name: 'Every N Days',
    description: 'Run every 3, 7, 14, 30 days etc.',
    icon: Clock,
    type: 'interval',
    intervalOptions: [1, 3, 7, 14, 30, 60, 90],
  },
  {
    id: 'weekly',
    name: 'Weekly',
    description: 'Run on specific days of the week',
    icon: CalendarDays,
    type: 'weekly',
  },
  {
    id: 'monthly',
    name: 'Monthly',
    description: 'Run on specific day of month',
    icon: TrendingUp,
    type: 'monthly',
    monthlyOptions: ['specific', 'first', 'last', 'firstBusiness', 'lastBusiness'],
  },
  {
    id: 'custom',
    name: 'Custom CRON',
    description: 'Advanced scheduling with CRON expression',
    icon: Settings,
    type: 'custom',
  },
];

const ScheduleTypeStep: React.FC<ScheduleTypeStepProps> = ({ config, onChange, onNext }) => {
  const handleTypeSelect = (preset: SchedulePreset) => {
    onChange({
      ...config,
      type: preset.type,
      intervalDays: preset.type === 'interval' ? 7 : undefined,
    });

    // Auto-advance for simple types
    if (preset.type === 'daily') {
      onNext();
    }
  };

  const handleIntervalSelect = (days: number) => {
    onChange({
      ...config,
      intervalDays: days,
    });
    onNext();
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">Choose Schedule Type</h3>
        <p className="text-gray-600 text-sm">
          Select how often you want this workflow to run
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {presets.map((preset) => {
          const Icon = preset.icon;
          const isSelected = config.type === preset.type;

          return (
            <div
              key={preset.id}
              onClick={() => handleTypeSelect(preset)}
              className={`
                border-2 rounded-lg p-4 cursor-pointer transition-all
                ${isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <div className="flex items-start">
                <div
                  className={`
                    p-2 rounded-lg mr-3
                    ${isSelected ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'}
                  `}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{preset.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{preset.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Interval Options */}
      {config.type === 'interval' && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Select Interval</h4>
          <div className="grid grid-cols-4 gap-2">
            {presets
              .find((p) => p.type === 'interval')
              ?.intervalOptions?.map((days) => (
                <button
                  key={days}
                  onClick={() => handleIntervalSelect(days)}
                  className={`
                    px-4 py-2 rounded-lg border text-sm font-medium transition-all
                    ${config.intervalDays === days
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    }
                  `}
                >
                  {days === 1 ? 'Daily' : `Every ${days} days`}
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Monthly Options */}
      {config.type === 'monthly' && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Monthly Schedule</h4>
          <div className="space-y-2">
            <button
              onClick={() => {
                onChange({ ...config, monthlyType: 'specific', dayOfMonth: 1 });
                onNext();
              }}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              <div className="font-medium">Specific Day</div>
              <div className="text-sm text-gray-600">Run on a specific day of the month (1-31)</div>
            </button>
            <button
              onClick={() => {
                onChange({ ...config, monthlyType: 'first' });
                onNext();
              }}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              <div className="font-medium">First Day</div>
              <div className="text-sm text-gray-600">Run on the 1st of each month</div>
            </button>
            <button
              onClick={() => {
                onChange({ ...config, monthlyType: 'last' });
                onNext();
              }}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              <div className="font-medium">Last Day</div>
              <div className="text-sm text-gray-600">Run on the last day of each month</div>
            </button>
            <button
              onClick={() => {
                onChange({ ...config, monthlyType: 'firstBusiness' });
                onNext();
              }}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              <div className="flex items-center">
                <Briefcase className="w-4 h-4 mr-2 text-gray-600" />
                <div className="font-medium">First Business Day</div>
              </div>
              <div className="text-sm text-gray-600 ml-6">Run on the first weekday of each month</div>
            </button>
            <button
              onClick={() => {
                onChange({ ...config, monthlyType: 'lastBusiness' });
                onNext();
              }}
              className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            >
              <div className="flex items-center">
                <Briefcase className="w-4 h-4 mr-2 text-gray-600" />
                <div className="font-medium">Last Business Day</div>
              </div>
              <div className="text-sm text-gray-600 ml-6">Run on the last weekday of each month</div>
            </button>
          </div>
        </div>
      )}

      {/* Weekly Options */}
      {config.type === 'weekly' && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Select Day of Week</h4>
          <div className="grid grid-cols-4 gap-2">
            {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(
              (day, index) => (
                <button
                  key={day}
                  onClick={() => {
                    onChange({ ...config, dayOfWeek: index });
                    onNext();
                  }}
                  className={`
                    px-4 py-2 rounded-lg border text-sm font-medium transition-all
                    ${config.dayOfWeek === index
                      ? 'border-blue-500 bg-blue-50 text-blue-600'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    }
                  `}
                >
                  {day.slice(0, 3)}
                </button>
              )
            )}
          </div>
        </div>
      )}

      {/* Custom CRON */}
      {config.type === 'custom' && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">CRON Expression</h4>
          <input
            type="text"
            placeholder="0 2 * * *"
            value={config.cronExpression || ''}
            onChange={(e) => onChange({ ...config, cronExpression: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-2">
            Format: minute hour day month weekday (e.g., "0 2 * * *" for daily at 2 AM)
          </p>
          <button
            onClick={onNext}
            disabled={!config.cronExpression}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continue
          </button>
        </div>
      )}
    </div>
  );
};

export default ScheduleTypeStep;