import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardsTable from '../DashboardsTable';
import type { Report } from '../../../types/report';

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

const mockReports: Report[] = [
  {
    id: '1',
    name: 'Daily Campaign Performance',
    description: 'Daily metrics for all campaigns',
    template_id: 'template1',
    instance_id: 'instance1',
    parameters: {
      start_date: '2025-09-01',
      end_date: '2025-09-15',
    },
    status: 'active',
    frequency: 'daily',
    last_run_at: '2025-09-14T10:00:00',
    next_run_at: '2025-09-15T10:00:00',
    created_at: '2025-09-01T00:00:00',
    updated_at: '2025-09-14T10:00:00',
    execution_count: 14,
    success_count: 13,
    failure_count: 1,
  },
  {
    id: '2',
    name: 'Weekly Conversion Report',
    description: 'Weekly conversion analysis',
    template_id: 'template2',
    instance_id: 'instance2',
    parameters: {
      metric_type: 'conversions',
    },
    status: 'paused',
    frequency: 'weekly',
    last_run_at: '2025-09-07T09:00:00',
    next_run_at: null,
    created_at: '2025-08-01T00:00:00',
    updated_at: '2025-09-07T09:00:00',
    execution_count: 6,
    success_count: 6,
    failure_count: 0,
  },
  {
    id: '3',
    name: 'Monthly ROAS Analysis',
    description: 'Monthly return on ad spend',
    template_id: 'template3',
    instance_id: 'instance1',
    parameters: {},
    status: 'active',
    frequency: 'monthly',
    last_run_at: '2025-09-01T00:00:00',
    next_run_at: '2025-10-01T00:00:00',
    created_at: '2025-07-01T00:00:00',
    updated_at: '2025-09-01T00:00:00',
    execution_count: 3,
    success_count: 2,
    failure_count: 1,
  },
];

describe('DashboardsTable', () => {
  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnRun = vi.fn();
  const mockOnPause = vi.fn();
  const mockOnResume = vi.fn();
  const mockOnViewResults = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders table with reports', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Daily Campaign Performance')).toBeInTheDocument();
    expect(screen.getByText('Weekly Conversion Report')).toBeInTheDocument();
    expect(screen.getByText('Monthly ROAS Analysis')).toBeInTheDocument();
  });

  it('displays status badges correctly', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const activeStatuses = screen.getAllByText('active');
    expect(activeStatuses).toHaveLength(2);
    expect(activeStatuses[0]).toHaveClass('bg-green-100');

    const pausedStatus = screen.getByText('paused');
    expect(pausedStatus).toHaveClass('bg-yellow-100');
  });

  it('displays frequency information', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('daily')).toBeInTheDocument();
    expect(screen.getByText('weekly')).toBeInTheDocument();
    expect(screen.getByText('monthly')).toBeInTheDocument();
  });

  it('formats dates correctly', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    // Check for formatted dates (these would be formatted by date-fns)
    expect(screen.getByText(/Sep 14, 2025/)).toBeInTheDocument();
    expect(screen.getByText(/Sep 15, 2025/)).toBeInTheDocument();
  });

  it('displays success rate', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    // Report 1: 13/14 = 92.8%
    expect(screen.getByText('92.8%')).toBeInTheDocument();

    // Report 2: 6/6 = 100%
    expect(screen.getByText('100%')).toBeInTheDocument();

    // Report 3: 2/3 = 66.7%
    expect(screen.getByText('66.7%')).toBeInTheDocument();
  });

  it('handles run action', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const runButtons = screen.getAllByTitle('Run now');
    await user.click(runButtons[0]);

    expect(mockOnRun).toHaveBeenCalledWith(mockReports[0]);
  });

  it('handles pause action for active reports', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const pauseButtons = screen.getAllByTitle('Pause schedule');
    await user.click(pauseButtons[0]);

    expect(mockOnPause).toHaveBeenCalledWith(mockReports[0]);
  });

  it('handles resume action for paused reports', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const resumeButton = screen.getByTitle('Resume schedule');
    await user.click(resumeButton);

    expect(mockOnResume).toHaveBeenCalledWith(mockReports[1]);
  });

  it('handles edit action', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const editButtons = screen.getAllByTitle('Edit report');
    await user.click(editButtons[0]);

    expect(mockOnEdit).toHaveBeenCalledWith(mockReports[0]);
  });

  it('handles delete action', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const deleteButtons = screen.getAllByTitle('Delete report');
    await user.click(deleteButtons[0]);

    expect(mockOnDelete).toHaveBeenCalledWith(mockReports[0]);
  });

  it('handles view results action', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const viewButtons = screen.getAllByTitle('View results');
    await user.click(viewButtons[0]);

    expect(mockOnViewResults).toHaveBeenCalledWith(mockReports[0]);
  });

  it('sorts reports by column', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const nameHeader = screen.getByText('Name');
    await user.click(nameHeader);

    // Check if reports are sorted alphabetically
    const reportNames = screen.getAllByRole('cell').filter(cell =>
      cell.textContent?.includes('Report') || cell.textContent?.includes('Analysis')
    );

    expect(reportNames[0].textContent).toContain('Daily Campaign Performance');
  });

  it('filters reports by search', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const searchInput = screen.getByPlaceholderText('Search reports...');
    await user.type(searchInput, 'conversion');

    await waitFor(() => {
      expect(screen.getByText('Weekly Conversion Report')).toBeInTheDocument();
      expect(screen.queryByText('Daily Campaign Performance')).not.toBeInTheDocument();
      expect(screen.queryByText('Monthly ROAS Analysis')).not.toBeInTheDocument();
    });
  });

  it('filters reports by status', async () => {
    const user = userEvent.setup();

    render(
      <DashboardsTable
        reports={mockReports}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    const statusFilter = screen.getByLabelText('Status');
    await user.selectOptions(statusFilter, 'paused');

    await waitFor(() => {
      expect(screen.getByText('Weekly Conversion Report')).toBeInTheDocument();
      expect(screen.queryByText('Daily Campaign Performance')).not.toBeInTheDocument();
      expect(screen.queryByText('Monthly ROAS Analysis')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no reports', () => {
    render(
      <DashboardsTable
        reports={[]}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('No reports found')).toBeInTheDocument();
    expect(screen.getByText('Create your first report to get started')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <DashboardsTable
        reports={mockReports}
        isLoading={true}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onRun={mockOnRun}
        onPause={mockOnPause}
        onResume={mockOnResume}
        onViewResults={mockOnViewResults}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Loading reports...')).toBeInTheDocument();
  });
});