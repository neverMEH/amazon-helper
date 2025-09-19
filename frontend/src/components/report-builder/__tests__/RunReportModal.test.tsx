import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import RunReportModal from '../RunReportModal';
import type { QueryTemplate } from '../../../types/queryTemplate';

// Mock the instanceService
vi.mock('../../../services/instanceService', () => ({
  instanceService: {
    list: vi.fn().mockResolvedValue([
      {
        id: '1',
        instanceId: 'instance1',
        instanceName: 'Test Instance 1',
      },
      {
        id: '2',
        instanceId: 'instance2',
        instanceName: 'Test Instance 2',
      },
    ]),
  },
}));

// Mock the queryTemplateService
vi.mock('../../../services/queryTemplateService', () => ({
  queryTemplateService: {
    listTemplates: vi.fn().mockResolvedValue({
      data: {
        templates: [
          {
            id: '1',
            name: 'Campaign Performance Report',
            description: 'Analyze campaign performance',
            category: 'performance',
            usage_count: 42,
            difficulty_level: 'BEGINNER',
            tags: ['campaign', 'performance'],
            sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
            sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
            parameters: {
              start_date: '2025-01-01',
              end_date: '2025-01-31',
            },
          },
          {
            id: '2',
            name: 'Attribution Analysis',
            description: 'Cross-channel attribution report',
            category: 'attribution',
            usage_count: 15,
            difficulty_level: 'ADVANCED',
            tags: ['attribution', 'multi-touch'],
            sqlTemplate: 'SELECT * FROM attribution WHERE campaign_id IN ({{campaign_ids}})',
            sql_query: 'SELECT * FROM attribution WHERE campaign_id IN ({{campaign_ids}})',
            parameters: {
              campaign_ids: ['CAMP001', 'CAMP002'],
            },
          },
        ],
        total: 2,
      },
    }),
    getTemplate: vi.fn().mockResolvedValue({
      id: '1',
      name: 'Campaign Performance Report',
      description: 'Analyze campaign performance',
      category: 'performance',
      sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
      sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
      parameters: {
        start_date: '2025-01-01',
        end_date: '2025-01-31',
      },
      parameter_definitions: {
        start_date: { type: 'date', label: 'Start Date', required: true },
        end_date: { type: 'date', label: 'End Date', required: true },
      },
    }),
    incrementUsage: vi.fn().mockResolvedValue({ success: true }),
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
  sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
  sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
  report_type: 'campaign',
  parameters: {
    start_date: '2025-01-01',
    end_date: '2025-01-31',
  },
  defaultParameters: {
    start_date: '2025-01-01',
    end_date: '2025-01-31',
  },
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

  it('shows multi-step wizard with correct steps including template selection', () => {
    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={null}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('1. Template Selection')).toBeInTheDocument();
    expect(screen.getByText('2. Parameters')).toBeInTheDocument();
    expect(screen.getByText('3. Execution Type')).toBeInTheDocument();
    // Schedule step is conditionally shown based on execution type (not shown for 'once')
    expect(screen.getByText(/Review/)).toBeInTheDocument();
  });

  it('shows multi-step wizard without template selection when template is provided', () => {
    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={mockTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByText(/Template Selection/)).not.toBeInTheDocument();
    expect(screen.getByText('1. Parameters')).toBeInTheDocument();
    expect(screen.getByText('2. Execution Type')).toBeInTheDocument();
    // Schedule step is conditionally shown based on execution type (not shown for 'once')
    expect(screen.getByText(/Review/)).toBeInTheDocument();
  });

  it('navigates through wizard steps', async () => {
    const user = userEvent.setup();

    // Use a template without parameter_definitions to simplify the test
    const simpleTemplate = {
      ...mockTemplate,
      parameter_definitions: {},
      parameters: {},
    };

    render(
      <RunReportModal
        isOpen={true}
        onClose={mockOnClose}
        template={simpleTemplate}
        onSubmit={mockOnSubmit}
      />,
      { wrapper: createWrapper() }
    );

    // Step 1: Parameters
    expect(screen.getByText('Configure Parameters')).toBeInTheDocument();

    // Since we have detected parameters from SQL, click Next button
    const nextButtons = screen.getAllByText('Next');
    await user.click(nextButtons[nextButtons.length - 1]); // Click the last Next button

    // Step 2: Execution Type
    await waitFor(() => {
      expect(screen.getByText('Select Execution Type')).toBeInTheDocument();
    });

    // Select execution type and continue
    const onceOption = screen.getByLabelText('Run Once');
    await user.click(onceOption);
    const nextButtonExecution = screen.getByRole('button', { name: /Next/i });
    await user.click(nextButtonExecution);

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

  describe('Template Selection Step', () => {
    it('displays template selection as first step when no template provided', () => {
      render(
        <RunReportModal
          isOpen={true}
          onClose={mockOnClose}
          template={null}
          onSubmit={mockOnSubmit}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Select Query Template')).toBeInTheDocument();
      expect(screen.getByText('Choose from Query Library')).toBeInTheDocument();
      expect(screen.getByText('Write Custom SQL')).toBeInTheDocument();
    });

    it('shows template browser when "Choose from Query Library" is selected', async () => {
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search templates...')).toBeInTheDocument();
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
        expect(screen.getByText('Attribution Analysis')).toBeInTheDocument();
      });
    });

    it('displays template metadata in selection grid', async () => {
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => {
        // Check for usage count display
        expect(screen.getByText('42 uses')).toBeInTheDocument();
        expect(screen.getByText('15 uses')).toBeInTheDocument();

        // Check for difficulty level
        expect(screen.getByText('BEGINNER')).toBeInTheDocument();
        expect(screen.getByText('ADVANCED')).toBeInTheDocument();

        // Check for tags
        expect(screen.getByText('campaign')).toBeInTheDocument();
        expect(screen.getByText('attribution')).toBeInTheDocument();
      });
    });

    it('allows template search and filtering', async () => {
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      const searchInput = await screen.findByPlaceholderText('Search templates...');
      await user.type(searchInput, 'attribution');

      await waitFor(() => {
        expect(screen.queryByText('Campaign Performance Report')).not.toBeInTheDocument();
        expect(screen.getByText('Attribution Analysis')).toBeInTheDocument();
      });
    });

    it('shows SQL editor when "Write Custom SQL" is selected', async () => {
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

      const customOption = screen.getByLabelText('Write Custom SQL');
      await user.click(customOption);

      await waitFor(() => {
        expect(screen.getByText('Custom SQL Query')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter your SQL query with {{parameter}} placeholders...')).toBeInTheDocument();
      });
    });

    it('detects parameters from custom SQL in real-time', async () => {
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

      const customOption = screen.getByLabelText('Write Custom SQL');
      await user.click(customOption);

      const sqlEditor = await screen.findByPlaceholderText('Enter your SQL query with {{parameter}} placeholders...');
      await user.type(sqlEditor, 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaign_ids}}) AND date >= {{start_date}}');

      await waitFor(() => {
        expect(screen.getByText('Detected Parameters (2)')).toBeInTheDocument();
        expect(screen.getByText('campaign_ids')).toBeInTheDocument();
        expect(screen.getByText('start_date')).toBeInTheDocument();
      });
    });

    it('shows SQL preview when template is selected', async () => {
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => screen.getByText('Campaign Performance Report'));

      const templateCard = screen.getByText('Campaign Performance Report').closest('div[role="button"]');
      await user.click(templateCard!);

      await waitFor(() => {
        expect(screen.getByText('SQL Preview')).toBeInTheDocument();
        expect(screen.getByText(/SELECT \* FROM campaigns WHERE date >=/)).toBeInTheDocument();
      });
    });

    it('increments template usage count when selected', async () => {
      const { queryTemplateService } = await import('../../../services/queryTemplateService');
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => screen.getByText('Campaign Performance Report'));

      const templateCard = screen.getByText('Campaign Performance Report').closest('div[role="button"]');
      await user.click(templateCard!);

      const selectButton = screen.getByText('Use This Template');
      await user.click(selectButton);

      await waitFor(() => {
        expect(queryTemplateService.incrementUsage).toHaveBeenCalledWith('1');
      });
    });

    it('transitions to parameter configuration after template selection', async () => {
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => screen.getByText('Campaign Performance Report'));

      const templateCard = screen.getByText('Campaign Performance Report').closest('div[role="button"]');
      await user.click(templateCard!);

      const selectButton = screen.getByText('Use This Template');
      await user.click(selectButton);

      await waitFor(() => {
        expect(screen.getByText('Configure Parameters')).toBeInTheDocument();
        expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
        expect(screen.getByLabelText('End Date')).toBeInTheDocument();
      });
    });

    it('allows switching between template and custom SQL modes', async () => {
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

      // Start with template mode
      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
      });

      // Switch to custom SQL mode
      const customOption = screen.getByLabelText('Write Custom SQL');
      await user.click(customOption);

      await waitFor(() => {
        expect(screen.queryByText('Campaign Performance Report')).not.toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter your SQL query with {{parameter}} placeholders...')).toBeInTheDocument();
      });

      // Switch back to template mode
      await user.click(libraryOption);

      await waitFor(() => {
        expect(screen.getByText('Campaign Performance Report')).toBeInTheDocument();
        expect(screen.queryByPlaceholderText('Enter your SQL query with {{parameter}} placeholders...')).not.toBeInTheDocument();
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

      const libraryOption = screen.getByLabelText('Choose from Query Library');
      await user.click(libraryOption);

      await waitFor(() => screen.getByText('All Categories'));

      const categorySelect = screen.getByLabelText('Category');
      await user.selectOptions(categorySelect, 'attribution');

      await waitFor(() => {
        expect(screen.queryByText('Campaign Performance Report')).not.toBeInTheDocument();
        expect(screen.getByText('Attribution Analysis')).toBeInTheDocument();
      });
    });
  });
});