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
  // Snowflake export fields
  snowflakeEnabled?: boolean;
  snowflake_enabled?: boolean;  // Backend returns snake_case
  snowflakeStatus?: string;
  snowflake_status?: string;  // Backend returns snake_case
  snowflakeTableName?: string;
  snowflake_table_name?: string;  // Backend returns snake_case
  snowflakeSchemaName?: string;
  snowflake_schema_name?: string;  // Backend returns snake_case
  snowflakeRowCount?: number;
  snowflake_row_count?: number;  // Backend returns snake_case
  snowflakeError?: string;
  snowflake_error?: string;  // Backend returns snake_case
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