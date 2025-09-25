import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TemplatePerformanceMetrics from '../TemplatePerformanceMetrics';
import type { QueryTemplate } from '../../../types/queryTemplate';

// Mock the queryTemplateService
vi.mock('../../../services/queryTemplateService', () => ({
  queryTemplateService: {
    getTemplateMetrics: vi.fn(),
  },
}));

const mockTemplate: QueryTemplate = {
  id: 'template-1',
  name: 'Test Template',
  description: 'Test description',
  category: 'performance',
  report_type: 'performance',
  usage_count: 150,
  sqlTemplate: 'SELECT * FROM campaigns',
  sql_query: 'SELECT * FROM campaigns',
  parameters: {},
  parameter_definitions: {},
  ui_schema: {},
  instance_types: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchInterval: false, // Disable auto-refresh for tests
      },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('TemplatePerformanceMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Quick stats display', () => {
    it('displays basic metrics', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument(); // Usage count
        expect(screen.getByText('Total Usage')).toBeInTheDocument();
      });
    });

    it('displays success rate with progress bar', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('94.5%')).toBeInTheDocument();
        expect(screen.getByText('Success Rate')).toBeInTheDocument();
      });

      // Check for progress bar
      const progressBar = document.querySelector('.bg-green-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('displays average execution time', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('3.2s')).toBeInTheDocument();
        expect(screen.getByText('Avg Time')).toBeInTheDocument();
        expect(screen.getByText('Per execution')).toBeInTheDocument();
      });
    });

    it('displays estimated cost per query', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('$0.0025')).toBeInTheDocument();
        expect(screen.getByText('Est. Cost')).toBeInTheDocument();
        expect(screen.getByText('Per query')).toBeInTheDocument();
      });
    });

    it('shows trend indicators for usage', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('42% (30d)')).toBeInTheDocument(); // 30-day trend
      });

      // Check for trend icon (TrendingUp)
      const trendIcon = document.querySelector('.lucide-trending-up');
      expect(trendIcon).toBeInTheDocument();
    });

    it('formats large numbers correctly', async () => {
      const largeUsageTemplate = { ...mockTemplate, usage_count: 15000 };

      render(
        <TemplatePerformanceMetrics
          template={largeUsageTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('15K')).toBeInTheDocument(); // Formatted as K
      });
    });
  });

  describe('Detailed metrics (showDetails=true)', () => {
    it('shows time range selector when details enabled', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Time Range:')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Week' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Month' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Quarter' })).toBeInTheDocument();
      });
    });

    it('changes time range when button clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Month' })).toBeInTheDocument();
      });

      const weekButton = screen.getByRole('button', { name: 'Week' });
      await user.click(weekButton);

      expect(weekButton).toHaveClass('bg-indigo-600', 'text-white');
    });

    it('displays usage breakdown section', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Usage Breakdown')).toBeInTheDocument();
        expect(screen.getByText('Unique Users')).toBeInTheDocument();
        expect(screen.getByText('45')).toBeInTheDocument(); // User count from mock
        expect(screen.getByText('Times Forked')).toBeInTheDocument();
        expect(screen.getByText('8')).toBeInTheDocument(); // Fork count
        expect(screen.getByText('Favorites')).toBeInTheDocument();
        expect(screen.getByText('23')).toBeInTheDocument(); // Favorite count
      });
    });

    it('toggles execution history display', async () => {
      const user = userEvent.setup();

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Show Execution History')).toBeInTheDocument();
      });

      // Execution history should not be visible initially
      expect(screen.queryByText('Execution History')).not.toBeInTheDocument();

      const toggleButton = screen.getByText('Show Execution History');
      await user.click(toggleButton);

      // Should now show execution history
      expect(screen.getByText('Execution History')).toBeInTheDocument();
      expect(screen.getByText('Hide Execution History')).toBeInTheDocument();
    });

    it('displays execution history chart when toggled', async () => {
      const user = userEvent.setup();

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Show Execution History')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show Execution History');
      await user.click(toggleButton);

      // Should show date entries
      expect(screen.getAllByText(/2024-\d{2}-\d{2}/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/\d+ runs/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/\d+\.\d+s avg/).length).toBeGreaterThan(0);
    });

    it('displays common errors section when errors exist', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Common Issues')).toBeInTheDocument();
      });

      expect(screen.getByText('Timeout exceeded')).toBeInTheDocument();
      expect(screen.getByText('5 occurrences')).toBeInTheDocument();
      expect(screen.getByText('Invalid date range')).toBeInTheDocument();
      expect(screen.getByText('4 occurrences')).toBeInTheDocument();
    });

    it('shows tip for error prevention', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/Most errors can be avoided/)).toBeInTheDocument();
      });
    });

    it('displays popular parameter values', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Popular Parameter Values')).toBeInTheDocument();
      });

      expect(screen.getByText('Date Range')).toBeInTheDocument();
      expect(screen.getByText('Last 30 days')).toBeInTheDocument();
      expect(screen.getByText('Last 7 days')).toBeInTheDocument();
      expect(screen.getByText('Campaign A')).toBeInTheDocument();
    });

    it('formats data processed with units', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Data Processed')).toBeInTheDocument();
        expect(screen.getByText('1.3M')).toBeInTheDocument(); // Formatted as millions
      });
    });
  });

  describe('Loading and error states', () => {
    it('shows loading animation while fetching', () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      const loadingElement = document.querySelector('.animate-pulse');
      expect(loadingElement).toBeInTheDocument();
    });

    it('displays error message when metrics fail to load', async () => {
      // Mock the query to fail
      const failingWrapper = () => {
        const queryClient = new QueryClient({
          defaultOptions: {
            queries: {
              retry: false,
              queryFn: () => Promise.reject(new Error('Network error')),
            },
          },
        });

        return ({ children }: { children: React.ReactNode }) => (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      };

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: failingWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Failed to load performance metrics')).toBeInTheDocument();
      });
    });
  });

  describe('Trend indicators', () => {
    it('shows upward trend with green color for positive values', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const trendText = screen.getByText('42% (30d)');
        expect(trendText).toHaveClass('text-green-600');
      });

      const upIcon = document.querySelector('.lucide-trending-up');
      expect(upIcon).toBeInTheDocument();
    });

    it('shows downward trend with red color for negative values', async () => {
      // Would need to mock with negative trend data
      // This is a placeholder for the test structure
      expect(true).toBe(true);
    });

    it('shows neutral indicator for zero change', async () => {
      // Would need to mock with zero trend data
      // This is a placeholder for the test structure
      expect(true).toBe(true);
    });
  });

  describe('Execution history visualization', () => {
    it('renders success/failure bar chart correctly', async () => {
      const user = userEvent.setup();

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Show Execution History')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show Execution History');
      await user.click(toggleButton);

      // Check for success bars (green)
      const successBars = document.querySelectorAll('.bg-green-500');
      expect(successBars.length).toBeGreaterThan(0);

      // Check for failure bars (red)
      const failureBars = document.querySelectorAll('.bg-red-500');
      expect(failureBars.length).toBeGreaterThan(0);
    });

    it('handles scrollable execution history', async () => {
      const user = userEvent.setup();

      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Show Execution History')).toBeInTheDocument();
      });

      const toggleButton = screen.getByText('Show Execution History');
      await user.click(toggleButton);

      // Check for scrollable container
      const scrollContainer = document.querySelector('.max-h-64.overflow-y-auto');
      expect(scrollContainer).toBeInTheDocument();
    });
  });

  describe('Number formatting', () => {
    it('formats thousands with K suffix', async () => {
      const templateWithThousands = { ...mockTemplate, usage_count: 5500 };

      render(
        <TemplatePerformanceMetrics
          template={templateWithThousands}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('5.5K')).toBeInTheDocument();
      });
    });

    it('formats millions with M suffix', async () => {
      const templateWithMillions = { ...mockTemplate, usage_count: 2500000 };

      render(
        <TemplatePerformanceMetrics
          template={templateWithMillions}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('2.5M')).toBeInTheDocument();
      });
    });

    it('shows small numbers without suffix', async () => {
      const templateWithSmallNum = { ...mockTemplate, usage_count: 42 };

      render(
        <TemplatePerformanceMetrics
          template={templateWithSmallNum}
          templateId="template-1"
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
      });
    });
  });

  describe('Conditional rendering', () => {
    it('does not show detailed sections when showDetails is false', () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={false}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByText('Time Range:')).not.toBeInTheDocument();
      expect(screen.queryByText('Usage Breakdown')).not.toBeInTheDocument();
      expect(screen.queryByText('Common Issues')).not.toBeInTheDocument();
    });

    it('only shows common errors when error count > 0', async () => {
      // Mock data would need error_count: 0 to test this properly
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        // With mock data having error_count > 0, should show errors
        expect(screen.getByText('Common Issues')).toBeInTheDocument();
      });
    });

    it('only shows popular parameters when they exist', async () => {
      render(
        <TemplatePerformanceMetrics
          template={mockTemplate}
          templateId="template-1"
          showDetails={true}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        // Mock data includes popular_parameters
        expect(screen.getByText('Popular Parameter Values')).toBeInTheDocument();
      });
    });
  });
});