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
  backfill_period?: number; // Days to backfill
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