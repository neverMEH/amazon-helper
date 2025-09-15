import { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Play, Clock, Calendar, Database } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import DynamicParameterForm from './DynamicParameterForm';
import InstanceSelector from '../query-builder/InstanceSelector';
import { UniversalParameterSelector } from '../parameter-detection';
import { ParameterDetector } from '../../utils/parameterDetection';
import { instanceService } from '../../services/instanceService';
import type { QueryTemplate } from '../../types/queryTemplate';
import type { CreateReportRequest, ScheduleConfig } from '../../types/report';
import type { DetectedParameter } from '../../utils/parameterDetection';

interface RunReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  template: QueryTemplate;
  onSubmit: (config: CreateReportRequest) => void;
}

type ExecutionType = 'once' | 'recurring' | 'backfill';
type WizardStep = 'parameters' | 'execution' | 'schedule' | 'review';

const WIZARD_STEPS: { id: WizardStep; label: string; icon: any }[] = [
  { id: 'parameters', label: 'Parameters', icon: Play },
  { id: 'execution', label: 'Execution Type', icon: Clock },
  { id: 'schedule', label: 'Schedule', icon: Calendar },
  { id: 'review', label: 'Review', icon: Database },
];

export default function RunReportModal({
  isOpen,
  onClose,
  template,
  onSubmit,
}: RunReportModalProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('parameters');
  const [reportName, setReportName] = useState(`${template.name} Report`);
  const [reportDescription, setReportDescription] = useState(template.description || '');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [executionType, setExecutionType] = useState<ExecutionType>('once');
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    frequency: 'daily',
    time: '09:00',
  });
  const [backfillPeriod, setBackfillPeriod] = useState(7);
  const [selectedInstance, setSelectedInstance] = useState('');
  const [detectedParameters, setDetectedParameters] = useState<DetectedParameter[]>([]);

  // Fetch instances
  const { data: instances = [], isLoading: loadingInstances } = useQuery({
    queryKey: ['instances'],
    queryFn: () => instanceService.list(),
    enabled: isOpen,
  });

  // Detect parameters from the SQL query
  useEffect(() => {
    if (template && isOpen) {
      const sqlQuery = template.sqlTemplate || template.sql_query || '';
      if (sqlQuery) {
        const detected = ParameterDetector.detectParameters(sqlQuery);
        setDetectedParameters(detected);

        // Initialize parameters with defaults if they exist
        const defaultParams: Record<string, any> = {};
        detected.forEach(param => {
          if (template.defaultParameters?.[param.name] !== undefined) {
            defaultParams[param.name] = template.defaultParameters[param.name];
          } else if (template.parameters?.[param.name] !== undefined) {
            defaultParams[param.name] = template.parameters[param.name];
          }
        });
        setParameters(defaultParams);
      }
    }
  }, [template, isOpen]);

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

  const handleFinalSubmit = () => {
    const config: CreateReportRequest = {
      name: reportName,
      description: reportDescription,
      template_id: template.id,
      instance_id: selectedInstance,
      parameters,
      execution_type: executionType === 'backfill' ? 'backfill' : executionType,
      schedule_config:
        executionType === 'recurring'
          ? scheduleConfig
          : executionType === 'backfill'
          ? { ...scheduleConfig, backfill_period: backfillPeriod }
          : undefined,
    };

    onSubmit(config);
  };

  const renderStepContent = () => {
    switch (currentStep) {
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
              {/* If template has predefined parameter definitions, use DynamicParameterForm */}
              {template.parameter_definitions && Object.keys(template.parameter_definitions).length > 0 ? (
                <DynamicParameterForm
                  parameterDefinitions={template.parameter_definitions}
                  uiSchema={template.ui_schema || {}}
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
                      <UniversalParameterSelector
                        parameter={param}
                        value={parameters[param.name]}
                        onChange={(value) => handleParameterChange(param.name, value)}
                        instanceId={selectedInstance}
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
                <div className="text-sm text-gray-900">{template.name}</div>
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
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              Run Report: {template.name}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Step Indicator */}
          <div className="mt-4 flex items-center justify-between">
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">{renderStepContent()}</div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
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
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md
                         hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Run Report
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}