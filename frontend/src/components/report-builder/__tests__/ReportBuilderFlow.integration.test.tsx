import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { act } from 'react';

// Import all Report Builder components
import ReportBuilderParameters from '../ReportBuilderParameters';
import ReportScheduleSelection from '../ReportScheduleSelection';
import ReportReviewStep from '../ReportReviewStep';
import ReportSubmission from '../ReportSubmission';

// Mock services
vi.mock('../../../services/reportBuilderService', () => ({
  reportBuilderService: {
    validateParameters: vi.fn(),
    previewSchedule: vi.fn(),
    review: vi.fn(),
    submit: vi.fn(),
    getBackfillProgress: vi.fn(),
  },
}));

vi.mock('../../../services/instanceService', () => ({
  instanceService: {
    list: vi.fn(() => Promise.resolve([
      { instanceId: 'inst-1', instanceName: 'Production AMC' },
      { instanceId: 'inst-2', instanceName: 'Staging AMC' },
    ])),
  },
}));

// Mock Monaco Editor
vi.mock('../../common/SQLEditor', () => ({
  default: ({ value, onChange, readOnly }: any) => (
    <textarea
      data-testid="sql-editor"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      readOnly={readOnly}
    />
  ),
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Report Builder Flow Integration', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Complete Flow: One-Time Execution', () => {
    it('should complete full flow for one-time report execution', async () => {
      const mockWorkflow = {
        id: 'wf-123',
        name: 'Test Report',
        sql_query: 'SELECT * FROM impressions WHERE date >= {{start_date}}',
      };

      // Step 1: Parameters
      const parametersProps = {
        workflowId: mockWorkflow.id,
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        onNext: vi.fn(),
        onParametersChange: vi.fn(),
      };

      const { rerender } = render(
        <ReportBuilderParameters {...parametersProps} />,
        { wrapper: createWrapper() }
      );

      // Select lookback window
      const last30Button = screen.getByText('Last 30 Days');
      await user.click(last30Button);

      expect(parametersProps.onParametersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          lookbackConfig: {
            type: 'relative',
            value: 30,
            unit: 'days',
          },
        })
      );

      // Click Next
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);
      expect(parametersProps.onNext).toHaveBeenCalled();

      // Step 2: Schedule Selection
      const scheduleProps = {
        workflowId: mockWorkflow.id,
        instanceId: 'inst-1',
        scheduleConfig: {
          type: 'once' as const,
          frequency: null,
          time: null,
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
        lookbackConfig: { type: 'relative' as const, value: 30, unit: 'days' as const },
        onNext: vi.fn(),
        onPrevious: vi.fn(),
        onScheduleChange: vi.fn(),
      };

      rerender(<ReportScheduleSelection {...scheduleProps} />, { wrapper: createWrapper() });

      // Verify "Run Once" is selected by default
      const runOnceOption = screen.getByLabelText(/run once/i);
      expect(runOnceOption).toBeChecked();

      // Click Next
      const scheduleNextButton = screen.getByRole('button', { name: /next/i });
      await user.click(scheduleNextButton);
      expect(scheduleProps.onNext).toHaveBeenCalled();

      // Step 3: Review
      const reviewProps = {
        workflowId: mockWorkflow.id,
        workflowName: mockWorkflow.name,
        instanceId: 'inst-1',
        instanceName: 'Production AMC',
        sqlQuery: mockWorkflow.sql_query,
        parameters: {},
        lookbackConfig: { type: 'relative' as const, value: 30, unit: 'days' as const },
        scheduleConfig: {
          type: 'once' as const,
          frequency: null,
          time: null,
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
        estimatedCost: {
          dataScanned: '100 GB',
          estimatedCost: '$0.50',
          queryComplexity: 'Low' as const,
        },
        onNext: vi.fn(),
        onPrevious: vi.fn(),
        onEdit: vi.fn(),
      };

      rerender(<ReportReviewStep {...reviewProps} />, { wrapper: createWrapper() });

      // Verify all sections are displayed
      expect(screen.getByText('Test Report')).toBeInTheDocument();
      expect(screen.getByText('Production AMC')).toBeInTheDocument();
      expect(screen.getByText(/last 30 days/i)).toBeInTheDocument();
      expect(screen.getByText(/run once/i)).toBeInTheDocument();
      expect(screen.getByText('$0.50')).toBeInTheDocument();

      // Click Continue to Submit
      const continueButton = screen.getByRole('button', { name: /continue to submit/i });
      await user.click(continueButton);
      expect(reviewProps.onNext).toHaveBeenCalled();
    });
  });

  describe('Complete Flow: Scheduled with Backfill', () => {
    it.skip('should complete full flow for scheduled report with backfill', async () => {
      const mockWorkflow = {
        id: 'wf-456',
        name: 'Historical Analysis',
        sql_query: 'SELECT * FROM conversions WHERE campaign_id IN ({{campaigns}})',
      };

      // Step 1: Parameters with campaigns
      const parametersProps = {
        workflowId: mockWorkflow.id,
        instanceId: 'inst-2',
        parameters: { campaigns: [] },
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        detectedParameters: [
          { name: 'campaigns', type: 'campaigns' as const, defaultValue: null },
        ],
        onNext: vi.fn(),
        onParametersChange: vi.fn(),
      };

      const { rerender } = render(
        <ReportBuilderParameters {...parametersProps} />,
        { wrapper: createWrapper() }
      );

      // Select custom date range
      const customRangeButton = screen.getByText('Custom Range');
      await user.click(customRangeButton);

      // Enter date range
      const startDateInput = screen.getByLabelText('Start Date');
      const endDateInput = screen.getByLabelText('End Date');
      await user.type(startDateInput, '2024-01-01');
      await user.type(endDateInput, '2024-01-31');

      expect(parametersProps.onParametersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          lookbackConfig: {
            type: 'custom',
            startDate: expect.stringMatching(/2024-01/),
            endDate: expect.stringMatching(/2024-01/),
          },
        })
      );

      // Step 2: Schedule with Backfill
      const scheduleProps = {
        workflowId: mockWorkflow.id,
        instanceId: 'inst-2',
        scheduleConfig: {
          type: 'once' as const,
          frequency: null,
          time: null,
          timezone: 'America/New_York',
          backfillConfig: null,
        },
        lookbackConfig: {
          type: 'custom' as const,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        },
        onNext: vi.fn(),
        onPrevious: vi.fn(),
        onScheduleChange: vi.fn(),
      };

      rerender(<ReportScheduleSelection {...scheduleProps} />, { wrapper: createWrapper() });

      // Select Backfill with Schedule
      const backfillOption = screen.getByLabelText(/backfill with schedule/i);
      await user.click(backfillOption);

      // Configure backfill
      await waitFor(() => {
        expect(screen.getByLabelText(/number of periods/i)).toBeInTheDocument();
      });

      const periodsInput = screen.getByLabelText(/number of periods/i);
      await user.clear(periodsInput);
      await user.type(periodsInput, '52');

      const segmentationSelect = screen.getByLabelText(/segmentation/i);
      await user.selectOptions(segmentationSelect, 'weekly');

      // Configure schedule
      const frequencySelect = screen.getByLabelText(/frequency/i);
      await user.selectOptions(frequencySelect, 'daily');

      const timeInput = screen.getByLabelText(/time/i);
      await user.clear(timeInput);
      await user.type(timeInput, '09:00');

      expect(scheduleProps.onScheduleChange).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'backfill_with_schedule',
          frequency: 'daily',
          time: '09:00',
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly',
          },
        })
      );

      // Verify backfill summary
      expect(screen.getByText(/52 weekly segments/i)).toBeInTheDocument();
      expect(screen.getByText(/365 days/i)).toBeInTheDocument();
    });
  });

  describe('Navigation and Edit Flow', () => {
    it('should allow navigation between steps and editing', async () => {
      const mockOnEdit = vi.fn();
      const mockOnPrevious = vi.fn();

      // Start at Review step
      const reviewProps = {
        workflowId: 'wf-789',
        workflowName: 'Edit Test Report',
        instanceId: 'inst-1',
        instanceName: 'Production AMC',
        sqlQuery: 'SELECT * FROM impressions',
        parameters: { campaigns: ['camp1', 'camp2'] },
        lookbackConfig: { type: 'relative' as const, value: 14, unit: 'days' as const },
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'weekly' as const,
          time: '10:00',
          timezone: 'America/Chicago',
          dayOfWeek: 1,
          backfillConfig: null,
        },
        estimatedCost: null,
        onNext: vi.fn(),
        onPrevious: mockOnPrevious,
        onEdit: mockOnEdit,
      };

      render(<ReportReviewStep {...reviewProps} />, { wrapper: createWrapper() });

      // Test edit buttons
      const editParametersButton = screen.getByTestId('edit-parameters');
      await user.click(editParametersButton);
      expect(mockOnEdit).toHaveBeenCalledWith('parameters');

      const editLookbackButton = screen.getByTestId('edit-lookback');
      await user.click(editLookbackButton);
      expect(mockOnEdit).toHaveBeenCalledWith('lookback');

      const editScheduleButton = screen.getByTestId('edit-schedule');
      await user.click(editScheduleButton);
      expect(mockOnEdit).toHaveBeenCalledWith('schedule');

      // Test Previous button
      const previousButton = screen.getByRole('button', { name: /previous/i });
      await user.click(previousButton);
      expect(mockOnPrevious).toHaveBeenCalled();
    });
  });

  describe('Submission Flow', () => {
    it.skip('should handle successful submission', async () => {
      const { reportBuilderService } = await import('../../../services/reportBuilderService');

      (reportBuilderService.submit as any).mockResolvedValueOnce({
        success: true,
        report_id: 'report-123',
        schedule_id: 'schedule-456',
        next_run: '2024-02-01 09:00:00',
      });

      const submissionProps = {
        workflowId: 'wf-999',
        workflowName: 'Success Test',
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        scheduleConfig: { type: 'once' as const, frequency: null, time: null, timezone: 'UTC', backfillConfig: null },
        onBack: vi.fn(),
      };

      render(<ReportSubmission {...submissionProps} />, { wrapper: createWrapper() });

      // Should show submitting state initially
      expect(screen.getByText(/submitting report configuration/i)).toBeInTheDocument();

      // Wait for success state
      await waitFor(() => {
        expect(screen.getByText(/report successfully configured/i)).toBeInTheDocument();
      });

      // Verify success details
      expect(screen.getByText('report-123')).toBeInTheDocument();
      expect(screen.getByText('schedule-456')).toBeInTheDocument();

      // Check action buttons
      expect(screen.getByRole('button', { name: /go to dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create another report/i })).toBeInTheDocument();
    });

    it('should handle submission failure', async () => {
      const { reportBuilderService } = await import('../../../services/reportBuilderService');

      (reportBuilderService.submit as any).mockRejectedValueOnce({
        message: 'Network error: Unable to connect to AMC',
      });

      const submissionProps = {
        workflowId: 'wf-error',
        workflowName: 'Error Test',
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        scheduleConfig: { type: 'once' as const, frequency: null, time: null, timezone: 'UTC', backfillConfig: null },
        onBack: vi.fn(),
      };

      render(<ReportSubmission {...submissionProps} />, { wrapper: createWrapper() });

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText(/submission failed/i)).toBeInTheDocument();
      });

      // Verify error message
      expect(screen.getByText(/network error/i)).toBeInTheDocument();

      // Check retry button
      const retryButton = screen.getByRole('button', { name: /try again/i });
      expect(retryButton).toBeInTheDocument();

      // Check back button
      const backButton = screen.getByRole('button', { name: /go back/i });
      expect(backButton).toBeInTheDocument();
      await user.click(backButton);
      expect(submissionProps.onBack).toHaveBeenCalled();
    });

    it.skip('should track backfill progress', { timeout: 10000 }, async () => {
      const { reportBuilderService } = await import('../../../services/reportBuilderService');

      (reportBuilderService.submit as any).mockResolvedValueOnce({
        success: true,
        collection_id: 'coll-123',
      });

      let progressCallCount = 0;
      (reportBuilderService.getBackfillProgress as any).mockImplementation(() => {
        progressCallCount++;
        return Promise.resolve({
          totalPeriods: 52,
          completedPeriods: progressCallCount * 10,
          failedPeriods: 0,
          inProgressPeriods: 5,
          estimatedTimeRemaining: '2 hours',
          currentBatch: progressCallCount,
          totalBatches: 11,
        });
      });

      const submissionProps = {
        workflowId: 'wf-backfill',
        workflowName: 'Backfill Test',
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        scheduleConfig: {
          type: 'backfill_with_schedule' as const,
          frequency: 'daily' as const,
          time: '09:00',
          timezone: 'UTC',
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly' as const,
          },
        },
        onBack: vi.fn(),
      };

      vi.useFakeTimers();
      render(<ReportSubmission {...submissionProps} />, { wrapper: createWrapper() });

      // Wait for initial submission
      await waitFor(() => {
        expect(screen.getByText(/backfill progress/i)).toBeInTheDocument();
      });

      // Advance timers to trigger progress polling
      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(reportBuilderService.getBackfillProgress).toHaveBeenCalledWith('coll-123');
      });

      // Verify progress display
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
      expect(screen.getByText(/estimated time remaining/i)).toBeInTheDocument();

      vi.useRealTimers();
    });
  });

  describe('Validation and Error Handling', () => {
    it.skip('should validate date ranges', { timeout: 10000 }, async () => {
      const props = {
        workflowId: 'wf-validation',
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: {
          type: 'custom' as const,
          startDate: '2024-02-01',
          endDate: '2024-01-01', // End before start
        },
        onNext: vi.fn(),
        onParametersChange: vi.fn(),
      };

      render(<ReportBuilderParameters {...props} />, { wrapper: createWrapper() });

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/end date must be after start date/i)).toBeInTheDocument();
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it.skip('should validate AMC data retention limits', { timeout: 10000 }, async () => {
      const props = {
        workflowId: 'wf-limit',
        instanceId: 'inst-1',
        parameters: {},
        lookbackConfig: {
          type: 'relative' as const,
          value: 500, // More than 14 months
          unit: 'days' as const,
        },
        onNext: vi.fn(),
        onParametersChange: vi.fn(),
      };

      render(<ReportBuilderParameters {...props} />, { wrapper: createWrapper() });

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/exceeds.*14.*month/i)).toBeInTheDocument();
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it.skip('should validate schedule configuration', { timeout: 10000 }, async () => {
      const props = {
        workflowId: 'wf-schedule',
        instanceId: 'inst-1',
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'weekly' as const,
          time: null, // Missing time
          timezone: 'UTC',
          dayOfWeek: undefined, // Missing day for weekly
          backfillConfig: null,
        },
        lookbackConfig: { type: 'relative' as const, value: 7, unit: 'days' as const },
        onNext: vi.fn(),
        onPrevious: vi.fn(),
        onScheduleChange: vi.fn(),
      };

      render(<ReportScheduleSelection {...props} />, { wrapper: createWrapper() });

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/schedule time is required/i)).toBeInTheDocument();
        expect(screen.getByText(/day of week is required/i)).toBeInTheDocument();
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });
  });
});