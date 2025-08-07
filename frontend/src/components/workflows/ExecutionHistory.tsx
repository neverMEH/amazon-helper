import AMCExecutionList from '../executions/AMCExecutionList';

interface ExecutionHistoryProps {
  workflowId: string;
  instanceId?: string;
}

export default function ExecutionHistory({ workflowId, instanceId }: ExecutionHistoryProps) {
  return (
    <AMCExecutionList 
      workflowId={workflowId}
      instanceId={instanceId}
      showInstanceBadge={!instanceId} // Show instance badge when not filtered by instance
    />
  );
}