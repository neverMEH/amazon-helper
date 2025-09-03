import React, { useState, useEffect } from 'react';
import { Package, ChevronDown, Search } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const ASINListParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<string[]>(value || []);
  const [showInput, setShowInput] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalValue(value || []);
  }, [value]);

  const validateSelection = (selection: string[]): boolean => {
    if (parameter.required && (!selection || selection.length === 0)) {
      setError('At least one ASIN must be provided');
      onError?.('At least one ASIN must be provided');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check min items
    if (rules.min_items && selection.length < rules.min_items) {
      const error = `At least ${rules.min_items} ASINs must be provided`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check max items
    if (rules.max_items && selection.length > rules.max_items) {
      const error = `No more than ${rules.max_items} ASINs can be provided`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Validate ASIN format (10 characters, alphanumeric)
    const invalidAsins = selection.filter(asin => !/^[A-Z0-9]{10}$/.test(asin.toUpperCase()));
    if (invalidAsins.length > 0) {
      const error = `Invalid ASIN format: ${invalidAsins.join(', ')}. ASINs must be 10 alphanumeric characters.`;
      setError(error);
      onError?.(error);
      return false;
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleAddAsins = () => {
    if (!inputValue.trim()) return;

    // Parse ASINs from input (comma, space, or newline separated)
    const newAsins = inputValue
      .split(/[,\s\n]+/)
      .map(asin => asin.trim().toUpperCase())
      .filter(asin => asin.length > 0)
      .filter(asin => !localValue.includes(asin)); // Remove duplicates

    const updatedSelection = [...localValue, ...newAsins];
    setLocalValue(updatedSelection);
    
    if (validateSelection(updatedSelection)) {
      onChange(updatedSelection);
    }
    
    setInputValue('');
    setShowInput(false);
  };

  const handleRemoveAsin = (asin: string) => {
    if (disabled) return;
    
    const newSelection = localValue.filter(id => id !== asin);
    setLocalValue(newSelection);
    
    if (validateSelection(newSelection)) {
      onChange(newSelection);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddAsins();
    } else if (e.key === 'Escape') {
      setShowInput(false);
      setInputValue('');
    }
  };

  const getDisplayText = () => {
    if (!localValue || localValue.length === 0) {
      return 'Add ASINs...';
    }
    
    if (localValue.length === 1) {
      return '1 ASIN added';
    }
    
    return `${localValue.length} ASINs added`;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Add ASIN button */}
      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setShowInput(true)}
          disabled={disabled}
          className={`
            w-full px-3 py-2 text-left
            border rounded-md shadow-sm
            focus:ring-indigo-500 focus:border-indigo-500
            ${error ? 'border-red-300' : 'border-gray-300'}
            ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white cursor-pointer hover:bg-gray-50'}
          `}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Package className="h-4 w-4 text-gray-400 mr-2" />
              <span className={`${!localValue.length ? 'text-gray-500' : 'text-gray-900'}`}>
                {getDisplayText()}
              </span>
            </div>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </div>
        </button>

        {/* ASIN input modal */}
        {showInput && (
          <div className="absolute top-full left-0 right-0 z-10 mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
            <div className="p-3">
              <div className="flex items-center space-x-2 mb-2">
                <Search className="h-4 w-4 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">Add ASINs</span>
              </div>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Enter ASINs separated by commas, spaces, or new lines..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                rows={3}
                autoFocus
              />
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-gray-500">
                  ASINs must be 10 alphanumeric characters
                </span>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowInput(false);
                      setInputValue('');
                    }}
                    className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAddAsins}
                    className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ASIN tags */}
        {localValue.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {localValue.slice(0, 10).map((asin) => (
              <span
                key={asin}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
              >
                {asin}
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => handleRemoveAsin(asin)}
                    className="ml-1 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
            {localValue.length > 10 && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                +{localValue.length - 10} more
              </span>
            )}
          </div>
        )}
      </div>

      {parameter.ui_config.help_text && !error && (
        <p className="text-xs text-gray-500">
          {parameter.ui_config.help_text}
        </p>
      )}

      {error && (
        <p className="text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
};

export default ASINListParameter;