import { useQuery, useQueryClient } from '@tanstack/react-query';
import { GitBranch, Plus, Play, Clock, CheckCircle, AlertCircle, Tag } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { AmazonAuthStatus } from '../AmazonAuthStatus';
import WorkflowForm from './WorkflowForm';
import ExecutionModal from './ExecutionModal';

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  parameters?: any;
  tags?: string[];
  isTemplate?: boolean;
  instance?: {
    id: string;
    name: string;
  };
  createdAt: string;
  lastExecuted?: string;
  status?: string;
}

export default function Workflows() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showWorkflowForm, setShowWorkflowForm] = useState(false);
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  
  const { data: workflows, isLoading } = useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows');
      return response.data;
    },
  });

  const handleExecute = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setShowExecutionModal(true);
  };

  return (
    <div className="p-6">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
          <p className="mt-1 text-sm text-gray-600">
            Create and manage AMC query workflows
          </p>
        </div>
        <button
          onClick={() => setShowWorkflowForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Workflow
        </button>
      </div>

      <div className="mb-4">
        <AmazonAuthStatus />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading workflows...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflows?.map((workflow) => (
            <div
              key={workflow.id || workflow.workflowId}
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              onClick={(e) => {
                // Don't navigate if clicking on the execute button
                if (!(e.target as HTMLElement).closest('button')) {
                  navigate(`/workflows/${workflow.workflowId}`);
                }
              }}
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <GitBranch className="h-8 w-8 text-indigo-500" />
                    {workflow.isTemplate && (
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Template
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleExecute(workflow)}
                    className="inline-flex items-center p-2 border border-transparent rounded-full text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Play className="h-4 w-4" />
                  </button>
                </div>
                <h3 className="text-lg font-medium text-gray-900">
                  {workflow.name}
                </h3>
                {workflow.description && (
                  <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                    {workflow.description}
                  </p>
                )}
                
                {workflow.instance && (
                  <div className="mt-2 text-xs text-gray-600">
                    Instance: {workflow.instance.name}
                  </div>
                )}
                
                {workflow.tags && workflow.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {workflow.tags.slice(0, 3).map((tag, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full"
                      >
                        <Tag className="h-3 w-3 mr-1" />
                        {tag}
                      </span>
                    ))}
                    {workflow.tags.length > 3 && (
                      <span className="text-xs text-gray-500">+{workflow.tags.length - 3} more</span>
                    )}
                  </div>
                )}
                
                <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {workflow.lastExecuted ? (
                      <span>Last run: {new Date(workflow.lastExecuted).toLocaleDateString()}</span>
                    ) : (
                      <span>Never executed</span>
                    )}
                  </div>
                  {workflow.status === 'active' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Workflow Form Modal */}
      {showWorkflowForm && (
        <WorkflowForm
          onClose={() => setShowWorkflowForm(false)}
        />
      )}

      {/* Execution Modal */}
      <ExecutionModal
        isOpen={showExecutionModal}
        onClose={() => {
          setShowExecutionModal(false);
          setSelectedWorkflow(null);
          // Refresh workflows to update last executed time
          queryClient.invalidateQueries({ queryKey: ['workflows'] });
        }}
        workflow={selectedWorkflow || undefined}
      />
    </div>
  );
}