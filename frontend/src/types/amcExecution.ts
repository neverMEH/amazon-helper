export interface AMCExecution {
  workflowExecutionId: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';
  startTime?: string;
  endTime?: string;
  workflowId?: string;
  workflowName?: string | null;
  localExecutionId?: string;
  triggeredBy?: string;
  instanceId: string;
  error?: string;
}

export interface AMCExecutionDetail extends AMCExecution {
  executionId: string;
  amcStatus: string;
  progress: number;
  resultData?: any;
  downloadUrls?: string[];
  error?: string;
  instanceInfo?: {
    instanceId: string;
    instanceName: string;
    region: string;
    accountId: string;
    accountName: string;
    marketplaceId: string;
  };
  brands?: string[];
  workflowInfo?: {
    id: string;
    name: string;
    description: string;
  };
}