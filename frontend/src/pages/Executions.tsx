import AMCExecutionList from '../components/executions/AMCExecutionList';

export default function Executions() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">All Executions</h1>
        <p className="mt-2 text-sm text-gray-600">
          View and manage all AMC workflow executions across all instances
        </p>
      </div>
      
      <AMCExecutionList showInstanceBadge={true} />
    </div>
  );
}