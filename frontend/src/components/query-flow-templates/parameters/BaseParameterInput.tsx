import React from 'react';
import type { BaseParameterInputProps } from '../../../types/queryFlowTemplate';

// Import specific parameter components
import DateParameter from './DateParameter';
import DateRangeParameter from './DateRangeParameter';
import StringParameter from './StringParameter';
import NumberParameter from './NumberParameter';
import BooleanParameter from './BooleanParameter';
import CampaignListParameter from './CampaignListParameter';
import ASINListParameter from './ASINListParameter';
import StringListParameter from './StringListParameter';

/**
 * Factory component that renders the appropriate parameter input based on type
 */
const BaseParameterInput: React.FC<BaseParameterInputProps> = ({
  parameter,
  value,
  onChange,
  onError,
  disabled = false,
  className = ''
}) => {
  // Map parameter types to their corresponding components
  const parameterComponents: Record<string, React.ComponentType<BaseParameterInputProps>> = {
    'date': DateParameter,
    'date_range': DateRangeParameter,
    'string': StringParameter,
    'number': NumberParameter,
    'boolean': BooleanParameter,
    'campaign_list': CampaignListParameter,
    'asin_list': ASINListParameter,
    'string_list': StringListParameter,
  };

  const Component = parameterComponents[parameter.parameter_type];

  if (!Component) {
    console.error(`Unknown parameter type: ${parameter.parameter_type}`);
    return (
      <div className="text-red-600">
        Unsupported parameter type: {parameter.parameter_type}
      </div>
    );
  }

  return (
    <Component
      parameter={parameter}
      value={value}
      onChange={onChange}
      onError={onError}
      disabled={disabled}
      className={className}
    />
  );
};

export default BaseParameterInput;