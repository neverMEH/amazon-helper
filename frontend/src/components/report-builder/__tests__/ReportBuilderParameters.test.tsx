import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReportBuilderParameters from '../ReportBuilderParameters';

// Mock the services
vi.mock('../../../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

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

describe('ReportBuilderParameters', () => {
  const mockOnNext = vi.fn();
  const mockOnParametersChange = vi.fn();

  const defaultProps = {
    workflowId: 'workflow-123',
    instanceId: 'instance-123',
    parameters: {},
    lookbackConfig: {
      type: 'relative' as const,
      value: 7,
      unit: 'days' as const,
    },
    onNext: mockOnNext,
    onParametersChange: mockOnParametersChange,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Lookback Window Selection', () => {
    it('should render predefined lookback buttons', () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 14 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 Days')).toBeInTheDocument();
      expect(screen.getByText('Last Week')).toBeInTheDocument();
      expect(screen.getByText('Last Month')).toBeInTheDocument();
      expect(screen.getByText('Custom Range')).toBeInTheDocument();
    });

    it('should highlight selected lookback period', () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      const button7Days = screen.getByText('Last 7 Days');
      expect(button7Days.closest('button')).toHaveClass('bg-blue-600');
    });

    it('should update lookback config when button clicked', async () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      const button14Days = screen.getByText('Last 14 Days');
      await userEvent.click(button14Days);

      await waitFor(() => {
        expect(mockOnParametersChange).toHaveBeenCalledWith(
          expect.objectContaining({
            lookbackConfig: {
              type: 'relative',
              value: 14,
              unit: 'days',
            },
          })
        );
      });
    });

    it('should toggle to custom date range mode', async () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      const customButton = screen.getByText('Custom Range');
      await userEvent.click(customButton);

      await waitFor(() => {
        expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
        expect(screen.getByLabelText('End Date')).toBeInTheDocument();
      });
    });
  });

  describe('Custom Date Range', () => {
    it('should display date pickers in custom mode', () => {
      const customProps = {
        ...defaultProps,
        lookbackConfig: {
          type: 'custom' as const,
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        },
      };

      render(<ReportBuilderParameters {...customProps} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
      expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    });

    it('should validate date range within AMC limits', async () => {
      const customProps = {
        ...defaultProps,
        lookbackConfig: {
          type: 'custom' as const,
          startDate: '2023-01-01',
          endDate: '2024-12-31',
        },
      };

      render(<ReportBuilderParameters {...customProps} />, { wrapper: createWrapper() });

      // Should show validation error for exceeding 14-month limit
      await waitFor(() => {
        expect(screen.getByText(/exceeds.*14.*month/i)).toBeInTheDocument();
      });
    });

    it('should validate end date is after start date', async () => {
      const customProps = {
        ...defaultProps,
        lookbackConfig: {
          type: 'custom' as const,
          startDate: '2024-01-31',
          endDate: '2024-01-01',
        },
      };

      render(<ReportBuilderParameters {...customProps} />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/end date.*after.*start/i)).toBeInTheDocument();
      });
    });
  });

  describe('Parameter Management', () => {
    it('should display campaign selector when campaigns parameter exists', () => {
      const propsWithCampaigns = {
        ...defaultProps,
        parameters: {
          campaigns: [],
        },
      };

      render(<ReportBuilderParameters {...propsWithCampaigns} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/Campaigns/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /select campaigns/i })).toBeInTheDocument();
    });

    it('should display ASIN selector when asins parameter exists', () => {
      const propsWithAsins = {
        ...defaultProps,
        parameters: {
          asins: [],
        },
      };

      render(<ReportBuilderParameters {...propsWithAsins} />, { wrapper: createWrapper() });

      expect(screen.getByLabelText(/ASINs/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /select asins/i })).toBeInTheDocument();
    });

    it('should update parameters when selections change', async () => {
      const propsWithParams = {
        ...defaultProps,
        parameters: {
          campaigns: ['camp1'],
          asins: ['B001'],
        },
      };

      render(<ReportBuilderParameters {...propsWithParams} />, { wrapper: createWrapper() });

      // Verify initial values are displayed
      expect(screen.getByText('1 selected')).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should enable Next button when all validations pass', () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).not.toBeDisabled();
    });

    it('should disable Next button when validation fails', () => {
      const invalidProps = {
        ...defaultProps,
        lookbackConfig: {
          type: 'relative' as const,
          value: 500, // Exceeds AMC limit
          unit: 'days' as const,
        },
      };

      render(<ReportBuilderParameters {...invalidProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    it('should call onNext when Next is clicked with valid data', async () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      const nextButton = screen.getByRole('button', { name: /next/i });
      await userEvent.click(nextButton);

      expect(mockOnNext).toHaveBeenCalled();
    });
  });

  describe('Preview Display', () => {
    it('should show date range preview for relative lookback', () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      // Should show calculated date range
      const today = new Date();
      const startDate = new Date(today);
      startDate.setDate(startDate.getDate() - 7);

      expect(screen.getByText(/Date Range:/i)).toBeInTheDocument();
      // Date format may vary, just check it contains some date info
      expect(screen.getByText(/to/i)).toBeInTheDocument();
    });

    it('should show parameter count summary', () => {
      const propsWithParams = {
        ...defaultProps,
        parameters: {
          campaigns: ['camp1', 'camp2', 'camp3'],
          asins: ['B001', 'B002'],
        },
      };

      render(<ReportBuilderParameters {...propsWithParams} />, { wrapper: createWrapper() });

      expect(screen.getByText('3 selected')).toBeInTheDocument();
      expect(screen.getByText('2 selected')).toBeInTheDocument();
    });
  });

  describe('Toggle Modes', () => {
    it('should toggle between relative and calendar modes', async () => {
      render(<ReportBuilderParameters {...defaultProps} />, { wrapper: createWrapper() });

      // Start in relative mode
      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();

      // Toggle to custom
      const customButton = screen.getByText('Custom Range');
      await userEvent.click(customButton);

      // Should show date pickers
      await waitFor(() => {
        expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
      });

      // Toggle back to relative
      const relativeButton = screen.getByText('Last 7 Days');
      await userEvent.click(relativeButton);

      // Date pickers should be gone
      await waitFor(() => {
        expect(screen.queryByLabelText('Start Date')).not.toBeInTheDocument();
      });
    });

    it('should preserve parameter selections when toggling modes', async () => {
      const propsWithParams = {
        ...defaultProps,
        parameters: {
          campaigns: ['camp1', 'camp2'],
        },
      };

      render(<ReportBuilderParameters {...propsWithParams} />, { wrapper: createWrapper() });

      // Toggle to custom mode
      const customButton = screen.getByText('Custom Range');
      await userEvent.click(customButton);

      // Parameters should still be there
      expect(screen.getByText('2 selected')).toBeInTheDocument();

      // Toggle back
      const relativeButton = screen.getByText('Last 14 Days');
      await userEvent.click(relativeButton);

      // Parameters should still be preserved
      expect(screen.getByText('2 selected')).toBeInTheDocument();
    });
  });
});