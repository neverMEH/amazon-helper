/**
 * API service for template execution operations
 *
 * Handles immediate execution and recurring schedule creation for instance templates.
 */

import api from './api';
import type {
  TemplateExecutionRequest,
  TemplateExecutionResponse,
  TemplateScheduleRequest,
  TemplateScheduleResponse,
} from '../types/templateExecution';

/**
 * Template Execution Service
 *
 * Provides methods for executing instance templates immediately or creating
 * recurring schedules with rolling date range support.
 */
export const templateExecutionService = {
  /**
   * Execute a template immediately (run once)
   *
   * Creates a workflow execution that starts immediately with the specified
   * date range and optional Snowflake integration.
   *
   * @param instanceId - Instance UUID (not the AMC instance string)
   * @param templateId - Template identifier (format: tpl_inst_xxx)
   * @param data - Execution request with date range and Snowflake config
   * @returns Promise resolving to execution details
   *
   * @example
   * ```typescript
   * const result = await templateExecutionService.execute(
   *   'uuid-instance-id',
   *   'tpl_inst_abc123def456',
   *   {
   *     name: 'Nike Brand - Top Products - 2025-10-01 - 2025-10-31',
   *     timeWindowStart: '2025-10-01',
   *     timeWindowEnd: '2025-10-31',
   *     snowflake_enabled: true,
   *     snowflake_table_name: 'amc_top_products',
   *   }
   * );
   * // Navigate to /executions page to monitor
   * ```
   */
  execute: async (
    instanceId: string,
    templateId: string,
    data: TemplateExecutionRequest
  ): Promise<TemplateExecutionResponse> => {
    try {
      const response = await api.post<TemplateExecutionResponse>(
        `/instances/${instanceId}/templates/${templateId}/execute`,
        data
      );
      return response.data;
    } catch (error: any) {
      // Enhanced error handling
      if (error.response?.status === 404) {
        throw new Error('Template not found or access denied');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      } else if (error.response?.status === 400) {
        const detail = error.response?.data?.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const messages = detail.map((d: any) => `${d.loc?.join(' > ')}: ${d.msg}`);
          throw new Error(`Validation error: ${messages.join(', ')}`);
        }
        throw new Error(detail || 'Invalid request data');
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Failed to create execution. Please try again.');
      }
      throw error;
    }
  },

  /**
   * Create a recurring schedule for a template
   *
   * Creates a workflow and schedule that will execute the template on the
   * specified frequency with rolling date range support.
   *
   * @param instanceId - Instance UUID (not the AMC instance string)
   * @param templateId - Template identifier (format: tpl_inst_xxx)
   * @param data - Schedule request with frequency and date range config
   * @returns Promise resolving to schedule details
   *
   * @example
   * ```typescript
   * const result = await templateExecutionService.createSchedule(
   *   'uuid-instance-id',
   *   'tpl_inst_abc123def456',
   *   {
   *     name: 'Nike Brand - Weekly Top Products - Rolling 30 Days',
   *     schedule_config: {
   *       frequency: 'weekly',
   *       time: '09:00',
   *       lookback_days: 30,
   *       date_range_type: 'rolling',
   *       timezone: 'America/New_York',
   *       day_of_week: 1, // Monday
   *     }
   *   }
   * );
   * // Navigate to /schedules page to view
   * ```
   */
  createSchedule: async (
    instanceId: string,
    templateId: string,
    data: TemplateScheduleRequest
  ): Promise<TemplateScheduleResponse> => {
    try {
      const response = await api.post<TemplateScheduleResponse>(
        `/instances/${instanceId}/templates/${templateId}/schedule`,
        data
      );
      return response.data;
    } catch (error: any) {
      // Enhanced error handling
      if (error.response?.status === 404) {
        throw new Error('Template not found or access denied');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in again.');
      } else if (error.response?.status === 400 || error.response?.status === 422) {
        const detail = error.response?.data?.detail;
        if (Array.isArray(detail)) {
          // Pydantic validation errors
          const messages = detail.map((d: any) => `${d.loc?.join(' > ')}: ${d.msg}`);
          throw new Error(`Validation error: ${messages.join(', ')}`);
        }
        throw new Error(detail || 'Invalid schedule configuration');
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Failed to create schedule. Please try again.');
      }
      throw error;
    }
  },
};

/**
 * Helper function to generate execution name
 *
 * Format: {Brand} - {Template} - {StartDate} - {EndDate}
 *
 * @param brandName - Brand name or instance name
 * @param templateName - Template name
 * @param startDate - Start date in YYYY-MM-DD format
 * @param endDate - End date in YYYY-MM-DD format
 * @returns Formatted execution name
 *
 * @example
 * ```typescript
 * const name = generateExecutionName('Nike Brand', 'Top Products', '2025-10-01', '2025-10-31');
 * // Returns: "Nike Brand - Top Products - 2025-10-01 - 2025-10-31"
 * ```
 */
export function generateExecutionName(
  brandName: string,
  templateName: string,
  startDate: string,
  endDate: string
): string {
  return `${brandName} - ${templateName} - ${startDate} - ${endDate}`;
}

/**
 * Helper function to calculate default date range accounting for AMC lag
 *
 * AMC has a 14-day data processing lag, so we always subtract 14 days
 * from today when calculating the end date.
 *
 * @param windowDays - Number of days in the lookback window (default: 30)
 * @returns Object with start and end dates in YYYY-MM-DD format
 *
 * @example
 * ```typescript
 * const { start, end } = calculateDefaultDateRange(30);
 * // If today is 2025-10-15:
 * // start = "2025-09-01" (Oct 1 - 14 days AMC lag - 30 days window)
 * // end = "2025-10-01" (Oct 15 - 14 days AMC lag)
 * ```
 */
export function calculateDefaultDateRange(windowDays: number = 30): {
  start: string;
  end: string;
} {
  const AMC_LAG_DAYS = 14;

  const today = new Date();

  // Calculate end date (account for AMC lag)
  const endDate = new Date(today);
  endDate.setDate(endDate.getDate() - AMC_LAG_DAYS);

  // Calculate start date (apply lookback window)
  const startDate = new Date(endDate);
  startDate.setDate(startDate.getDate() - windowDays);

  return {
    start: startDate.toISOString().split('T')[0],
    end: endDate.toISOString().split('T')[0],
  };
}

/**
 * Helper function to format schedule config for display
 *
 * @param config - Schedule configuration
 * @returns Human-readable schedule description
 *
 * @example
 * ```typescript
 * const description = formatScheduleDescription({
 *   frequency: 'weekly',
 *   time: '09:00',
 *   day_of_week: 1,
 *   timezone: 'America/New_York'
 * });
 * // Returns: "Every Monday at 09:00 America/New_York"
 * ```
 */
export function formatScheduleDescription(config: {
  frequency: string;
  time: string;
  day_of_week?: number;
  day_of_month?: number;
  timezone: string;
}): string {
  const { frequency, time, day_of_week, day_of_month, timezone } = config;

  let frequencyText = '';

  if (frequency === 'daily') {
    frequencyText = 'Every day';
  } else if (frequency === 'weekly') {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayName = days[day_of_week ?? 1];
    frequencyText = `Every ${dayName}`;
  } else if (frequency === 'monthly') {
    const day = day_of_month ?? 1;
    frequencyText = `Every month on the ${day}${getOrdinalSuffix(day)}`;
  }

  return `${frequencyText} at ${time} ${timezone}`;
}

/**
 * Helper to get ordinal suffix for day numbers (1st, 2nd, 3rd, etc.)
 */
function getOrdinalSuffix(day: number): string {
  if (day >= 11 && day <= 13) return 'th';
  switch (day % 10) {
    case 1:
      return 'st';
    case 2:
      return 'nd';
    case 3:
      return 'rd';
    default:
      return 'th';
  }
}

export default templateExecutionService;
