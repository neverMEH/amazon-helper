import React, { useState, useEffect } from 'react';
import { Database, AlertCircle, CheckCircle, Loader2, Settings } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import type { ScheduleConfig } from '../../types/schedule';

interface SnowflakeConfigStepProps {
  config: ScheduleConfig;
  workflowName: string;
  instanceInfo?: {
    instanceName?: string;
    brands?: string[];
  };
  onChange: (config: ScheduleConfig) => void;
  onNext: () => void;
  onBack: () => void;
}

const SnowflakeConfigStep: React.FC<SnowflakeConfigStepProps> = ({
  config,
  workflowName,
  instanceInfo,
  onChange,
  onNext,
  onBack,
}) => {
  const [tableName, setTableName] = useState<string>(config.snowflakeTableName || '');
  const [schemaName, setSchemaName] = useState<string>(config.snowflakeSchemaName || '');
  const [enabled, setEnabled] = useState<boolean>(config.snowflakeEnabled || false);
  const [strategy, setStrategy] = useState<string>(config.snowflakeStrategy || 'upsert');
  const [tableNamePreview, setTableNamePreview] = useState<string>('');

  // Check if user has Snowflake configuration
  const { data: hasSnowflakeConfig, isLoading: configLoading } = useQuery({
    queryKey: ['snowflake-config-check'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/snowflake/config/check', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });
        if (response.ok) {
          const data = await response.json();
          return data.hasConfig || false;
        }
        return false;
      } catch (error) {
        console.error('Error checking Snowflake config:', error);
        return false;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Auto-generate table name if empty
  useEffect(() => {
    if (enabled && !tableName) {
      const sanitizeName = (name: string) =>
        name.toLowerCase()
          .replace(/\s+/g, '_')
          .replace(/[^a-z0-9_]/g, '')
          .substring(0, 63); // Snowflake max length

      const instancePart = instanceInfo?.instanceName ? `${sanitizeName(instanceInfo.instanceName)}_` : '';
      const workflowPart = sanitizeName(workflowName);
      const generated = `amc_${instancePart}${workflowPart}`;

      setTableName(generated);
      setTableNamePreview(generated);
    }
  }, [enabled, workflowName, instanceInfo]);

  // Update table name preview on change
  useEffect(() => {
    if (tableName) {
      const sanitized = tableName
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_]/g, '')
        .substring(0, 63);
      setTableNamePreview(sanitized);
    } else {
      setTableNamePreview('');
    }
  }, [tableName]);

  // Update config when values change
  useEffect(() => {
    onChange({
      ...config,
      snowflakeEnabled: enabled,
      snowflakeTableName: tableNamePreview || undefined,
      snowflakeSchemaName: schemaName || undefined,
      snowflakeStrategy: strategy,
    });
  }, [enabled, tableNamePreview, schemaName, strategy]);

  const handleNext = () => {
    // Validation: if enabled, must have table name
    if (enabled && !tableNamePreview) {
      return;
    }
    onNext();
  };

  if (configLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-3 text-gray-600">Checking Snowflake configuration...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          <Database className="h-5 w-5 mr-2 text-blue-600" />
          Snowflake Configuration
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Optionally upload execution results to Snowflake for data warehousing
        </p>
      </div>

      {/* Snowflake Config Status Banner */}
      {!hasSnowflakeConfig && (
        <div className="rounded-md bg-yellow-50 p-4 border border-yellow-200">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0" />
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-yellow-800">
                Snowflake Not Configured
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  You haven't configured Snowflake yet. To enable Snowflake uploads, go to{' '}
                  <a href="/settings#snowflake" className="font-medium underline hover:text-yellow-900">
                    Settings → Snowflake Configuration
                  </a>{' '}
                  to set up your connection first.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex-1">
          <label htmlFor="snowflake-enabled" className="text-sm font-medium text-gray-900 flex items-center">
            <Database className="h-4 w-4 mr-2 text-gray-600" />
            Enable Snowflake Upload
          </label>
          <p className="text-xs text-gray-500 mt-1">
            {hasSnowflakeConfig
              ? 'Upload execution results to your Snowflake data warehouse'
              : 'Configure Snowflake in Settings to enable this feature'
            }
          </p>
        </div>
        <button
          type="button"
          id="snowflake-enabled"
          onClick={() => setEnabled(!enabled)}
          disabled={!hasSnowflakeConfig}
          className={`
            relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
            transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            ${enabled ? 'bg-blue-600' : 'bg-gray-200'}
            ${!hasSnowflakeConfig ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          role="switch"
          aria-checked={enabled}
        >
          <span
            className={`
              pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
              transition duration-200 ease-in-out
              ${enabled ? 'translate-x-5' : 'translate-x-0'}
            `}
          />
        </button>
      </div>

      {/* Configuration Form (only shown when enabled) */}
      {enabled && hasSnowflakeConfig && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          {/* Success Banner */}
          <div className="flex items-start space-x-2 text-sm text-blue-700">
            <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Snowflake Upload Enabled</p>
              <p className="text-xs mt-1">Results will be uploaded after each execution using UPSERT strategy</p>
            </div>
          </div>

          {/* Table Name Input */}
          <div>
            <label htmlFor="table-name" className="block text-sm font-medium text-gray-700">
              Table Name
            </label>
            <input
              type="text"
              id="table-name"
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              placeholder="amc_workflow_results"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            {tableNamePreview && tableNamePreview !== tableName && (
              <p className="mt-1 text-xs text-gray-500">
                Sanitized: <code className="bg-gray-100 px-1 py-0.5 rounded">{tableNamePreview}</code>
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Table will use UPSERT strategy with composite key: (execution_id, time_window_start, time_window_end)
            </p>
          </div>

          {/* Schema Name Input (Optional) */}
          <div>
            <label htmlFor="schema-name" className="block text-sm font-medium text-gray-700">
              Schema Name <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              id="schema-name"
              value={schemaName}
              onChange={(e) => setSchemaName(e.target.value)}
              placeholder="Uses default schema if empty"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">
              Leave empty to use your default Snowflake schema
            </p>
          </div>

          {/* Strategy Selector (Locked to UPSERT for schedules) */}
          <div>
            <label htmlFor="strategy" className="block text-sm font-medium text-gray-700">
              Upload Strategy
            </label>
            <div className="mt-1 relative">
              <select
                id="strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                disabled
                className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm opacity-75 cursor-not-allowed"
              >
                <option value="upsert">UPSERT (Recommended for schedules)</option>
                <option value="append">APPEND</option>
                <option value="replace">REPLACE</option>
                <option value="create_new">CREATE NEW</option>
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-8 pointer-events-none">
                <Settings className="h-4 w-4 text-gray-400" />
              </div>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              UPSERT is locked for schedules to maintain a single, continuously updated table
            </p>
          </div>

          {/* Variable Guide */}
          <div className="bg-white p-3 rounded border border-gray-200">
            <h4 className="text-xs font-medium text-gray-700 mb-2">UPSERT Behavior</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Same date range → Updates existing row</li>
              <li>• New date range → Inserts new row</li>
              <li>• Prevents duplicate data automatically</li>
              <li>• Maintains single table across all schedule runs</li>
            </ul>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={enabled && !tableNamePreview}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continue to Review
        </button>
      </div>
    </div>
  );
};

export default SnowflakeConfigStep;
