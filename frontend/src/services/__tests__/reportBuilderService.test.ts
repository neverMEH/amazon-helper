import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { reportBuilderService } from '../reportBuilderService';
import api from '../api';
import type {
  ReportBuilderSubmitRequest,
  ReportBuilderValidateResponse,
  ReportBuilderPreviewResponse,
  ReportBuilderReviewResponse,
  ReportBuilderSubmitResponse,
  BackfillProgress
} from '../reportBuilderService';

// Mock the api module
vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  }
}));

describe('ReportBuilderService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('validateParameters', () => {
    it('should validate parameters successfully', async () => {
      const mockResponse: ReportBuilderValidateResponse = {
        valid: true,
        warnings: ['Large date range selected'],
        parameter_summary: {
          campaigns: ['campaign1', 'campaign2'],
          lookback_days: 30
        }
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request = {
        workflow_id: 'workflow123',
        parameters: { campaigns: ['campaign1', 'campaign2'] },
        lookback_config: {
          type: 'relative' as const,
          value: 30,
          unit: 'days' as const
        }
      };

      const result = await reportBuilderService.validateParameters(request);

      expect(api.post).toHaveBeenCalledWith('/api/report-builder/validate-parameters', request);
      expect(result).toEqual(mockResponse);
    });

    it('should handle validation errors', async () => {
      const mockResponse: ReportBuilderValidateResponse = {
        valid: false,
        errors: ['Date range exceeds AMC limit', 'Invalid parameter format']
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request = {
        workflow_id: 'workflow123',
        parameters: {},
        lookback_config: {
          type: 'custom' as const,
          start_date: '2023-01-01',
          end_date: '2025-01-01'
        }
      };

      const result = await reportBuilderService.validateParameters(request);

      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(2);
    });

    it('should handle network errors', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Network error'));

      const request = {
        workflow_id: 'workflow123',
        parameters: {},
        lookback_config: {
          type: 'relative' as const,
          value: 7,
          unit: 'days' as const
        }
      };

      await expect(reportBuilderService.validateParameters(request)).rejects.toThrow('Network error');
    });
  });

  describe('previewSchedule', () => {
    it('should preview schedule configuration', async () => {
      const mockResponse: ReportBuilderPreviewResponse = {
        schedule_preview: {
          next_runs: ['2025-09-18T09:00:00', '2025-09-19T09:00:00'],
          frequency_description: 'Daily at 9:00 AM',
          timezone: 'America/New_York'
        },
        cost_estimate: {
          data_scanned: '1.5 TB',
          estimated_cost: '$75.00',
          query_complexity: 'Medium'
        }
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        lookback_config: {
          type: 'relative' as const,
          value: 7,
          unit: 'days' as const
        },
        schedule_config: {
          type: 'scheduled' as const,
          frequency: 'daily' as const,
          time: '09:00',
          timezone: 'America/New_York'
        }
      };

      const result = await reportBuilderService.previewSchedule(request);

      expect(api.post).toHaveBeenCalledWith('/api/report-builder/preview-schedule', request);
      expect(result.schedule_preview.frequency_description).toBe('Daily at 9:00 AM');
    });

    it('should handle backfill preview', async () => {
      const mockResponse: ReportBuilderPreviewResponse = {
        schedule_preview: {
          next_runs: ['2025-09-18T09:00:00'],
          frequency_description: 'Weekly on Monday',
          timezone: 'UTC'
        },
        backfill_preview: {
          total_periods: 52,
          estimated_duration: '4.3 hours',
          parallel_executions: 5,
          segments: [
            { period: 1, start_date: '2024-09-11', end_date: '2024-09-17' },
            { period: 2, start_date: '2024-09-18', end_date: '2024-09-24' }
          ]
        }
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        lookback_config: {
          type: 'custom' as const,
          start_date: '2024-09-17',
          end_date: '2025-09-17'
        },
        schedule_config: {
          type: 'backfill_with_schedule' as const,
          frequency: 'weekly' as const,
          backfill_config: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly' as const
          }
        }
      };

      const result = await reportBuilderService.previewSchedule(request);

      expect(result.backfill_preview).toBeDefined();
      expect(result.backfill_preview?.total_periods).toBe(52);
    });
  });

  describe('review', () => {
    it('should get review summary', async () => {
      const mockResponse: ReportBuilderReviewResponse = {
        configuration_summary: {
          workflow: 'Sales Performance Report',
          instance: 'Production AMC',
          lookback: 'Last 30 days',
          schedule: 'Daily at 9:00 AM EST'
        },
        validation_status: {
          passed: true,
          warnings: ['Large data volume expected']
        },
        sql_preview: 'SELECT * FROM campaigns WHERE date >= {{start_date}}',
        estimated_first_run: '2025-09-18T09:00:00'
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request: ReportBuilderSubmitRequest = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        parameters: { campaigns: ['c1'] },
        lookback_config: {
          type: 'relative',
          value: 30,
          unit: 'days'
        },
        schedule_config: {
          type: 'scheduled',
          frequency: 'daily',
          time: '09:00',
          timezone: 'America/New_York'
        }
      };

      const result = await reportBuilderService.review(request);

      expect(api.post).toHaveBeenCalledWith('/api/report-builder/review', request);
      expect(result.validation_status.passed).toBe(true);
      expect(result.sql_preview).toContain('SELECT * FROM campaigns');
    });
  });

  describe('submit', () => {
    it('should submit report configuration successfully', async () => {
      const mockResponse: ReportBuilderSubmitResponse = {
        success: true,
        report_id: 'report789',
        schedule_id: 'schedule456',
        collection_id: 'collection123',
        next_run: '2025-09-18T09:00:00',
        message: 'Report scheduled successfully'
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request: ReportBuilderSubmitRequest = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        parameters: {},
        lookback_config: {
          type: 'relative',
          value: 7,
          unit: 'days'
        },
        schedule_config: {
          type: 'once'
        }
      };

      const result = await reportBuilderService.submit(request);

      expect(api.post).toHaveBeenCalledWith('/api/report-builder/submit', request);
      expect(result.success).toBe(true);
      expect(result.report_id).toBe('report789');
    });

    it('should handle submission failure', async () => {
      const mockResponse: ReportBuilderSubmitResponse = {
        success: false,
        error: 'Invalid configuration: Missing required parameters'
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const request: ReportBuilderSubmitRequest = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        parameters: {},
        lookback_config: {
          type: 'relative',
          value: 7,
          unit: 'days'
        },
        schedule_config: {
          type: 'once'
        }
      };

      const result = await reportBuilderService.submit(request);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Missing required parameters');
    });

    it('should handle network timeout', async () => {
      vi.mocked(api.post).mockImplementation(() =>
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      );

      const request: ReportBuilderSubmitRequest = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        parameters: {},
        lookback_config: {
          type: 'relative',
          value: 7,
          unit: 'days'
        },
        schedule_config: {
          type: 'once'
        }
      };

      await expect(reportBuilderService.submit(request)).rejects.toThrow('Timeout');
    });
  });

  describe('getBackfillProgress', () => {
    it('should get backfill progress', async () => {
      const mockApiResponse = {
        total_periods: 52,
        completed_periods: 25,
        failed_periods: 2,
        in_progress_periods: 3,
        estimated_time_remaining: '2 hours 15 minutes',
        current_batch: 6,
        total_batches: 11
      };

      vi.mocked(api.get).mockResolvedValue({ data: mockApiResponse });

      const result = await reportBuilderService.getBackfillProgress('collection123');

      expect(api.get).toHaveBeenCalledWith('/api/data-collections/collection123/progress');
      expect(result).toEqual({
        totalPeriods: 52,
        completedPeriods: 25,
        failedPeriods: 2,
        inProgressPeriods: 3,
        estimatedTimeRemaining: '2 hours 15 minutes',
        currentBatch: 6,
        totalBatches: 11
      });
    });

    it('should handle missing progress data', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: {} });

      const result = await reportBuilderService.getBackfillProgress('collection123');

      expect(result).toEqual({
        totalPeriods: 52,
        completedPeriods: 0,
        failedPeriods: 0,
        inProgressPeriods: 0,
        estimatedTimeRemaining: 'Calculating...',
        currentBatch: 1,
        totalBatches: 11
      });
    });

    it('should handle progress API errors', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('API Error'));

      await expect(reportBuilderService.getBackfillProgress('collection123')).rejects.toThrow('API Error');
    });
  });

  describe('cancel', () => {
    it('should cancel report submission', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { success: true } });

      await reportBuilderService.cancel('report123');

      expect(api.post).toHaveBeenCalledWith('/api/reports/report123/cancel');
    });

    it('should handle cancel errors', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Cannot cancel completed report'));

      await expect(reportBuilderService.cancel('report123')).rejects.toThrow('Cannot cancel completed report');
    });
  });

  describe('retry', () => {
    it('should retry failed report', async () => {
      const mockResponse: ReportBuilderSubmitResponse = {
        success: true,
        report_id: 'report123-retry',
        message: 'Report retry initiated'
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const result = await reportBuilderService.retry('report123');

      expect(api.post).toHaveBeenCalledWith('/api/reports/report123/retry');
      expect(result.success).toBe(true);
      expect(result.report_id).toBe('report123-retry');
    });

    it('should handle retry failure', async () => {
      const mockResponse: ReportBuilderSubmitResponse = {
        success: false,
        error: 'Report is still running'
      };

      vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

      const result = await reportBuilderService.retry('report123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Report is still running');
    });
  });

  describe('getAvailableInstances', () => {
    it('should get available instances', async () => {
      const mockInstances = [
        { id: '1', instance_id: 'inst1', instance_name: 'Production', account_name: 'Account 1' },
        { id: '2', instance_id: 'inst2', instance_name: 'Development', account_name: 'Account 2' }
      ];

      vi.mocked(api.get).mockResolvedValue({ data: mockInstances });

      const result = await reportBuilderService.getAvailableInstances();

      expect(api.get).toHaveBeenCalledWith('/api/instances/');
      expect(result).toEqual(mockInstances);
      expect(result).toHaveLength(2);
    });

    it('should handle empty instances', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });

      const result = await reportBuilderService.getAvailableInstances();

      expect(result).toEqual([]);
    });
  });

  describe('getWorkflow', () => {
    it('should get workflow details', async () => {
      const mockWorkflow = {
        id: 'workflow123',
        name: 'Sales Performance',
        sql_query: 'SELECT * FROM campaigns',
        parameters: {
          campaigns: { type: 'array', required: true },
          start_date: { type: 'date', required: true }
        },
        description: 'Analyzes campaign performance metrics'
      };

      vi.mocked(api.get).mockResolvedValue({ data: mockWorkflow });

      const result = await reportBuilderService.getWorkflow('workflow123');

      expect(api.get).toHaveBeenCalledWith('/api/workflows/workflow123');
      expect(result).toEqual(mockWorkflow);
      expect(result.name).toBe('Sales Performance');
    });

    it('should handle workflow not found', async () => {
      vi.mocked(api.get).mockRejectedValue({
        response: { status: 404, data: { detail: 'Workflow not found' } }
      });

      await expect(reportBuilderService.getWorkflow('nonexistent')).rejects.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 unauthorized errors', async () => {
      vi.mocked(api.post).mockRejectedValue({
        response: { status: 401, data: { detail: 'Unauthorized' } }
      });

      const request = {
        workflow_id: 'workflow123',
        parameters: {},
        lookback_config: {
          type: 'relative' as const,
          value: 7,
          unit: 'days' as const
        }
      };

      await expect(reportBuilderService.validateParameters(request)).rejects.toThrow();
    });

    it('should handle 500 server errors', async () => {
      vi.mocked(api.post).mockRejectedValue({
        response: { status: 500, data: { detail: 'Internal Server Error' } }
      });

      const request: ReportBuilderSubmitRequest = {
        workflow_id: 'workflow123',
        instance_id: 'instance456',
        parameters: {},
        lookback_config: {
          type: 'relative',
          value: 7,
          unit: 'days'
        },
        schedule_config: {
          type: 'once'
        }
      };

      await expect(reportBuilderService.submit(request)).rejects.toThrow();
    });

    it('should handle malformed response data', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: 'invalid data' });

      const request = {
        workflow_id: 'workflow123',
        parameters: {},
        lookback_config: {
          type: 'relative' as const,
          value: 7,
          unit: 'days' as const
        }
      };

      const result = await reportBuilderService.validateParameters(request);

      // Service should pass through whatever the API returns
      expect(result).toBe('invalid data');
    });
  });

  describe('Concurrent Requests', () => {
    it('should handle multiple concurrent requests', async () => {
      const mockResponses = [
        { valid: true },
        { valid: true },
        { valid: false, errors: ['Error'] }
      ];

      let callIndex = 0;
      vi.mocked(api.post).mockImplementation(() =>
        Promise.resolve({ data: mockResponses[callIndex++] })
      );

      const requests = [
        reportBuilderService.validateParameters({
          workflow_id: 'w1',
          parameters: {},
          lookback_config: { type: 'relative', value: 7, unit: 'days' }
        }),
        reportBuilderService.validateParameters({
          workflow_id: 'w2',
          parameters: {},
          lookback_config: { type: 'relative', value: 14, unit: 'days' }
        }),
        reportBuilderService.validateParameters({
          workflow_id: 'w3',
          parameters: {},
          lookback_config: { type: 'relative', value: 30, unit: 'days' }
        })
      ];

      const results = await Promise.all(requests);

      expect(results[0].valid).toBe(true);
      expect(results[1].valid).toBe(true);
      expect(results[2].valid).toBe(false);
    });
  });
});