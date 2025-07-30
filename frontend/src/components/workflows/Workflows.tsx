import { useQuery } from '@tanstack/react-query';
import { GitBranch, Plus, Play, Clock } from 'lucide-react';
import api from '../../services/api';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  sqlQuery: string;
  parameters?: any;
  createdAt: string;
  lastExecuted?: string;
  status?: string;
}

export default function Workflows() {
  const { data: workflows, isLoading } = useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows/');
      return response.data;
    },
  });

  const handleExecute = async (workflowId: string) => {
    try {
      await api.post(`/workflows/${workflowId}/execute/`);
      // TODO: Show execution status
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
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
          onClick={() => console.log('Create workflow modal - TODO')}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Workflow
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading workflows...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workflows?.map((workflow) => (
            <div
              key={workflow.id}
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <GitBranch className="h-8 w-8 text-indigo-500" />
                  <button
                    onClick={() => handleExecute(workflow.id)}
                    className="inline-flex items-center p-2 border border-transparent rounded-full text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Play className="h-4 w-4" />
                  </button>
                </div>
                <h3 className="text-lg font-medium text-gray-900">
                  {workflow.name}
                </h3>
                {workflow.description && (
                  <p className="mt-1 text-sm text-gray-500">
                    {workflow.description}
                  </p>
                )}
                <div className="mt-4 flex items-center text-sm text-gray-500">
                  <Clock className="h-4 w-4 mr-1" />
                  {workflow.lastExecuted ? (
                    <span>Last run: {new Date(workflow.lastExecuted).toLocaleDateString()}</span>
                  ) : (
                    <span>Never executed</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TODO: Add create workflow modal */}
    </div>
  );
}