import React, { useState, useEffect } from 'react';
import { List, Plus, Search } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const StringListParameter: React.FC<BaseParameterInputProps> = ({
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
      setError('At least one item must be provided');
      onError?.('At least one item must be provided');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check min items
    if (rules.min_items && selection.length < rules.min_items) {
      const error = `At least ${rules.min_items} items must be provided`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check max items
    if (rules.max_items && selection.length > rules.max_items) {
      const error = `No more than ${rules.max_items} items can be provided`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Validate individual items
    if (rules.pattern) {
      const regex = new RegExp(rules.pattern);
      const invalidItems = selection.filter(item => !regex.test(item));
      if (invalidItems.length > 0) {
        const error = `Invalid format for: ${invalidItems.join(', ')}`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    // Check min/max length for individual items
    if (rules.min_length) {
      const shortItems = selection.filter(item => item.length < rules.min_length);
      if (shortItems.length > 0) {
        const error = `Items must be at least ${rules.min_length} characters: ${shortItems.join(', ')}`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    if (rules.max_length) {
      const longItems = selection.filter(item => item.length > rules.max_length);
      if (longItems.length > 0) {
        const error = `Items must not exceed ${rules.max_length} characters: ${longItems.join(', ')}`;
        setError(error);
        onError?.(error);
        return false;
      }
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleAddItems = () => {
    if (!inputValue.trim()) return;

    // Parse items from input (comma, semicolon, or newline separated)
    const newItems = inputValue
      .split(/[,;\n]+/)
      .map(item => item.trim())
      .filter(item => item.length > 0)
      .filter(item => !localValue.includes(item)); // Remove duplicates

    const updatedSelection = [...localValue, ...newItems];
    setLocalValue(updatedSelection);
    
    if (validateSelection(updatedSelection)) {
      onChange(updatedSelection);
    }
    
    setInputValue('');
    setShowInput(false);
  };

  const handleAddSingleItem = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const newItem = inputValue.trim();
      if (newItem && !localValue.includes(newItem)) {
        const updatedSelection = [...localValue, newItem];
        setLocalValue(updatedSelection);
        
        if (validateSelection(updatedSelection)) {
          onChange(updatedSelection);
        }
        
        setInputValue('');
      }
    }
  };

  const handleRemoveItem = (item: string) => {
    if (disabled) return;
    
    const newSelection = localValue.filter(i => i !== item);
    setLocalValue(newSelection);
    
    if (validateSelection(newSelection)) {
      onChange(newSelection);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddItems();
    } else if (e.key === 'Escape') {
      setShowInput(false);
      setInputValue('');
    }
  };

  const getDisplayText = () => {
    if (!localValue || localValue.length === 0) {
      return `Add ${parameter.display_name.toLowerCase()}...`;
    }
    
    if (localValue.length === 1) {
      return '1 item added';
    }
    
    return `${localValue.length} items added`;
  };

  const inputMode = parameter.ui_config.input_mode || 'bulk'; // 'bulk' or 'single'

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Single item input mode */}
      {inputMode === 'single' && (
        <div className="flex space-x-2">
          <div className="flex-1">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleAddSingleItem}
              placeholder={parameter.ui_config.placeholder || 'Enter item and press Enter'}
              disabled={disabled}
              className={`
                block w-full px-3 py-2
                border rounded-md shadow-sm
                focus:ring-indigo-500 focus:border-indigo-500
                ${error ? 'border-red-300' : 'border-gray-300'}
                ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
              `}
              maxLength={parameter.validation_rules.max_length}
            />
          </div>
          <button
            type="button"
            onClick={() => {
              const newItem = inputValue.trim();
              if (newItem && !localValue.includes(newItem)) {
                const updatedSelection = [...localValue, newItem];
                setLocalValue(updatedSelection);
                if (validateSelection(updatedSelection)) {
                  onChange(updatedSelection);
                }
                setInputValue('');
              }
            }}
            disabled={disabled || !inputValue.trim()}
            className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Bulk input mode */}
      {inputMode === 'bulk' && (
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
                <List className="h-4 w-4 text-gray-400 mr-2" />
                <span className={`${!localValue.length ? 'text-gray-500' : 'text-gray-900'}`}>
                  {getDisplayText()}
                </span>
              </div>
              <Plus className="h-4 w-4 text-gray-400" />
            </div>
          </button>

          {/* Bulk input modal */}
          {showInput && (
            <div className="absolute top-full left-0 right-0 z-10 mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
              <div className="p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Search className="h-4 w-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">
                    Add {parameter.display_name}
                  </span>
                </div>
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={parameter.ui_config.placeholder || "Enter items separated by commas, semicolons, or new lines..."}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  rows={3}
                  autoFocus
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-500">
                    {parameter.validation_rules.min_length && parameter.validation_rules.max_length
                      ? `Items: ${parameter.validation_rules.min_length}-${parameter.validation_rules.max_length} characters`
                      : parameter.validation_rules.min_length
                      ? `Min ${parameter.validation_rules.min_length} characters per item`
                      : parameter.validation_rules.max_length
                      ? `Max ${parameter.validation_rules.max_length} characters per item`
                      : 'Enter items separated by commas'
                    }
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
                      onClick={handleAddItems}
                      className="px-2 py-1 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700"
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Item tags */}
      {localValue.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {localValue.slice(0, 8).map((item, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800"
            >
              {item.length > 20 ? `${item.substring(0, 20)}...` : item}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => handleRemoveItem(item)}
                  className="ml-1 text-purple-600 hover:text-purple-800"
                >
                  ×
                </button>
              )}
            </span>
          ))}
          {localValue.length > 8 && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
              +{localValue.length - 8} more
            </span>
          )}
        </div>
      )}

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

export default StringListParameter;