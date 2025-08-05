import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Check, X } from 'lucide-react';
import { toast } from 'react-hot-toast';
import QueryEditorStep from '../components/query-builder/QueryEditorStep';
import QueryConfigurationStep from '../components/query-builder/QueryConfigurationStep';
import QueryReviewStep from '../components/query-builder/QueryReviewStep';
import api from '../services/api';
import { queryTemplateService } from '../services/queryTemplateService';

interface QueryBuilderState {
  // Query details
  sqlQuery: string;
  name: string;
  description: string;
  
  // Configuration
  instanceId: string;
  timezone: string;
  advancedOptions: {
    ignoreDataGaps: boolean;
    appendThresholdColumns: boolean;
  };
  
  // Export settings
  exportSettings: {
    name: string;
    email: string;
    format: 'CSV' | 'PARQUET' | 'JSON';
    password?: string;
  };
  
  // Parameters extracted from query
  parameters: Record<string, any>;
}

const WIZARD_STEPS = [
  { id: 'edit', title: 'Edit Query', component: QueryEditorStep },
  { id: 'configure', title: 'Basic Information', component: QueryConfigurationStep },
  { id: 'review', title: 'Review & Execute', component: QueryReviewStep }
];

export default function QueryBuilder() {
  const { templateId, workflowId } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);
  
  // Initialize state
  const [queryState, setQueryState] = useState<QueryBuilderState>({
    sqlQuery: '',
    name: '',
    description: '',
    instanceId: '',
    timezone: 'UTC',
    advancedOptions: {
      ignoreDataGaps: false,
      appendThresholdColumns: false
    },
    exportSettings: {
      name: '',
      email: '',
      format: 'CSV'
    },
    parameters: {}
  });

  // Load template if templateId is provided
  const { data: template } = useQuery({
    queryKey: ['query-template', templateId],
    queryFn: () => queryTemplateService.getTemplate(templateId!),
    enabled: !!templateId
  });

  // Load workflow if editing
  const { data: workflow } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}`);
      return response.data;
    },
    enabled: !!workflowId
  });

  // Load instances for configuration
  const { data: instances = [] } = useQuery({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances');
      return response.data;
    }
  });

  // Initialize from template or workflow
  useEffect(() => {
    if (template) {
      setQueryState(prev => ({
        ...prev,
        sqlQuery: template.sqlTemplate,
        name: template.name,
        description: template.description || '',
        parameters: template.defaultParameters || {}
      }));
    }
  }, [template]);

  useEffect(() => {
    if (workflow) {
      setQueryState(prev => ({
        ...prev,
        sqlQuery: workflow.sqlQuery || workflow.sql_query,
        name: workflow.name,
        description: workflow.description || '',
        instanceId: workflow.instance?.id || '',
        parameters: workflow.parameters || {}
      }));
    }
  }, [workflow]);

  // Create/Update workflow mutation
  const saveMutation = useMutation({
    mutationFn: async (asDraft: boolean = false) => {
      const payload = {
        name: queryState.name,
        description: queryState.description,
        instance_id: queryState.instanceId,
        sql_query: queryState.sqlQuery,
        parameters: queryState.parameters,
        tags: ['query-builder'],
        status: asDraft ? 'draft' : 'active'
      };

      if (workflowId) {
        return await api.put(`/workflows/${workflowId}`, payload);
      } else {
        return await api.post('/workflows/', payload);
      }
    },
    onSuccess: (response) => {
      toast.success(workflowId ? 'Query updated successfully' : 'Query saved successfully');
      if (!workflowId) {
        // Navigate to the new workflow
        navigate(`/query-builder/edit/${response.data.workflow_id || response.data.workflowId}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save query');
    }
  });

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: async () => {
      // First save the workflow if not saved yet
      let wfId = workflowId;
      if (!wfId) {
        const saveResponse = await saveMutation.mutateAsync(false);
        wfId = saveResponse.data.workflow_id || saveResponse.data.workflowId;
      }

      // Execute the workflow with output format
      const response = await api.post(`/workflows/${wfId}/execute`, {
        ...queryState.parameters,
        output_format: queryState.exportSettings.format || 'CSV'
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('Query execution started');
      // Navigate to execution details
      navigate(`/executions/${data.execution_id}`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to execute query');
    }
  });

  const handleNext = () => {
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      await executeMutation.mutateAsync();
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCancel = () => {
    if (window.confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
      navigate('/query-library');
    }
  };

  const StepComponent = WIZARD_STEPS[currentStep].component;

  return (
    <div className="h-full flex flex-col">
      {/* Header with Steps */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-semibold text-gray-900">
            {workflowId ? 'Edit Query' : templateId ? 'Create from Template' : 'New Query'}
          </h1>
          <button
            onClick={handleCancel}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-between">
          {WIZARD_STEPS.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center ${
                index < WIZARD_STEPS.length - 1 ? 'flex-1' : ''
              }`}
            >
              <div className="flex items-center">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                    index < currentStep
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : index === currentStep
                      ? 'border-blue-600 text-blue-600'
                      : 'border-gray-300 text-gray-400'
                  }`}
                >
                  {index < currentStep ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                <span
                  className={`ml-2 text-sm font-medium ${
                    index <= currentStep ? 'text-gray-900' : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </span>
              </div>
              {index < WIZARD_STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-4 ${
                    index < currentStep ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="flex-1 overflow-hidden">
        <StepComponent
          state={queryState}
          setState={setQueryState}
          instances={instances}
        />
      </div>

      {/* Footer with Navigation */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            {currentStep > 0 && (
              <button
                onClick={handlePrevious}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                Previous
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCancel}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
            
            {currentStep < WIZARD_STEPS.length - 1 ? (
              <button
                onClick={handleNext}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Next
                <ChevronRight className="h-4 w-4 ml-2" />
              </button>
            ) : (
              <>
                <button
                  onClick={() => saveMutation.mutate(true)}
                  disabled={saveMutation.isPending}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Save as Draft
                </button>
                <button
                  onClick={handleExecute}
                  disabled={isExecuting || !queryState.instanceId || !queryState.sqlQuery}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isExecuting ? 'Executing...' : 'Execute Query'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}