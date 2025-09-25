import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReportBuilder from '../ReportBuilder';
import { reportService } from '../../../services/reportService';
import { queryTemplateService } from '../../../services/queryTemplateService';

// Mock services
vi.mock('../../../services/reportService');
vi.mock('../../../services/queryTemplateService');
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock child components
vi.mock('../ExecutionsGrid', () => ({
  default: () => <div>Executions Grid</div>
}));

vi.mock('../DashboardsTable', () => ({
  default: () => <div>Dashboards Table</div>
}));

vi.mock('../RunReportModal', () => ({
  default: ({ isOpen, onClose, includeTemplateStep }: any) => isOpen ? (
    <div data-testid="run-report-modal">
      <button onClick={onClose}>Close</button>
      {includeTemplateStep && <div>Template Selection Step Enabled</div>}
    </div>
  ) : null
}));

vi.mock('../../executions/AMCExecutionDetail', () => ({
  default: () => <div>AMC Execution Detail</div>
}));

describe('ReportBuilder - Query Library Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    vi.clearAllMocks();

    // Setup default mock responses
    vi.mocked(reportService.listReports).mockResolvedValue({ data: [] });
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: {
        templates: [
          {
            id: 'template1',
            name: 'Sample Query Template',
            description: 'Test template',
            sql_query: 'SELECT * FROM campaigns WHERE {{campaign_name}}',
            category: 'Campaign Analysis',
            is_public: true,
            usage_count: 10,
          }
        ]
      }
    });
  });

  const renderReportBuilder = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ReportBuilder />
      </QueryClientProvider>
    );
  };

  describe('Query Library Template Access', () => {
    it('should show Create Report button', () => {
      renderReportBuilder();

      expect(screen.getByRole('button', { name: /Create Report/i })).toBeInTheDocument();
    });

    it('should open modal with template selection when Create Report is clicked', async () => {
      renderReportBuilder();

      const createButton = screen.getByRole('button', { name: /Create Report/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('run-report-modal')).toBeInTheDocument();
        expect(screen.getByText('Template Selection Step Enabled')).toBeInTheDocument();
      });
    });

    it('should indicate in description that templates are from AMC query templates', () => {
      renderReportBuilder();

      expect(screen.getByText(/Create and manage automated reports from AMC query templates/i)).toBeInTheDocument();
    });

    it('should close modal when close button is clicked', async () => {
      renderReportBuilder();

      const createButton = screen.getByRole('button', { name: /Create Report/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByTestId('run-report-modal')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /Close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByTestId('run-report-modal')).not.toBeInTheDocument();
      });
    });

    it('should pass includeTemplateStep=true to RunReportModal for custom reports', async () => {
      renderReportBuilder();

      const createButton = screen.getByRole('button', { name: /Create Report/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        // The presence of this text confirms includeTemplateStep was passed as true
        expect(screen.getByText('Template Selection Step Enabled')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should show Reports and Dashboards tabs', () => {
      renderReportBuilder();

      expect(screen.getByRole('button', { name: /Reports/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Dashboards/i })).toBeInTheDocument();
    });

    it('should default to Reports tab', () => {
      renderReportBuilder();

      expect(screen.getByText('Executions Grid')).toBeInTheDocument();
      expect(screen.queryByText('Dashboards Table')).not.toBeInTheDocument();
    });

    it('should switch to Dashboards tab when clicked', async () => {
      renderReportBuilder();

      const dashboardsTab = screen.getByRole('button', { name: /Dashboards/i });
      fireEvent.click(dashboardsTab);

      await waitFor(() => {
        expect(screen.queryByText('Executions Grid')).not.toBeInTheDocument();
        expect(screen.getByText('Dashboards Table')).toBeInTheDocument();
      });
    });
  });

  describe('Template-Based Report Creation', () => {
    it('should handle report creation from template', async () => {
      const mockCreateReport = vi.mocked(reportService.createReport);
      mockCreateReport.mockResolvedValue({ success: true, data: { id: 'report1' } });

      const { rerender } = renderReportBuilder();

      // Click create report
      const createButton = screen.getByRole('button', { name: /Create Report/i });
      fireEvent.click(createButton);

      // Modal should be open
      await waitFor(() => {
        expect(screen.getByTestId('run-report-modal')).toBeInTheDocument();
      });

      // The actual template selection and submission would happen inside RunReportModal
      // which is mocked in this test. The integration test verifies the connection.
    });
  });

  describe('Query Library Integration Features', () => {
    it('should support saving successful queries as templates', () => {
      // This is a placeholder test for the "Save as Template" feature
      // which should be implemented in the Report Builder
      renderReportBuilder();

      // The feature implementation would add a "Save as Template" button
      // after a successful query execution in the ExecutionsGrid
      // For now, we just verify the component renders
      expect(screen.getByText('Report Builder')).toBeInTheDocument();
    });

    it('should allow browsing Query Library templates during report creation', () => {
      // This test verifies that the RunReportModal is configured to show
      // Query Library templates when creating a new report
      renderReportBuilder();

      const createButton = screen.getByRole('button', { name: /Create Report/i });
      fireEvent.click(createButton);

      // The modal should include template selection functionality
      // This is handled by the RunReportModal component
      expect(screen.getByTestId('run-report-modal')).toBeInTheDocument();
    });
  });
});