/**
 * Types for creating a schedule from an execution
 * Used by CreateScheduleFromExecutionModal
 */

import type { AMCExecutionDetail } from './amcExecution';

/**
 * Schedule frequency options
 */
export type ScheduleFrequency = 'daily' | 'weekly' | 'monthly';

/**
 * Snowflake upload strategy options
 */
export type SnowflakeStrategy = 'upsert' | 'append' | 'replace' | 'create_new';

/**
 * Data extracted from an execution for pre-populating the schedule wizard
 */
export interface ExecutionScheduleData {
  // Required - schedule needs a workflow to run
  workflowId: string;

  // For display/context
  workflowName?: string;
  sqlQuery?: string;
  instanceId: string;
  instanceInfo?: {
    instanceId: string;
    instanceName: string;
    region?: string;
    accountId?: string;
    accountName?: string;
  };

  // Date range from execution parameters
  dateRange?: {
    start?: string;
    end?: string;
  };

  // Calculated lookback days
  lookbackDays: number;

  // Snowflake configuration from execution
  snowflakeEnabled: boolean;
  snowflakeTableName?: string;
  snowflakeSchemaName?: string;
}

/**
 * Wizard step state
 */
export interface ScheduleWizardState {
  // Step 1: Schedule Type
  frequency: ScheduleFrequency;

  // Step 2: Timing
  executeTime: string;  // HH:mm format
  timezone: string;
  dayOfWeek?: number;   // 0-6 (Sunday-Saturday) for weekly
  dayOfMonth?: number;  // 1-31 for monthly

  // Step 3: Date Range
  lookbackDays: number;
  dateRangeType: 'rolling' | 'fixed';

  // Step 4: Snowflake Config
  snowflakeEnabled: boolean;
  snowflakeTableName: string;
  snowflakeSchemaName: string;
  snowflakeStrategy: SnowflakeStrategy;

  // Schedule metadata
  name: string;
  description: string;
}

/**
 * Props for CreateScheduleFromExecutionModal
 */
export interface CreateScheduleFromExecutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  execution: AMCExecutionDetail;
  onSuccess?: () => void;
}

/**
 * API request payload for creating schedule from preset
 */
export interface ScheduleCreateFromExecutionPayload {
  preset_type: ScheduleFrequency;
  name: string;
  description?: string;
  timezone: string;
  execute_time: string;
  day_of_week?: number;
  day_of_month?: number;
  lookback_days: number;
  date_range_type: 'rolling' | 'fixed';
  parameters?: Record<string, unknown>;
  snowflake_enabled: boolean;
  snowflake_table_name?: string;
  snowflake_schema_name?: string;
  snowflake_strategy?: SnowflakeStrategy;
}

/**
 * Helper to extract schedule data from an execution
 */
export function extractExecutionScheduleData(execution: AMCExecutionDetail): ExecutionScheduleData | null {
  const workflowId = execution.workflowId || execution.workflowInfo?.id;

  if (!workflowId) {
    return null;
  }

  // Extract date range from execution parameters
  const params = execution.executionParameters || {};
  const startDate = params.timeWindowStart || params.startDate || params.start_date;
  const endDate = params.timeWindowEnd || params.endDate || params.end_date;

  // Calculate lookback days
  const lookbackDays = calculateLookbackDays(startDate, endDate);

  return {
    workflowId,
    workflowName: execution.workflowName || execution.workflowInfo?.name,
    sqlQuery: execution.sqlQuery || execution.workflowInfo?.sqlQuery,
    instanceId: execution.instanceId,
    instanceInfo: execution.instanceInfo,
    dateRange: startDate && endDate ? { start: startDate, end: endDate } : undefined,
    lookbackDays,
    snowflakeEnabled: execution.snowflake_enabled || execution.snowflakeEnabled || false,
    snowflakeTableName: execution.snowflake_table_name || execution.snowflakeTableName,
    snowflakeSchemaName: execution.snowflake_schema_name || execution.snowflakeSchemaName,
  };
}

/**
 * Calculate lookback days from date range
 */
export function calculateLookbackDays(startDate?: string, endDate?: string): number {
  if (!startDate || !endDate) {
    return 30; // Default lookback
  }

  try {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end.getTime() - start.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    // Validate the result
    if (diffDays > 0 && diffDays <= 365) {
      return diffDays;
    }
  } catch {
    // Invalid date format
  }

  return 30; // Default if calculation fails
}

/**
 * Suggest frequency based on lookback days
 */
export function suggestFrequency(lookbackDays: number): ScheduleFrequency {
  if (lookbackDays <= 7) return 'daily';
  if (lookbackDays <= 30) return 'weekly';
  return 'monthly';
}

/**
 * Get default wizard state from execution data
 */
export function getDefaultWizardState(data: ExecutionScheduleData): ScheduleWizardState {
  const suggestedFrequency = suggestFrequency(data.lookbackDays);
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // Generate default schedule name
  const baseName = data.workflowName || 'Scheduled Query';
  const defaultName = `${baseName} - ${suggestedFrequency.charAt(0).toUpperCase() + suggestedFrequency.slice(1)}`;

  return {
    frequency: suggestedFrequency,
    executeTime: '02:00',
    timezone: userTimezone,
    dayOfWeek: suggestedFrequency === 'weekly' ? 1 : undefined, // Monday
    dayOfMonth: suggestedFrequency === 'monthly' ? 1 : undefined, // 1st of month
    lookbackDays: data.lookbackDays,
    dateRangeType: 'rolling',
    snowflakeEnabled: data.snowflakeEnabled,
    snowflakeTableName: data.snowflakeTableName || '',
    snowflakeSchemaName: data.snowflakeSchemaName || '',
    snowflakeStrategy: 'upsert',
    name: defaultName,
    description: `Created from execution on ${new Date().toLocaleDateString()}`,
  };
}

/**
 * Common timezone options
 */
export const TIMEZONE_OPTIONS = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
  { value: 'UTC', label: 'UTC' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET/CEST)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET/CEST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST/AEDT)' },
];

/**
 * Days of week for weekly schedules
 */
export const DAYS_OF_WEEK = [
  { value: 0, label: 'Sunday' },
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
];

/**
 * Lookback presets for date range step
 */
export const LOOKBACK_PRESETS = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 60, label: '60 days' },
  { value: 90, label: '90 days' },
];
