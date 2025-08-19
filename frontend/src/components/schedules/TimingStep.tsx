import React, { useEffect, useState } from 'react';
import { Clock, Globe, AlertCircle } from 'lucide-react';
import { format, addDays } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';
import type { ScheduleConfig } from '../../types/schedule';
import { scheduleService } from '../../services/scheduleService';

interface TimingStepProps {
  config: ScheduleConfig;
  onChange: (config: ScheduleConfig) => void;
  onNext: () => void;
  onBack: () => void;
}

const commonTimezones = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEDT)' },
];

const TimingStep: React.FC<TimingStepProps> = ({ config, onChange, onNext, onBack }) => {
  const [nextRuns, setNextRuns] = useState<string[]>([]);
  const [localTime, setLocalTime] = useState('');

  useEffect(() => {
    // Update local time display
    const updateLocalTime = () => {
      if (config.timezone && config.executeTime) {
        const [hour, minute] = config.executeTime.split(':');
        const now = new Date();
        now.setHours(parseInt(hour), parseInt(minute), 0, 0);
        
        try {
          const formatted = formatInTimeZone(now, config.timezone, 'h:mm a zzz');
          setLocalTime(formatted);
        } catch {
          setLocalTime(config.executeTime);
        }
      }
    };

    updateLocalTime();
  }, [config.timezone, config.executeTime]);

  useEffect(() => {
    // Preview next runs
    const calculateNextRuns = () => {
      const runs: string[] = [];
      scheduleService.generateCronExpression(config);
      
      // Simple preview calculation
      const now = new Date();
      const [hour, minute] = config.executeTime.split(':');
      
      for (let i = 0; i < 5; i++) {
        const nextRun = addDays(now, i);
        nextRun.setHours(parseInt(hour), parseInt(minute), 0, 0);
        
        // Skip dates based on schedule type
        if (config.type === 'weekly' && config.dayOfWeek !== undefined) {
          if (nextRun.getDay() !== config.dayOfWeek) continue;
        }
        
        runs.push(format(nextRun, 'EEE, MMM d, yyyy'));
        if (runs.length >= 3) break;
      }
      
      setNextRuns(runs);
    };

    calculateNextRuns();
  }, [config]);

  const handleTimeChange = (time: string) => {
    onChange({ ...config, executeTime: time });
  };

  const handleTimezoneChange = (timezone: string) => {
    onChange({ ...config, timezone });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-2">Set Execution Time</h3>
        <p className="text-gray-600 text-sm">
          Choose when the workflow should run in your selected timezone
        </p>
      </div>

      {/* Time Picker */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Clock className="w-4 h-4 inline mr-2" />
          Execution Time
        </label>
        <div className="flex items-center space-x-4">
          <input
            type="time"
            value={config.executeTime}
            onChange={(e) => handleTimeChange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {localTime && (
            <span className="text-sm text-gray-600">
              {localTime}
            </span>
          )}
        </div>
      </div>

      {/* Timezone Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Globe className="w-4 h-4 inline mr-2" />
          Timezone
        </label>
        <select
          value={config.timezone}
          onChange={(e) => handleTimezoneChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {commonTimezones.map((tz) => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
      </div>

      {/* Day of Month for Monthly Schedules */}
      {config.type === 'monthly' && config.monthlyType === 'specific' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Day of Month
          </label>
          <select
            value={config.dayOfMonth || 1}
            onChange={(e) => onChange({ ...config, dayOfMonth: parseInt(e.target.value) })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {Array.from({ length: 31 }, (_, i) => i + 1).map((day) => (
              <option key={day} value={day}>
                {day}{day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Next Runs Preview */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Next Scheduled Runs</h4>
        <div className="space-y-1">
          {nextRuns.length > 0 ? (
            nextRuns.map((run, index) => (
              <div key={index} className="text-sm text-blue-700">
                {run} at {config.executeTime}
              </div>
            ))
          ) : (
            <div className="text-sm text-blue-700">Calculating...</div>
          )}
        </div>
      </div>

      {/* Data Lag Warning */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-yellow-600 mr-2 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <strong>Important:</strong> AMC data has a 14-day lag. The workflow will automatically
            query data from 14 days ago, not the current date.
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

export default TimingStep;