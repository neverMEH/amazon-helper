import api from './api';
import type { Report, CreateReportRequest } from '../types/report';
import { workflowService } from './workflowService';
import { scheduleService } from './scheduleService';
import { reportApiService } from './reportApiService';

export const reportService = {
  // Report CRUD operations - Using workflows API
  listReports: async () => {
    // Get workflows that were created from templates (reports)
    const response = await api.get('/workflows/');
    const workflows = response.data;

    // Transform workflows to Report format
    return {
      data: workflows.filter((w: any) => w.template_id).map((w: any) => ({
        id: w.id,
        name: w.name,
        description: w.description,
        template_id: w.template_id,
        instance_id: w.instance_id,
        parameters: w.parameters || {},
        status: w.status || 'active',
        created_at: w.created_at,
        updated_at: w.updated_at,
      }))
    };
  },

  getReport: async (id: string) => {
    const workflow = await workflowService.getWorkflow(id);
    return workflow;
  },

  createReport: async (data: CreateReportRequest) => {
    console.log('reportService.createReport called with:', data);

    // For Report Builder, we need to use the report API endpoints
    // First create the report definition
    const reportData = {
      name: data.name,
      description: data.description,
      template_id: data.template_id || '',
      instance_id: data.instance_id,
      parameters: data.parameters,
    };

    console.log('Creating report definition with data:', reportData);
    const report = await reportApiService.createReport(reportData);
    const reportId = report.data.id;

    // Handle different execution types
    if (data.execution_type === 'once') {
      // Execute immediately with date range
      console.log('Executing report immediately with date range:', data.time_window_start, 'to', data.time_window_end);
      await reportApiService.executeReport(reportId, {
        parameters: data.parameters,
        time_window_start: data.time_window_start,
        time_window_end: data.time_window_end,
      });
    } else if (data.execution_type === 'recurring' && data.schedule_config) {
      // Create a schedule
      const scheduleData = {
        frequency: data.schedule_config.frequency,
        time_of_day: data.schedule_config.time,
        day_of_week: data.schedule_config.day_of_week,
        day_of_month: data.schedule_config.day_of_month,
        timezone: data.schedule_config.timezone || 'UTC',
        is_active: true,
        parameters: data.parameters,
      };
      await reportApiService.createSchedule(reportId, scheduleData);
    } else if (data.execution_type === 'backfill') {
      // Create a backfill collection
      const backfillData = {
        start_date: data.time_window_start || '',
        end_date: data.time_window_end || '',
        frequency: 'weekly' as const,
      };
      await reportApiService.createBackfill(reportId, backfillData);
    }

    console.log('Report creation complete, returning report:', report.data);
    return report.data;
  },

  updateReport: async (id: string, data: Partial<Report>) => {
    return await workflowService.updateWorkflow(id, {
      name: data.name,
      description: data.description,
      parameters: data.parameters,
    });
  },

  deleteReport: async (id: string) => {
    return await workflowService.deleteWorkflow(id);
  },

  // Report execution operations
  runReport: async (id: string) => {
    const workflow = await workflowService.getWorkflow(id);
    return await workflowService.executeWorkflow(
      id,
      workflow.instance_id,
      workflow.parameters || {}
    );
  },

  pauseReport: async (id: string) => {
    // Find and disable associated schedule
    const schedules = await scheduleService.listWorkflowSchedules(id);
    const schedule = schedules[0];  // Get first active schedule
    if (schedule) {
      await scheduleService.disableSchedule(schedule.id);
    }
    return { id, status: 'paused' } as any;
  },

  resumeReport: async (id: string) => {
    // Find and enable associated schedule
    const schedules = await scheduleService.listWorkflowSchedules(id);
    const schedule = schedules[0];  // Get first inactive schedule
    if (schedule) {
      await scheduleService.enableSchedule(schedule.id);
    }
    return { id, status: 'active' } as any;
  },

  // Report executions
  listExecutions: async (reportId: string) => {
    const executions = await workflowService.getWorkflowExecutions(reportId);
    return executions;
  },

  getExecution: async (_reportId: string, executionId: string) => {
    return await workflowService.getExecutionDetail(executionId);
  },

  // Backfill operations - using collection API
  startBackfill: async (_reportId: string, _period: number) => {
    // This would use data collections API for backfill
    return { message: 'Backfill started', task_id: 'temp-id' };
  },

  getBackfillStatus: async (_reportId: string, _taskId: string) => {
    return { status: 'running', progress: 50 };
  },
};

// Export individual functions for backward compatibility
export const {
  listReports,
  getReport,
  createReport,
  updateReport,
  deleteReport,
  runReport,
  pauseReport,
  resumeReport,
  listExecutions,
  getExecution,
  startBackfill,
  getBackfillStatus,
} = reportService;