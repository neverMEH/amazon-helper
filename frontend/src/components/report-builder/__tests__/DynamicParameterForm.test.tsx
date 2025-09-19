import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DynamicParameterForm from '../DynamicParameterForm';
import type { ParameterDefinition } from '../../../types/report';

const mockParameterDefinitions: Record<string, ParameterDefinition> = {
  start_date: {
    type: 'date',
    label: 'Start Date',
    required: true,
    description: 'Report start date',
  },
  end_date: {
    type: 'date',
    label: 'End Date',
    required: true,
    description: 'Report end date',
  },
  campaigns: {
    type: 'array',
    label: 'Campaigns',
    required: false,
    description: 'Select campaigns to include',
    options: [
      { value: 'camp1', label: 'Campaign 1' },
      { value: 'camp2', label: 'Campaign 2' },
      { value: 'camp3', label: 'Campaign 3' },
    ],
  },
  metric_type: {
    type: 'select',
    label: 'Metric Type',
    required: true,
    description: 'Select metric type',
    options: [
      { value: 'impressions', label: 'Impressions' },
      { value: 'clicks', label: 'Clicks' },
      { value: 'conversions', label: 'Conversions' },
    ],
  },
  threshold: {
    type: 'number',
    label: 'Threshold',
    required: false,
    description: 'Minimum threshold value',
    min: 0,
    max: 1000,
  },
  include_archived: {
    type: 'boolean',
    label: 'Include Archived',
    required: false,
    description: 'Include archived campaigns',
  },
};

const mockUiSchema = {
  'ui:order': ['start_date', 'end_date', 'campaigns', 'metric_type', 'threshold', 'include_archived'],
  start_date: {
    'ui:widget': 'date',
    'ui:placeholder': 'Select start date',
  },
  end_date: {
    'ui:widget': 'date',
    'ui:placeholder': 'Select end date',
  },
  campaigns: {
    'ui:widget': 'multiselect',
    'ui:placeholder': 'Select campaigns',
  },
  metric_type: {
    'ui:widget': 'select',
    'ui:placeholder': 'Choose metric',
  },
};

describe('DynamicParameterForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all form fields based on parameter definitions', () => {
    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    expect(screen.getByLabelText('Campaigns')).toBeInTheDocument();
    expect(screen.getByLabelText('Metric Type')).toBeInTheDocument();
    expect(screen.getByLabelText('Threshold')).toBeInTheDocument();
    expect(screen.getByLabelText('Include Archived')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const submitButton = screen.getByText('Submit');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Start Date is required')).toBeInTheDocument();
      expect(screen.getByText('End Date is required')).toBeInTheDocument();
      expect(screen.getByText('Metric Type is required')).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    // Fill in required fields
    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-01');

    const endDate = screen.getByLabelText('End Date');
    await user.type(endDate, '2025-09-15');

    const metricType = screen.getByLabelText('Metric Type');
    await user.selectOptions(metricType, 'impressions');

    const submitButton = screen.getByText('Submit');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        start_date: '2025-09-01',
        end_date: '2025-09-15',
        metric_type: 'impressions',
        campaigns: [],
        threshold: undefined,
        include_archived: false,
      });
    });
  });

  it('calls onChange when form values change', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-01');

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: '2025-09-01',
        })
      );
    });
  });

  it('validates number field constraints', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const threshold = screen.getByLabelText('Threshold');
    await user.type(threshold, '5000'); // Above max

    await waitFor(() => {
      expect(screen.getByText('Threshold must be less than or equal to 1000')).toBeInTheDocument();
    });

    await user.clear(threshold);
    await user.type(threshold, '-10'); // Below min

    await waitFor(() => {
      expect(screen.getByText('Threshold must be greater than or equal to 0')).toBeInTheDocument();
    });
  });

  it('handles multiselect fields correctly', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const campaigns = screen.getByLabelText('Campaigns');
    await user.selectOptions(campaigns, ['camp1', 'camp2']);

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          campaigns: ['camp1', 'camp2'],
        })
      );
    });
  });

  it('handles boolean fields correctly', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const includeArchived = screen.getByLabelText('Include Archived');
    await user.click(includeArchived);

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith(
        expect.objectContaining({
          include_archived: true,
        })
      );
    });
  });

  it('uses initial values when provided', () => {
    const initialValues = {
      start_date: '2025-09-01',
      end_date: '2025-09-15',
      metric_type: 'clicks',
      campaigns: ['camp1'],
      threshold: 100,
      include_archived: true,
    };

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        initialValues={initialValues}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    expect((screen.getByLabelText('Start Date') as HTMLInputElement).value).toBe('2025-09-01');
    expect((screen.getByLabelText('End Date') as HTMLInputElement).value).toBe('2025-09-15');
    expect((screen.getByLabelText('Metric Type') as HTMLSelectElement).value).toBe('clicks');
    expect((screen.getByLabelText('Threshold') as HTMLInputElement).value).toBe('100');
    expect((screen.getByLabelText('Include Archived') as HTMLInputElement).checked).toBe(true);
  });

  it('displays field descriptions as help text', () => {
    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('Report start date')).toBeInTheDocument();
    expect(screen.getByText('Report end date')).toBeInTheDocument();
    expect(screen.getByText('Select campaigns to include')).toBeInTheDocument();
    expect(screen.getByText('Select metric type')).toBeInTheDocument();
    expect(screen.getByText('Minimum threshold value')).toBeInTheDocument();
    expect(screen.getByText('Include archived campaigns')).toBeInTheDocument();
  });

  it('validates date range', async () => {
    const user = userEvent.setup();

    render(
      <DynamicParameterForm
        parameterDefinitions={mockParameterDefinitions}
        uiSchema={mockUiSchema}
        onSubmit={mockOnSubmit}
        onChange={mockOnChange}
      />
    );

    const startDate = screen.getByLabelText('Start Date');
    await user.type(startDate, '2025-09-15');

    const endDate = screen.getByLabelText('End Date');
    await user.type(endDate, '2025-09-01');

    const submitButton = screen.getByText('Submit');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('End date must be after start date')).toBeInTheDocument();
    });
  });
});