import React, { useState } from 'react';
import { X, Clock, Calendar, AlertCircle } from 'lucide-react';
import { format, addHours, addMinutes, isAfter, endOfDay } from 'date-fns';
import type { Schedule } from '../../types/schedule';

interface ScheduleRunModalProps {
  schedule: Schedule;
  onSchedule: (scheduledTime: Date) => Promise<void>;
  onClose: () => void;
}

const ScheduleRunModal: React.FC<ScheduleRunModalProps> = ({ schedule, onSchedule, onClose }) => {
  const now = new Date();
  const [selectedOption, setSelectedOption] = useState<'predefined' | 'custom'>('predefined');
  const [predefinedTime, setPredefinedTime] = useState<string>('30');
  const [customTime, setCustomTime] = useState<string>(
    format(addHours(now, 1), 'HH:mm')
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate time options for the rest of today
  const generateTimeOptions = () => {
    const options = [];
    const nowPlus5Minutes = addMinutes(now, 5);
    
    // Predefined quick options
    options.push({ value: '5', label: 'In 5 minutes', time: addMinutes(now, 5) });
    options.push({ value: '15', label: 'In 15 minutes', time: addMinutes(now, 15) });
    options.push({ value: '30', label: 'In 30 minutes', time: addMinutes(now, 30) });
    options.push({ value: '60', label: 'In 1 hour', time: addHours(now, 1) });
    options.push({ value: '120', label: 'In 2 hours', time: addHours(now, 2) });
    options.push({ value: '240', label: 'In 4 hours', time: addHours(now, 4) });
    
    // Filter out options that go past today
    const todayEnd = endOfDay(now);
    return options.filter(opt => isAfter(todayEnd, opt.time) && isAfter(opt.time, nowPlus5Minutes));
  };

  const timeOptions = generateTimeOptions();

  const handleSubmit = async () => {
    setError(null);
    setIsSubmitting(true);

    try {
      let scheduledTime: Date;

      if (selectedOption === 'predefined') {
        const selectedMinutes = parseInt(predefinedTime);
        scheduledTime = addMinutes(now, selectedMinutes);
      } else {
        const [hours, minutes] = customTime.split(':').map(Number);
        scheduledTime = new Date(now);
        scheduledTime.setHours(hours, minutes, 0, 0);
      }

      // Validate the scheduled time
      const minTime = addMinutes(now, 5);
      const maxTime = endOfDay(now);

      if (!isAfter(scheduledTime, minTime)) {
        throw new Error('Scheduled time must be at least 5 minutes from now');
      }

      if (!isAfter(maxTime, scheduledTime)) {
        throw new Error('Scheduled time must be within today');
      }

      await onSchedule(scheduledTime);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to schedule run');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getMinCustomTime = () => {
    const minTime = addMinutes(now, 5);
    return format(minTime, 'HH:mm');
  };

  const getMaxCustomTime = () => {
    return '23:59';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Schedule Run</h2>
            <p className="text-sm text-gray-600 mt-1">
              {schedule.name || schedule.workflows?.name || 'Workflow'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* Info Alert */}
          <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-start">
            <AlertCircle className="h-5 w-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Schedule a one-time run today</p>
              <p>This will execute the workflow once at the specified time. Regular schedule will continue as configured.</p>
            </div>
          </div>

          {/* Time Selection */}
          <div className="space-y-4">
            {/* Option 1: Quick Select */}
            <div>
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={selectedOption === 'predefined'}
                  onChange={() => setSelectedOption('predefined')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-900">Quick select</span>
              </label>
              {selectedOption === 'predefined' && timeOptions.length > 0 && (
                <div className="mt-3 ml-6">
                  <select
                    value={predefinedTime}
                    onChange={(e) => setPredefinedTime(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {timeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label} ({format(option.time, 'h:mm a')})
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {selectedOption === 'predefined' && timeOptions.length === 0 && (
                <div className="mt-3 ml-6 text-sm text-gray-500">
                  No quick options available for today. Use custom time instead.
                </div>
              )}
            </div>

            {/* Option 2: Custom Time */}
            <div>
              <label className="flex items-center">
                <input
                  type="radio"
                  checked={selectedOption === 'custom'}
                  onChange={() => setSelectedOption('custom')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-900">Specific time today</span>
              </label>
              {selectedOption === 'custom' && (
                <div className="mt-3 ml-6">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-gray-400" />
                    <input
                      type="time"
                      value={customTime}
                      onChange={(e) => setCustomTime(e.target.value)}
                      min={getMinCustomTime()}
                      max={getMaxCustomTime()}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    Must be between {getMinCustomTime()} and 23:59 today
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Preview */}
          <div className="mt-6 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center text-sm">
              <Calendar className="h-4 w-4 text-gray-500 mr-2" />
              <span className="text-gray-700">
                Will run on: {format(now, 'MMMM d, yyyy')} at{' '}
                {(() => {
                  if (selectedOption === 'predefined' && timeOptions.length > 0) {
                    const option = timeOptions.find(o => o.value === predefinedTime);
                    return option ? format(option.time, 'h:mm a') : '--:--';
                  } else if (selectedOption === 'custom') {
                    const [hours, minutes] = customTime.split(':').map(Number);
                    const time = new Date(now);
                    time.setHours(hours, minutes, 0, 0);
                    return format(time, 'h:mm a');
                  }
                  return '--:--';
                })()}
              </span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (selectedOption === 'predefined' && timeOptions.length === 0)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? 'Scheduling...' : 'Schedule Run'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScheduleRunModal;