import { useState, useEffect } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';

interface ParameterEditorProps {
  parameters: Record<string, any>;
  onChange: (parameters: Record<string, any>) => void;
  schema?: Record<string, any>;
}

interface DateRange {
  label: string;
  value: number;
  unit: 'days' | 'months' | 'year';
}

const PRESET_RANGES: DateRange[] = [
  { label: 'Last 7 days', value: 7, unit: 'days' },
  { label: 'Last 14 days', value: 14, unit: 'days' },
  { label: 'Last 30 days', value: 30, unit: 'days' },
  { label: 'Last 60 days', value: 60, unit: 'days' },
  { label: 'Last 90 days', value: 90, unit: 'days' },
  { label: 'Last 180 days', value: 180, unit: 'days' },
  { label: 'Last 365 days', value: 365, unit: 'days' },
  { label: 'Month to date', value: 0, unit: 'months' },
  { label: 'Year to date', value: 0, unit: 'year' },
  { label: 'Custom range', value: -1, unit: 'days' },
];

export default function ParameterEditor({ parameters, onChange, schema }: ParameterEditorProps) {
  const [selectedRange, setSelectedRange] = useState<string>('custom');
  const [showPresets, setShowPresets] = useState(false);
  const [localParams, setLocalParams] = useState(parameters);

  // Detect common date parameters
  const hasDateParams = 'start_date' in parameters || 'end_date' in parameters;

  useEffect(() => {
    setLocalParams(parameters);
  }, [parameters]);

  const formatDate = (date: Date): string => {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const calculateDateRange = (range: DateRange): { start: string; end: string; lookback?: number } => {
    const end = new Date();
    let start = new Date();

    switch (range.unit) {
      case 'days':
        if (range.value > 0) {
          start.setDate(end.getDate() - range.value + 1);
        }
        break;
      case 'months':
        // Month to date
        start = new Date(end.getFullYear(), end.getMonth(), 1);
        break;
      case 'year':
        // Year to date
        start = new Date(end.getFullYear(), 0, 1);
        break;
    }

    return {
      start: formatDate(start),
      end: formatDate(end),
      lookback: range.value > 0 ? range.value : undefined
    };
  };

  const handlePresetSelect = (range: DateRange) => {
    if (range.value === -1) {
      // Custom range selected
      setSelectedRange('custom');
      setShowPresets(false);
      return;
    }

    setSelectedRange(range.label);
    const { start, end, lookback } = calculateDateRange(range);
    
    const newParams = { ...localParams };
    
    if ('start_date' in parameters) {
      newParams.start_date = start;
    }
    if ('end_date' in parameters) {
      newParams.end_date = end;
    }
    if ('lookback_days' in parameters && lookback) {
      newParams.lookback_days = lookback;
    }

    setLocalParams(newParams);
    onChange(newParams);
    setShowPresets(false);
  };

  const handleInputChange = (key: string, value: any) => {
    const newParams = { ...localParams, [key]: value };
    setLocalParams(newParams);
    onChange(newParams);
    setSelectedRange('custom');
  };

  const renderParameterInput = (key: string, value: any) => {
    const paramSchema = schema?.properties?.[key];
    const paramType = paramSchema?.type || typeof value;

    // Date parameters
    if (key === 'start_date' || key === 'end_date' || paramSchema?.format === 'date') {
      return (
        <input
          type="date"
          value={value || ''}
          onChange={(e) => handleInputChange(key, e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
      );
    }

    // Number parameters
    if (paramType === 'number' || paramType === 'integer') {
      return (
        <input
          type="number"
          value={value || 0}
          onChange={(e) => handleInputChange(key, parseInt(e.target.value, 10))}
          min={paramSchema?.minimum}
          max={paramSchema?.maximum}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
      );
    }

    // Array parameters
    if (Array.isArray(value)) {
      return (
        <input
          type="text"
          value={value.join(', ')}
          onChange={(e) => handleInputChange(key, e.target.value.split(',').map(s => s.trim()))}
          placeholder="Enter comma-separated values"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
      );
    }

    // Default to text input
    return (
      <input
        type="text"
        value={value || ''}
        onChange={(e) => handleInputChange(key, e.target.value)}
        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
      />
    );
  };

  return (
    <div className="space-y-4">
      {/* Date Range Presets */}
      {hasDateParams && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowPresets(!showPresets)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Calendar className="h-4 w-4 mr-2" />
            {selectedRange === 'custom' ? 'Select date range' : selectedRange}
            <ChevronDown className="h-4 w-4 ml-2" />
          </button>

          {showPresets && (
            <div className="absolute z-10 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5">
              <div className="py-1" role="menu">
                {PRESET_RANGES.map((range) => (
                  <button
                    key={range.label}
                    onClick={() => handlePresetSelect(range)}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    role="menuitem"
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Parameter Fields */}
      <div className="space-y-4">
        {Object.entries(localParams).map(([key, value]) => (
          <div key={key}>
            <label htmlFor={key} className="block text-sm font-medium text-gray-700">
              {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
              {schema?.required?.includes(key) && <span className="text-red-500 ml-1">*</span>}
            </label>
            {renderParameterInput(key, value)}
            {schema?.properties?.[key]?.description && (
              <p className="mt-1 text-sm text-gray-500">{schema.properties[key].description}</p>
            )}
          </div>
        ))}
      </div>

      {/* Add Parameter Button (if schema allows additional properties) */}
      {(!schema || schema.additionalProperties !== false) && (
        <button
          type="button"
          onClick={() => {
            const newKey = prompt('Enter parameter name:');
            if (newKey && !(newKey in localParams)) {
              handleInputChange(newKey, '');
            }
          }}
          className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          + Add Parameter
        </button>
      )}
    </div>
  );
}