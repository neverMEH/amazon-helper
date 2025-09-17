import api from './api';

export interface ReportBuilderSubmitRequest {
  workflow_id: string;
  instance_id: string;
  parameters: Record<string, any>;
  lookback_config: {
    type: 'relative' | 'custom';
    value?: number;
    unit?: 'days' | 'weeks' | 'months';
    start_date?: string;
    end_date?: string;
  };
  schedule_config: {
    type: 'once' | 'scheduled' | 'backfill_with_schedule';
    frequency?: 'daily' | 'weekly' | 'monthly';
    time?: string;
    timezone?: string;
    day_of_week?: number;
    day_of_month?: number;
    backfill_config?: {
      enabled: boolean;
      periods: number;
      segmentation: 'daily' | 'weekly' | 'monthly';
    };
  };
}

export interface ReportBuilderValidateResponse {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
  parameter_summary?: Record<string, any>;
}

export interface ReportBuilderPreviewResponse {
  schedule_preview: {
    next_runs: string[];
    frequency_description: string;
    timezone: string;
  };
  backfill_preview?: {
    total_periods: number;
    estimated_duration: string;
    parallel_executions: number;
    segments: Array<{
      period: number;
      start_date: string;
      end_date: string;
    }>;
  };
  cost_estimate?: {
    data_scanned: string;
    estimated_cost: string;
    query_complexity: 'Low' | 'Medium' | 'High';
  };
}

export interface ReportBuilderReviewResponse {
  configuration_summary: Record<string, any>;
  validation_status: {
    passed: boolean;
    warnings?: string[];
  };
  sql_preview: string;
  estimated_first_run?: string;
}

export interface ReportBuilderSubmitResponse {
  success: boolean;
  report_id?: string;
  schedule_id?: string;
  collection_id?: string;
  next_run?: string;
  message?: string;
  error?: string;
}

export interface BackfillProgress {
  totalPeriods: number;
  completedPeriods: number;
  failedPeriods: number;
  inProgressPeriods: number;
  estimatedTimeRemaining: string;
  currentBatch: number;
  totalBatches: number;
}

class ReportBuilderService {
  /**
   * Validate parameters for a report configuration
   */
  async validateParameters(request: {
    workflow_id: string;
    parameters: Record<string, any>;
    lookback_config: ReportBuilderSubmitRequest['lookback_config'];
  }): Promise<ReportBuilderValidateResponse> {
    const response = await api.post('/api/report-builder/validate-parameters', request);
    return response.data;
  }

  /**
   * Preview schedule configuration
   */
  async previewSchedule(request: {
    workflow_id: string;
    instance_id: string;
    lookback_config: ReportBuilderSubmitRequest['lookback_config'];
    schedule_config: ReportBuilderSubmitRequest['schedule_config'];
  }): Promise<ReportBuilderPreviewResponse> {
    const response = await api.post('/api/report-builder/preview-schedule', request);
    return response.data;
  }

  /**
   * Get review summary for configuration
   */
  async review(request: ReportBuilderSubmitRequest): Promise<ReportBuilderReviewResponse> {
    const response = await api.post('/api/report-builder/review', request);
    return response.data;
  }

  /**
   * Submit report configuration
   */
  async submit(request: ReportBuilderSubmitRequest): Promise<ReportBuilderSubmitResponse> {
    const response = await api.post('/api/report-builder/submit', request);
    return response.data;
  }

  /**
   * Get backfill progress for a collection
   */
  async getBackfillProgress(collectionId: string): Promise<BackfillProgress> {
    const response = await api.get(`/api/data-collections/${collectionId}/progress`);

    // Transform the response to match our interface
    const data = response.data;
    return {
      totalPeriods: data.total_periods || 52,
      completedPeriods: data.completed_periods || 0,
      failedPeriods: data.failed_periods || 0,
      inProgressPeriods: data.in_progress_periods || 0,
      estimatedTimeRemaining: data.estimated_time_remaining || 'Calculating...',
      currentBatch: data.current_batch || 1,
      totalBatches: data.total_batches || Math.ceil(52 / 5),
    };
  }

  /**
   * Cancel a report submission
   */
  async cancel(reportId: string): Promise<void> {
    await api.post(`/api/reports/${reportId}/cancel`);
  }

  /**
   * Retry a failed report
   */
  async retry(reportId: string): Promise<ReportBuilderSubmitResponse> {
    const response = await api.post(`/api/reports/${reportId}/retry`);
    return response.data;
  }

  /**
   * Get available instances for report builder
   */
  async getAvailableInstances(): Promise<Array<{
    id: string;
    instance_id: string;
    instance_name: string;
    account_name: string;
  }>> {
    const response = await api.get('/api/instances/');
    return response.data;
  }

  /**
   * Get workflow details for report builder
   */
  async getWorkflow(workflowId: string): Promise<{
    id: string;
    name: string;
    sql_query: string;
    parameters?: Record<string, any>;
    description?: string;
  }> {
    const response = await api.get(`/api/workflows/${workflowId}`);
    return response.data;
  }
}

export const reportBuilderService = new ReportBuilderService();