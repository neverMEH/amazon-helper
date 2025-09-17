import { useState } from 'react';
import { ChevronRight, Check } from 'lucide-react';
import ReportBuilderParameters from './ReportBuilderParameters';
import ReportScheduleSelection from './ReportScheduleSelection';
import ReportReviewStep from './ReportReviewStep';
import ReportSubmission from './ReportSubmission';
// import toast from 'react-hot-toast'; // Uncomment when handleSubmit is connected

export default function ReportBuilder() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<any>({
    // Workflow & Instance
    workflowId: '',
    workflowName: '',
    instanceId: '',
    instanceName: '',
    sqlQuery: '',

    // Step 1: Template & Parameters
    templateId: null,
    parameters: {},
    detectedParameters: [],
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
    name: '',
    description: '',
    tags: [],
    estimatedCost: null,
    validationWarnings: []
  });

  const steps = [
    { id: 1, name: 'Parameters', description: 'Select template and configure' },
    { id: 2, name: 'Schedule', description: 'Set up recurring runs' },
    { id: 3, name: 'Review', description: 'Review configuration' },
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

  // TODO: Connect this when ReportSubmission is updated to accept onSubmit
  // const handleSubmit = async (submissionData: any) => {
  //   try {
  //     // Merge submission data with existing form data
  //     const finalData = {
  //       ...formData,
  //       ...submissionData
  //     };

  //     // TODO: Call API to create report
  //     console.log('Submitting report:', finalData);
  //     toast.success('Report created successfully!');

  //     // Reset form or navigate away
  //     setCurrentStep(1);
  //     setFormData({
  //       // Reset to initial state
  //     });
  //   } catch (error: any) {
  //     toast.error(error.message || 'Failed to create report');
  //   }
  // };

  const handleEdit = (section: 'parameters' | 'lookback' | 'schedule') => {
    // Navigate to the appropriate step for editing
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
          <p className="mt-2 text-gray-600">
            Create and schedule automated reports with historical data collection
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
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
                        <div className="h-10 w-10 rounded-full bg-green-600 flex items-center justify-center">
                          <Check className="h-5 w-5 text-white" />
                        </div>
                      ) : currentStep === step.id ? (
                        <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                          <span className="text-white font-semibold">{step.id}</span>
                        </div>
                      ) : (
                        <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-gray-600 font-semibold">{step.id}</span>
                        </div>
                      )}
                    </div>
                    <div className="ml-4">
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
                        className={`hidden sm:block absolute top-5 left-full w-full h-0.5 ${
                          currentStep > step.id ? 'bg-green-600' : 'bg-gray-300'
                        }`}
                        style={{ width: 'calc(100% - 2.5rem)', marginLeft: '2.5rem' }}
                      />
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {currentStep === 1 && (
            <ReportBuilderParameters
              workflowId={formData.workflowId}
              instanceId={formData.instanceId}
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
            <ReportSubmission
              workflowId={formData.workflowId}
              workflowName={formData.workflowName}
              instanceId={formData.instanceId}
              parameters={formData.parameters}
              lookbackConfig={formData.lookbackConfig}
              scheduleConfig={formData.scheduleConfig}
              onBack={handleBack}
            />
          )}
        </div>

        {/* Navigation Buttons (for steps that don't have their own) */}
        {currentStep === 1 && (
          <div className="mt-6 flex justify-end">
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