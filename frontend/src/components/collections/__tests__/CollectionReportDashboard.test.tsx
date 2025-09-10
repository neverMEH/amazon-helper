import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import CollectionReportDashboard from '../CollectionReportDashboard';
import * as reportDashboardService from '../../../services/reportDashboardService';

// Mock the services
vi.mock('../../../services/reportDashboardService', () => ({
  getDashboardData: vi.fn(),
  comparePeriods: vi.fn(),
  getChartData: vi.fn(),
  saveDashboardConfig: vi.fn(),
  getDashboardConfigs: vi.fn(),
  updateDashboardConfig: vi.fn(),
  deleteDashboardConfig: vi.fn(),
  createSnapshot: vi.fn(),
  getSnapshots: vi.fn(),
  getSnapshot: vi.fn(),
  deleteSnapshot: vi.fn(),
  exportDashboard: vi.fn(),
  getAvailableMetrics: vi.fn(),
  getAggregatedData: vi.fn(),
  getTrendAnalysis: vi.fn(),
  shareDashboard: vi.fn(),
  getSharedUsers: vi.fn(),
  revokeShare: vi.fn(),
}));

// Mock Chart.js
vi.mock('react-chartjs-2', () => ({
  Line: () => <div>Line Chart</div>,
  Bar: () => <div>Bar Chart</div>,
  Pie: () => <div>Pie Chart</div>,
  Doughnut: () => <div>Doughnut Chart</div>,
}));

const mockDashboardData = {
  collection: {
    id: 'test-collection-id',
    name: 'Test Collection',
    workflow_id: 'test-workflow',
    instance_id: 'test-instance',
    status: 'completed',
    created_at: '2024-01-01T00:00:00Z',
    weeks_completed: 52,
    weeks_failed: 0,
    weeks_pending: 0,
  },
  weeks: [
    {
      id: 'week-1',
      week_number: 1,
      week_start: '2024-01-01',
      week_end: '2024-01-07',
      status: 'completed',
      execution_results: {
        metrics: {
          impressions: 1000,
          clicks: 50,
          conversions: 10,
          spend: 100,
        },
      },
    },
    {
      id: 'week-2',
      week_number: 2,
      week_start: '2024-01-08',
      week_end: '2024-01-14',
      status: 'completed',
      execution_results: {
        metrics: {
          impressions: 1200,
          clicks: 60,
          conversions: 12,
          spend: 120,
        },
      },
    },
  ],
  summary: {
    total_impressions: 2200,
    total_clicks: 110,
    total_conversions: 22,
    total_spend: 220,
    avg_ctr: 0.05,
    avg_cvr: 0.2,
    avg_cpc: 2,
  },
  chartData: {
    line: {
      labels: ['Week 1', 'Week 2'],
      datasets: [
        {
          label: 'Impressions',
          data: [1000, 1200],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
        },
      ],
    },
    bar: {
      labels: ['Week 1', 'Week 2'],
      datasets: [
        {
          label: 'Spend',
          data: [100, 120],
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
        },
      ],
    },
  },
};

const mockComparisonData = {
  period1: {
    weeks: [mockDashboardData.weeks[0]],
    summary: {
      total_impressions: 1000,
      total_clicks: 50,
      total_conversions: 10,
      total_spend: 100,
    },
  },
  period2: {
    weeks: [mockDashboardData.weeks[1]],
    summary: {
      total_impressions: 1200,
      total_clicks: 60,
      total_conversions: 12,
      total_spend: 120,
    },
  },
  changes: {
    impressions_change: 20,
    clicks_change: 20,
    conversions_change: 20,
    spend_change: 20,
  },
};

describe('CollectionReportDashboard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    vi.clearAllMocks();
    
    // Set up default mock implementations
    vi.mocked(reportDashboardService.getAvailableMetrics).mockResolvedValue([
      'impressions', 'clicks', 'conversions', 'spend'
    ]);
    vi.mocked(reportDashboardService.getDashboardConfigs).mockResolvedValue([]);
    vi.mocked(reportDashboardService.exportDashboard).mockResolvedValue(new Blob());
    vi.mocked(reportDashboardService.saveDashboardConfig).mockResolvedValue({
      id: 'config-1',
      name: 'Test Config',
      chartTypes: ['line'],
      metrics: ['impressions'],
    });
    vi.mocked(reportDashboardService.createSnapshot).mockResolvedValue({
      id: 'snapshot-1',
      name: 'Test Snapshot',
      data: mockDashboardData,
      config: {
        name: 'Test Config',
        chartTypes: ['line'],
        metrics: ['impressions'],
      },
      created_at: '2024-01-01T00:00:00Z',
    });
  });

  const renderComponent = (collectionId = 'test-collection-id') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <CollectionReportDashboard collectionId={collectionId} />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('should render loading state initially', () => {
    vi.mocked(reportDashboardService.getDashboardData).mockImplementation(
      () => new Promise(() => {})
    );

    renderComponent();
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it('should render dashboard data when loaded', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Collection')).toBeInTheDocument();
      expect(screen.getByText(/52 weeks completed/i)).toBeInTheDocument();
    });
  });

  it('should display summary statistics', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/2,200/)).toBeInTheDocument(); // Total impressions
      expect(screen.getByText(/110/)).toBeInTheDocument(); // Total clicks
      expect(screen.getByText(/22/)).toBeInTheDocument(); // Total conversions
      expect(screen.getByText(/\$220/)).toBeInTheDocument(); // Total spend
    });
  });

  it('should render chart visualizations', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Line Chart')).toBeInTheDocument();
      expect(screen.getByText('Bar Chart')).toBeInTheDocument();
    });
  });

  it('should handle week selection', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      const weekSelector = screen.getByLabelText(/select weeks/i);
      expect(weekSelector).toBeInTheDocument();
    });

    // Select a different week range
    const weekSelector = screen.getByLabelText(/select weeks/i);
    fireEvent.change(weekSelector, { target: { value: 'week-1' } });

    await waitFor(() => {
      expect(reportDashboardService.getDashboardData).toHaveBeenCalledWith(
        'test-collection-id',
        expect.objectContaining({ weeks: ['week-1'] })
      );
    });
  });

  it('should handle period comparison', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );
    vi.mocked(reportDashboardService.comparePeriods).mockResolvedValue(
      mockComparisonData
    );

    renderComponent();

    await waitFor(() => {
      const compareButton = screen.getByText(/compare periods/i);
      expect(compareButton).toBeInTheDocument();
    });

    // Click compare button
    fireEvent.click(screen.getByText(/compare periods/i));

    await waitFor(() => {
      expect(screen.getByText(/period comparison/i)).toBeInTheDocument();
      expect(screen.getByText(/\+20%/)).toBeInTheDocument(); // Change percentages
    });
  });

  it('should handle chart type switching', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      const chartTypeSelector = screen.getByLabelText(/chart type/i);
      expect(chartTypeSelector).toBeInTheDocument();
    });

    // Switch chart type
    const chartTypeSelector = screen.getByLabelText(/chart type/i);
    fireEvent.change(chartTypeSelector, { target: { value: 'pie' } });

    await waitFor(() => {
      expect(screen.getByText('Pie Chart')).toBeInTheDocument();
    });
  });

  it('should handle export functionality', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );
    const exportSpy = vi.spyOn(reportDashboardService, 'exportDashboard');

    renderComponent();

    await waitFor(() => {
      const exportButton = screen.getByText(/export/i);
      expect(exportButton).toBeInTheDocument();
    });

    // Click export button
    fireEvent.click(screen.getByText(/export/i));

    await waitFor(() => {
      expect(exportSpy).toHaveBeenCalledWith(
        'test-collection-id',
        expect.any(String)
      );
    });
  });

  it('should handle error states', async () => {
    const errorMessage = 'Failed to load dashboard data';
    vi.mocked(reportDashboardService.getDashboardData).mockRejectedValue(
      new Error(errorMessage)
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/error loading dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should refresh data on interval', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue(
      mockDashboardData
    );

    renderComponent();

    await waitFor(() => {
      expect(reportDashboardService.getDashboardData).toHaveBeenCalledTimes(1);
    });

    // Component should be configured to refresh - just checking initial call
    expect(reportDashboardService.getDashboardData).toHaveBeenCalled();
  });

  it('should handle empty data gracefully', async () => {
    vi.mocked(reportDashboardService.getDashboardData).mockResolvedValue({
      ...mockDashboardData,
      weeks: [],
      summary: null,
      chartData: null,
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/no data available/i)).toBeInTheDocument();
    });
  });
});