import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TemplateGrid from '../TemplateGrid';
import type { QueryTemplate } from '../../../types/queryTemplate';

const mockTemplates: QueryTemplate[] = [
  {
    id: '1',
    name: 'Campaign Performance',
    description: 'Analyze campaign performance metrics',
    category: 'performance',
    sql_query: 'SELECT * FROM campaigns',
    report_type: 'campaign',
    parameters: {},
    parameter_definitions: {},
    ui_schema: {},
    instance_types: ['seller'],
    created_at: '2025-09-01',
    updated_at: '2025-09-01',
  },
  {
    id: '2',
    name: 'Product Conversion',
    description: 'Track product conversion rates',
    category: 'conversion',
    sql_query: 'SELECT * FROM conversions',
    report_type: 'conversion',
    parameters: {},
    parameter_definitions: {},
    ui_schema: {},
    instance_types: ['seller', 'vendor'],
    created_at: '2025-09-01',
    updated_at: '2025-09-01',
  },
  {
    id: '3',
    name: 'Audience Insights',
    description: 'Analyze audience segments',
    category: 'audience',
    sql_query: 'SELECT * FROM audience',
    report_type: 'audience',
    parameters: {},
    parameter_definitions: {},
    ui_schema: {},
    instance_types: ['vendor'],
    created_at: '2025-09-01',
    updated_at: '2025-09-01',
  },
];

describe('TemplateGrid', () => {
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all templates', () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
    expect(screen.getByText('Product Conversion')).toBeInTheDocument();
    expect(screen.getByText('Audience Insights')).toBeInTheDocument();
  });

  it('filters templates by search term', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'campaign' } });

    await waitFor(() => {
      expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
      expect(screen.queryByText('Product Conversion')).not.toBeInTheDocument();
      expect(screen.queryByText('Audience Insights')).not.toBeInTheDocument();
    });
  });

  it('filters templates by category', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const categoryFilter = screen.getByLabelText('Category');
    fireEvent.change(categoryFilter, { target: { value: 'conversion' } });

    await waitFor(() => {
      expect(screen.queryByText('Campaign Performance')).not.toBeInTheDocument();
      expect(screen.getByText('Product Conversion')).toBeInTheDocument();
      expect(screen.queryByText('Audience Insights')).not.toBeInTheDocument();
    });
  });

  it('filters templates by instance type', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const instanceFilter = screen.getByLabelText('Instance Type');
    fireEvent.change(instanceFilter, { target: { value: 'vendor' } });

    await waitFor(() => {
      expect(screen.queryByText('Campaign Performance')).not.toBeInTheDocument();
      expect(screen.getByText('Product Conversion')).toBeInTheDocument();
      expect(screen.getByText('Audience Insights')).toBeInTheDocument();
    });
  });

  it('filters templates by report type', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const reportTypeFilter = screen.getByLabelText('Report Type');
    fireEvent.change(reportTypeFilter, { target: { value: 'audience' } });

    await waitFor(() => {
      expect(screen.queryByText('Campaign Performance')).not.toBeInTheDocument();
      expect(screen.queryByText('Product Conversion')).not.toBeInTheDocument();
      expect(screen.getByText('Audience Insights')).toBeInTheDocument();
    });
  });

  it('calls onSelect when template is clicked', () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const template = screen.getByText('Campaign Performance');
    fireEvent.click(template.closest('div[role="button"]')!);

    expect(mockOnSelect).toHaveBeenCalledWith(mockTemplates[0]);
  });

  it('applies multiple filters simultaneously', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'conversion' } });

    const instanceFilter = screen.getByLabelText('Instance Type');
    fireEvent.change(instanceFilter, { target: { value: 'seller' } });

    await waitFor(() => {
      expect(screen.queryByText('Campaign Performance')).not.toBeInTheDocument();
      expect(screen.getByText('Product Conversion')).toBeInTheDocument();
      expect(screen.queryByText('Audience Insights')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no templates match filters', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No templates found')).toBeInTheDocument();
    });
  });

  it('resets filters when clear button is clicked', async () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const searchInput = screen.getByPlaceholderText('Search templates...');
    fireEvent.change(searchInput, { target: { value: 'campaign' } });

    await waitFor(() => {
      expect(screen.queryByText('Product Conversion')).not.toBeInTheDocument();
    });

    const clearButton = screen.getByText('Clear filters');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
      expect(screen.getByText('Product Conversion')).toBeInTheDocument();
      expect(screen.getByText('Audience Insights')).toBeInTheDocument();
    });
  });

  it('displays template category badges', () => {
    render(<TemplateGrid templates={mockTemplates} onSelect={mockOnSelect} />);

    const performanceBadge = screen.getByText('performance');
    const conversionBadge = screen.getByText('conversion');
    const audienceBadge = screen.getByText('audience');

    expect(performanceBadge).toHaveClass('bg-blue-100');
    expect(conversionBadge).toHaveClass('bg-green-100');
    expect(audienceBadge).toHaveClass('bg-purple-100');
  });
});