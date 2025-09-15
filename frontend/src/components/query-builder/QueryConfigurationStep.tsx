import { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Info, AlertCircle, Package } from 'lucide-react';
import InstanceSelector from './InstanceSelector';
import ASINSelectionModal from './ASINSelectionModal';
import CampaignSelectionModal from './CampaignSelectionModal';

interface QueryConfigurationStepProps {
  state: any;
  setState: (state: any) => void;
  instances: any[];
  onNavigateToStep?: (step: number) => void;
  currentStep?: number;
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
  const [showASINModal, setShowASINModal] = useState(false);
  const [currentASINParam, setCurrentASINParam] = useState<string | null>(null);
  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [currentCampaignParam, setCurrentCampaignParam] = useState<string | null>(null);

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

  // Auto-generate export name
  const generateExportName = () => {
    const queryName = state.name || 'Query';
    const instanceName = selectedInstance?.instanceName || 'Instance';
    
    // Get date range from parameters or use default
    const startDate = state.parameters?.startDate || state.parameters?.start_date || '';
    const endDate = state.parameters?.endDate || state.parameters?.end_date || '';
    const dateRange = startDate && endDate ? `${startDate} to ${endDate}` : 'Date Range';
    
    // Format current date and time
    const now = new Date();
    const dateTimeRan = now.toISOString().split('T')[0] + '_' + 
                       now.toTimeString().split(' ')[0].replace(/:/g, '-');
    
    return `${queryName} - ${instanceName} - ${dateRange} - ${dateTimeRan}`;
  };


  const handleParameterChange = (param: string, value: any) => {
    console.log('[QueryConfigurationStep] Updating parameter:', {
      param,
      oldValue: state.parameters[param],
      newValue: value
    });
    
    setState((prev: any) => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [param]: value
      }
    }));
  };

  const handleASINSelect = (paramName: string) => {
    setCurrentASINParam(paramName);
    setShowASINModal(true);
  };

  const handleASINModalConfirm = (asins: string[]) => {
    console.log('[QueryConfigurationStep] ASIN selection confirmed:', {
      param: currentASINParam,
      asins,
      asinCount: asins.length
    });
    
    if (currentASINParam) {
      // Always inject ASINs directly into SQL query instead of using parameters
      console.log('[QueryConfigurationStep] Injecting ASINs into SQL VALUES clause');
      
      // Generate VALUES clause for SQL injection
      const valuesClause = asins.map(asin => `    ('${asin}')`).join(',\n');
      const sqlComment = `-- Updated ${currentASINParam} with ${asins.length} ASINs\n`;
      
      // Store special marker for SQL injection
      handleParameterChange(currentASINParam, {
        _sqlInject: true,
        _values: asins,
        _valuesClause: valuesClause,
        _comment: sqlComment,
        _type: 'asin'
      });
    }
    setShowASINModal(false);
    setCurrentASINParam(null);
  };

  const handleCampaignSelect = (paramName: string) => {
    setCurrentCampaignParam(paramName);
    setShowCampaignModal(true);
  };

  const handleCampaignModalConfirm = (campaigns: string[]) => {
    console.log('[QueryConfigurationStep] Campaign selection confirmed:', {
      param: currentCampaignParam,
      campaigns,
      campaignCount: campaigns.length
    });
    
    if (currentCampaignParam) {
      // Always inject campaigns directly into SQL query instead of using parameters
      console.log('[QueryConfigurationStep] Injecting campaigns into SQL VALUES clause');
      
      // Generate VALUES clause for SQL injection
      const valuesClause = campaigns.map(campaign => `    ('${campaign}')`).join(',\n');
      const sqlComment = `-- Updated ${currentCampaignParam} with ${campaigns.length} campaigns\n`;
      
      // Store special marker for SQL injection
      handleParameterChange(currentCampaignParam, {
        _sqlInject: true,
        _values: campaigns,
        _valuesClause: valuesClause,
        _comment: sqlComment,
        _type: 'campaign'
      });
    }
    setShowCampaignModal(false);
    setCurrentCampaignParam(null);
  };

  /**
   * Determines if a parameter should trigger ASIN selection UI
   * Trigger keywords include:
   * - tracked_asins: ASINs being monitored/tracked
   * - target_asins: ASINs being targeted in campaigns
   * - promoted_asins: ASINs being promoted
   * - competitor_asins: Competitor product ASINs
   * - purchased_asins: ASINs that were purchased
   * - viewed_asins: ASINs that were viewed
   */
  const isASINParameter = (paramName: string): boolean => {
    const lowerParam = paramName.toLowerCase();
    // Specific trigger keywords for ASIN selection
    const asinTriggers = [
      'tracked_asins',
      'tracked_asin',
      'target_asins',
      'target_asin',
      'promoted_asins',
      'promoted_asin',
      'competitor_asins',
      'competitor_asin',
      'purchased_asins',
      'purchased_asin',
      'viewed_asins',
      'viewed_asin'
    ];
    
    // Check for exact matches first
    if (asinTriggers.includes(lowerParam)) {
      return true;
    }
    
    // Then check for partial matches with specific keywords
    return lowerParam === 'asin' || 
           lowerParam === 'asins' ||
           lowerParam.includes('tracked_asin') ||
           lowerParam.includes('target_asin') ||
           lowerParam.includes('promoted_asin') ||
           lowerParam.includes('competitor_asin') ||
           lowerParam.includes('purchased_asin') ||
           lowerParam.includes('viewed_asin');
  };

  const isCampaignParameter = (paramName: string): boolean => {
    const lowerParam = paramName.toLowerCase();
    return lowerParam.includes('campaign') || lowerParam.includes('camp_id') || lowerParam.includes('campaign_id');
  };

  const getParameterType = (paramName: string): 'asin' | 'campaign' | 'date' | 'number' | 'text' => {
    if (isASINParameter(paramName)) return 'asin';
    if (isCampaignParameter(paramName)) return 'campaign';
    if (paramName.toLowerCase().includes('date')) return 'date';
    // Check if current value is a number
    const currentValue = state.parameters[paramName];
    if (typeof currentValue === 'number') return 'number';
    return 'text';
  };

  const selectedInstance = instances.find(i => i.instanceId === state.instanceId || i.id === state.instanceId);

  // Auto-generate export name when relevant fields change
  useEffect(() => {
    if (!state.exportSettings.name || state.exportSettings.name === '') {
      const autoGeneratedName = generateExportName();
      setState((prev: any) => ({
        ...prev,
        exportSettings: {
          ...prev.exportSettings,
          name: autoGeneratedName
        }
      }));
    }
  }, [state.name, selectedInstance?.instanceName, state.parameters?.startDate, state.parameters?.endDate, state.parameters?.start_date, state.parameters?.end_date]);

  return (
    <>
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
            {Object.entries(state.parameters).map(([param, value]) => {
              const paramType = getParameterType(param);
              return (
                <div key={param}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    {`{{${param}}}`}
                  </label>
                  {paramType === 'asin' ? (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={
                          value && typeof value === 'object' && '_sqlInject' in value && value._sqlInject 
                            ? `${(value as any)._values.length} ASINs (SQL injection mode)`
                            : Array.isArray(value) ? value.join(', ') : (value as string)
                        }
                        onChange={(e) => handleParameterChange(param, e.target.value)}
                        placeholder="Enter ASINs or select from catalog"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        readOnly={Boolean(value && typeof value === 'object' && '_sqlInject' in value && (value as any)._sqlInject)}
                      />
                      <button
                        type="button"
                        onClick={() => handleASINSelect(param)}
                        className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
                        title="Select ASINs from catalog"
                      >
                        <Package className="w-4 h-4" />
                        Select
                      </button>
                    </div>
                  ) : paramType === 'campaign' ? (
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={
                          value && typeof value === 'object' && '_sqlInject' in value && value._sqlInject 
                            ? `${(value as any)._values.length} campaigns (SQL injection mode)`
                            : Array.isArray(value) ? value.join(', ') : (value as string)
                        }
                        onChange={(e) => handleParameterChange(param, e.target.value)}
                        placeholder="Enter Campaign IDs or select from list"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        readOnly={Boolean(value && typeof value === 'object' && '_sqlInject' in value && (value as any)._sqlInject)}
                      />
                      <button
                        type="button"
                        onClick={() => handleCampaignSelect(param)}
                        className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
                        title="Select campaigns from instance"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        Select
                      </button>
                    </div>
                  ) : paramType === 'date' ? (
                    <input
                      type="date"
                      value={value as string}
                      onChange={(e) => handleParameterChange(param, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  ) : paramType === 'number' ? (
                    <input
                      type="number"
                      value={typeof value === 'number' ? value : 0}
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
                  ) : (param.toLowerCase().includes('pattern') || param.toLowerCase().includes('like')) ? (
                    <div>
                      <input
                        type="text"
                        value={typeof value === 'string' ? value : ''}
                        onChange={(e) => handleParameterChange(param, e.target.value)}
                        placeholder="Enter pattern (will be wrapped with %...%)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      />
                      {typeof value === 'string' && value.length > 0 && (
                        <p className="mt-1 text-xs text-gray-500">
                          Will be formatted as: <code className="bg-gray-100 px-1 py-0.5 rounded">%{value}%</code>
                        </p>
                      )}
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={value as string}
                      onChange={(e) => handleParameterChange(param, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  )}
                </div>
              );
            })}
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
              Export Name
            </label>
            <input
              type="text"
              value={state.exportSettings.name}
              onChange={(e) => handleExportSettingChange('name', e.target.value)}
              placeholder="Auto-generated: [Query Name] - [Instance] - [Date Range] - [Date and Time Ran]"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Automatically generated based on query name, instance, date range, and execution time. You can customize if needed.
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
      
      {/* ASIN Selection Modal */}
      <ASINSelectionModal
        isOpen={showASINModal}
        onClose={() => {
          setShowASINModal(false);
          setCurrentASINParam(null);
        }}
        onSelect={handleASINModalConfirm}
        currentValue={currentASINParam ? state.parameters[currentASINParam] : []}
        multiple={true}
        title={`Select ASINs for {{${currentASINParam || 'parameter'}}}`}
        defaultBrand=""
        brandLocked={false}
      />

      {/* Campaign Selection Modal */}
      <CampaignSelectionModal
        isOpen={showCampaignModal}
        onClose={() => {
          setShowCampaignModal(false);
          setCurrentCampaignParam(null);
        }}
        onSelect={handleCampaignModalConfirm}
        instanceId={state.instanceId}
        currentValue={currentCampaignParam ? state.parameters[currentCampaignParam] : []}
        multiple={true}
        title={`Select Campaigns for {{${currentCampaignParam || 'parameter'}}}`}
        valueType={currentCampaignParam?.toLowerCase().includes('name') ? 'names' : 'ids'}
      />
    </>
  );
}