import { useState, useEffect, useMemo } from 'react';
import { X, ChevronLeft, ChevronRight, Play, Clock, Calendar, Database, Code, Library, Search, Tag, GitBranch, BarChart3, Link } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import DynamicParameterForm from './DynamicParameterForm';
import InstanceSelector from '../query-builder/InstanceSelector';
// import { UniversalParameterSelector } from '../parameter-detection';
import { EnhancedParameterSelector } from '../parameter-detection/EnhancedParameterSelector';
import TemplateForkDialog from '../query-library/TemplateForkDialog';
import TemplateTagsManager from '../query-library/TemplateTagsManager';
import TemplatePerformanceMetrics from '../query-library/TemplatePerformanceMetrics';
import { ParameterDetector } from '../../utils/parameterDetection';
// import { ParameterProcessor } from '../../utils/parameterProcessor';
import { detectParametersWithContext, replaceParametersInSQL, analyzeParameterContext } from '../../utils/sqlParameterAnalyzer';
import { instanceService } from '../../services/instanceService';
import { queryTemplateService } from '../../services/queryTemplateService';
import { useInstanceMappings } from '../../hooks/useInstanceMappings';
import { autoPopulateParameters, extractParameterValues } from '../../utils/parameterAutoPopulator';
import toast from 'react-hot-toast';
import SQLEditor from '../common/SQLEditor';
import type { QueryTemplate } from '../../types/queryTemplate';
import type { CreateReportRequest, ScheduleConfig } from '../../types/report';
import type { DetectedParameter } from '../../utils/parameterDetection';

interface RunReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  template?: QueryTemplate | null;
  onSubmit: (config: CreateReportRequest) => void;
  includeTemplateStep?: boolean;
}

type ExecutionType = 'once' | 'recurring' | 'backfill';
type WizardStep = 'template' | 'parameters' | 'execution' | 'schedule' | 'review';
type TemplateSelectionMode = 'library' | 'custom';

const getWizardSteps = (includeTemplate: boolean): { id: WizardStep; label: string; icon: any }[] => {
  const steps = [];
  if (includeTemplate) {
    steps.push({ id: 'template' as WizardStep, label: 'Template Selection', icon: Library });
  }
  steps.push(
    { id: 'parameters' as WizardStep, label: 'Parameters', icon: Play },
    { id: 'execution' as WizardStep, label: 'Execution Type', icon: Clock },
    { id: 'schedule' as WizardStep, label: 'Schedule', icon: Calendar },
    { id: 'review' as WizardStep, label: 'Review', icon: Database }
  );
  return steps;
};

export default function RunReportModal({
  isOpen,
  onClose,
  template: initialTemplate,
  onSubmit,
  includeTemplateStep: includeTemplateStepProp = false,
}: RunReportModalProps) {
  // Template selection state
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(initialTemplate || null);
  const [templateSelectionMode, setTemplateSelectionMode] = useState<TemplateSelectionMode>('library');
  const [customSql, setCustomSql] = useState('');
  const [templateSearch, setTemplateSearch] = useState('');
  const [templateCategory, setTemplateCategory] = useState('');

  // Determine if we need the template selection step
  const includeTemplateStep = includeTemplateStepProp || !initialTemplate;
  const WIZARD_STEPS = getWizardSteps(includeTemplateStep);

  const [currentStep, setCurrentStep] = useState<WizardStep>(includeTemplateStep ? 'template' : 'parameters');
  const [reportName, setReportName] = useState(initialTemplate ? `${initialTemplate.name} Report` : 'Custom Report');
  const [reportDescription, setReportDescription] = useState(initialTemplate?.description || '');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [executionType, setExecutionType] = useState<ExecutionType>('once');
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    frequency: 'daily',
    time: '09:00',
  });
  const [backfillPeriod, setBackfillPeriod] = useState(7);
  const [selectedInstance, setSelectedInstance] = useState('');
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);
  const [showQueryPreview, setShowQueryPreview] = useState(true);
  const [showForkDialog, setShowForkDialog] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [templateToFork, setTemplateToFork] = useState<QueryTemplate | null>(null);
  const [hasAutoPopulated, setHasAutoPopulated] = useState(false);

  // Fetch instance mappings for auto-population
  const { data: instanceMappings, isLoading: loadingMappings, refetch: refetchMappings } = useInstanceMappings(selectedInstance, isOpen);

  // Refetch mappings when instance changes to get latest data
  useEffect(() => {
    if (selectedInstance && isOpen) {
      console.log('[RunReportModal] Refetching mappings for instance:', selectedInstance);
      refetchMappings();
    }
  }, [selectedInstance, isOpen, refetchMappings]);

  // Snowflake integration state
  const [snowflakeEnabled, setSnowflakeEnabled] = useState(false);
  const [snowflakeTableName, setSnowflakeTableName] = useState('');
  const [snowflakeSchemaName, setSnowflakeSchemaName] = useState('');

  // Date range state for ad-hoc execution
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return {
      start: thirtyDaysAgo.toISOString().split('T')[0],
      end: today.toISOString().split('T')[0]
    };
  });

  // Rolling window state
  const [useRollingWindow, setUseRollingWindow] = useState(false);
  const [rollingWindowDays, setRollingWindowDays] = useState(30);

  // Update date range when rolling window changes
  useEffect(() => {
    if (useRollingWindow) {
      const today = new Date();
      const AMC_LAG_DAYS = 14;
      const endDate = new Date(today);
      endDate.setDate(endDate.getDate() - AMC_LAG_DAYS);

      const startDate = new Date(endDate);
      startDate.setDate(startDate.getDate() - rollingWindowDays);

      setDateRange({
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0]
      });
    }
  }, [useRollingWindow, rollingWindowDays]);

  // Fetch instances
  const { data: instances = [], isLoading: loadingInstances } = useQuery({
    queryKey: ['instances'],
    queryFn: () => instanceService.list(),
    enabled: isOpen,
  });

  // Fetch templates for selection
  const { data: templatesData, isLoading: loadingTemplates } = useQuery({
    queryKey: ['queryTemplates', templateCategory, templateSearch],
    queryFn: () => queryTemplateService.listTemplates(true, {
      category: templateCategory || undefined,
      search: templateSearch || undefined,
      include_public: true,
      sort_by: 'usage_count',
    }),
    enabled: isOpen && includeTemplateStep && currentStep === 'template',
  });

  const templates = templatesData?.data?.templates || [];

  // Detect parameters from the SQL query with enhanced context awareness
  useEffect(() => {
    const currentTemplate = selectedTemplate || initialTemplate;
    if (currentTemplate && isOpen) {
      const sqlQuery = currentTemplate.sqlTemplate || currentTemplate.sql_query || '';
      if (sqlQuery) {
        // Use both detection methods for maximum compatibility
        const basicDetected = ParameterDetector.detectParameters(sqlQuery);
        const contextDetected = detectParametersWithContext(sqlQuery);

        // Merge detection results, preferring context-aware detection
        const mergedDetection = basicDetected.map(basic => {
          const contextParam = contextDetected.find(c => c.name === basic.name);
          if (contextParam) {
            return {
              ...basic,
              type: contextParam.type as any,
              // sqlContext and formatPattern come from context analysis
              // not from the basic detected parameter
            };
          }
          return basic;
        });

        setDetectedParameters(mergedDetection);

        // Initialize parameters with smart defaults based on type
        const defaultParams: Record<string, any> = {};
        mergedDetection.forEach(param => {
          if (currentTemplate.defaultParameters?.[param.name] !== undefined) {
            defaultParams[param.name] = currentTemplate.defaultParameters[param.name];
          } else if (currentTemplate.parameters?.[param.name] !== undefined) {
            defaultParams[param.name] = currentTemplate.parameters[param.name];
          } else {
            // Set intelligent defaults based on parameter type
            const context = analyzeParameterContext(sqlQuery, param.name);
            if (context.type === 'date') {
              const today = new Date();
              const thirtyDaysAgo = new Date(today);
              thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

              // Check if this is a start or end date
              if (param.name.toLowerCase().includes('start')) {
                defaultParams[param.name] = thirtyDaysAgo.toISOString().split('T')[0];
              } else if (param.name.toLowerCase().includes('end')) {
                defaultParams[param.name] = today.toISOString().split('T')[0];
              } else {
                defaultParams[param.name] = today.toISOString().split('T')[0];
              }
            } else if (context.type === 'number') {
              defaultParams[param.name] = 100;
            } else if (context.type === 'list' || param.type === 'asin_list' || param.type === 'campaign_list') {
              defaultParams[param.name] = [];
            } else {
              defaultParams[param.name] = '';
            }
          }
        });
        setParameters(defaultParams);
      }
    } else if (customSql && templateSelectionMode === 'custom') {
      // Real-time parameter detection for custom SQL
      const contextDetected = detectParametersWithContext(customSql);
      const basicDetected = ParameterDetector.detectParameters(customSql);

      // Merge with context awareness
      const mergedDetection = basicDetected.map(basic => {
        const contextParam = contextDetected.find(c => c.name === basic.name);
        if (contextParam) {
          return {
            ...basic,
            type: contextParam.type as any,
            // sqlContext and formatPattern come from context analysis
            // not from the basic detected parameter
          };
        }
        return basic;
      });

      setDetectedParameters(mergedDetection);
    }
  }, [selectedTemplate, initialTemplate, customSql, templateSelectionMode, isOpen]);

  // Auto-populate parameters from instance mappings
  useEffect(() => {
    if (instanceMappings && detectedParameters.length > 0 && selectedInstance && !hasAutoPopulated) {
      // Map parameter names based on detected parameter types
      const parameterNameMap: { brands?: string; asins?: string; campaigns?: string } = {};

      console.log('[RunReportModal] Auto-population check:', {
        detectedParameters: detectedParameters.map(p => ({ name: p.name, type: p.type })),
        instanceMappings,
        selectedInstance,
        hasASINs: instanceMappings?.asins_by_brand ? Object.keys(instanceMappings.asins_by_brand).length : 0,
        hasCampaigns: instanceMappings?.campaigns_by_brand ? Object.keys(instanceMappings.campaigns_by_brand).length : 0,
        rawMappingsData: JSON.stringify(instanceMappings),
      });

      // Log ASIN details if we have them
      if (instanceMappings?.asins_by_brand) {
        console.log('[RunReportModal] ASINs by brand:', instanceMappings.asins_by_brand);
        Object.entries(instanceMappings.asins_by_brand).forEach(([brand, asins]) => {
          console.log(`  - ${brand}: ${Array.isArray(asins) ? asins.length : 0} ASINs`);
        });
      }

      // Log campaign details if we have them
      if (instanceMappings?.campaigns_by_brand) {
        console.log('[RunReportModal] Campaigns by brand:', instanceMappings.campaigns_by_brand);
        Object.entries(instanceMappings.campaigns_by_brand).forEach(([brand, campaigns]) => {
          console.log(`  - ${brand}: ${Array.isArray(campaigns) ? campaigns.length : 0} campaigns`);
        });
      }

      detectedParameters.forEach(param => {
        const lowerName = param.name.toLowerCase();
        const paramType = param.type as string;

        // Check for ASIN parameters - be more flexible with naming
        if (paramType === 'asin' || paramType === 'asin_list' ||
            lowerName.includes('asin') || lowerName.includes('tracked')) {
          parameterNameMap.asins = param.name;
          console.log('[RunReportModal] Matched ASIN parameter:', param.name);
        }
        // Check for campaign parameters
        else if (paramType === 'campaign' || paramType === 'campaign_list' ||
                 lowerName.includes('campaign')) {
          parameterNameMap.campaigns = param.name;
          console.log('[RunReportModal] Matched campaign parameter:', param.name);
        }
        // Check for brand parameters
        else if (lowerName.includes('brand')) {
          parameterNameMap.brands = param.name;
          console.log('[RunReportModal] Matched brand parameter:', param.name);
        }
      });

      console.log('[RunReportModal] Parameter name map:', parameterNameMap);

      // Only auto-populate if we have mappings and relevant parameters
      if (Object.keys(parameterNameMap).length > 0) {
        console.log('[RunReportModal] Calling autoPopulateParameters with:', {
          instanceMappings,
          currentParameters: parameters,
          parameterNameMap,
        });

        const autoPopulated = autoPopulateParameters(instanceMappings, parameters, parameterNameMap);
        console.log('[RunReportModal] autoPopulated result:', autoPopulated);

        const newValues = extractParameterValues(autoPopulated);

        console.log('[RunReportModal] Auto-populated values:', newValues);
        console.log('[RunReportModal] Current parameters:', parameters);

        // Check if any values were actually auto-populated
        const hasNewValues = Object.keys(parameterNameMap).some(key => {
          const paramName = parameterNameMap[key as keyof typeof parameterNameMap];
          if (!paramName) return false;

          const newValue = newValues[paramName];
          const currentValue = parameters[paramName];

          console.log(`[RunReportModal] Checking ${paramName}:`, { newValue, currentValue });

          // Check if current value is effectively empty
          const currentIsEmpty = !currentValue ||
                                currentValue === '' ||
                                (Array.isArray(currentValue) && currentValue.length === 0);

          console.log(`[RunReportModal]   currentIsEmpty: ${currentIsEmpty}`);

          // Has new value if:
          // 1. Current is empty AND new value is array with items
          // 2. Current is empty AND new value is non-empty string/value
          if (currentIsEmpty) {
            if (Array.isArray(newValue) && newValue.length > 0) {
              console.log(`[RunReportModal] ✓ ${paramName} has new array values (${newValue.length} items)`);
              return true;
            }
            if (newValue && !Array.isArray(newValue) && newValue !== '') {
              console.log(`[RunReportModal] ✓ ${paramName} has new value`);
              return true;
            }
          }

          console.log(`[RunReportModal] ✗ ${paramName} skipped (already has value or no new value)`);
          return false;
        });

        console.log('[RunReportModal] Has new values to populate?', hasNewValues);

        if (hasNewValues) {
          setParameters(newValues);
          setHasAutoPopulated(true);
          toast.success('Parameters populated from instance mappings', { icon: '🔗' });
        } else {
          console.log('[RunReportModal] No new values to auto-populate');
        }
      }
    }
  }, [instanceMappings, detectedParameters, selectedInstance, hasAutoPopulated, parameters]);

  // Reset auto-populate flag when instance changes
  useEffect(() => {
    setHasAutoPopulated(false);
  }, [selectedInstance]);

  // Generate preview SQL with context-aware parameter substitution
  const previewSQL = useMemo(() => {
    const currentTemplate = selectedTemplate || initialTemplate;
    const sql = templateSelectionMode === 'custom' ? customSql :
                (currentTemplate?.sqlTemplate || currentTemplate?.sql_query || '');

    if (!sql) return '';

    try {
      // Check if all required parameters are provided
      const hasAllParams = detectedParameters.every(param =>
        parameters[param.name] !== undefined && parameters[param.name] !== '' &&
        (Array.isArray(parameters[param.name]) ? parameters[param.name].length > 0 : true)
      );

      if (hasAllParams) {
        // Use context-aware replacement for accurate preview
        return replaceParametersInSQL(sql, parameters);
      } else {
        // Show SQL with highlighted parameters that need values
        return sql.replace(/\{\{(\w+)\}\}/g, (match, paramName) => {
          const value = parameters[paramName];
          if (value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
            return `/* ${match} - Required */`;
          }
          // Show the actual substituted value for filled parameters
          // const context = analyzeParameterContext(sql, paramName);
          const formattedValue = replaceParametersInSQL(`{{${paramName}}}`, { [paramName]: value });
          return formattedValue;
        });
      }
    } catch (error) {
      console.warn('Parameter processing error:', error);
      // Fallback to showing placeholders
      return sql.replace(/\{\{(\w+)\}\}/g, (_match, paramName) => {
        return `/* Parameter: ${paramName} (not set) */`;
      });
    }
  }, [selectedTemplate, initialTemplate, customSql, templateSelectionMode, parameters, detectedParameters]);

  if (!isOpen) return null;

  const currentStepIndex = WIZARD_STEPS.findIndex((s) => s.id === currentStep);
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStep === 'review';

  const goToNextStep = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < WIZARD_STEPS.length) {
      // Skip schedule step if execution type is 'once'
      if (WIZARD_STEPS[nextIndex].id === 'schedule' && executionType === 'once') {
        setCurrentStep('review');
      } else {
        setCurrentStep(WIZARD_STEPS[nextIndex].id);
      }
    }
  };

  const goToPreviousStep = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      // Skip schedule step if execution type is 'once'
      if (WIZARD_STEPS[prevIndex].id === 'schedule' && executionType === 'once') {
        setCurrentStep('execution');
      } else {
        setCurrentStep(WIZARD_STEPS[prevIndex].id);
      }
    }
  };

  const handleParameterSubmit = (values: Record<string, any>) => {
    // No need to extract instance_id separately as it's managed by selectedInstance state
    setParameters(values);
    goToNextStep();
  };

  const handleParameterChange = (paramName: string, value: any) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const handleTemplateSelect = async (template: QueryTemplate) => {
    setSelectedTemplate(template);
    setReportName(`${template.name} Report`);
    setReportDescription(template.description || '');

    // Increment usage count
    try {
      await queryTemplateService.incrementUsage(template.id);
    } catch (error) {
      console.error('Failed to increment template usage:', error);
    }
  };

  const handleCustomSqlSubmit = () => {
    // Create a pseudo-template from custom SQL
    const customTemplate: QueryTemplate = {
      id: 'custom',
      name: 'Custom Query',
      description: reportDescription,
      sqlTemplate: customSql,
      sql_query: customSql,
      category: 'custom',
      report_type: 'custom',
      parameters: {},
      parameter_definitions: {},
      ui_schema: {},
      instance_types: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setSelectedTemplate(customTemplate);
    goToNextStep();
  };

  const handleFinalSubmit = () => {
    console.log('handleFinalSubmit called');

    // Validate required fields
    if (!reportName) {
      alert('Please enter a report name');
      return;
    }

    if (!selectedInstance) {
      alert('Please select an AMC instance');
      return;
    }

    const currentTemplate = selectedTemplate || initialTemplate;

    // For recurring schedules, filter out date parameters since they'll be calculated dynamically
    // Keep only non-date parameters (ASINs, campaigns, brands, etc.)
    const parametersToSubmit = executionType === 'recurring'
      ? Object.fromEntries(
          Object.entries(parameters).filter(([key]) =>
            !key.toLowerCase().includes('date') &&
            !key.toLowerCase().includes('start') &&
            !key.toLowerCase().includes('end')
          )
        )
      : parameters;

    // For custom reports without a template
    if (!currentTemplate || currentTemplate.id === 'custom' || templateSelectionMode === 'custom') {
      if (!customSql) {
        alert('Please enter SQL query for custom report');
        return;
      }

      const config: CreateReportRequest = {
        name: reportName,
        description: reportDescription,
        template_id: undefined,
        custom_sql: customSql,
        instance_id: selectedInstance,
        parameters: parametersToSubmit,
        execution_type: executionType === 'backfill' ? 'backfill' : executionType,
        schedule_config:
          executionType === 'recurring'
            ? { ...scheduleConfig, lookback_days: useRollingWindow ? rollingWindowDays : undefined }
            : executionType === 'backfill'
            ? { ...scheduleConfig, backfill_period: backfillPeriod }
            : undefined,
        // Add date range for ad-hoc execution
        time_window_start: executionType === 'once' ? dateRange.start : undefined,
        time_window_end: executionType === 'once' ? dateRange.end : undefined,
        // Add rolling window metadata for once execution
        ...(executionType === 'once' && useRollingWindow ? { lookback_days: rollingWindowDays } : {}),
        // Snowflake integration options
        snowflake_enabled: snowflakeEnabled,
        snowflake_table_name: snowflakeTableName || undefined,
        snowflake_schema_name: snowflakeSchemaName || undefined,
      };
      console.log('Submitting custom report config:', config);
      onSubmit(config);
      return;
    }

    // For template-based reports
    const config: CreateReportRequest = {
      name: reportName,
      description: reportDescription,
      template_id: currentTemplate.id,
      custom_sql: undefined,
      instance_id: selectedInstance,
      parameters: parametersToSubmit,
      execution_type: executionType === 'backfill' ? 'backfill' : executionType,
      schedule_config:
        executionType === 'recurring'
          ? { ...scheduleConfig, lookback_days: useRollingWindow ? rollingWindowDays : undefined }
          : executionType === 'backfill'
          ? { ...scheduleConfig, backfill_period: backfillPeriod }
          : undefined,
      // Add date range for ad-hoc execution
      time_window_start: executionType === 'once' ? dateRange.start : undefined,
      time_window_end: executionType === 'once' ? dateRange.end : undefined,
      // Add rolling window metadata for once execution
      ...(executionType === 'once' && useRollingWindow ? { lookback_days: rollingWindowDays } : {}),
      // Snowflake integration options
      snowflake_enabled: snowflakeEnabled,
      snowflake_table_name: snowflakeTableName || undefined,
      snowflake_schema_name: snowflakeSchemaName || undefined,
    };
    console.log('Submitting template report config:', config);
    onSubmit(config);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'template':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select Query Template</h3>
              <p className="text-sm text-gray-500">
                Choose from the Query Library or write your own custom SQL query.
              </p>
            </div>

            {/* Template Mode Selection */}
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="templateMode"
                  value="library"
                  checked={templateSelectionMode === 'library'}
                  onChange={(e) => setTemplateSelectionMode(e.target.value as TemplateSelectionMode)}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-900">Choose from Query Library</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="templateMode"
                  value="custom"
                  checked={templateSelectionMode === 'custom'}
                  onChange={(e) => setTemplateSelectionMode(e.target.value as TemplateSelectionMode)}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-900">Write Custom SQL</span>
              </label>
            </div>

            {/* Template Library Selection */}
            {templateSelectionMode === 'library' && (
              <div className="space-y-4">
                {/* Search and Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="template-search" className="sr-only">Search templates</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        id="template-search"
                        type="text"
                        value={templateSearch}
                        onChange={(e) => setTemplateSearch(e.target.value)}
                        placeholder="Search templates..."
                        className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md text-sm
                                 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="category" className="sr-only">Category</label>
                    <select
                      id="category"
                      value={templateCategory}
                      onChange={(e) => setTemplateCategory(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="">All Categories</option>
                      <option value="performance">Performance Analysis</option>
                      <option value="attribution">Attribution</option>
                      <option value="audience">Audience Building</option>
                      <option value="incrementality">Incrementality</option>
                      <option value="cross-channel">Cross-Channel</option>
                      <option value="optimization">Optimization</option>
                    </select>
                  </div>
                </div>

                {/* Template Grid */}
                {loadingTemplates ? (
                  <div className="text-center py-8">
                    <div className="inline-flex items-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                      <span className="ml-2 text-sm text-gray-500">Loading templates...</span>
                    </div>
                  </div>
                ) : templates.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No templates found. Try adjusting your search or filters.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
                    {templates.map((tmpl) => (
                      <div
                        key={tmpl.id}
                        role="button"
                        onClick={() => handleTemplateSelect(tmpl)}
                        className={`p-4 border rounded-lg cursor-pointer transition-all
                                   ${selectedTemplate?.id === tmpl.id
                                     ? 'border-indigo-500 bg-indigo-50'
                                     : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'}`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium text-gray-900">{tmpl.name}</h4>
                          {/* Difficulty level badge would go here if available */}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{tmpl.description}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex gap-2">
                            {tmpl.tags?.slice(0, 2).map((tag) => (
                              <span key={tag} className="inline-flex items-center gap-1 text-xs text-gray-500">
                                <Tag className="h-3 w-3" />
                                {tag}
                              </span>
                            ))}
                          </div>
                          {tmpl.usageCount !== undefined && (
                            <span className="text-xs text-gray-500">{tmpl.usageCount} uses</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* SQL Preview for Selected Template */}
                {selectedTemplate && templateSelectionMode === 'library' && (
                  <div className="border-t pt-4 space-y-4">
                    {/* Template Actions */}
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setShowMetrics(!showMetrics)}
                        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md
                                 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <BarChart3 className="h-4 w-4" />
                        {showMetrics ? 'Hide' : 'Show'} Metrics
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setTemplateToFork(selectedTemplate);
                          setShowForkDialog(true);
                        }}
                        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md
                                 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <GitBranch className="h-4 w-4" />
                        Fork Template
                      </button>
                    </div>

                    {/* Performance Metrics */}
                    {showMetrics && (
                      <div className="border border-gray-200 rounded-lg p-4">
                        <TemplatePerformanceMetrics
                          template={selectedTemplate}
                          templateId={selectedTemplate.id}
                          showDetails={true}
                        />
                      </div>
                    )}

                    {/* Tags Display */}
                    <div className="border border-gray-200 rounded-lg p-4">
                      <TemplateTagsManager
                        template={selectedTemplate}
                        onUpdate={() => {}}
                        readOnly={true}
                      />
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">SQL Preview</h4>
                      <div className="border border-gray-200 rounded-lg overflow-hidden">
                        <SQLEditor
                          value={selectedTemplate.sqlTemplate || selectedTemplate.sql_query || ''}
                          onChange={() => {}}
                          height="200px"
                          readOnly={true}
                        />
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => goToNextStep()}
                      disabled={!selectedTemplate}
                      className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                               hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Use This Template
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Custom SQL Editor */}
            {templateSelectionMode === 'custom' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Custom SQL Query</label>
                  <SQLEditor
                    value={customSql}
                    onChange={setCustomSql}
                    height="300px"
                  />
                </div>

                {/* Detected Parameters with Context */}
                {detectedParameters.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Detected Parameters ({detectedParameters.length})
                    </h4>
                    <div className="space-y-2">
                      {detectedParameters.map((param) => {
                        const context = analyzeParameterContext(customSql, param.name);
                        return (
                          <div key={param.name} className="flex items-start gap-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 text-sm">
                              <Code className="h-3 w-3 mr-1" />
                              {param.name}
                            </span>
                            <div className="flex-1 text-xs text-gray-500">
                              <span className="font-medium">Type:</span> {param.type || context.type}
                              {context.formatHint && (
                                <span className="ml-2">• {context.formatHint}</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Report Name and Description */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Report Name</label>
                    <input
                      type="text"
                      value={reportName}
                      onChange={(e) => setReportName(e.target.value)}
                      placeholder="Enter report name..."
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <textarea
                      value={reportDescription}
                      onChange={(e) => setReportDescription(e.target.value)}
                      placeholder="Describe your report..."
                      rows={2}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleCustomSqlSubmit}
                  disabled={!customSql.trim() || !reportName.trim()}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                           hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Continue with Custom Query
                </button>
              </div>
            )}
          </div>
        );

      case 'parameters':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Configure Parameters</h3>
              <p className="text-sm text-gray-500">
                Set the parameters for your report based on the template requirements.
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Report Name</label>
                <input
                  type="text"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                           focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={reportDescription}
                  onChange={(e) => setReportDescription(e.target.value)}
                  rows={2}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                           focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              {/* Instance Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AMC Instance <span className="text-red-500">*</span>
                </label>
                {loadingInstances ? (
                  <div className="text-sm text-gray-500">Loading instances...</div>
                ) : (
                  <InstanceSelector
                    instances={instances}
                    value={selectedInstance}
                    onChange={setSelectedInstance}
                    placeholder="Select an AMC instance..."
                  />
                )}
              </div>
            </div>

            <div className="border-t pt-4">
              {/* Auto-population indicator and loading state */}
              {loadingMappings && selectedInstance && (
                <div className="mb-3 text-xs text-blue-600 flex items-center gap-2">
                  <div className="animate-spin h-3 w-3 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  Loading instance mappings...
                </div>
              )}
              {hasAutoPopulated && instanceMappings && (
                <div className="mb-3 flex items-center gap-1 px-3 py-2 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
                  <Link className="h-4 w-4" />
                  Parameters auto-populated from instance mappings
                </div>
              )}

              {/* If template has predefined parameter definitions, use DynamicParameterForm */}
              {(selectedTemplate || initialTemplate)?.parameter_definitions &&
               Object.keys((selectedTemplate || initialTemplate)?.parameter_definitions || {}).length > 0 ? (
                <DynamicParameterForm
                  parameterDefinitions={(selectedTemplate || initialTemplate)?.parameter_definitions || {}}
                  uiSchema={(selectedTemplate || initialTemplate)?.ui_schema || {}}
                  initialValues={parameters}
                  onSubmit={handleParameterSubmit}
                  submitLabel="Next"
                />
              ) : detectedParameters.length > 0 ? (
                /* Use detected parameters from SQL query */
                <div className="space-y-4">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    Query Parameters
                  </div>
                  {detectedParameters.map((param) => (
                    <div key={param.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {param.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </label>
                      <EnhancedParameterSelector
                        parameter={{
                          name: param.name,
                          type: param.type as any,
                          required: true,
                          // Additional context fields would be populated from analysis
                          // sqlContext, formatPattern, description
                        }}
                        instanceId={selectedInstance}
                        value={parameters[param.name]}
                        onChange={(value) => handleParameterChange(param.name, value)}
                      />
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => handleParameterSubmit(parameters)}
                    disabled={!selectedInstance}
                    className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                             hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              ) : (
                /* No parameters needed */
                <div className="text-sm text-gray-500">
                  No parameters required for this template.
                  <button
                    type="button"
                    onClick={() => handleParameterSubmit({})}
                    disabled={!selectedInstance}
                    className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                             hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                             disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        );

      case 'execution':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select Execution Type</h3>
              <p className="text-sm text-gray-500">
                Choose how you want to run this report.
              </p>
            </div>

            <div className="space-y-3">
              <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="executionType"
                  value="once"
                  checked={executionType === 'once'}
                  onChange={(e) => setExecutionType(e.target.value as ExecutionType)}
                  className="mt-1 text-indigo-600 focus:ring-indigo-500"
                />
                <div className="ml-3">
                  <div className="font-medium text-gray-900">Run Once</div>
                  <div className="text-sm text-gray-500">
                    Execute the report immediately with the specified parameters
                  </div>
                </div>
              </label>

              <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="executionType"
                  value="recurring"
                  checked={executionType === 'recurring'}
                  onChange={(e) => setExecutionType(e.target.value as ExecutionType)}
                  className="mt-1 text-indigo-600 focus:ring-indigo-500"
                />
                <div className="ml-3">
                  <div className="font-medium text-gray-900">Recurring Schedule</div>
                  <div className="text-sm text-gray-500">
                    Run the report automatically on a regular schedule
                  </div>
                </div>
              </label>

              <label className="flex items-start p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="executionType"
                  value="backfill"
                  checked={executionType === 'backfill'}
                  onChange={(e) => setExecutionType(e.target.value as ExecutionType)}
                  className="mt-1 text-indigo-600 focus:ring-indigo-500"
                />
                <div className="ml-3">
                  <div className="font-medium text-gray-900">Backfill Historical Data</div>
                  <div className="text-sm text-gray-500">
                    Run the report for historical data over a specified period
                  </div>
                </div>
              </label>
            </div>

            {/* Date Range Selection for Run Once */}
            {executionType === 'once' && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Date Range</h4>
                <p className="text-xs text-gray-500 mb-3">
                  Select the date range for this ad-hoc execution. Note: AMC has a 14-day data lag.
                </p>

                {/* Rolling Window Toggle */}
                <div className="mb-4 flex items-center">
                  <input
                    type="checkbox"
                    id="use-rolling-window"
                    checked={useRollingWindow}
                    onChange={(e) => setUseRollingWindow(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="use-rolling-window" className="ml-2 block text-sm text-gray-900">
                    Use Rolling Window
                    <span className="ml-2 text-xs text-gray-500">
                      (automatically calculates dates accounting for AMC lag)
                    </span>
                  </label>
                </div>

                {/* Rolling Window Size Selector */}
                {useRollingWindow && (
                  <div className="mb-4">
                    <label htmlFor="window-size" className="block text-sm font-medium text-gray-700 mb-2">
                      Window Size (days)
                    </label>
                    <div className="flex gap-2">
                      {[7, 14, 30, 60, 90].map(days => (
                        <button
                          key={days}
                          type="button"
                          onClick={() => setRollingWindowDays(days)}
                          className={`px-3 py-2 text-sm rounded-md border ${
                            rollingWindowDays === days
                              ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          {days} days
                        </button>
                      ))}
                      <input
                        type="number"
                        id="window-size"
                        min="1"
                        max="365"
                        value={rollingWindowDays}
                        onChange={(e) => setRollingWindowDays(parseInt(e.target.value) || 30)}
                        className="w-24 px-3 py-2 text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Custom"
                      />
                    </div>
                    <p className="mt-2 text-xs text-gray-500">
                      Calculated range: {dateRange.start} to {dateRange.end} (accounting for 14-day lag)
                    </p>
                  </div>
                )}

                {/* Manual Date Pickers */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">
                      Start Date
                    </label>
                    <input
                      type="date"
                      id="start-date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                      disabled={useRollingWindow}
                      className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 ${
                        useRollingWindow ? 'bg-gray-100 cursor-not-allowed' : ''
                      }`}
                    />
                  </div>
                  <div>
                    <label htmlFor="end-date" className="block text-sm font-medium text-gray-700">
                      End Date
                    </label>
                    <input
                      type="date"
                      id="end-date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                      min={dateRange.start}
                      disabled={useRollingWindow}
                      className={`mt-1 block w-full border-gray-300 rounded-md shadow-sm sm:text-sm focus:ring-indigo-500 focus:border-indigo-500 ${
                        useRollingWindow ? 'bg-gray-100 cursor-not-allowed' : ''
                      }`}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Snowflake Integration for Run Once */}
            {executionType === 'once' && (
              <div className="mt-4 space-y-4">
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Data Storage Options</h4>
                  <p className="text-xs text-gray-500 mb-3">
                    Choose where to store your execution results.
                  </p>
                </div>

                {/* Snowflake Toggle */}
                <div className="flex items-start p-4 border rounded-lg">
                  <input
                    type="checkbox"
                    id="snowflakeEnabled"
                    checked={snowflakeEnabled}
                    onChange={(e) => setSnowflakeEnabled(e.target.checked)}
                    className="mt-1 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div className="ml-3 flex-1">
                    <label htmlFor="snowflakeEnabled" className="text-sm font-medium text-gray-900 cursor-pointer">
                      Upload to Snowflake Data Warehouse
                    </label>
                    <p className="text-xs text-gray-500 mt-1">
                      Store execution results in your Snowflake data warehouse for advanced analytics and reporting.
                    </p>
                  </div>
                </div>

                {/* Snowflake Configuration Fields */}
                {snowflakeEnabled && (
                  <div className="ml-7 space-y-3 border-l-2 border-indigo-200 pl-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Table Name (Optional)
                      </label>
                      <input
                        type="text"
                        value={snowflakeTableName}
                        onChange={(e) => setSnowflakeTableName(e.target.value)}
                        placeholder="Leave empty for auto-generated name"
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                                 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        If empty, a table name will be generated automatically
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Schema Name (Optional)
                      </label>
                      <input
                        type="text"
                        value={snowflakeSchemaName}
                        onChange={(e) => setSnowflakeSchemaName(e.target.value)}
                        placeholder="Leave empty for default schema"
                        className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                                 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        If empty, the default schema will be used
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 'schedule':
        if (executionType === 'recurring') {
          return (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Configure Schedule</h3>
                <p className="text-sm text-gray-500">
                  Set when and how often the report should run.
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Frequency</label>
                  <select
                    value={scheduleConfig.frequency}
                    onChange={(e) =>
                      setScheduleConfig({ ...scheduleConfig, frequency: e.target.value as any })
                    }
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Time</label>
                  <input
                    type="time"
                    value={scheduleConfig.time}
                    onChange={(e) =>
                      setScheduleConfig({ ...scheduleConfig, time: e.target.value })
                    }
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>

                {scheduleConfig.frequency === 'weekly' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Day of Week</label>
                    <select
                      value={scheduleConfig.day_of_week || 1}
                      onChange={(e) =>
                        setScheduleConfig({
                          ...scheduleConfig,
                          day_of_week: parseInt(e.target.value),
                        })
                      }
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="0">Sunday</option>
                      <option value="1">Monday</option>
                      <option value="2">Tuesday</option>
                      <option value="3">Wednesday</option>
                      <option value="4">Thursday</option>
                      <option value="5">Friday</option>
                      <option value="6">Saturday</option>
                    </select>
                  </div>
                )}

                {scheduleConfig.frequency === 'monthly' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Day of Month</label>
                    <input
                      type="number"
                      min="1"
                      max="31"
                      value={scheduleConfig.day_of_month || 1}
                      onChange={(e) =>
                        setScheduleConfig({
                          ...scheduleConfig,
                          day_of_month: parseInt(e.target.value),
                        })
                      }
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                )}
              </div>
            </div>
          );
        } else if (executionType === 'backfill') {
          return (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Configure Backfill</h3>
                <p className="text-sm text-gray-500">
                  Select the historical period to backfill data for.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Backfill Period
                </label>
                <div className="space-y-2">
                  {[7, 30, 90, 365].map((days) => (
                    <label key={days} className="flex items-center">
                      <input
                        type="radio"
                        name="backfillPeriod"
                        value={days}
                        checked={backfillPeriod === days}
                        onChange={(e) => setBackfillPeriod(parseInt(e.target.value))}
                        className="text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="ml-2 text-sm text-gray-900">
                        {days === 7 && '7 days'}
                        {days === 30 && '30 days'}
                        {days === 90 && '90 days'}
                        {days === 365 && '365 days'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          );
        }

        // For 'once' execution type, the schedule step is skipped
        // Snowflake options are now shown in the execution step
        return null;

      case 'review':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Review Configuration</h3>
              <p className="text-sm text-gray-500">
                Review your report configuration before submitting.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div>
                <div className="text-sm font-medium text-gray-700">Report:</div>
                <div className="text-sm text-gray-900">{reportName}</div>
                {reportDescription && (
                  <div className="text-xs text-gray-500 mt-1">{reportDescription}</div>
                )}
              </div>

              <div>
                <div className="text-sm font-medium text-gray-700">Template:</div>
                <div className="text-sm text-gray-900">
                  {(selectedTemplate || initialTemplate)?.name || 'Custom Query'}
                </div>
              </div>

              <div>
                <div className="text-sm font-medium text-gray-700">Execution Type:</div>
                <div className="text-sm text-gray-900">
                  {executionType === 'once' && 'Run Once'}
                  {executionType === 'recurring' && 'Recurring Schedule'}
                  {executionType === 'backfill' && 'Backfill Historical Data'}
                </div>
              </div>

              {executionType === 'recurring' && (
                <div>
                  <div className="text-sm font-medium text-gray-700">Schedule:</div>
                  <div className="text-sm text-gray-900">
                    {scheduleConfig.frequency} at {scheduleConfig.time}
                  </div>
                </div>
              )}

              {executionType === 'backfill' && (
                <div>
                  <div className="text-sm font-medium text-gray-700">Backfill Period:</div>
                  <div className="text-sm text-gray-900">{backfillPeriod} days</div>
                </div>
              )}

              {executionType === 'once' && (
                <div>
                  <div className="text-sm font-medium text-gray-700">Date Range:</div>
                  <div className="text-sm text-gray-900">
                    {dateRange.start} to {dateRange.end}
                  </div>
                </div>
              )}

              <div>
                <div className="text-sm font-medium text-gray-700">Instance:</div>
                <div className="text-sm text-gray-900">
                  {instances.find(i => i.instanceId === selectedInstance)?.instanceName || selectedInstance}
                </div>
              </div>

              {Object.keys(parameters).length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-700">Parameters:</div>
                  <div className="text-sm text-gray-900 space-y-1">
                    {Object.entries(parameters).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span className="text-gray-900">
                          {Array.isArray(value) ? `${value.length} selected` :
                           typeof value === 'object' ? JSON.stringify(value) :
                           String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {snowflakeEnabled && (
                <div>
                  <div className="text-sm font-medium text-gray-700">Snowflake Storage:</div>
                  <div className="text-sm text-gray-900">
                    <div className="flex items-center">
                      <svg className="h-4 w-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Enabled
                    </div>
                    {snowflakeTableName && (
                      <div className="mt-1 text-gray-600">Table: {snowflakeTableName}</div>
                    )}
                    {snowflakeSchemaName && (
                      <div className="mt-1 text-gray-600">Schema: {snowflakeSchemaName}</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* SQL Query Preview */}
            <div className="mt-4 border-t pt-4">
              <button
                type="button"
                onClick={() => setShowQueryPreview(!showQueryPreview)}
                className="flex items-center gap-2 mb-2 w-full text-left hover:bg-gray-50 p-2 rounded-md transition-colors"
              >
                <ChevronRight
                  className={`h-4 w-4 text-gray-600 transition-transform ${showQueryPreview ? 'rotate-90' : ''}`}
                />
                <Code className="h-4 w-4 text-gray-600" />
                <h4 className="text-sm font-medium text-gray-700">Query Preview</h4>
                <span className="text-xs text-gray-500 ml-auto">
                  {showQueryPreview ? 'Click to hide' : 'Click to show'}
                </span>
              </button>

              {showQueryPreview && (
                <>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <SQLEditor
                      value={previewSQL}
                      onChange={() => {}} // Read-only
                      height="300px"
                      readOnly={true}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    This is a preview of the SQL query with your parameters injected.
                    The actual query execution may include additional optimizations.
                  </p>
                </>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[95vh] flex flex-col">
        {/* Header - Fixed */}
        <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              {includeTemplateStep && !selectedTemplate
                ? 'Create New Report'
                : `Run Report: ${(selectedTemplate || initialTemplate)?.name || 'Custom Query'}`}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Step Indicator */}
          <div className="mt-4 flex items-center justify-between flex-wrap gap-2">
            {WIZARD_STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = index < currentStepIndex;
              const shouldShow = step.id !== 'schedule' || executionType !== 'once';

              if (!shouldShow) return null;

              return (
                <div key={step.id} className="flex items-center">
                  <div
                    className={`flex items-center justify-center w-8 h-8 rounded-full ${
                      isActive
                        ? 'bg-indigo-600 text-white'
                        : isCompleted
                        ? 'bg-indigo-100 text-indigo-600'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <span
                    className={`ml-2 text-sm font-medium ${
                      isActive ? 'text-indigo-600' : 'text-gray-500'
                    }`}
                  >
                    {index + 1}. {step.label}
                  </span>
                  {index < WIZARD_STEPS.length - 1 && (
                    <ChevronRight className="mx-2 h-4 w-4 text-gray-400" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 min-h-0">{renderStepContent()}</div>

        {/* Footer - Fixed */}
        <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 flex justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md
                     hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>

          <div className="flex gap-2">
            {!isFirstStep && currentStep !== 'parameters' && (
              <button
                onClick={goToPreviousStep}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md
                         hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <div className="flex items-center">
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back
                </div>
              </button>
            )}

            {!isLastStep && currentStep !== 'parameters' && (
              <button
                onClick={goToNextStep}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                         hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <div className="flex items-center">
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </div>
              </button>
            )}

            {isLastStep && (
              <button
                onClick={handleFinalSubmit}
                disabled={!reportName || !selectedInstance}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                         hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Report
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Fork Dialog */}
      {templateToFork && (
        <TemplateForkDialog
          isOpen={showForkDialog}
          onClose={() => {
            setShowForkDialog(false);
            setTemplateToFork(null);
          }}
          template={templateToFork}
          onForked={(forkedTemplate) => {
            // Switch to the forked template
            setSelectedTemplate(forkedTemplate);
            toast.success('Now using your forked template');
          }}
        />
      )}
    </div>
  );
}