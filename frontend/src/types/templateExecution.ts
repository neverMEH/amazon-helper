/**
 * Types and interfaces for template execution
 *
 * Supports both immediate (run once) and recurring schedule execution
 * of instance templates.
 */

/**
 * Request payload for immediate template execution
 */
export interface TemplateExecutionRequest {
  /** Auto-generated execution name: {Brand} - {Template} - {StartDate} - {EndDate} */
  name: string;
  /** ISO date format: YYYY-MM-DD (e.g., 2025-10-01) */
  timeWindowStart: string;
  /** ISO date format: YYYY-MM-DD (e.g., 2025-10-31) */
  timeWindowEnd: string;
  /** Whether to upload results to Snowflake after execution */
  snowflake_enabled?: boolean;
  /** Snowflake table name (auto-generated if empty) */
  snowflake_table_name?: string;
  /** Snowflake schema name (uses default if empty) */
  snowflake_schema_name?: string;
}

/**
 * Schedule configuration for recurring template execution
 */
export interface TemplateScheduleConfig {
  /** Schedule frequency: daily, weekly, or monthly */
  frequency: 'daily' | 'weekly' | 'monthly';
  /** Execution time in HH:mm format (e.g., 09:00) */
  time: string;
  /** Number of days to look back for data (1-365) */
  lookback_days?: number;
  /** How date range is calculated: rolling or fixed */
  date_range_type?: 'rolling' | 'fixed';
  /** Explicit window size for clarity (alias for lookback_days) */
  window_size_days?: number;
  /** Timezone for execution (e.g., America/New_York) */
  timezone: string;
  /** For weekly schedules: 0=Sunday, 1=Monday, ..., 6=Saturday */
  day_of_week?: number;
  /** For monthly schedules: 1-31 */
  day_of_month?: number;
}

/**
 * Request payload for creating a recurring schedule from a template
 */
export interface TemplateScheduleRequest {
  /** Auto-generated schedule name */
  name: string;
  /** Schedule configuration details */
  schedule_config: TemplateScheduleConfig;
  /** Whether to upload results to Snowflake after execution */
  snowflake_enabled?: boolean;
  /** Snowflake table name (auto-generated if empty) */
  snowflake_table_name?: string;
  /** Snowflake schema name (uses default if empty) */
  snowflake_schema_name?: string;
  /** Snowflake upload strategy (always 'upsert' for schedules) */
  snowflake_strategy?: 'upsert' | 'append' | 'replace' | 'create_new';
}

/**
 * Response from immediate template execution
 */
export interface TemplateExecutionResponse {
  /** UUID of the created workflow execution record */
  workflow_execution_id: string;
  /** AMC execution ID (null if AMC API call failed) */
  amc_execution_id: string | null;
  /** Execution status: PENDING, RUNNING, COMPLETED, or FAILED */
  status: string;
  /** ISO 8601 timestamp when the execution was created */
  created_at: string;
}

/**
 * Response from recurring schedule creation
 */
export interface TemplateScheduleResponse {
  /** Schedule ID (format: sched_<random>) */
  schedule_id: string;
  /** Created workflow ID (format: wf_<random>) */
  workflow_id: string;
  /** ISO 8601 timestamp of next scheduled execution */
  next_run_at: string | null;
  /** ISO 8601 timestamp when the schedule was created */
  created_at: string;
}

/**
 * Execution type for template execution wizard
 */
export type ExecutionType = 'once' | 'recurring';

/**
 * Wizard step identifiers
 */
export type WizardStep = 1 | 2 | 3 | 4;

/**
 * Instance information for template execution
 */
export interface TemplateExecutionInstanceInfo {
  /** Instance UUID for API calls */
  id: string;
  /** AMC instance ID string (e.g., "amcibersblt") */
  instanceId: string;
  /** Human-readable instance name */
  instanceName: string;
  /** Associated brand names */
  brands?: string[];
}

/**
 * Complete wizard state for template execution
 */
export interface TemplateExecutionWizardState {
  /** Current wizard step (1-4) */
  currentStep: WizardStep;
  /** Execution type: run once or recurring */
  executionType: ExecutionType;
  /** Date range for run once execution */
  dateRange: {
    start: string;
    end: string;
  };
  /** Whether to use rolling window for run once */
  useRollingWindow: boolean;
  /** Number of days for rolling window */
  rollingWindowDays: number;
  /** Schedule configuration for recurring execution */
  scheduleConfig: TemplateScheduleConfig;
  /** Snowflake integration enabled */
  snowflakeEnabled: boolean;
  /** Snowflake table name */
  snowflakeTableName: string;
  /** Snowflake schema name */
  snowflakeSchemaName: string;
}

/**
 * Props for TemplateExecutionWizard component
 */
export interface TemplateExecutionWizardProps {
  /** Whether the wizard modal is open */
  isOpen: boolean;
  /** Callback when wizard is closed */
  onClose: () => void;
  /** Template to execute */
  template: {
    templateId: string;
    name: string;
    sqlQuery: string;
  };
  /** Instance information */
  instanceInfo: TemplateExecutionInstanceInfo;
  /** Callback when execution/schedule is successfully created */
  onComplete: () => void;
}
