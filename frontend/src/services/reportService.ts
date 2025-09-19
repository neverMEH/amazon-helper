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

    // For now, we need to use the existing workflow-based approach
    // until we implement proper ad-hoc report execution in the backend

    // First create the workflow (which acts as our report)
    const workflowData = {
      name: data.name,
      description: data.description,
      instance_id: data.instance_id,
      sql_query: data.custom_sql || '',  // Will be populated from template if template_id provided
      parameters: data.parameters,
      template_id: data.template_id,
    };

    console.log('Creating workflow with data:', workflowData);
    const workflow = await workflowService.createWorkflow(workflowData);

    // If it's a recurring report, create a schedule
    if (data.execution_type === 'recurring' && data.schedule_config) {
      const scheduleData = {
        instance_id: data.instance_id,
        frequency: data.schedule_config.frequency,
        time_of_day: data.schedule_config.time,
        day_of_week: data.schedule_config.day_of_week,
        day_of_month: data.schedule_config.day_of_month,
        timezone: data.schedule_config.timezone || 'UTC',
        is_active: true,
        execution_parameters: data.parameters,
      };
      await scheduleService.createSchedulePreset(workflow.id, scheduleData as any);
    }

    // If it's a one-time execution, run it immediately with date parameters
    if (data.execution_type === 'once') {
      console.log('Executing workflow immediately with date range:', data.time_window_start, 'to', data.time_window_end);

      // Include the date range in the parameters for execution
      const executionParams = {
        ...data.parameters,
        timeWindowStart: data.time_window_start,
        timeWindowEnd: data.time_window_end
      };

      await workflowService.executeWorkflow(
        workflow.id,
        data.instance_id,
        executionParams
      );
    } else if (data.execution_type === 'backfill') {
      // For backfill, also execute with date parameters
      await workflowService.executeWorkflow(
        workflow.id,
        data.instance_id,
        data.parameters
      );
    }

    console.log('Report creation complete, returning workflow:', workflow);
    return workflow;
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