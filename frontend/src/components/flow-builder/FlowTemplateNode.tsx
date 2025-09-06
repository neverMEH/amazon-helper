import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { Settings, Database, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import clsx from 'clsx';

export interface FlowTemplateNodeData {
  template_id: string;
  name: string;
  description?: string;
  parameters?: Array<{
    name: string;
    type: string;
    required?: boolean;
    default_value?: any;
  }>;
  config?: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
  error?: string;
  result?: any;
  onConfigure?: (nodeId: string) => void;
}

const FlowTemplateNode: React.FC<NodeProps<FlowTemplateNodeData>> = ({ 
  data, 
  selected,
  id 
}) => {

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Database className="h-4 w-4 text-gray-400" />;
    }
  };

  const getNodeClasses = () => {
    return clsx(
      'bg-white rounded-lg shadow-lg border-2 min-w-[250px] transition-all',
      {
        'border-blue-500 shadow-blue-200': selected,
        'border-gray-200 hover:border-gray-300': !selected,
        'ring-2 ring-green-400': data.status === 'success',
        'ring-2 ring-red-400': data.status === 'error',
        'ring-2 ring-blue-400': data.status === 'running',
      }
    );
  };

  const handleConfigClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (data.onConfigure) {
      data.onConfigure(id);
    }
  };

  return (
    <div className={getNodeClasses()}>
      {/* Input Handle */}
      <Handle
        id="input"
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500 !border-2 !border-white"
        style={{ top: -6 }}
        isConnectable={true}
      />

      {/* Node Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <h3 className="font-medium text-sm text-gray-900 line-clamp-1">
                {data.name}
              </h3>
            </div>
            {data.description && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {data.description}
              </p>
            )}
          </div>
          <button
            onClick={handleConfigClick}
            className="ml-2 p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            title="Configure node"
          >
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Parameters Section */}
      {data.parameters && data.parameters.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-100">
          <div className="text-xs font-medium text-gray-600 mb-1">Parameters:</div>
          <div className="flex flex-wrap gap-1">
            {data.parameters.map((param) => (
              <div
                key={param.name}
                className={clsx(
                  'text-xs px-2 py-0.5 rounded',
                  {
                    'bg-orange-100 text-orange-700': param.required && !data.config?.[param.name],
                    'bg-green-100 text-green-700': data.config?.[param.name],
                    'bg-gray-100 text-gray-600': !param.required && !data.config?.[param.name],
                  }
                )}
                title={`${param.name} (${param.type})${param.required ? ' - Required' : ''}`}
              >
                {param.name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Section */}
      {data.status && data.status !== 'idle' && (
        <div className="px-4 py-2">
          {data.status === 'error' && data.error && (
            <div className="text-xs text-red-600 bg-red-50 rounded p-2">
              {data.error}
            </div>
          )}
          {data.status === 'success' && data.result && (
            <div className="text-xs text-green-600 bg-green-50 rounded p-2">
              <div className="font-medium">Result ready</div>
              {data.result.row_count && (
                <div className="mt-1">{data.result.row_count} rows</div>
              )}
            </div>
          )}
          {data.status === 'running' && (
            <div className="text-xs text-blue-600 bg-blue-50 rounded p-2">
              Executing query...
            </div>
          )}
        </div>
      )}

      {/* Output Handle */}
      <Handle
        id="output"
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-500 !border-2 !border-white"
        style={{ bottom: -6 }}
        isConnectable={true}
      />

      {/* Visual Indicators for Connection Status */}
      <div className="absolute -top-8 left-1/2 transform -translate-x-1/2">
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full whitespace-nowrap">
            Configured
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(FlowTemplateNode);