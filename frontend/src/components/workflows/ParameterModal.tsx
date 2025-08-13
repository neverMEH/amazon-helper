import { useState, useEffect } from 'react';
import { X, Play, Calendar, Hash, Type, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface ParameterModalProps {
  parameters: Record<string, any>;
  onExecute: (parameters: Record<string, any>) => void;
  onClose: () => void;
  isExecuting?: boolean;
}

interface ParameterConfig {
  name: string;
  value: any;
  type: 'string' | 'number' | 'date' | 'boolean' | 'json';
  description?: string;
}

export default function ParameterModal({
  parameters,
  onExecute,
  onClose,
  isExecuting = false,
}: ParameterModalProps) {
  const [paramConfigs, setParamConfigs] = useState<ParameterConfig[]>([]);
  const [paramValues, setParamValues] = useState<Record<string, any>>({});

  useEffect(() => {
    // Initialize parameter configurations
    const configs: ParameterConfig[] = Object.entries(parameters).map(([name, value]) => {
      let type: ParameterConfig['type'] = 'string';
      let description = '';

      // Infer type from parameter name and value
      if (typeof value === 'number') {
        type = 'number';
      } else if (typeof value === 'boolean') {
        type = 'boolean';
      } else if (typeof value === 'object') {
        type = 'json';
      } else if (
        name.toLowerCase().includes('date') ||
        name.toLowerCase().includes('_dt') ||
        name.toLowerCase().includes('_at')
      ) {
        type = 'date';
        // Convert to date input format if it's a date string
        if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
          value = value.split('T')[0];
        }
      }

      // Add descriptions based on common parameter names
      if (name.toLowerCase().includes('start')) {
        description = 'Start date for the analysis period';
      } else if (name.toLowerCase().includes('end')) {
        description = 'End date for the analysis period';
      } else if (name.toLowerCase().includes('window') || name.toLowerCase().includes('days')) {
        description = 'Number of days to include in the analysis';
      } else if (name.toLowerCase().includes('campaign')) {
        description = 'Campaign identifier or filter';
      } else if (name.toLowerCase().includes('brand')) {
        description = 'Brand name or identifier';
      } else if (name.toLowerCase().includes('threshold')) {
        description = 'Minimum threshold value';
      } else if (name.toLowerCase().includes('limit')) {
        description = 'Maximum number of results to return';
      }

      return {
        name,
        value,
        type,
        description,
      };
    });

    setParamConfigs(configs);
    setParamValues(parameters);
  }, [parameters]);

  const handleValueChange = (name: string, value: any, type: ParameterConfig['type']) => {
    let processedValue = value;

    // Process value based on type
    switch (type) {
      case 'number':
        processedValue = value === '' ? 0 : Number(value);
        break;
      case 'boolean':
        processedValue = value === 'true';
        break;
      case 'json':
        try {
          processedValue = value ? JSON.parse(value) : {};
        } catch (e) {
          // Keep as string if invalid JSON
          processedValue = value;
        }
        break;
      case 'date':
        // Keep as string in YYYY-MM-DD format
        processedValue = value;
        break;
    }

    setParamValues(prev => ({
      ...prev,
      [name]: processedValue,
    }));
  };

  const handleExecute = () => {
    // Validate required parameters
    const emptyParams = paramConfigs.filter(
      config => !paramValues[config.name] && paramValues[config.name] !== 0 && paramValues[config.name] !== false
    );

    if (emptyParams.length > 0) {
      toast.error(`Please fill in all parameters: ${emptyParams.map(p => p.name).join(', ')}`);
      return;
    }

    // Validate JSON parameters
    for (const config of paramConfigs) {
      if (config.type === 'json' && paramValues[config.name]) {
        try {
          if (typeof paramValues[config.name] === 'string') {
            JSON.parse(paramValues[config.name]);
          }
        } catch (e) {
          toast.error(`Invalid JSON for parameter "${config.name}"`);
          return;
        }
      }
    }

    onExecute(paramValues);
  };

  const getParameterIcon = (type: ParameterConfig['type']) => {
    switch (type) {
      case 'date':
        return <Calendar className="h-4 w-4 text-gray-400" />;
      case 'number':
        return <Hash className="h-4 w-4 text-gray-400" />;
      case 'json':
        return <FileText className="h-4 w-4 text-gray-400" />;
      default:
        return <Type className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Customize Query Parameters
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-180px)]">
          {paramConfigs.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">
              No parameters required for this query
            </p>
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-4">
                Customize the parameters below before executing the workflow. These values will be substituted into your SQL query.
              </p>

              {paramConfigs.map((config) => (
                <div key={config.name} className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    <div className="flex items-center space-x-2">
                      {getParameterIcon(config.type)}
                      <span>{config.name}</span>
                      <span className="text-xs text-gray-500">({config.type})</span>
                    </div>
                  </label>
                  
                  {config.description && (
                    <p className="text-xs text-gray-500">{config.description}</p>
                  )}

                  {config.type === 'boolean' ? (
                    <select
                      value={String(paramValues[config.name])}
                      onChange={(e) => handleValueChange(config.name, e.target.value, config.type)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    >
                      <option value="true">True</option>
                      <option value="false">False</option>
                    </select>
                  ) : config.type === 'json' ? (
                    <textarea
                      value={
                        typeof paramValues[config.name] === 'object'
                          ? JSON.stringify(paramValues[config.name], null, 2)
                          : paramValues[config.name]
                      }
                      onChange={(e) => handleValueChange(config.name, e.target.value, config.type)}
                      rows={4}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                      placeholder='{"key": "value"}'
                    />
                  ) : (
                    <input
                      type={config.type === 'number' ? 'number' : config.type === 'date' ? 'date' : 'text'}
                      value={paramValues[config.name] || ''}
                      onChange={(e) => handleValueChange(config.name, e.target.value, config.type)}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                      placeholder={
                        config.type === 'date' ? 'YYYY-MM-DD' :
                        config.type === 'number' ? '0' :
                        'Enter value...'
                      }
                    />
                  )}
                </div>
              ))}

              {/* Preview */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Parameter Preview</h4>
                <pre className="text-xs text-gray-600 overflow-x-auto">
                  {JSON.stringify(paramValues, null, 2)}
                </pre>
              </div>
            </>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={isExecuting || paramConfigs.length === 0}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4 mr-2" />
            Execute Workflow
          </button>
        </div>
      </div>
    </div>
  );
}