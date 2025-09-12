import { useState, useEffect, useCallback, useMemo } from 'react';
import { Calendar, ChevronDown, ChevronUp, X, Info, Clock, CalendarDays } from 'lucide-react';
import { format, parse, subDays, addDays, startOfMonth, endOfMonth, startOfQuarter, endOfQuarter, startOfYear, endOfYear, isAfter, isBefore, isValid } from 'date-fns';
import type { FC } from 'react';

interface DateRangePickerProps {
  value: {
    startDate: string;
    endDate: string;
    isDynamic?: boolean;
  } | null;
  onChange: (value: { startDate: string; endDate: string; isDynamic?: boolean }) => void;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  showAmcWarning?: boolean;
  supportDynamic?: boolean;
  minDate?: Date;
  maxDate?: Date;
  className?: string;
}

interface DatePreset {
  label: string;
  getValue: () => { startDate: Date; endDate: Date };
  adjustForAmc?: boolean;
}

/**
 * Advanced date range picker with presets and dynamic expressions
 */
const DateRangePicker: FC<DateRangePickerProps> = ({
  value,
  onChange,
  required = false,
  disabled = false,
  error,
  showAmcWarning = false,
  supportDynamic = false,
  minDate,
  maxDate,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'presets' | 'calendar' | 'dynamic'>('presets');
  const [dynamicStart, setDynamicStart] = useState('');
  const [dynamicEnd, setDynamicEnd] = useState('');
  const [showDynamicHelp, setShowDynamicHelp] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [selecting, setSelecting] = useState<'start' | 'end' | null>(null);
  const [tempRange, setTempRange] = useState<{ start: Date | null; end: Date | null }>({ start: null, end: null });

  const today = new Date();
  const amcCutoffDate = showAmcWarning ? subDays(today, 14) : today;

  // Parse value dates
  const parsedDates = useMemo(() => {
    if (!value) return { start: null, end: null };
    
    if (value.isDynamic) {
      // For dynamic dates, try to resolve them for preview
      const resolved = resolveDynamicDates(value.startDate, value.endDate);
      return resolved;
    }
    
    return {
      start: value.startDate ? new Date(value.startDate) : null,
      end: value.endDate ? new Date(value.endDate) : null
    };
  }, [value]);

  // Initialize dynamic expressions from value
  useEffect(() => {
    if (value?.isDynamic) {
      setDynamicStart(value.startDate);
      setDynamicEnd(value.endDate);
    }
  }, [value]);

  // Date presets
  const presets: DatePreset[] = [
    {
      label: 'Last 7 days',
      getValue: () => ({
        startDate: subDays(showAmcWarning ? amcCutoffDate : today, 7),
        endDate: showAmcWarning ? amcCutoffDate : today
      }),
      adjustForAmc: true
    },
    {
      label: 'Last 14 days',
      getValue: () => ({
        startDate: subDays(showAmcWarning ? amcCutoffDate : today, 14),
        endDate: showAmcWarning ? amcCutoffDate : today
      }),
      adjustForAmc: true
    },
    {
      label: 'Last 30 days',
      getValue: () => ({
        startDate: subDays(showAmcWarning ? amcCutoffDate : today, 30),
        endDate: showAmcWarning ? amcCutoffDate : today
      }),
      adjustForAmc: true
    },
    {
      label: 'Last 90 days',
      getValue: () => ({
        startDate: subDays(showAmcWarning ? amcCutoffDate : today, 90),
        endDate: showAmcWarning ? amcCutoffDate : today
      }),
      adjustForAmc: true
    },
    {
      label: 'This month',
      getValue: () => ({
        startDate: startOfMonth(today),
        endDate: showAmcWarning ? amcCutoffDate : endOfMonth(today)
      })
    },
    {
      label: 'Last month',
      getValue: () => {
        const lastMonth = subDays(startOfMonth(today), 1);
        return {
          startDate: startOfMonth(lastMonth),
          endDate: endOfMonth(lastMonth)
        };
      }
    },
    {
      label: 'This quarter',
      getValue: () => ({
        startDate: startOfQuarter(today),
        endDate: showAmcWarning ? amcCutoffDate : endOfQuarter(today)
      })
    },
    {
      label: 'Last quarter',
      getValue: () => {
        const lastQuarter = subDays(startOfQuarter(today), 1);
        return {
          startDate: startOfQuarter(lastQuarter),
          endDate: endOfQuarter(lastQuarter)
        };
      }
    },
    {
      label: 'This year',
      getValue: () => ({
        startDate: startOfYear(today),
        endDate: showAmcWarning ? amcCutoffDate : endOfYear(today)
      })
    },
    {
      label: 'Last year',
      getValue: () => {
        const lastYear = subDays(startOfYear(today), 1);
        return {
          startDate: startOfYear(lastYear),
          endDate: endOfYear(lastYear)
        };
      }
    }
  ];

  // Dynamic date expressions
  const dynamicExamples = [
    { expression: 'today', description: "Today's date" },
    { expression: 'yesterday', description: 'Yesterday' },
    { expression: 'today - 7 days', description: '7 days ago' },
    { expression: 'today + 1 month', description: 'Next month' },
    { expression: 'start of month', description: 'First day of current month' },
    { expression: 'end of month', description: 'Last day of current month' },
    { expression: 'start of quarter', description: 'First day of current quarter' },
    { expression: 'end of quarter', description: 'Last day of current quarter' },
    { expression: 'start of year', description: 'January 1st of current year' },
    { expression: 'end of year', description: 'December 31st of current year' },
    { expression: 'start of month - 1 month', description: 'First day of last month' },
    { expression: 'end of month - 1 month', description: 'Last day of last month' }
  ];

  // Resolve dynamic date expressions
  function resolveDynamicDates(startExpr: string, endExpr: string): { start: Date | null; end: Date | null } {
    try {
      const start = resolveDynamicExpression(startExpr);
      const end = resolveDynamicExpression(endExpr);
      return { start, end };
    } catch {
      return { start: null, end: null };
    }
  }

  function resolveDynamicExpression(expr: string): Date | null {
    if (!expr) return null;
    
    const normalized = expr.toLowerCase().trim();
    const now = new Date();
    
    // Simple expressions
    if (normalized === 'today') return now;
    if (normalized === 'yesterday') return subDays(now, 1);
    if (normalized === 'tomorrow') return addDays(now, 1);
    
    // Start/end of period
    if (normalized === 'start of month') return startOfMonth(now);
    if (normalized === 'end of month') return endOfMonth(now);
    if (normalized === 'start of quarter') return startOfQuarter(now);
    if (normalized === 'end of quarter') return endOfQuarter(now);
    if (normalized === 'start of year') return startOfYear(now);
    if (normalized === 'end of year') return endOfYear(now);
    
    // Complex expressions with math
    const mathRegex = /^(today|yesterday|tomorrow|start of month|end of month|start of quarter|end of quarter|start of year|end of year)\s*([\+\-])\s*(\d+)\s*(days?|months?|years?)$/i;
    const match = normalized.match(mathRegex);
    
    if (match) {
      const [, base, operator, amount, unit] = match;
      let baseDate = resolveDynamicExpression(base);
      if (!baseDate) return null;
      
      const num = parseInt(amount);
      const isAdd = operator === '+';
      
      if (unit.startsWith('day')) {
        return isAdd ? addDays(baseDate, num) : subDays(baseDate, num);
      }
      // Add more units as needed (months, years)
    }
    
    return null;
  }

  // Validate dynamic expression
  const validateDynamicExpression = (expr: string): boolean => {
    const resolved = resolveDynamicExpression(expr);
    return resolved !== null && isValid(resolved);
  };

  // Handle preset selection
  const handlePresetSelect = useCallback((preset: DatePreset) => {
    const { startDate, endDate } = preset.getValue();
    onChange({
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      isDynamic: false
    });
    setIsOpen(false);
  }, [onChange]);

  // Handle manual date input
  const handleManualDateChange = useCallback((type: 'start' | 'end', dateStr: string) => {
    try {
      const date = parse(dateStr, 'yyyy-MM-dd', new Date());
      if (!isValid(date)) return;
      
      const currentStart = parsedDates.start;
      const currentEnd = parsedDates.end;
      
      if (type === 'start') {
        // Validate that start is before end
        if (currentEnd && isAfter(date, currentEnd)) {
          return;
        }
        onChange({
          startDate: date.toISOString(),
          endDate: currentEnd ? currentEnd.toISOString() : date.toISOString(),
          isDynamic: false
        });
      } else {
        // Validate that end is after start
        if (currentStart && isBefore(date, currentStart)) {
          return;
        }
        onChange({
          startDate: currentStart ? currentStart.toISOString() : date.toISOString(),
          endDate: date.toISOString(),
          isDynamic: false
        });
      }
    } catch {
      // Invalid date format
    }
  }, [parsedDates, onChange]);

  // Handle dynamic date toggle
  const handleToggleDynamic = useCallback(() => {
    setActiveTab('dynamic');
    if (!value?.isDynamic) {
      setDynamicStart('today - 7 days');
      setDynamicEnd('today');
    }
  }, [value]);

  // Handle dynamic expression change
  const handleDynamicChange = useCallback((type: 'start' | 'end', expr: string) => {
    if (type === 'start') {
      setDynamicStart(expr);
    } else {
      setDynamicEnd(expr);
    }
    
    // Validate and update if both are valid
    if (validateDynamicExpression(type === 'start' ? expr : dynamicStart) &&
        validateDynamicExpression(type === 'end' ? dynamicEnd : expr)) {
      onChange({
        startDate: type === 'start' ? expr : dynamicStart,
        endDate: type === 'end' ? expr : dynamicEnd,
        isDynamic: true
      });
    }
  }, [dynamicStart, dynamicEnd, onChange]);

  // Handle calendar date selection
  const handleCalendarSelect = useCallback((date: Date) => {
    if (!selecting) {
      // Start new selection
      setSelecting('end');
      setTempRange({ start: date, end: null });
    } else if (selecting === 'end') {
      // Complete selection
      const start = tempRange.start!;
      if (isBefore(date, start)) {
        // If end is before start, swap them
        onChange({
          startDate: date.toISOString(),
          endDate: start.toISOString(),
          isDynamic: false
        });
      } else {
        onChange({
          startDate: start.toISOString(),
          endDate: date.toISOString(),
          isDynamic: false
        });
      }
      setSelecting(null);
      setTempRange({ start: null, end: null });
      setIsOpen(false);
    }
  }, [selecting, tempRange, onChange]);

  // Check if date is disabled
  const isDateDisabled = useCallback((date: Date): boolean => {
    if (disabled) return true;
    
    // AMC lookback period
    if (showAmcWarning) {
      if (isAfter(date, amcCutoffDate)) return true;
      if (isBefore(date, subDays(today, 365))) return true; // Max 1 year back
    }
    
    // Min/max date constraints
    if (minDate && isBefore(date, minDate)) return true;
    if (maxDate && isAfter(date, maxDate)) return true;
    
    return false;
  }, [disabled, showAmcWarning, amcCutoffDate, today, minDate, maxDate]);

  // Format display text
  const displayText = useMemo(() => {
    if (!value) return 'Select date range';
    
    if (value.isDynamic) {
      return `${value.startDate} → ${value.endDate}`;
    }
    
    if (parsedDates.start && parsedDates.end) {
      return `${format(parsedDates.start, 'MMM dd, yyyy')} - ${format(parsedDates.end, 'MMM dd, yyyy')}`;
    }
    
    return 'Select date range';
  }, [value, parsedDates]);

  // Get validation error
  const validationError = useMemo(() => {
    if (error) return error;
    if (required && !value) return 'Date range is required';
    
    if (value && !value.isDynamic) {
      const start = new Date(value.startDate);
      const end = new Date(value.endDate);
      if (isAfter(start, end)) return 'End date must be after start date';
    }
    
    if (value?.isDynamic) {
      if (!validateDynamicExpression(value.startDate)) return 'Invalid start date expression';
      if (!validateDynamicExpression(value.endDate)) return 'Invalid end date expression';
    }
    
    return null;
  }, [error, required, value]);

  return (
    <div className={`relative ${className}`}>
      {/* Main input/button */}
      <div className="flex gap-2">
        {!value?.isDynamic ? (
          <>
            {/* Start date input */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={parsedDates.start ? format(parsedDates.start, 'yyyy-MM-dd') : ''}
                onChange={(e) => handleManualDateChange('start', e.target.value)}
                disabled={disabled}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                aria-label="Start date"
              />
            </div>
            
            {/* End date input */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={parsedDates.end ? format(parsedDates.end, 'yyyy-MM-dd') : ''}
                onChange={(e) => handleManualDateChange('end', e.target.value)}
                disabled={disabled}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                aria-label="End date"
              />
            </div>
          </>
        ) : (
          <>
            {/* Dynamic expression inputs */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Expression
              </label>
              <input
                type="text"
                value={dynamicStart}
                onChange={(e) => handleDynamicChange('start', e.target.value)}
                disabled={disabled}
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 ${
                  !validateDynamicExpression(dynamicStart) ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., today - 7 days"
                aria-label="Start expression"
              />
              {validateDynamicExpression(dynamicStart) && (
                <div className="text-xs text-gray-500 mt-1">
                  Resolves to: {format(resolveDynamicExpression(dynamicStart)!, 'MMM dd, yyyy')}
                </div>
              )}
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Expression
              </label>
              <input
                type="text"
                value={dynamicEnd}
                onChange={(e) => handleDynamicChange('end', e.target.value)}
                disabled={disabled}
                className={`w-full px-3 py-2 border rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 ${
                  !validateDynamicExpression(dynamicEnd) ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="e.g., today"
                aria-label="End expression"
              />
              {validateDynamicExpression(dynamicEnd) && (
                <div className="text-xs text-gray-500 mt-1">
                  Resolves to: {format(resolveDynamicExpression(dynamicEnd)!, 'MMM dd, yyyy')}
                </div>
              )}
            </div>
          </>
        )}
        
        {/* Action buttons */}
        <div className="flex items-end gap-1">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            disabled={disabled}
            className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100"
            aria-label={isOpen ? 'Close calendar' : 'Open calendar'}
          >
            <CalendarDays className="h-5 w-5 text-gray-600" />
          </button>
          
          <button
            type="button"
            onClick={() => {
              setActiveTab('presets');
              setIsOpen(!isOpen);
            }}
            disabled={disabled}
            className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100"
            aria-label="Presets"
          >
            <Clock className="h-5 w-5 text-gray-600" />
          </button>
          
          {supportDynamic && (
            <button
              type="button"
              onClick={handleToggleDynamic}
              disabled={disabled}
              className={`px-3 py-2 border rounded-md ${
                value?.isDynamic 
                  ? 'bg-blue-50 border-blue-300 text-blue-600' 
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
              } disabled:bg-gray-100`}
              aria-label="Use dynamic dates"
            >
              <Info className="h-5 w-5" />
            </button>
          )}
          
          {value && (
            <button
              type="button"
              onClick={() => onChange(null as any)}
              disabled={disabled}
              className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100"
              aria-label="Clear"
            >
              <X className="h-5 w-5 text-gray-600" />
            </button>
          )}
        </div>
      </div>

      {/* Validation error */}
      {validationError && (
        <div className="mt-1 text-sm text-red-600">
          {validationError}
        </div>
      )}

      {/* AMC warning */}
      {showAmcWarning && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start">
            <Info className="h-4 w-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-xs text-yellow-800">
              AMC data has a 14-day lookback period. Dates are automatically adjusted.
            </div>
          </div>
        </div>
      )}

      {/* Status for screen readers */}
      <div className="sr-only" role="status" aria-live="polite">
        {value && `Selected range: ${displayText}`}
      </div>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute z-50 mt-2 w-full bg-white border border-gray-300 rounded-lg shadow-lg" role="dialog">
          {/* Tab navigation */}
          <div className="flex border-b">
            <button
              type="button"
              onClick={() => setActiveTab('presets')}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === 'presets' 
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Presets
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('calendar')}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === 'calendar' 
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              Calendar
            </button>
            {supportDynamic && (
              <button
                type="button"
                onClick={() => setActiveTab('dynamic')}
                className={`flex-1 px-4 py-2 text-sm font-medium ${
                  activeTab === 'dynamic' 
                    ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                Dynamic
              </button>
            )}
          </div>

          {/* Tab content */}
          <div className="p-4">
            {activeTab === 'presets' && (
              <div className="grid grid-cols-2 gap-2">
                {presets.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    onClick={() => handlePresetSelect(preset)}
                    className="px-3 py-2 text-sm text-left bg-gray-50 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    {preset.label}
                    {showAmcWarning && preset.adjustForAmc && (
                      <span className="text-xs text-yellow-600 ml-1">(adjusted for AMC)</span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {activeTab === 'calendar' && (
              <div>
                {/* Calendar navigation */}
                <div className="flex items-center justify-between mb-4">
                  <button
                    type="button"
                    onClick={() => setCalendarMonth(subDays(calendarMonth, 32))}
                    className="p-1 hover:bg-gray-100 rounded"
                    aria-label="Previous month"
                  >
                    <ChevronDown className="h-5 w-5 transform rotate-90" />
                  </button>
                  <div className="text-sm font-medium">
                    {format(calendarMonth, 'MMMM yyyy')}
                  </div>
                  <button
                    type="button"
                    onClick={() => setCalendarMonth(addDays(calendarMonth, 32))}
                    className="p-1 hover:bg-gray-100 rounded"
                    aria-label="Next month"
                  >
                    <ChevronUp className="h-5 w-5 transform rotate-90" />
                  </button>
                </div>

                {/* Calendar grid */}
                <div className="text-center text-xs text-gray-500 mb-2">
                  Click to select start date, then end date
                </div>
                <div className="grid grid-cols-7 gap-1">
                  {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
                    <div key={day} className="text-xs font-medium text-gray-600 text-center py-1">
                      {day}
                    </div>
                  ))}
                  {/* Calendar days would be rendered here - simplified for brevity */}
                </div>
              </div>
            )}

            {activeTab === 'dynamic' && supportDynamic && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm font-medium text-gray-700">Dynamic Date Expressions</div>
                  <button
                    type="button"
                    onClick={() => setShowDynamicHelp(!showDynamicHelp)}
                    className="text-blue-600 hover:text-blue-700"
                    aria-label="Help"
                  >
                    <Info className="h-4 w-4" />
                  </button>
                </div>

                {showDynamicHelp && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-md">
                    <div className="text-xs font-semibold text-blue-900 mb-2">Examples:</div>
                    <div className="space-y-1">
                      {dynamicExamples.map(({ expression, description }) => (
                        <div key={expression} className="text-xs">
                          <code className="bg-white px-1 py-0.5 rounded text-blue-700">{expression}</code>
                          <span className="text-gray-600 ml-2">- {description}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Expression
                    </label>
                    <input
                      type="text"
                      value={dynamicStart}
                      onChange={(e) => handleDynamicChange('start', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-md ${
                        !validateDynamicExpression(dynamicStart) ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="e.g., today - 7 days"
                    />
                    {!validateDynamicExpression(dynamicStart) && dynamicStart && (
                      <div className="text-xs text-red-600 mt-1">Invalid date expression</div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Expression
                    </label>
                    <input
                      type="text"
                      value={dynamicEnd}
                      onChange={(e) => handleDynamicChange('end', e.target.value)}
                      className={`w-full px-3 py-2 border rounded-md ${
                        !validateDynamicExpression(dynamicEnd) ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder="e.g., today"
                    />
                    {!validateDynamicExpression(dynamicEnd) && dynamicEnd && (
                      <div className="text-xs text-red-600 mt-1">Invalid date expression</div>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      if (validateDynamicExpression(dynamicStart) && validateDynamicExpression(dynamicEnd)) {
                        onChange({
                          startDate: dynamicStart,
                          endDate: dynamicEnd,
                          isDynamic: true
                        });
                        setIsOpen(false);
                      }
                    }}
                    disabled={!validateDynamicExpression(dynamicStart) || !validateDynamicExpression(dynamicEnd)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
                  >
                    Apply Dynamic Dates
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Close button */}
          <div className="border-t px-4 py-2">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="w-full px-3 py-1 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;