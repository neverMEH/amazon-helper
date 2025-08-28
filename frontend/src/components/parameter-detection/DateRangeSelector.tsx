import { useState, useEffect, useCallback } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { format, subDays } from 'date-fns';
import type { FC } from 'react';

interface DateRangeSelectorProps {
  value: any;
  onChange: (value: any) => void;
  parameterName: string;
  className?: string;
}

type DatePreset = {
  label: string;
  getValue: () => { start: Date; end: Date };
};

/**
 * Component for selecting date ranges with presets
 */
export const DateRangeSelector: FC<DateRangeSelectorProps> = ({
  value,
  onChange,
  parameterName,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('custom');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Date presets
  const presets: DatePreset[] = [
    {
      label: 'Last 7 days',
      getValue: () => ({
        start: subDays(new Date(), 7),
        end: new Date()
      })
    },
    {
      label: 'Last 14 days',
      getValue: () => ({
        start: subDays(new Date(), 14),
        end: new Date()
      })
    },
    {
      label: 'Last 30 days',
      getValue: () => ({
        start: subDays(new Date(), 30),
        end: new Date()
      })
    }
  ];

  // Initialize dates from value prop
  useEffect(() => {
    if (value) {
      if (typeof value === 'object' && value.start && value.end) {
        setStartDate(formatDateForInput(value.start));
        setEndDate(formatDateForInput(value.end));
      } else if (typeof value === 'string') {
        // Single date value - use for both start and end
        setStartDate(formatDateForInput(value));
        setEndDate(formatDateForInput(value));
      }
    }
  }, [value]);

  // Format date for HTML input
  const formatDateForInput = (date: Date | string): string => {
    if (!date) return '';
    const d = typeof date === 'string' ? new Date(date) : date;
    return format(d, 'yyyy-MM-dd');
  };

  // Format date for AMC (no timezone)
  const formatDateForAMC = (date: Date | string): string => {
    if (!date) return '';
    const d = typeof date === 'string' ? new Date(date) : date;
    return format(d, "yyyy-MM-dd'T'HH:mm:ss");
  };

  // Handle preset selection
  const handlePresetSelect = useCallback((preset: DatePreset, presetLabel: string) => {
    const { start, end } = preset.getValue();
    
    setSelectedPreset(presetLabel);
    setStartDate(formatDateForInput(start));
    setEndDate(formatDateForInput(end));
    
    // Update the value based on parameter name
    if (parameterName.toLowerCase().includes('start')) {
      onChange(formatDateForAMC(start));
    } else if (parameterName.toLowerCase().includes('end')) {
      onChange(formatDateForAMC(end));
    } else {
      // For generic date parameters, return an object with both
      onChange({
        start: formatDateForAMC(start),
        end: formatDateForAMC(end)
      });
    }
    
    setIsOpen(false);
  }, [parameterName, onChange]);

  // Handle custom date change
  const handleDateChange = useCallback((type: 'start' | 'end', dateStr: string) => {
    if (type === 'start') {
      setStartDate(dateStr);
    } else {
      setEndDate(dateStr);
    }
    
    setSelectedPreset('custom');
    
    // Update value when both dates are set
    if (type === 'start' && endDate) {
      updateValue(dateStr, endDate);
    } else if (type === 'end' && startDate) {
      updateValue(startDate, dateStr);
    }
  }, [startDate, endDate]);

  // Update the value prop
  const updateValue = useCallback((start: string, end: string) => {
    if (!start || !end) return;
    
    const startDateTime = formatDateForAMC(new Date(start));
    const endDateTime = formatDateForAMC(new Date(end));
    
    // Update based on parameter name
    if (parameterName.toLowerCase().includes('start')) {
      onChange(startDateTime);
    } else if (parameterName.toLowerCase().includes('end')) {
      onChange(endDateTime);
    } else {
      onChange({
        start: startDateTime,
        end: endDateTime
      });
    }
  }, [parameterName, onChange]);

  // Get display text
  const getDisplayText = (): string => {
    if (selectedPreset !== 'custom') {
      const preset = presets.find(p => p.label === selectedPreset);
      if (preset) return preset.label;
    }
    
    if (startDate && endDate) {
      return `${startDate} to ${endDate}`;
    }
    
    return 'Select date range...';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 hover:bg-gray-50"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Calendar className="h-4 w-4 text-gray-400 mr-2" />
            <span className={startDate && endDate ? 'text-gray-900' : 'text-gray-500'}>
              {getDisplayText()}
            </span>
          </div>
          <ChevronDown className="h-4 w-4 text-gray-400" />
        </div>
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg p-3">
          {/* Presets */}
          <div className="mb-3">
            <div className="text-xs font-medium text-gray-700 mb-2">Quick select:</div>
            <div className="space-y-1">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => handlePresetSelect(preset, preset.label)}
                  className={`w-full px-3 py-2 text-sm text-left rounded-md transition-colors ${
                    selectedPreset === preset.label
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom date inputs */}
          <div className="border-t pt-3">
            <div className="text-xs font-medium text-gray-700 mb-2">Custom range:</div>
            <div className="space-y-2">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Start date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  max={endDate || undefined}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">End date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  min={startDate || undefined}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Apply button */}
          <div className="mt-3 pt-3 border-t">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              disabled={!startDate || !endDate}
              className="w-full px-3 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  );
};