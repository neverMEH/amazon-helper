import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReportScheduleSelection from '../ReportScheduleSelection';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('ReportScheduleSelection', () => {
  const mockOnNext = vi.fn();
  const mockOnScheduleChange = vi.fn();
  const mockOnPrevious = vi.fn();

  const defaultProps = {
    workflowId: 'workflow-123',
    instanceId: 'instance-123',
    scheduleConfig: {
      type: 'once' as const,
      frequency: null,
      time: null,
      timezone: 'America/Los_Angeles',
      backfillConfig: null,
    },
    lookbackConfig: {
      type: 'relative' as const,
      value: 7,
      unit: 'days' as const,
    },
    onNext: mockOnNext,
    onPrevious: mockOnPrevious,
    onScheduleChange: mockOnScheduleChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Schedule Type Selection', () => {
    it('should render all schedule type options', () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/run once/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/scheduled/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/backfill with schedule/i)).toBeInTheDocument();
    });

    it('should highlight selected schedule type', () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      const onceOption = screen.getByLabelText(/run once/i);
      expect(onceOption).toBeChecked();
    });

    it('should update schedule type on selection', async () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      const scheduledOption = screen.getByLabelText(/^scheduled$/i);
      await userEvent.click(scheduledOption);

      await waitFor(() => {
        expect(mockOnScheduleChange).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'scheduled',
          })
        );
      });
    });

    it('should show description for each schedule type', () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/execute immediately/i)).toBeInTheDocument();
      expect(screen.getByText(/run automatically on a schedule/i)).toBeInTheDocument();
      expect(screen.getByText(/backfill historical data.*then continue/i)).toBeInTheDocument();
    });
  });

  describe('Schedule Frequency Configuration', () => {
    it('should show frequency options when scheduled type is selected', async () => {
      const scheduledProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'scheduled' as const,
        },
      };

      render(<ReportScheduleSelection {...scheduledProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/frequency/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/time/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/timezone/i)).toBeInTheDocument();
    });

    it('should support daily, weekly, and monthly frequencies', async () => {
      const scheduledProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'scheduled' as const,
        },
      };

      render(<ReportScheduleSelection {...scheduledProps} />, { wrapper: createWrapper() });

      const frequencySelect = screen.getByLabelText(/frequency/i);
      expect(frequencySelect).toBeInTheDocument();

      // Check options
      fireEvent.click(frequencySelect);
      expect(screen.getByText('Daily')).toBeInTheDocument();
      expect(screen.getByText('Weekly')).toBeInTheDocument();
      expect(screen.getByText('Monthly')).toBeInTheDocument();
    });

    it('should show day selector for weekly frequency', async () => {
      const weeklyProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'weekly',
          time: '09:00',
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
      };

      render(<ReportScheduleSelection {...weeklyProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/day of week/i)).toBeInTheDocument();
    });

    it('should show date selector for monthly frequency', async () => {
      const monthlyProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'monthly',
          time: '09:00',
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
      };

      render(<ReportScheduleSelection {...monthlyProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/day of month/i)).toBeInTheDocument();
    });
  });

  describe('Backfill Configuration', () => {
    it('should show backfill options when backfill type is selected', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/backfill configuration/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/number of periods/i)).toBeInTheDocument();
    });

    it('should calculate and display total backfill duration', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      // Should show 52 weeks = 365 days
      expect(screen.getByText(/365 days/i)).toBeInTheDocument();
    });

    it('should support different segmentation options', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 12,
            segmentation: 'monthly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      const segmentationSelect = screen.getByLabelText(/segmentation/i);
      expect(segmentationSelect).toBeInTheDocument();

      fireEvent.click(segmentationSelect);
      expect(screen.getByText('Daily')).toBeInTheDocument();
      expect(screen.getByText('Weekly')).toBeInTheDocument();
      expect(screen.getByText('Monthly')).toBeInTheDocument();
    });

    it('should show warning for large backfill operations', () => {
      const largeBackfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 365,
            segmentation: 'daily',
          },
        },
      };

      render(<ReportScheduleSelection {...largeBackfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/large backfill/i)).toBeInTheDocument();
      expect(screen.getByText(/may take several hours/i)).toBeInTheDocument();
    });
  });

  describe('Timezone Selection', () => {
    it('should display common timezone options', () => {
      const scheduledProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'scheduled' as const,
        },
      };

      render(<ReportScheduleSelection {...scheduledProps} />, { wrapper: createWrapper() });

      const timezoneSelect = screen.getByLabelText(/timezone/i);
      fireEvent.click(timezoneSelect);

      expect(screen.getByText(/Pacific Time/i)).toBeInTheDocument();
      expect(screen.getByText(/Eastern Time/i)).toBeInTheDocument();
      expect(screen.getByText(/Central Time/i)).toBeInTheDocument();
      expect(screen.getByText(/Mountain Time/i)).toBeInTheDocument();
    });

    it('should update timezone selection', async () => {
      const scheduledProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'scheduled' as const,
        },
      };

      render(<ReportScheduleSelection {...scheduledProps} />, { wrapper: createWrapper() });

      const timezoneSelect = screen.getByLabelText(/timezone/i);
      fireEvent.change(timezoneSelect, { target: { value: 'America/New_York' } });

      await waitFor(() => {
        expect(mockOnScheduleChange).toHaveBeenCalledWith(
          expect.objectContaining({
            timezone: 'America/New_York',
          })
        );
      });
    });
  });

  describe('Progress Calculation', () => {
    it('should show estimated completion time for backfill', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/estimated completion/i)).toBeInTheDocument();
      // With 5 parallel executions, 52 weeks = ~10-11 batches
      expect(screen.getByText(/2-3 hours/i)).toBeInTheDocument();
    });

    it('should show progress preview for segmented backfill', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 12,
            segmentation: 'monthly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/12 monthly segments/i)).toBeInTheDocument();
      expect(screen.getByText(/parallel processing/i)).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should validate required fields for scheduled type', () => {
      const invalidProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: null,
          time: null,
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
      };

      render(<ReportScheduleSelection {...invalidProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it('should validate backfill period limits', () => {
      const invalidBackfillProps = {
        ...defaultProps,
        scheduleConfig: {
          ...defaultProps.scheduleConfig,
          type: 'backfill_with_schedule' as const,
          backfillConfig: {
            enabled: true,
            periods: 500, // Exceeds AMC limit
            segmentation: 'daily',
          },
        },
      };

      render(<ReportScheduleSelection {...invalidBackfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/exceeds.*14.*month/i)).toBeInTheDocument();
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it('should enable Next button when all validations pass', () => {
      const validProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'daily',
          time: '09:00',
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
      };

      render(<ReportScheduleSelection {...validProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });
  });

  describe('Navigation', () => {
    it('should call onPrevious when Previous button is clicked', async () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      const previousButton = screen.getByRole('button', { name: /previous/i });
      await userEvent.click(previousButton);

      expect(mockOnPrevious).toHaveBeenCalled();
    });

    it('should call onNext when Next button is clicked', async () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      await userEvent.click(nextButton);

      expect(mockOnNext).toHaveBeenCalled();
    });
  });

  describe('Schedule Summary Display', () => {
    it('should show summary for once execution', () => {
      render(<ReportScheduleSelection {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/run once/i)).toBeInTheDocument();
      expect(screen.getByText(/immediate execution/i)).toBeInTheDocument();
    });

    it('should show summary for scheduled execution', () => {
      const scheduledProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'scheduled' as const,
          frequency: 'daily',
          time: '09:00',
          timezone: 'America/Los_Angeles',
          backfillConfig: null,
        },
      };

      render(<ReportScheduleSelection {...scheduledProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/daily at 09:00/i)).toBeInTheDocument();
      expect(screen.getByText(/Pacific Time/i)).toBeInTheDocument();
    });

    it('should show summary for backfill with schedule', () => {
      const backfillProps = {
        ...defaultProps,
        scheduleConfig: {
          type: 'backfill_with_schedule' as const,
          frequency: 'daily',
          time: '09:00',
          timezone: 'America/Los_Angeles',
          backfillConfig: {
            enabled: true,
            periods: 52,
            segmentation: 'weekly',
          },
        },
      };

      render(<ReportScheduleSelection {...backfillProps} />, { wrapper: createWrapper() });

      expect(screen.getByText(/52 weeks historical/i)).toBeInTheDocument();
      expect(screen.getByText(/then daily at 09:00/i)).toBeInTheDocument();
    });
  });
});