import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RunReportModal from '../RunReportModal';
import type { QueryTemplate } from '../../../types/queryTemplate';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

const mockTemplate: QueryTemplate = {
  id: '1',
  name: 'Campaign Performance Report',
  description: 'Analyze campaign performance',
  category: 'performance',
  sql_query: 'SELECT * FROM campaigns WHERE date >= :start_date AND date <= :end_date',
  report_type: 'campaign',
  parameters: {},
  parameter_definitions: {
    start_date: {
      type: 'date',
      label: 'Start Date',
      required: true,
    },
    end_date: {
      type: 'date',
      label: 'End Date',
      required: true,
    },
    instance_id: {
      type: 'select',
      label: 'AMC Instance',
      required: true,
    },
  },
  ui_schema: {},
  instance_types: ['seller'],
  created_at: '2025-09-01',
  updated_at: '2025-09-01',
};

describe('RunReportModal', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal with template information', () => {
    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Run Report: Campaign Performance Report')).toBeInTheDocument();
    expect(screen.getByText('Analyze campaign performance')).toBeInTheDocument();
  });

  it('shows multi-step wizard with correct steps', () => {
    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('1. Parameters')).toBeInTheDocument();
    expect(screen.getByText('2. Execution Type')).toBeInTheDocument();
    expect(screen.getByText('3. Schedule')).toBeInTheDocument();
    expect(screen.getByText('4. Review')).toBeInTheDocument();
  });

  it('navigates through wizard steps', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Step 1: Parameters
    expect(screen.getByText('Configure Parameters')).toBeInTheDocument();

    // Fill parameters and go to next step
    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Step 2: Execution Type
    await waitFor(() => {
      expect(screen.getByText('Select Execution Type')).toBeInTheDocument();
    });

    // Select execution type and continue
    const onceOption = screen.getByLabelText('Run Once');
    await user.click(onceOption);
    await user.click(nextButton);

    // Step 3: Schedule (skipped for 'once' execution)
    // Step 4: Review
    await waitFor(() => {
      expect(screen.getByText('Review Configuration')).toBeInTheDocument();
    });
  });

  it('handles different execution types', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Check all execution type options
    expect(screen.getByLabelText('Run Once')).toBeInTheDocument();
    expect(screen.getByLabelText('Recurring Schedule')).toBeInTheDocument();
    expect(screen.getByLabelText('Backfill Historical Data')).toBeInTheDocument();

    // Select recurring
    const recurringOption = screen.getByLabelText('Recurring Schedule');
    await user.click(recurringOption);
    await user.click(nextButton);

    // Should show schedule configuration
    await waitFor(() => {
      expect(screen.getByText('Configure Schedule')).toBeInTheDocument();
      expect(screen.getByLabelText('Frequency')).toBeInTheDocument();
      expect(screen.getByLabelText('Time')).toBeInTheDocument();
    });
  });

  it('handles backfill configuration', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    const backfillOption = screen.getByLabelText('Backfill Historical Data');
    await user.click(backfillOption);
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Configure Backfill')).toBeInTheDocument();
      expect(screen.getByLabelText('Backfill Period')).toBeInTheDocument();
      expect(screen.getByText('7 days')).toBeInTheDocument();
      expect(screen.getByText('30 days')).toBeInTheDocument();
      expect(screen.getByText('90 days')).toBeInTheDocument();
      expect(screen.getByText('365 days')).toBeInTheDocument();
    });
  });

  it('validates required fields before submission', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Try to proceed without filling required fields
    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('Please fill in all required parameters')).toBeInTheDocument();
    });
  });

  it('shows review summary before submission', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Fill parameters
    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-01');

    const endDate = screen.getByLabelText('End Date');
    await user.type(endDate, '2025-09-15');

    const instanceSelect = screen.getByLabelText('AMC Instance');
    await user.selectOptions(instanceSelect, 'instance1');

    // Navigate to execution type
    let nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Select run once
    const onceOption = screen.getByLabelText('Run Once');
    await user.click(onceOption);

    // Navigate to review
    nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Check review content
    await waitFor(() => {
      expect(screen.getByText('Review Configuration')).toBeInTheDocument();
      expect(screen.getByText('Report:')).toBeInTheDocument();
      expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      expect(screen.getByText('Execution Type:')).toBeInTheDocument();
      expect(screen.getByText('Run Once')).toBeInTheDocument();
      expect(screen.getByText('Parameters:')).toBeInTheDocument();
    });
  });

  it('submits report configuration correctly', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Fill parameters
    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-01');

    const endDate = screen.getByLabelText('End Date');
    await user.type(endDate, '2025-09-15');

    const instanceSelect = screen.getByLabelText('AMC Instance');
    await user.selectOptions(instanceSelect, 'instance1');

    // Navigate through wizard
    let nextButton = screen.getByText('Next');
    await user.click(nextButton);

    const onceOption = screen.getByLabelText('Run Once');
    await user.click(onceOption);

    nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Submit
    const submitButton = screen.getByText('Run Report');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        template_id: '1',
        parameters: {
          start_date: '2025-09-01',
          end_date: '2025-09-15',
          instance_id: 'instance1',
        },
        execution_type: 'once',
        schedule: null,
      });
    });
  });

  it('handles recurring schedule configuration', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Fill parameters
    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-01');

    const endDate = screen.getByLabelText('End Date');
    await user.type(endDate, '2025-09-15');

    const instanceSelect = screen.getByLabelText('AMC Instance');
    await user.selectOptions(instanceSelect, 'instance1');

    // Navigate to execution type
    let nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Select recurring
    const recurringOption = screen.getByLabelText('Recurring Schedule');
    await user.click(recurringOption);

    nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Configure schedule
    const frequencySelect = screen.getByLabelText('Frequency');
    await user.selectOptions(frequencySelect, 'daily');

    const timeInput = screen.getByLabelText('Time');
    await user.type(timeInput, '09:00');

    nextButton = screen.getByText('Next');
    await user.click(nextButton);

    // Submit
    const submitButton = screen.getByText('Run Report');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        template_id: '1',
        parameters: {
          start_date: '2025-09-01',
          end_date: '2025-09-15',
          instance_id: 'instance1',
        },
        execution_type: 'recurring',
        schedule: {
          frequency: 'daily',
          time: '09:00',
        },
      });
    });
  });

  it('closes modal when cancel is clicked', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('allows navigation back through wizard', async () => {
    const user = userEvent.setup();

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Go to step 2
    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    expect(screen.getByText('Select Execution Type')).toBeInTheDocument();

    // Go back to step 1
    const backButton = screen.getByText('Back');
    await user.click(backButton);

    expect(screen.getByText('Configure Parameters')).toBeInTheDocument();
  });
});