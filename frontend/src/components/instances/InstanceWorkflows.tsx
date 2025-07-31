import { useQuery } from '@tanstack/react-query';
import { Clock, CheckCircle, XCircle, PlayCircle, Settings } from 'lucide-react';
import api from '../../services/api';

interface Workflow {
  workflowId: string;
  name: string;
  description: string;
  status: string;
  isTemplate: boolean;
  tags: string[];
  createdAt: string;
  lastExecutedAt: string | null;
  sourceInstanceId?: string;
}

interface InstanceWorkflowsProps {
  instanceId: string;
}

export default function InstanceWorkflows({ instanceId }: InstanceWorkflowsProps) {
  const { data: workflows, isLoading } = useQuery<Workflow[]>({
    queryKey: ['instance-workflows', instanceId],
    queryFn: async () => {
      const response = await api.get(`/instances/${instanceId}/workflows`);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">Loading workflows...</div>
      </div>
    );
  }

  if (!workflows || workflows.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Settings className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new workflow for this instance.
          </p>
          <div className="mt-6">
            <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
              <PlayCircle className="h-4 w-4 mr-2" />
              Create Workflow
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="space-y-4">
        {workflows.map((workflow) => (
          <div
            key={workflow.workflowId}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  <h3 className="text-sm font-medium text-gray-900">{workflow.name}</h3>
                  {workflow.isTemplate && (
                    <span className="ml-2 inline-flex px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                      Global Template
                    </span>
                  )}
                  {workflow.sourceInstanceId && workflow.sourceInstanceId !== instanceId && (
                    <span className="ml-2 inline-flex px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      From Another Instance
                    </span>
                  )}
                </div>
                {workflow.description && (
                  <p className="mt-1 text-sm text-gray-500">{workflow.description}</p>
                )}
                <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center">
                    <Clock className="h-3 w-3 mr-1" />
                    Created {new Date(workflow.createdAt).toLocaleDateString()}
                  </span>
                  {workflow.lastExecutedAt && (
                    <span className="flex items-center">
                      <PlayCircle className="h-3 w-3 mr-1" />
                      Last run {new Date(workflow.lastExecutedAt).toLocaleDateString()}
                    </span>
                  )}
                </div>
                {workflow.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {workflow.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="inline-flex px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="ml-4 flex-shrink-0">
                {workflow.status === 'active' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button className="text-sm text-indigo-600 hover:text-indigo-500 font-medium">
                View Details
              </button>
              <span className="text-gray-300">•</span>
              <button 
                className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
                title={`Execute on this instance (${instanceId})`}
              >
                Execute Here
              </button>
              <span className="text-gray-300">•</span>
              <button className="text-sm text-indigo-600 hover:text-indigo-500 font-medium">
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}