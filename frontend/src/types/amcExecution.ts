export interface AMCExecution {
  workflowExecutionId: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELLED';
  startTime?: string;
  endTime?: string;
  workflowId?: string;
  workflowName?: string | null;
  workflowDescription?: string;
  sqlQuery?: string;
  executionParameters?: Record<string, any>;
  localExecutionId?: string;
  triggeredBy?: string;
  instanceId: string;
  error?: string;
  rowCount?: number;
  durationSeconds?: number;
  createdAt?: string;
  completedAt?: string;
}

export interface AMCErrorDetails {
  failureReason?: string;
  validationErrors?: string[];
  errorCode?: string;
  errorMessage?: string;
  errorDetails?: string;
  queryValidation?: string;
  message?: string;
}

export interface AMCExecutionDetail extends AMCExecution {
  executionId: string;
  amcStatus: string;
  progress: number;
  resultData?: any;
  downloadUrls?: string[];
  errorMessage?: string;
  error_message?: string;  // Backend returns snake_case
  message?: string;  // Additional message from backend
  errorDetails?: AMCErrorDetails;
  startedAt?: string;
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
    sqlQuery?: string;
    parameters?: Record<string, any>;
    createdAt?: string;
    updatedAt?: string;
  };
}