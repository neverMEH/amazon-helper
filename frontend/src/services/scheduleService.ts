/**
 * Schedule service for API communication
 */

import api from './api';
import type {
  Schedule,
  ScheduleRun,
  ScheduleMetrics,
  ScheduleCreatePreset,
  ScheduleCreateCustom,
  ScheduleUpdate
} from '../types/schedule';

class ScheduleService {
  /**
   * Create a schedule from a preset
   */
  async createSchedulePreset(workflowId: string, data: ScheduleCreatePreset): Promise<Schedule> {
    const response = await api.post(`/workflows/${workflowId}/schedules`, data);
    return response.data;
  }

  /**
   * Create a schedule with custom CRON expression
   */
  async createScheduleCustom(workflowId: string, data: ScheduleCreateCustom): Promise<Schedule> {
    const response = await api.post(`/workflows/${workflowId}/schedules/custom`, data);
    return response.data;
  }

  /**
   * List schedules for a workflow
   */
  async listWorkflowSchedules(
    workflowId: string,
    params?: {
      is_active?: boolean;
      limit?: number;
      offset?: number;
    }
  ): Promise<Schedule[]> {
    const response = await api.get(`/workflows/${workflowId}/schedules`, { params });
    return response.data;
  }

  /**
   * List all schedules for the current user
   */
  async listAllSchedules(params?: {
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<Schedule[]> {
    const response = await api.get('/schedules', { params });
    return response.data;
  }

  /**
   * Get schedule details
   */
  async getSchedule(scheduleId: string): Promise<Schedule> {
    const response = await api.get(`/schedules/${scheduleId}`);
    return response.data;
  }

  /**
   * Update a schedule
   */
  async updateSchedule(scheduleId: string, data: ScheduleUpdate): Promise<Schedule> {
    const response = await api.put(`/schedules/${scheduleId}`, data);
    return response.data;
  }

  /**
   * Delete a schedule
   */
  async deleteSchedule(scheduleId: string): Promise<void> {
    await api.delete(`/schedules/${scheduleId}`);
  }

  /**
   * Enable a schedule
   */
  async enableSchedule(scheduleId: string): Promise<void> {
    await api.post(`/schedules/${scheduleId}/enable`);
  }

  /**
   * Disable a schedule
   */
  async disableSchedule(scheduleId: string): Promise<void> {
    await api.post(`/schedules/${scheduleId}/disable`);
  }

  /**
   * Get next run times for a schedule
   */
  async getNextRuns(scheduleId: string, count: number = 10): Promise<string[]> {
    const response = await api.get(`/schedules/${scheduleId}/next-runs`, {
      params: { count }
    });
    return response.data.next_runs;
  }

  /**
   * Execute a test run of a schedule (scheduled for 1 minute from now)
   */
  async testRun(scheduleId: string, parameters?: Record<string, any>): Promise<{
    message: string;
    scheduled_at: string;
    run_id: string;
  }> {
    const response = await api.post(`/schedules/${scheduleId}/test-run`, parameters);
    return response.data;
  }

  /**
   * Schedule a run at a specific time
   */
  async scheduleRunAtTime(
    scheduleId: string, 
    scheduledTime: Date, 
    parameters?: Record<string, any>
  ): Promise<{
    message: string;
    scheduled_at: string;
    run_id: string;
  }> {
    const response = await api.post(`/schedules/${scheduleId}/schedule-run`, {
      scheduled_time: scheduledTime.toISOString(),
      parameters
    });
    return response.data;
  }

  /**
   * Get schedule run history
   */
  async getScheduleRuns(
    scheduleId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<{ runs: ScheduleRun[]; total_count: number; limit: number; offset: number } | ScheduleRun[]> {
    const response = await api.get(`/schedules/${scheduleId}/runs`, { params });
    // Handle both old format (array) and new format (object with runs and total_count)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data;
  }

  /**
   * Get schedule metrics
   */
  async getScheduleMetrics(
    scheduleId: string,
    periodDays: number = 30
  ): Promise<ScheduleMetrics> {
    const response = await api.get(`/schedules/${scheduleId}/metrics`, {
      params: { period_days: periodDays }
    });
    return response.data;
  }

  /**
   * Generate CRON expression from user-friendly inputs
   */
  generateCronExpression(config: {
    type: string;
    intervalDays?: number;
    executeTime: string;
    dayOfWeek?: number;
    dayOfMonth?: number;
    monthlyType?: string;
  }): string {
    const [hour, minute] = config.executeTime.split(':');
    
    switch (config.type) {
      case 'daily':
        return `${minute} ${hour} * * *`;
      
      case 'interval':
        if (config.intervalDays === 1) {
          return `${minute} ${hour} * * *`;
        }
        return `${minute} ${hour} */${config.intervalDays} * *`;
      
      case 'weekly':
        return `${minute} ${hour} * * ${config.dayOfWeek || 1}`;
      
      case 'monthly':
        if (config.monthlyType === 'last') {
          return `${minute} ${hour} L * *`;
        } else if (config.monthlyType === 'firstBusiness') {
          return `${minute} ${hour} 1-3 * 1-5`;
        } else if (config.monthlyType === 'lastBusiness') {
          return `${minute} ${hour} L * 1-5`;
        } else {
          return `${minute} ${hour} ${config.dayOfMonth || 1} * *`;
        }
      
      default:
        return `${minute} ${hour} * * *`;
    }
  }

  /**
   * Parse CRON expression to user-friendly format
   */
  parseCronExpression(cron: string): string {
    const parts = cron.split(' ');
    if (parts.length !== 5) return cron;

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
    const time = `${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;

    // Daily
    if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
      return `Daily at ${time}`;
    }

    // Every N days
    if (dayOfMonth.startsWith('*/') && month === '*' && dayOfWeek === '*') {
      const days = dayOfMonth.substring(2);
      return `Every ${days} days at ${time}`;
    }

    // Weekly
    if (dayOfMonth === '*' && month === '*' && dayOfWeek !== '*') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const dayIndex = parseInt(dayOfWeek);
      return `Every ${days[dayIndex]} at ${time}`;
    }

    // Monthly specific day
    if (dayOfMonth !== '*' && dayOfMonth !== 'L' && month === '*') {
      return `Monthly on day ${dayOfMonth} at ${time}`;
    }

    // Last day of month
    if (dayOfMonth === 'L' && month === '*' && dayOfWeek === '*') {
      return `Last day of month at ${time}`;
    }

    // Business days
    if (dayOfMonth === 'L' && dayOfWeek === '1-5') {
      return `Last business day at ${time}`;
    }
    if (dayOfMonth === '1-3' && dayOfWeek === '1-5') {
      return `First business day at ${time}`;
    }

    return cron;
  }

  /**
   * Calculate next run time locally (for UI preview)
   */
  calculateNextRun(_cron: string, _timezone: string = 'UTC'): Date {
    // This is a simplified calculation for UI preview
    // The actual calculation happens on the backend
    const now = new Date();
    return new Date(now.getTime() + 3600000); // Default to 1 hour from now
  }
}

export const scheduleService = new ScheduleService();