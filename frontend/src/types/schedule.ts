/**
 * Types and interfaces for workflow scheduling
 */

export interface Schedule {
  id: string;
  schedule_id: string;
  workflow_id: string;
  user_id: string;
  name?: string;  // User-friendly name for the schedule
  description?: string;  // Optional description or notes
  schedule_type: 'daily' | 'interval' | 'weekly' | 'monthly' | 'custom';
  interval_days?: number;
  lookback_days?: number;  // Number of days to look back for data
  interval_config?: {
    type: string;
    value?: number;
    dayOfWeek?: number;
    dayOfMonth?: number;
  };
  cron_expression: string;
  timezone: string;
  default_parameters?: Record<string, any>;
  notification_config?: {
    on_success: boolean;
    on_failure: boolean;
    email?: string;
    webhook_url?: string;
  };
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  execution_history_limit: number;
  cost_limit?: number;
  auto_pause_on_failure: boolean;
  failure_threshold: number;
  consecutive_failures: number;
  created_at: string;
  updated_at?: string;
  workflows?: {
    id: string;
    workflow_id: string;
    name: string;
    sql_query: string;
    instance_id?: string;  // Direct foreign key to amc_instances
    amc_instances?: {
      id: string;
      instance_id: string;
      instance_name: string;
      brands?: string[];  // Brand associations from instance_brands table
    };
  };
  brands?: string[];  // Extracted/flattened brand list for easier display
}

export interface ScheduleRun {
  id: string;
  schedule_id: string;
  run_number: number;
  scheduled_at: string;
  started_at?: string;
  completed_at?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  execution_count: number;
  successful_count: number;
  failed_count: number;
  total_rows: number;
  total_cost: number;
  error_summary?: string;
  created_at: string;
  updated_at?: string;
  workflow_execution_id?: string;  // Added for direct execution reference
  workflow_executions?: WorkflowExecution[];
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  instance_id: string;
  schedule_run_id?: string;
  amc_execution_id?: string;
  amc_workflow_id?: string;
  status: string;
  query_text: string;
  parameters?: Record<string, any>;
  results?: any;
  error_details?: {
    message: string;
    details?: string;
    line?: number;
    column?: number;
  };
  started_at?: string;
  completed_at?: string;
  row_count?: number;
  created_at: string;
}

export interface ScheduleMetrics {
  schedule_id: string;
  period_days: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  pending_runs: number;
  running_runs: number;
  success_rate: number;
  avg_runtime_seconds?: number;
  total_rows_processed: number;
  total_cost: number;
  next_run?: string;
  last_run?: string;
  first_run_in_period?: string;
  last_run_in_period?: string;
}

export interface ScheduleCreatePreset {
  preset_type: string;
  name?: string;  // Custom name for the schedule
  description?: string;  // Optional description
  interval_days?: number;
  lookback_days?: number;  // Custom lookback window
  timezone: string;
  execute_time: string;
  parameters?: Record<string, any>;
  notification_config?: {
    on_success: boolean;
    on_failure: boolean;
    email?: string;
  };
}

export interface ScheduleCreateCustom {
  cron_expression: string;
  name?: string;  // Custom name for the schedule
  description?: string;  // Optional description
  timezone: string;
  parameters?: Record<string, any>;
  notification_config?: {
    on_success: boolean;
    on_failure: boolean;
    email?: string;
  };
}

export interface ScheduleUpdate {
  name?: string;  // Update schedule name
  description?: string;  // Update description
  cron_expression?: string;
  timezone?: string;
  default_parameters?: Record<string, any>;
  notification_config?: Record<string, any>;
  is_active?: boolean;
  auto_pause_on_failure?: boolean;
  failure_threshold?: number;
  cost_limit?: number;
}

export interface SchedulePreset {
  id: string;
  name: string;
  description: string;
  icon?: any;
  type: 'daily' | 'interval' | 'weekly' | 'monthly' | 'custom';
  cron?: string;
  intervalOptions?: number[];
  monthlyOptions?: string[];
}

export interface ScheduleConfig {
  name?: string;  // Custom name for the schedule
  description?: string;  // Optional description
  type: 'daily' | 'interval' | 'weekly' | 'monthly' | 'custom';
  intervalDays?: number;
  lookbackDays?: number;  // Custom lookback window
  dateRangeType?: 'rolling' | 'fixed';  // How date range is calculated
  windowSizeDays?: number;  // Explicit window size for clarity (alias for lookbackDays)
  timezone: string;
  executeTime: string;
  dayOfWeek?: number; // 0-6 (Sunday-Saturday)
  dayOfMonth?: number; // 1-31
  weekOfMonth?: number; // 1-5
  monthlyType?: 'specific' | 'first' | 'last' | 'firstBusiness' | 'lastBusiness';
  cronExpression?: string;
  parameters: Record<string, any>;
  notifications: {
    onSuccess: boolean;
    onFailure: boolean;
    email?: string;
  };
  autoPauseOnFailure?: boolean;
  costLimit?: number;
}