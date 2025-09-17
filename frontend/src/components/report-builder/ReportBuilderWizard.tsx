import { useState } from 'react';
import { X, ChevronRight, Check } from 'lucide-react';
import ReportBuilderParameters from './ReportBuilderParameters';
import ReportScheduleSelection from './ReportScheduleSelection';
import ReportReviewStep from './ReportReviewStep';
import ReportSubmission from './ReportSubmission';
import type { QueryTemplate } from '../../types/queryTemplate';

interface ReportBuilderWizardProps {
  isOpen: boolean;
  onClose: () => void;
  template?: QueryTemplate;
  onSuccess?: () => void;
}

// Function to extract parameters from SQL query
function extractParametersFromSQL(sql: string): Record<string, any> {
  const params: Record<string, any> = {};
  const regex = /\{\{(\w+)\}\}/g;
  let match;

  while ((match = regex.exec(sql)) !== null) {
    const paramName = match[1];
    // Set default values based on parameter name
    if (paramName.toLowerCase().includes('date')) {
      params[paramName] = new Date().toISOString().split('T')[0];
    } else if (paramName.toLowerCase().includes('asin')) {
      params[paramName] = '';
    } else if (paramName.toLowerCase().includes('campaign')) {
      params[paramName] = '';
    } else {
      params[paramName] = '';
    }
  }

  return params;
}

export default function ReportBuilderWizard({
  isOpen,
  onClose,
  template,
  onSuccess
}: ReportBuilderWizardProps) {
  // Get SQL query from either field name
  const templateSQL = template?.sql_query || template?.sqlTemplate || '';

  // Debug: Log template data to see what we're receiving
  if (template) {
    console.log('Report Builder Wizard - Template loaded:', {
      id: template.id,
      name: template.name,
      hasSQL: !!templateSQL,
      sqlLength: templateSQL?.length,
      extractedParams: templateSQL ? extractParametersFromSQL(templateSQL) : null,
      defaultParams: template.defaultParameters,
      parametersSchema: template.parametersSchema
    });
  }

  // Extract parameters from template SQL if available
  const initialParameters = templateSQL
    ? extractParametersFromSQL(templateSQL)
    : template?.parameters || template?.defaultParameters || {};

  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<any>({
    // Workflow & Instance
    workflowId: template?.id || '',
    workflowName: template?.name || '',
    instanceId: '',
    instanceName: '',
    sqlQuery: templateSQL,

    // Step 1: Template & Parameters
    templateId: template?.id || null,
    parameters: initialParameters,
    detectedParameters: Object.keys(initialParameters).map(key => ({
      name: key,
      type: key.toLowerCase().includes('campaign') ? 'campaigns' as const :
            key.toLowerCase().includes('asin') ? 'asins' as const :
            key.toLowerCase().includes('date') ? 'date' as const :
            'string' as const,
      defaultValue: initialParameters[key]
    })),
    lookbackConfig: {
      type: 'relative',
      value: 7,
      unit: 'days'
    },

    // Step 2: Schedule
    scheduleConfig: {
      enabled: false,
      frequency: 'daily',
      time: '09:00',
      timezone: 'America/Los_Angeles',
      daysOfWeek: [],
      dayOfMonth: 1
    },
    backfillConfig: {
      enabled: false,
      weeksToBackfill: 4
    },

    // Step 3: Review
    name: template?.name ? `${template.name} Report` : '',
    description: template?.description || '',
    tags: [],
    estimatedCost: null,
    validationWarnings: []
  });

  const steps = [
    { id: 1, name: 'Parameters', description: 'Configure parameters' },
    { id: 2, name: 'Schedule', description: 'Set up scheduling' },
    { id: 3, name: 'Review', description: 'Review settings' },
    { id: 4, name: 'Submit', description: 'Launch report' }
  ];

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleUpdateFormData = (updates: any) => {
    setFormData((prev: any) => ({
      ...prev,
      ...updates
    }));
  };

  const handleEdit = (section: 'parameters' | 'lookback' | 'schedule') => {
    switch (section) {
      case 'parameters':
      case 'lookback':
        setCurrentStep(1);
        break;
      case 'schedule':
        setCurrentStep(2);
        break;
    }
  };

  const handleComplete = () => {
    // Success callback
    if (onSuccess) {
      onSuccess();
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {template ? `Configure: ${template.name}` : 'Create Report'}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Set up your report with custom parameters and scheduling
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-gray-100">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {steps.map((step, stepIdx) => (
                <li
                  key={step.id}
                  className={stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20 flex-1' : ''}
                >
                  <div className="flex items-center">
                    <div className="relative">
                      {currentStep > step.id ? (
                        <div className="h-8 w-8 rounded-full bg-green-600 flex items-center justify-center">
                          <Check className="h-4 w-4 text-white" />
                        </div>
                      ) : currentStep === step.id ? (
                        <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                          <span className="text-white text-sm font-semibold">{step.id}</span>
                        </div>
                      ) : (
                        <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-gray-600 text-sm font-semibold">{step.id}</span>
                        </div>
                      )}
                    </div>
                    <div className="ml-3">
                      <p
                        className={`text-sm font-medium ${
                          currentStep >= step.id ? 'text-gray-900' : 'text-gray-500'
                        }`}
                      >
                        {step.name}
                      </p>
                      <p className="text-xs text-gray-500">{step.description}</p>
                    </div>
                    {stepIdx !== steps.length - 1 && (
                      <div
                        className={`hidden sm:block absolute top-4 left-full w-full h-0.5 ${
                          currentStep > step.id ? 'bg-green-600' : 'bg-gray-300'
                        }`}
                        style={{ width: 'calc(100% - 2rem)', marginLeft: '2rem' }}
                      />
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentStep === 1 && (
            <ReportBuilderParameters
              workflowId={formData.workflowId}
              instanceId={formData.instanceId}
              sqlQuery={formData.sqlQuery}
              parameters={formData.parameters}
              lookbackConfig={formData.lookbackConfig}
              detectedParameters={formData.detectedParameters}
              onNext={handleNext}
              onParametersChange={(data) => handleUpdateFormData(data)}
            />
          )}

          {currentStep === 2 && (
            <ReportScheduleSelection
              workflowId={formData.workflowId}
              instanceId={formData.instanceId}
              scheduleConfig={formData.scheduleConfig}
              lookbackConfig={formData.lookbackConfig}
              onNext={handleNext}
              onPrevious={handleBack}
              onScheduleChange={(config) => handleUpdateFormData({ scheduleConfig: config })}
            />
          )}

          {currentStep === 3 && (
            <ReportReviewStep
              workflowId={formData.workflowId}
              workflowName={formData.workflowName}
              instanceId={formData.instanceId}
              instanceName={formData.instanceName}
              sqlQuery={formData.sqlQuery}
              parameters={formData.parameters}
              lookbackConfig={formData.lookbackConfig}
              scheduleConfig={formData.scheduleConfig}
              estimatedCost={formData.estimatedCost}
              validationWarnings={formData.validationWarnings}
              onNext={handleNext}
              onPrevious={handleBack}
              onEdit={handleEdit}
            />
          )}

          {currentStep === 4 && (
            <div>
              <ReportSubmission
                workflowId={formData.workflowId}
                workflowName={formData.workflowName}
                instanceId={formData.instanceId}
                parameters={formData.parameters}
                lookbackConfig={formData.lookbackConfig}
                scheduleConfig={formData.scheduleConfig}
                onBack={handleBack}
              />
              {/* Add a completion handler */}
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleComplete}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Complete Setup
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation (for steps without built-in navigation) */}
        {currentStep === 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:text-gray-900"
            >
              Cancel
            </button>
            <button
              onClick={handleNext}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}