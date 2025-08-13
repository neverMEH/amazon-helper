import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Check, X } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { debounce } from 'lodash';
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
  };
  
  // Parameters extracted from query
  parameters: Record<string, any>;
}

const WIZARD_STEPS = [
  { id: 'edit', title: 'Edit Query', component: QueryEditorStep },
  { id: 'configure', title: 'Basic Information', component: QueryConfigurationStep },
  { id: 'review', title: 'Review & Execute', component: QueryReviewStep }
];

// Generate smart workflow name based on query content
function generateWorkflowName(sqlQuery: string): string {
  const query = sqlQuery.toLowerCase();
  const date = new Date().toISOString().split('T')[0];
  
  // Identify query type
  if (query.includes('conversion') || query.includes('path')) {
    return `Conversion Path Analysis - ${date}`;
  } else if (query.includes('campaign')) {
    return `Campaign Analysis - ${date}`;
  } else if (query.includes('audience') || query.includes('segment')) {
    return `Audience Segmentation - ${date}`;
  } else if (query.includes('overlap')) {
    return `Overlap Analysis - ${date}`;
  } else if (query.includes('performance')) {
    return `Performance Metrics - ${date}`;
  } else if (query.includes('attribution')) {
    return `Attribution Analysis - ${date}`;
  } else {
    return `Query Development - ${date}`;
  }
}

export default function QueryBuilder() {
  const { templateId, workflowId } = useParams();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isExecuting, setIsExecuting] = useState(false);
  
  // Check if we're in copy mode
  const isCopyMode = window.location.pathname.includes('/copy/');
  const [currentWorkflowId, setCurrentWorkflowId] = useState<string | undefined>(
    isCopyMode ? undefined : workflowId // Don't use original ID if copying
  );
  
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
      name: ''
    },
    parameters: {}
  });

  // Load template if templateId is provided
  const { data: template } = useQuery({
    queryKey: ['query-template', templateId],
    queryFn: () => queryTemplateService.getTemplate(templateId!),
    enabled: !!templateId
  });

  // Load workflow if editing or copying
  const { data: workflow } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: async () => {
      const response = await api.get(`/workflows/${workflowId}`);
      return response.data;
    },
    enabled: !!workflowId // Load for both edit and copy modes
  });

  // Load instances for configuration
  const { data: instances = [] } = useQuery({
    queryKey: ['instances'],
    queryFn: async () => {
      const response = await api.get('/instances');
      return response.data;
    }
  });

  // Load from sessionStorage if available (for examples from data sources)
  useEffect(() => {
    if (!templateId && !workflowId) {
      const draft = sessionStorage.getItem('queryBuilderDraft');
      if (draft) {
        try {
          const parsedDraft = JSON.parse(draft);
          setQueryState(prev => ({
            ...prev,
            sqlQuery: parsedDraft.sql_query || '',
            name: parsedDraft.name || '',
            description: parsedDraft.description || '',
            parameters: parsedDraft.parameters || {}
          }));
          // Clear the draft after loading
          sessionStorage.removeItem('queryBuilderDraft');
        } catch (error) {
          console.error('Failed to load draft from sessionStorage:', error);
        }
      }
    }
  }, []); // Only run once on mount

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
      if (isCopyMode) {
        // In copy mode, create a new workflow with copied data but clear instance
        setQueryState(prev => ({
          ...prev,
          sqlQuery: workflow.sqlQuery || workflow.sql_query,
          name: `Copy of ${workflow.name}`,
          description: workflow.description || '',
          instanceId: '', // Clear instance so user must select a new one
          parameters: workflow.parameters || {}
        }));
      } else {
        // In edit mode, load all data including instance
        setQueryState(prev => ({
          ...prev,
          sqlQuery: workflow.sqlQuery || workflow.sql_query,
          name: workflow.name,
          description: workflow.description || '',
          instanceId: workflow.instance?.id || '',
          parameters: workflow.parameters || {}
        }));
      }
    }
  }, [workflow, isCopyMode]);

  // Create/Update workflow mutation
  const saveMutation = useMutation({
    mutationFn: async (options: { silent?: boolean; asDraft?: boolean } = {}) => {
      // Generate smart name if not provided
      const workflowName = queryState.name || generateWorkflowName(queryState.sqlQuery);
      
      const payload = {
        name: workflowName,
        description: queryState.description || 'Query under development',
        instance_id: queryState.instanceId,
        sql_query: queryState.sqlQuery,
        parameters: queryState.parameters,
        tags: ['query-builder', 'iterative-development'],
        status: options.asDraft ? 'draft' : 'active'
      };

      if (currentWorkflowId) {
        return await api.put(`/workflows/${currentWorkflowId}`, payload);
      } else {
        return await api.post('/workflows/', payload);
      }
    },
    onSuccess: (response, variables) => {
      if (!variables?.silent) {
        toast.success(currentWorkflowId ? 'Workflow updated' : 'Workflow saved');
      }
      if (!currentWorkflowId) {
        const newWorkflowId = response.data.workflow_id || response.data.workflowId;
        setCurrentWorkflowId(newWorkflowId);
        // Update URL without full navigation to prevent losing state
        window.history.replaceState(null, '', `/query-builder/edit/${newWorkflowId}`);
      }
    },
    onError: (error: any, variables) => {
      if (!variables?.silent) {
        toast.error(error.response?.data?.detail || 'Failed to save workflow');
      }
    }
  });

  // Auto-save functionality - debounced to avoid too many saves
  const autoSave = useCallback(
    debounce(async () => {
      if (queryState.sqlQuery && queryState.instanceId) {
        await saveMutation.mutateAsync({ silent: true });
      }
    }, 3000), // Save after 3 seconds of no changes
    [queryState.sqlQuery, queryState.instanceId, currentWorkflowId]
  );

  // Trigger auto-save when query changes
  useEffect(() => {
    if (queryState.sqlQuery && queryState.instanceId) {
      autoSave();
    }
  }, [queryState.sqlQuery, queryState.instanceId]);


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

  const handleCreateWorkflow = async () => {
    setIsExecuting(true);
    try {
      // Save the workflow first
      const response = await saveMutation.mutateAsync({ asDraft: false });
      const workflowId = response.data.workflow_id || response.data.workflowId || currentWorkflowId;
      
      // Navigate to the workflow detail page
      toast.success('Workflow created successfully');
      navigate(`/workflows/${workflowId}`);
    } catch (error) {
      toast.error('Failed to create workflow');
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
            {isCopyMode ? 'Copy Workflow' : workflowId ? 'Edit Workflow' : templateId ? 'Create from Template' : 'New Workflow'}
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
                  onClick={() => saveMutation.mutate({ asDraft: true })}
                  disabled={saveMutation.isPending}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Save as Draft
                </button>
                <button
                  onClick={handleCreateWorkflow}
                  disabled={isExecuting || !queryState.instanceId || !queryState.sqlQuery}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isExecuting ? 'Creating...' : 'Create Workflow'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}