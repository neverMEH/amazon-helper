export interface Report {
  id: string;
  name: string;
  description?: string;
  template_id: string;
  instance_id: string;
  parameters: Record<string, any>;
  status: 'active' | 'paused' | 'failed' | 'completed';
  frequency?: 'once' | 'daily' | 'weekly' | 'monthly';
  schedule_config?: ScheduleConfig;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
  updated_at: string;
  execution_count?: number;
  success_count?: number;
  failure_count?: number;
}

export interface ScheduleConfig {
  frequency: 'daily' | 'weekly' | 'monthly';
  time?: string; // HH:MM format
  day_of_week?: number; // 0-6 for weekly
  day_of_month?: number; // 1-31 for monthly
  timezone?: string;
  lookback_days?: number; // Number of days to look back for data (unified terminology with schedule.ts)
  date_range_type?: 'rolling' | 'fixed';  // How date range is calculated
  window_size_days?: number;  // Explicit window size for clarity (alias for lookback_days)
  // Deprecated: use lookback_days instead
  backfill_period?: number; // @deprecated - use lookback_days
}

export interface ReportExecution {
  id: string;
  report_id: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  started_at: string;
  completed_at?: string;
  result_data?: any;
  error_message?: string;
  execution_time_ms?: number;
}

export interface CreateReportRequest {
  name: string;
  description?: string;
  template_id?: string;
  custom_sql?: string;
  instance_id: string;
  parameters: Record<string, any>;
  execution_type: 'once' | 'recurring' | 'backfill';
  schedule_config?: ScheduleConfig;
  time_window_start?: string; // ISO date string for ad-hoc execution
  time_window_end?: string; // ISO date string for ad-hoc execution
  // Snowflake integration options
  snowflake_enabled?: boolean;
  snowflake_table_name?: string;
  snowflake_schema_name?: string;
}

export interface ParameterDefinition {
  type: 'string' | 'number' | 'date' | 'boolean' | 'array' | 'select';
  label: string;
  required: boolean;
  description?: string;
  default?: any;
  options?: Array<{ value: string; label: string }>;
  min?: number;
  max?: number;
  pattern?: string;
}

export interface SnowflakeConfiguration {
  id: string;
  user_id: string;
  account_identifier: string;
  warehouse: string;
  database: string;
  schema: string;
  role?: string;
  username?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SnowflakeTable {
  name: string;
  type: string;
  row_count: number;
  size_bytes: number;
  created: string;
  last_altered: string;
}