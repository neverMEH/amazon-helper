import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import ReportBuilder from '../ReportBuilder';
import * as reportService from '../../../services/reportService';
import * as queryTemplateService from '../../../services/queryTemplateService';

// Mock services
vi.mock('../../../services/reportService');
vi.mock('../../../services/queryTemplateService');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('ReportBuilder', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with tab navigation', () => {
    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: { templates: [] }
    });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    expect(screen.getByText('Reports')).toBeInTheDocument();
    expect(screen.getByText('Dashboards')).toBeInTheDocument();
  });

  it('switches between tabs', async () => {
    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: { templates: [] }
    });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    const dashboardsTab = screen.getByText('Dashboards');
    fireEvent.click(dashboardsTab);

    await waitFor(() => {
      expect(dashboardsTab).toHaveClass('text-indigo-600');
    });
  });

  it('displays template grid in Reports tab', async () => {
    const mockTemplates = [
      {
        id: '1',
        name: 'Campaign Performance',
        description: 'Analyze campaign metrics',
        category: 'performance',
        report_type: 'campaign',
      },
      {
        id: '2',
        name: 'Conversion Analysis',
        description: 'Track conversion rates',
        category: 'conversion',
        report_type: 'conversion',
      },
    ];

    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: { templates: mockTemplates }
    });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
      expect(screen.getByText('Conversion Analysis')).toBeInTheDocument();
    });
  });

  it('displays reports table in Dashboards tab', async () => {
    const mockReports = [
      {
        id: '1',
        name: 'Daily Campaign Report',
        status: 'active',
        frequency: 'daily',
        last_run_at: '2025-09-15T10:00:00',
        next_run_at: '2025-09-16T10:00:00',
      },
    ];

    vi.mocked(reportService.listReports).mockResolvedValue({ data: mockReports });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: { templates: [] }
    });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    const dashboardsTab = screen.getByText('Dashboards');
    fireEvent.click(dashboardsTab);

    await waitFor(() => {
      expect(screen.getByText('Daily Campaign Report')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
      expect(screen.getByText('daily')).toBeInTheDocument();
    });
  });

  it('handles create report button click', async () => {
    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: { templates: [] }
    });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    const createButton = screen.getByText('Create Report');
    expect(createButton).toBeInTheDocument();
  });

  it('handles error states gracefully', async () => {
    const errorMessage = 'Failed to load templates';
    vi.mocked(queryTemplateService.listTemplates).mockRejectedValue(
      new Error(errorMessage)
    );
    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });

    render(<ReportBuilder />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Error loading templates/i)).toBeInTheDocument();
    });
  });
});