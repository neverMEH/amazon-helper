import api from './api';
import type { Report, CreateReportRequest, ReportExecution } from '../types/report';

export const reportService = {
  // Report CRUD operations
  listReports: () => api.get<Report[]>('/reports/'),

  getReport: (id: string) => api.get<Report>(`/reports/${id}`),

  createReport: (data: CreateReportRequest) => api.post<Report>('/reports/', data),

  updateReport: (id: string, data: Partial<Report>) =>
    api.put<Report>(`/reports/${id}`, data),

  deleteReport: (id: string) => api.delete(`/reports/${id}`),

  // Report execution operations
  runReport: (id: string) =>
    api.post<ReportExecution>(`/reports/${id}/execute`),

  pauseReport: (id: string) =>
    api.post<Report>(`/reports/${id}/pause`),

  resumeReport: (id: string) =>
    api.post<Report>(`/reports/${id}/resume`),

  // Report executions
  listExecutions: (reportId: string) =>
    api.get<ReportExecution[]>(`/reports/${reportId}/executions`),

  getExecution: (reportId: string, executionId: string) =>
    api.get<ReportExecution>(`/reports/${reportId}/executions/${executionId}`),

  // Backfill operations
  startBackfill: (reportId: string, period: number) =>
    api.post<{ message: string; task_id: string }>(`/reports/${reportId}/backfill`, {
      period_days: period
    }),

  getBackfillStatus: (reportId: string, taskId: string) =>
    api.get<{ status: string; progress: number; message?: string }>(
      `/reports/${reportId}/backfill/${taskId}`
    ),
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