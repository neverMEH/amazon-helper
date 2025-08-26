import React, { useState } from 'react';
import { X, ChevronRight, Calendar, Clock, Bell, CheckCircle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { scheduleService } from '../../services/scheduleService';
import type { ScheduleConfig, ScheduleCreatePreset } from '../../types/schedule';
import ScheduleTypeStep from './ScheduleTypeStep';
import TimingStep from './TimingStep';
import ParametersStep from './ParametersStep';
import ReviewStep from './ReviewStep';

interface ScheduleWizardProps {
  workflowId: string;
  workflowName: string;
  instanceInfo?: {
    instanceName?: string;
    brands?: string[];
  };
  onComplete: () => void;
  onCancel: () => void;
}

const steps = [
  { id: 1, name: 'Schedule Type', icon: Calendar },
  { id: 2, name: 'Timing', icon: Clock },
  { id: 3, name: 'Parameters', icon: Bell },
  { id: 4, name: 'Review', icon: CheckCircle },
];

const ScheduleWizard: React.FC<ScheduleWizardProps> = ({
  workflowId,
  workflowName,
  instanceInfo,
  onComplete,
  onCancel,
}) => {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(1);
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    name: workflowName ? `${workflowName} Schedule` : '',
    description: '',
    type: 'daily',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    executeTime: '09:00',
    parameters: {},
    notifications: {
      onSuccess: false,
      onFailure: true,
    },
  });

  const createScheduleMutation = useMutation({
    mutationFn: async (data: ScheduleCreatePreset) => {
      return scheduleService.createSchedulePreset(workflowId, data);
    },
    onSuccess: () => {
      toast.success('Schedule created successfully');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['workflows', workflowId] });
      onComplete();
    },
    onError: (error: any) => {
      console.error('Schedule creation error - Full error:', error);
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
      console.error('Response detail:', error.response?.data?.detail);
      
      // Handle validation errors from FastAPI
      if (error.response?.status === 422) {
        const data = error.response.data;
        console.error('422 Error data structure:', data);
        
        if (data?.detail) {
          if (Array.isArray(data.detail)) {
            // FastAPI validation error format
            const errorMsg = data.detail.map((d: any) => {
              console.error('Validation error item:', d);
              return `${d.loc?.join(' > ')}: ${d.msg}`;
            }).join(', ');
            toast.error(`Validation error: ${errorMsg}`);
          } else if (typeof data.detail === 'string') {
            toast.error(data.detail);
          } else {
            toast.error('Validation error: ' + JSON.stringify(data.detail));
          }
        } else {
          toast.error('Validation error: ' + JSON.stringify(data));
        }
      } else {
        toast.error(error.response?.data?.detail || error.message || 'Failed to create schedule');
      }
    },
  });

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    // Convert config to API format
    const scheduleData: ScheduleCreatePreset = {
      preset_type: scheduleConfig.type,
      name: scheduleConfig.name,
      description: scheduleConfig.description,
      interval_days: scheduleConfig.intervalDays,
      lookback_days: scheduleConfig.lookbackDays,
      timezone: scheduleConfig.timezone,
      execute_time: scheduleConfig.executeTime,
      parameters: scheduleConfig.parameters,
      notification_config: {
        on_success: scheduleConfig.notifications.onSuccess,
        on_failure: scheduleConfig.notifications.onFailure,
        email: scheduleConfig.notifications.email,
      },
    };

    console.log('Sending schedule data:', scheduleData);
    console.log('Workflow ID:', workflowId);
    
    createScheduleMutation.mutate(scheduleData);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <ScheduleTypeStep
            config={scheduleConfig}
            onChange={setScheduleConfig}
            onNext={handleNext}
          />
        );
      case 2:
        return (
          <TimingStep
            config={scheduleConfig}
            onChange={setScheduleConfig}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <ParametersStep
            config={scheduleConfig}
            onChange={setScheduleConfig}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <ReviewStep
            config={scheduleConfig}
            workflowName={workflowName}
            instanceInfo={instanceInfo}
            onComplete={handleComplete}
            onBack={handleBack}
            isLoading={createScheduleMutation.isPending}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">Create Schedule</h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = step.id < currentStep;

              return (
                <React.Fragment key={step.id}>
                  <div className="flex items-center">
                    <div
                      className={`
                        w-10 h-10 rounded-full flex items-center justify-center
                        ${isActive
                          ? 'bg-blue-600 text-white'
                          : isCompleted
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-400'
                        }
                      `}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <Icon className="w-5 h-5" />
                      )}
                    </div>
                    <span
                      className={`ml-3 text-sm font-medium ${
                        isActive ? 'text-gray-900' : 'text-gray-500'
                      }`}
                    >
                      {step.name}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <ChevronRight className="w-5 h-5 text-gray-300" />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {renderStep()}
        </div>
      </div>
    </div>
  );
};

export default ScheduleWizard;