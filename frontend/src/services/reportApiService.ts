import api from './api';

// Report definition management
export const reportApiService = {
  // List all report definitions
  listReports: async () => {
    return await api.get('/reports/');
  },

  // Get a specific report definition
  getReport: async (id: string) => {
    return await api.get(`/reports/${id}`);
  },

  // Create a new report definition
  createReport: async (data: {
    name: string;
    description?: string;
    template_id: string;
    instance_id: string;
    parameters: Record<string, any>;
  }) => {
    return await api.post('/reports/', data);
  },

  // Update a report definition
  updateReport: async (id: string, data: any) => {
    return await api.put(`/reports/${id}`, data);
  },

  // Delete a report definition
  deleteReport: async (id: string) => {
    return await api.delete(`/reports/${id}`);
  },

  // Execute a report ad-hoc
  executeReport: async (reportId: string, data: {
    parameters?: Record<string, any>;
    time_window_start?: string;
    time_window_end?: string;
  }) => {
    return await api.post(`/reports/${reportId}/execute`, data);
  },

  // Get executions for a report
  listExecutions: async (reportId: string) => {
    return await api.get(`/reports/${reportId}/executions`);
  },

  // Get execution status
  getExecution: async (executionId: string) => {
    return await api.get(`/reports/executions/${executionId}`);
  },

  // Schedule operations
  createSchedule: async (reportId: string, data: any) => {
    return await api.post(`/reports/${reportId}/schedule`, data);
  },

  updateSchedule: async (reportId: string, scheduleId: string, data: any) => {
    return await api.put(`/reports/${reportId}/schedules/${scheduleId}`, data);
  },

  deleteSchedule: async (reportId: string, scheduleId: string) => {
    return await api.delete(`/reports/${reportId}/schedules/${scheduleId}`);
  },

  pauseSchedule: async (scheduleId: string) => {
    return await api.post(`/schedules/${scheduleId}/pause`);
  },

  resumeSchedule: async (scheduleId: string) => {
    return await api.post(`/schedules/${scheduleId}/resume`);
  },

  // Backfill operations
  createBackfill: async (reportId: string, data: {
    start_date: string;
    end_date: string;
    frequency: 'daily' | 'weekly';
  }) => {
    return await api.post(`/reports/${reportId}/backfill`, data);
  },

  getBackfillStatus: async (reportId: string, collectionId: string) => {
    return await api.get(`/reports/${reportId}/backfill/${collectionId}`);
  },
};