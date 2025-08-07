import AMCExecutionList from '../executions/AMCExecutionList';

interface InstanceExecutionsProps {
  instanceId: string;
}

export default function InstanceExecutions({ instanceId }: InstanceExecutionsProps) {


  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900">Execution History</h2>
        <p className="mt-1 text-sm text-gray-500">
          View all workflow executions for this AMC instance
        </p>
      </div>

      <AMCExecutionList instanceId={instanceId} />
    </div>
  );
}