import { useState } from 'react';
import { ChevronDown, ChevronUp, Info, Check, AlertCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import InstanceSelector from './InstanceSelector';

interface QueryConfigurationStepProps {
  state: any;
  setState: (state: any) => void;
  instances: any[];
}

const TIMEZONES = [
  { value: 'UTC', label: '-00:00 UTC' },
  { value: 'America/New_York', label: '-05:00 EST' },
  { value: 'America/Chicago', label: '-06:00 CST' },
  { value: 'America/Denver', label: '-07:00 MST' },
  { value: 'America/Los_Angeles', label: '-08:00 PST' },
  { value: 'Europe/London', label: '+00:00 GMT' },
  { value: 'Europe/Paris', label: '+01:00 CET' },
  { value: 'Asia/Tokyo', label: '+09:00 JST' },
  { value: 'Australia/Sydney', label: '+10:00 AEST' }
];

export default function QueryConfigurationStep({ state, setState, instances }: QueryConfigurationStepProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [emailVerified, setEmailVerified] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const handleInstanceChange = (instanceId: string) => {
    setState((prev: any) => ({ ...prev, instanceId }));
  };

  const handleTimezoneChange = (timezone: string) => {
    setState((prev: any) => ({ ...prev, timezone }));
  };

  const handleAdvancedOptionChange = (option: string, value: boolean) => {
    setState((prev: any) => ({
      ...prev,
      advancedOptions: {
        ...prev.advancedOptions,
        [option]: value
      }
    }));
  };

  const handleExportSettingChange = (field: string, value: string) => {
    setState((prev: any) => ({
      ...prev,
      exportSettings: {
        ...prev.exportSettings,
        [field]: value
      }
    }));
  };

  const handleVerifyEmail = async () => {
    if (!state.exportSettings.email) {
      toast.error('Please enter an email address');
      return;
    }

    setVerifying(true);
    try {
      // Simulate email verification
      await new Promise(resolve => setTimeout(resolve, 1500));
      setEmailVerified(true);
      toast.success('Email verified successfully');
    } catch (error) {
      toast.error('Failed to verify email');
    } finally {
      setVerifying(false);
    }
  };

  const handleParameterChange = (param: string, value: any) => {
    setState((prev: any) => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [param]: value
      }
    }));
  };

  const selectedInstance = instances.find(i => i.instanceId === state.instanceId || i.id === state.instanceId);

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Instance Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          AMC Instance <span className="text-red-500">*</span>
        </label>
        <InstanceSelector
          instances={instances}
          value={state.instanceId}
          onChange={handleInstanceChange}
          placeholder="Select an instance..."
          required={true}
        />
        {selectedInstance && (
          <p className="mt-2 text-xs text-gray-500">
            Selected: {selectedInstance.accountName} account in {selectedInstance.region}
          </p>
        )}
      </div>

      {/* Timezone Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timezone
        </label>
        <select
          value={state.timezone}
          onChange={(e) => handleTimezoneChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          {TIMEZONES.map(tz => (
            <option key={tz.value} value={tz.value}>
              {tz.label}
            </option>
          ))}
        </select>
      </div>

      {/* Query Parameters */}
      {Object.keys(state.parameters).length > 0 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Query Parameters
          </label>
          <div className="bg-gray-50 rounded-md p-4 space-y-3">
            {Object.entries(state.parameters).map(([param, value]) => (
              <div key={param}>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {`{{${param}}}`}
                </label>
                {param.includes('date') ? (
                  <input
                    type="date"
                    value={value as string}
                    onChange={(e) => handleParameterChange(param, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                ) : typeof value === 'number' ? (
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => handleParameterChange(param, parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                ) : Array.isArray(value) ? (
                  <textarea
                    value={value.join(', ')}
                    onChange={(e) => handleParameterChange(param, e.target.value.split(',').map(v => v.trim()))}
                    placeholder="Enter comma-separated values"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    rows={2}
                  />
                ) : (
                  <input
                    type="text"
                    value={value as string}
                    onChange={(e) => handleParameterChange(param, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Options */}
      <div className="mb-6">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4 mr-1" />
          ) : (
            <ChevronDown className="h-4 w-4 mr-1" />
          )}
          Advanced Options
        </button>

        {showAdvanced && (
          <div className="mt-3 bg-gray-50 rounded-md p-4 space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={state.advancedOptions.ignoreDataGaps}
                onChange={(e) => handleAdvancedOptionChange('ignoreDataGaps', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Ignore data gaps</span>
              <Info className="h-3 w-3 ml-1 text-gray-400" />
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={state.advancedOptions.appendThresholdColumns}
                onChange={(e) => handleAdvancedOptionChange('appendThresholdColumns', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Append aggregation threshold columns</span>
              <Info className="h-3 w-3 ml-1 text-gray-400" />
            </label>
          </div>
        )}
      </div>

      {/* Export Configuration */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Export Configuration</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={state.exportSettings.name}
              onChange={(e) => handleExportSettingChange('name', e.target.value)}
              placeholder="e.g., Campaign Analysis Q4 2024"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email for Results
            </label>
            <div className="flex space-x-2">
              <input
                type="email"
                value={state.exportSettings.email}
                onChange={(e) => {
                  handleExportSettingChange('email', e.target.value);
                  setEmailVerified(false);
                }}
                placeholder="your.email@company.com"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={handleVerifyEmail}
                disabled={verifying || emailVerified}
                className={`px-4 py-2 text-sm font-medium rounded-md ${
                  emailVerified
                    ? 'bg-green-100 text-green-700 border border-green-300'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {verifying ? (
                  'Verifying...'
                ) : emailVerified ? (
                  <>
                    <Check className="h-4 w-4 inline mr-1" />
                    Verified
                  </>
                ) : (
                  'Verify'
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={state.exportSettings.format}
              onChange={(e) => handleExportSettingChange('format', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="CSV">CSV</option>
              <option value="PARQUET">Parquet</option>
              <option value="JSON">JSON</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password Protection (Optional)
            </label>
            <input
              type="password"
              value={state.exportSettings.password || ''}
              onChange={(e) => handleExportSettingChange('password', e.target.value)}
              placeholder="Enter password for encrypted export"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Protect your export file with a password for added security
            </p>
          </div>
        </div>
      </div>

      {/* Validation Messages */}
      {!state.instanceId && (
        <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-md flex items-start">
          <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
          <p className="text-sm text-yellow-800">Please select an AMC instance to continue</p>
        </div>
      )}
    </div>
  );
}