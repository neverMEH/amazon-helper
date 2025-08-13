import { useState, useEffect } from 'react';
import { Calendar } from 'lucide-react';

interface DateRangeSelectorProps {
  value?: {
    startDate: string;
    endDate: string;
    preset?: string;
  };
  onChange: (dateRange: { startDate: string; endDate: string; preset?: string }) => void;
  className?: string;
}

export default function DateRangeSelector({ value, onChange, className = '' }: DateRangeSelectorProps) {
  const [preset, setPreset] = useState(value?.preset || '30');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [isCustom, setIsCustom] = useState(false);

  // Calculate dates based on preset
  const calculateDateRange = (days: string) => {
    const endDate = new Date();
    const startDate = new Date();
    
    if (days === 'custom') {
      return {
        startDate: customStartDate,
        endDate: customEndDate,
        preset: 'custom'
      };
    }
    
    const daysNum = parseInt(days);
    startDate.setDate(startDate.getDate() - daysNum);
    
    return {
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
      preset: days
    };
  };

  // Update parent when preset changes
  useEffect(() => {
    if (preset !== 'custom') {
      const range = calculateDateRange(preset);
      onChange(range);
    }
  }, [preset]);

  // Update parent when custom dates change
  useEffect(() => {
    if (isCustom && customStartDate && customEndDate) {
      onChange({
        startDate: customStartDate,
        endDate: customEndDate,
        preset: 'custom'
      });
    }
  }, [customStartDate, customEndDate, isCustom]);

  const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setPreset(value);
    setIsCustom(value === 'custom');
  };

  const presetOptions = [
    { value: '7', label: 'Last 7 days' },
    { value: '14', label: 'Last 14 days' },
    { value: '30', label: 'Last 30 days' },
    { value: '60', label: 'Last 60 days' },
    { value: '90', label: 'Last 90 days' },
    { value: '180', label: 'Last 180 days' },
    { value: 'custom', label: 'Custom range' }
  ];

  return (
    <div className={`space-y-3 ${className}`}>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          <Calendar className="inline h-4 w-4 mr-1" />
          Date Range
        </label>
        <select
          value={preset}
          onChange={handlePresetChange}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
        >
          {presetOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {isCustom && (
        <div className="grid grid-cols-2 gap-3 p-3 bg-gray-50 rounded-md">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
              max={customEndDate || new Date().toISOString().split('T')[0]}
              className="block w-full px-2 py-1 text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              required={isCustom}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
              min={customStartDate}
              max={new Date().toISOString().split('T')[0]}
              className="block w-full px-2 py-1 text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              required={isCustom}
            />
          </div>
        </div>
      )}

      {/* Display selected range */}
      {value && (
        <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
          <strong>Selected range:</strong> {value.startDate} to {value.endDate}
        </div>
      )}
    </div>
  );
}