import { FileText, Code } from 'lucide-react';

interface InstanceQueriesProps {
  instanceId: string;
}

export default function InstanceQueries({}: InstanceQueriesProps) {
  // In a real implementation, this would fetch query templates and recent executions
  // For now, we'll show a placeholder
  
  return (
    <div className="p-6">
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Query Templates</h3>
        <p className="mt-1 text-sm text-gray-500">
          Query templates and execution history will be displayed here.
        </p>
        <div className="mt-6">
          <button className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
            <Code className="h-4 w-4 mr-2" />
            Browse Templates
          </button>
        </div>
      </div>
    </div>
  );
}