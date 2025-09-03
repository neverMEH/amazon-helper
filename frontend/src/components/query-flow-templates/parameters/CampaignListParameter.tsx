import React, { useState, useEffect } from 'react';
import { Target, ChevronDown } from 'lucide-react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';
import { CampaignSelector } from '../../parameter-detection/CampaignSelector';

const CampaignListParameter: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  const [localValue, setLocalValue] = useState<string[]>(value || []);
  const [showSelector, setShowSelector] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalValue(value || []);
  }, [value]);

  const validateSelection = (selection: string[]): boolean => {
    if (parameter.required && (!selection || selection.length === 0)) {
      setError('At least one campaign must be selected');
      onError?.('At least one campaign must be selected');
      return false;
    }

    const rules = parameter.validation_rules;

    // Check min selections
    if (rules.min_selections && selection.length < rules.min_selections) {
      const error = `At least ${rules.min_selections} campaigns must be selected`;
      setError(error);
      onError?.(error);
      return false;
    }

    // Check max selections
    if (rules.max_selections && selection.length > rules.max_selections) {
      const error = `No more than ${rules.max_selections} campaigns can be selected`;
      setError(error);
      onError?.(error);
      return false;
    }

    setError(null);
    onError?.(null);
    return true;
  };

  const handleCampaignSelectorChange = (value: string[]) => {
    setLocalValue(value);
    
    if (validateSelection(value)) {
      onChange(value);
    }
    
    setShowSelector(false);
  };

  const handleRemoveCampaign = (campaignId: string) => {
    if (disabled) return;
    
    const newSelection = localValue.filter(id => id !== campaignId);
    setLocalValue(newSelection);
    
    if (validateSelection(newSelection)) {
      onChange(newSelection);
    }
  };

  const handleShowAllToggle = () => {
    if (disabled) return;
    
    if (localValue.includes('ALL')) {
      const newSelection: string[] = [];
      setLocalValue(newSelection);
      onChange(newSelection);
    } else {
      const newSelection = ['ALL'];
      setLocalValue(newSelection);
      onChange(newSelection);
    }
  };

  const getDisplayText = () => {
    if (!localValue || localValue.length === 0) {
      return 'Select campaigns...';
    }
    
    if (localValue.includes('ALL')) {
      return 'All campaigns';
    }
    
    if (localValue.length === 1) {
      return '1 campaign selected';
    }
    
    return `${localValue.length} campaigns selected`;
  };

  return (
    <div className={`space-y-1 ${className}`}>
      <label className="block text-sm font-medium text-gray-700">
        {parameter.display_name}
        {parameter.required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Show All option */}
      {parameter.ui_config.show_all_option !== false && (
        <div className="flex items-center">
          <input
            type="checkbox"
            id={`${parameter.parameter_name}-all`}
            checked={localValue.includes('ALL')}
            onChange={handleShowAllToggle}
            disabled={disabled}
            className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
          />
          <label 
            htmlFor={`${parameter.parameter_name}-all`}
            className="ml-2 text-sm text-gray-700 cursor-pointer"
          >
            All campaigns
          </label>
        </div>
      )}

      {/* Campaign selector button */}
      <div className="relative">
        <button
          type="button"
          onClick={() => !disabled && setShowSelector(true)}
          disabled={disabled || localValue.includes('ALL')}
          className={`
            w-full px-3 py-2 text-left
            border rounded-md shadow-sm
            focus:ring-indigo-500 focus:border-indigo-500
            ${error ? 'border-red-300' : 'border-gray-300'}
            ${disabled || localValue.includes('ALL') ? 'bg-gray-100 cursor-not-allowed' : 'bg-white cursor-pointer hover:bg-gray-50'}
          `}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Target className="h-4 w-4 text-gray-400 mr-2" />
              <span className={`${!localValue.length && !localValue.includes('ALL') ? 'text-gray-500' : 'text-gray-900'}`}>
                {getDisplayText()}
              </span>
            </div>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </div>
        </button>

        {/* Campaign tags */}
        {localValue.length > 0 && !localValue.includes('ALL') && (
          <div className="mt-2 flex flex-wrap gap-1">
            {localValue.slice(0, 5).map((campaignId) => (
              <span
                key={campaignId}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-indigo-100 text-indigo-800"
              >
                {campaignId}
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => handleRemoveCampaign(campaignId)}
                    className="ml-1 text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
            {localValue.length > 5 && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-600">
                +{localValue.length - 5} more
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

      {/* Campaign selector modal */}
      {showSelector && (
        <CampaignSelector
          value={localValue.filter(id => id !== 'ALL')}
          onChange={handleCampaignSelectorChange}
          multiple={parameter.ui_config.multi_select !== false}
        />
      )}
    </div>
  );
};

export default CampaignListParameter;