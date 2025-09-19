import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RunReportModal from '../RunReportModal';
import type { QueryTemplate } from '../../../types/queryTemplate';

// Mock all services
vi.mock('../../../services/instanceService', () => ({
  instanceService: {
    list: vi.fn().mockResolvedValue([
      {
        id: '1',
        instanceId: 'instance1',
        instanceName: 'Production Instance',
      },
      {
        id: '2',
        instanceId: 'instance2',
        instanceName: 'Staging Instance',
      },
    ]),
  },
}));

vi.mock('../../../services/queryTemplateService', () => ({
  queryTemplateService: {
    listTemplates: vi.fn(),
    incrementUsage: vi.fn().mockResolvedValue({ success: true }),
    forkTemplate: vi.fn(),
    getTemplateMetrics: vi.fn().mockResolvedValue({
      usage_count: 150,
      success_rate: 94.5,
      average_execution_time: 3.2,
    }),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock child components with minimal implementation
vi.mock('../../common/SQLEditor', () => ({
  default: ({ value, onChange, readOnly, height }: any) => (
    <textarea
      data-testid="sql-editor"
      value={value}
      onChange={(e) => !readOnly && onChange?.(e.target.value)}
      readOnly={readOnly}
      style={{ height }}
      placeholder="SQL Editor"
    />
  ),
}));

vi.mock('../DynamicParameterForm', () => ({
  default: ({ onSubmit, submitLabel }: any) => (
    <div data-testid="dynamic-parameter-form">
      <button onClick={() => onSubmit({})}>{submitLabel || 'Submit'}</button>
    </div>
  ),
}));

vi.mock('../../parameter-detection/EnhancedParameterSelector', () => ({
  EnhancedParameterSelector: ({ parameter, value, onChange }: any) => (
    <div data-testid={`param-selector-${parameter.name}`}>
      <label>{parameter.name}</label>
      <input
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={`Enter ${parameter.name}`}
      />
    </div>
  ),
}));

vi.mock('../InstanceSelector', () => ({
  default: ({ value, onChange, placeholder }: any) => (
    <select
      data-testid="instance-selector"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
      <option value="instance1">Production Instance</option>
      <option value="instance2">Staging Instance</option>
    </select>
  ),
}));

vi.mock('../../query-library/TemplateForkDialog', () => ({
  default: ({ isOpen, onClose, template, onForked }: any) =>
    isOpen ? (
      <div data-testid="fork-dialog">
        <h2>Fork Template</h2>
        <p>Forking: {template?.name}</p>
        <button onClick={onClose}>Close</button>
        <button
          onClick={() => {
            onForked({ ...template, id: 'forked-1', name: 'Forked Template' });
            onClose();
          }}
        >
          Create Fork
        </button>
      </div>
    ) : null,
}));

vi.mock('../../query-library/TemplateTagsManager', () => ({
  default: ({ template, readOnly }: any) => (
    <div data-testid="tags-manager">
      <p>Category: {template?.category}</p>
      <p>Tags: {template?.tags?.join(', ')}</p>
      {readOnly && <p>Read-only mode</p>}
    </div>
  ),
}));

vi.mock('../../query-library/TemplatePerformanceMetrics', () => ({
  default: ({ template, showDetails }: any) => (
    <div data-testid="performance-metrics">
      <p>Usage: {template?.usage_count || 0}</p>
      {showDetails && <p>Detailed metrics shown</p>}
    </div>
  ),
}));

import { queryTemplateService } from '../../../services/queryTemplateService';
import toast from 'react-hot-toast';

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

const mockTemplates: QueryTemplate[] = [
  {
    id: '1',
    name: 'Campaign Performance Report',
    description: 'Analyze campaign performance metrics',
    category: 'performance',
    report_type: 'performance',
    tags: ['campaign', 'performance', 'roas'],
    difficulty_level: 'BEGINNER',
    usage_count: 42,
    sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}} AND campaign_name LIKE {{search}}',
    sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}} AND campaign_name LIKE {{search}}',
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-01-31',
      search: 'Summer',
    },
    parameter_definitions: {},
    ui_schema: {},
    instance_types: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: '2',
    name: 'Attribution Analysis',
    description: 'Multi-touch attribution report',
    category: 'attribution',
    report_type: 'attribution',
    tags: ['attribution', 'multi-touch'],
    difficulty_level: 'ADVANCED',
    usage_count: 15,
    sqlTemplate: 'SELECT * FROM attribution WHERE asin IN {{asin_list}}',
    sql_query: 'SELECT * FROM attribution WHERE asin IN {{asin_list}}',
    parameters: {},
    parameter_definitions: {},
    ui_schema: {},
    instance_types: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
];

describe('RunReportModal Integration Tests', () => {
  const mockOnClose = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
      data: {
        templates: mockTemplates,
        total: mockTemplates.length,
      },
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Complete workflow - Template Selection to Submission', () => {
    it('completes full workflow from template selection to report creation', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Step 1: Template Selection
      expect(screen.getByText('Select Query Template')).toBeInTheDocument();

      // Wait for templates to load
      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      // Select a template
      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Click "Use This Template"
      const useButton = await screen.findByRole('button', { name: /Use This Template/i });
      await user.click(useButton);

      // Step 2: Parameters
      await waitFor(() => {
        expect(screen.getByText('Configure Parameters')).toBeInTheDocument();
      });

      // Select instance
      const instanceSelector = screen.getByTestId('instance-selector');
      await user.selectOptions(instanceSelector, 'instance1');

      // Parameters are detected from SQL
      expect(screen.getByTestId('param-selector-start_date')).toBeInTheDocument();
      expect(screen.getByTestId('param-selector-end_date')).toBeInTheDocument();
      expect(screen.getByTestId('param-selector-search')).toBeInTheDocument();

      // Fill parameters
      const startDateInput = within(screen.getByTestId('param-selector-start_date')).getByRole('textbox');
      await user.clear(startDateInput);
      await user.type(startDateInput, '2024-01-01');

      const endDateInput = within(screen.getByTestId('param-selector-end_date')).getByRole('textbox');
      await user.clear(endDateInput);
      await user.type(endDateInput, '2024-01-31');

      const searchInput = within(screen.getByTestId('param-selector-search')).getByRole('textbox');
      await user.type(searchInput, 'Campaign');

      // Click Next
      const nextButtons = screen.getAllByText('Next');
      await user.click(nextButtons[nextButtons.length - 1]);

      // Step 3: Execution Type
      await waitFor(() => {
        expect(screen.getByText('Select Execution Type')).toBeInTheDocument();
      });

      const recurringOption = screen.getByLabelText('Recurring Schedule');
      await user.click(recurringOption);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      await user.click(nextButton);

      // Step 4: Schedule
      await waitFor(() => {
        expect(screen.getByText('Configure Schedule')).toBeInTheDocument();
      });

      const frequencySelect = screen.getByRole('combobox');
      await user.selectOptions(frequencySelect, 'weekly');

      await user.click(nextButton);

      // Step 5: Review
      await waitFor(() => {
        expect(screen.getByText('Review Configuration')).toBeInTheDocument();
      });

      // Verify all settings are shown
      expect(screen.getByText('Campaign Performance Report Report')).toBeInTheDocument();
      expect(screen.getByText('Recurring Schedule')).toBeInTheDocument();

      // Submit
      const runButton = screen.getByRole('button', { name: /Run Report/i });
      await user.click(runButton);

      // Verify submission
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Campaign Performance Report Report',
          template_id: '1',
          instance_id: 'instance1',
          execution_type: 'recurring',
          parameters: expect.objectContaining({
            start_date: '2024-01-01',
            end_date: '2024-01-31',
            search: 'Campaign',
          }),
        })
      );
    });

    it('completes workflow with custom SQL', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Wait for initial render
      await waitFor(() => {
        expect(screen.getByText('Select Query Template')).toBeInTheDocument();
      });

      // Select custom SQL mode
      const customSqlRadio = screen.getByLabelText('Write Custom SQL');
      await user.click(customSqlRadio);

      // Enter custom SQL
      const sqlEditor = screen.getByTestId('sql-editor');
      await user.type(sqlEditor, 'SELECT * FROM orders WHERE amount > {{min_amount}}');

      // Enter report details
      const nameInput = screen.getByPlaceholderText('Enter report name...');
      await user.type(nameInput, 'Custom Order Report');

      const descriptionInput = screen.getByPlaceholderText('Describe your report...');
      await user.type(descriptionInput, 'Orders above threshold');

      // Parameters should be detected
      await waitFor(() => {
        expect(screen.getByText('min_amount')).toBeInTheDocument();
      });

      // Continue with custom query
      const continueButton = screen.getByRole('button', { name: /Continue with Custom Query/i });
      await user.click(continueButton);

      // Configure parameters
      await waitFor(() => {
        expect(screen.getByText('Configure Parameters')).toBeInTheDocument();
      });

      // Select instance
      const instanceSelector = screen.getByTestId('instance-selector');
      await user.selectOptions(instanceSelector, 'instance2');

      // Fill detected parameter
      const minAmountInput = within(screen.getByTestId('param-selector-min_amount')).getByRole('textbox');
      await user.type(minAmountInput, '1000');

      // Continue through remaining steps
      const nextButtons = screen.getAllByText('Next');
      await user.click(nextButtons[nextButtons.length - 1]);

      // Select once execution
      await waitFor(() => {
        expect(screen.getByText('Select Execution Type')).toBeInTheDocument();
      });

      const onceOption = screen.getByLabelText('Run Once');
      await user.click(onceOption);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      await user.click(nextButton);

      // Should skip schedule and go to review
      await waitFor(() => {
        expect(screen.getByText('Review Configuration')).toBeInTheDocument();
      });

      // Submit
      const runButton = screen.getByRole('button', { name: /Run Report/i });
      await user.click(runButton);

      // Verify submission with custom SQL
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Custom Order Report',
          description: 'Orders above threshold',
          custom_sql: 'SELECT * FROM orders WHERE amount > {{min_amount}}',
          template_id: undefined,
          instance_id: 'instance2',
          execution_type: 'once',
          parameters: expect.objectContaining({
            min_amount: '1000',
          }),
        })
      );
    });
  });

  describe('Template features integration', () => {
    it('shows and hides performance metrics', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Wait for templates to load
      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      // Select a template
      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Initially metrics should not be visible
      expect(screen.queryByTestId('performance-metrics')).not.toBeInTheDocument();

      // Click show metrics
      const metricsButton = screen.getByRole('button', { name: /Show Metrics/i });
      await user.click(metricsButton);

      // Metrics should now be visible
      expect(screen.getByTestId('performance-metrics')).toBeInTheDocument();
      expect(screen.getByText('Usage: 42')).toBeInTheDocument();
      expect(screen.getByText('Detailed metrics shown')).toBeInTheDocument();

      // Hide metrics
      const hideMetricsButton = screen.getByRole('button', { name: /Hide Metrics/i });
      await user.click(hideMetricsButton);

      // Metrics should be hidden
      expect(screen.queryByTestId('performance-metrics')).not.toBeInTheDocument();
    });

    it('opens fork dialog and creates fork', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Wait for templates and select one
      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Click fork button
      const forkButton = screen.getByRole('button', { name: /Fork Template/i });
      await user.click(forkButton);

      // Fork dialog should open
      expect(screen.getByTestId('fork-dialog')).toBeInTheDocument();
      expect(screen.getByText('Forking: Campaign Performance Report')).toBeInTheDocument();

      // Create fork
      const createForkButton = screen.getByRole('button', { name: /Create Fork/i });
      await user.click(createForkButton);

      // Should switch to forked template
      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith('Now using your forked template');
      });

      // Fork dialog should close
      expect(screen.queryByTestId('fork-dialog')).not.toBeInTheDocument();
    });

    it('displays tags and category information', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Wait for templates
      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      // Select a template
      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Tags manager should be visible
      expect(screen.getByTestId('tags-manager')).toBeInTheDocument();
      expect(screen.getByText('Category: performance')).toBeInTheDocument();
      expect(screen.getByText('Tags: campaign, performance, roas')).toBeInTheDocument();
      expect(screen.getByText('Read-only mode')).toBeInTheDocument();
    });
  });

  describe('Search and filtering', () => {
    it('filters templates by search query', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search templates...');
      await user.type(searchInput, 'Attribution');

      // Mock the filtered response
      vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
        data: {
          templates: [mockTemplates[1]], // Only attribution template
          total: 1,
        },
      });

      await waitFor(() => {
        expect(queryTemplateService.listTemplates).toHaveBeenCalledWith(
          true,
          expect.objectContaining({
            search: 'Attribution',
          })
        );
      });
    });

    it('filters templates by category', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Category')).toBeInTheDocument();
      });

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'attribution');

      // Mock the filtered response
      vi.mocked(queryTemplateService.listTemplates).mockResolvedValue({
        data: {
          templates: [mockTemplates[1]],
          total: 1,
        },
      });

      await waitFor(() => {
        expect(queryTemplateService.listTemplates).toHaveBeenCalledWith(
          true,
          expect.objectContaining({
            category: 'attribution',
          })
        );
      });
    });
  });

  describe('Parameter detection and substitution', () => {
    it('detects parameters with context from SQL', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      // Select template with multiple parameter types
      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Use the template
      const useButton = await screen.findByRole('button', { name: /Use This Template/i });
      await user.click(useButton);

      // Should detect parameters with correct types
      await waitFor(() => {
        // Date parameters for BETWEEN context
        expect(screen.getByTestId('param-selector-start_date')).toBeInTheDocument();
        expect(screen.getByTestId('param-selector-end_date')).toBeInTheDocument();

        // Pattern parameter for LIKE context
        expect(screen.getByTestId('param-selector-search')).toBeInTheDocument();
      });
    });

    it('shows SQL preview with parameter substitution', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplates[0]}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Go to parameters step
      await waitFor(() => {
        expect(screen.getByText('Configure Parameters')).toBeInTheDocument();
      });

      // Fill parameters
      const searchInput = within(screen.getByTestId('param-selector-search')).getByRole('textbox');
      await user.type(searchInput, 'Summer');

      // Navigate to review step
      const nextButtons = screen.getAllByText('Next');
      await user.click(nextButtons[nextButtons.length - 1]);

      // Skip through execution type
      await waitFor(() => {
        expect(screen.getByText('Select Execution Type')).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /Next/i });
      await user.click(nextButton);

      // Should be at review
      await waitFor(() => {
        expect(screen.getByText('Review Configuration')).toBeInTheDocument();
      });

      // Toggle query preview
      const queryToggle = screen.getByText('Query Preview');
      await user.click(queryToggle);

      // SQL editor should show substituted SQL
      const sqlEditor = screen.getByTestId('sql-editor');
      expect(sqlEditor).toBeInTheDocument();
    });
  });

  describe('Error handling', () => {
    it('shows error toast when template usage increment fails', async () => {
      const user = userEvent.setup();
      vi.mocked(queryTemplateService.incrementUsage).mockRejectedValue(new Error('Network error'));

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      const templateCard = screen.getByText('Campaign Performance Report').closest('[role="button"]');
      await user.click(templateCard!);

      // Error should be logged but not break the flow
      await waitFor(() => {
        expect(queryTemplateService.incrementUsage).toHaveBeenCalled();
      });
    });

    it('validates required fields before submission', async () => {
      const user = userEvent.setup();

      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplates[0]}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      // Try to proceed without selecting instance
      const nextButtons = screen.getAllByText('Next');
      const nextButton = nextButtons[nextButtons.length - 1];

      // Button should be disabled without instance
      expect(nextButton).toBeDisabled();

      // Select instance
      const instanceSelector = screen.getByTestId('instance-selector');
      await user.selectOptions(instanceSelector, 'instance1');

      // Now button should be enabled
      expect(nextButton).not.toBeDisabled();
    });
  });
});