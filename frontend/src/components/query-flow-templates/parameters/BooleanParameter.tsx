import React, { useState, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

const BooleanParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<boolean>(value ?? false);

  useEffect(() => {
    setLocalValue(value ?? false);
  }, [value]);

  useEffect(() => {
    // Clear any errors when component mounts (boolean fields can't really be invalid)
    onError?.(null);
  }, [onError]);

  const handleChange = (newValue: boolean) => {
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleToggleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleChange(e.target.checked);
  };

  const handleButtonClick = (newValue: boolean) => {
    if (!disabled) {
      handleChange(newValue);
    }
  };

  // Determine display style from ui_config
  const displayStyle = parameter.ui_config.display_style || 'toggle';

  if (displayStyle === 'buttons') {
    return (
      <div className={`space-y-1 ${className}`}>
        <label className="block text-sm font-medium text-gray-700">
          {parameter.display_name}
          {parameter.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={() => handleButtonClick(true)}
            disabled={disabled}
            className={`
              px-4 py-2 rounded-md text-sm font-medium border transition-colors
              ${localValue 
                ? 'bg-green-100 border-green-300 text-green-800' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <Check className="h-4 w-4 inline mr-1" />
            Yes
          </button>
          <button
            type="button"
            onClick={() => handleButtonClick(false)}
            disabled={disabled}
            className={`
              px-4 py-2 rounded-md text-sm font-medium border transition-colors
              ${!localValue 
                ? 'bg-red-100 border-red-300 text-red-800' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <X className="h-4 w-4 inline mr-1" />
            No
          </button>
        </div>

        {parameter.ui_config.help_text && (
          <p className="text-xs text-gray-500">
            {parameter.ui_config.help_text}
          </p>
        )}
      </div>
    );
  }

  // Default toggle switch
  return (
    <div className={`space-y-1 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          {parameter.display_name}
          {parameter.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={localValue}
            onChange={handleToggleChange}
            disabled={disabled}
            className="sr-only"
          />
          <div className={`
            w-11 h-6 rounded-full transition-colors
            ${localValue ? 'bg-indigo-600' : 'bg-gray-200'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}>
            <div className={`
              absolute top-0.5 left-0.5 bg-white border border-gray-300 rounded-full h-5 w-5 transition-transform
              ${localValue ? 'transform translate-x-5' : ''}
            `} />
          </div>
        </label>
      </div>

      {parameter.ui_config.help_text && (
        <p className="text-xs text-gray-500">
          {parameter.ui_config.help_text}
        </p>
      )}
    </div>
  );
};

export default BooleanParameter;