import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EnhancedParameterSelector } from '../EnhancedParameterSelector';
import type { ParameterDefinition } from '../../../utils/sqlParameterAnalyzer';

// Mock the child components
vi.mock('../ASINSelector', () => ({
  ASINSelector: ({ value, onChange, placeholder }: any) => (
    <div data-testid="asin-selector">
      <input
        data-testid="asin-input"
        placeholder={placeholder}
        value={value?.join(',') || ''}
        onChange={(e) => onChange(e.target.value.split(',').filter(Boolean))}
      />
    </div>
  ),
}));

vi.mock('../CampaignSelector', () => ({
  CampaignSelector: ({ value, onChange, placeholder }: any) => (
    <div data-testid="campaign-selector">
      <input
        data-testid="campaign-input"
        placeholder={placeholder}
        value={value?.join(',') || ''}
        onChange={(e) => onChange(e.target.value.split(',').filter(Boolean))}
      />
    </div>
  ),
}));

vi.mock('../DateRangeSelector', () => ({
  DateRangeSelector: ({ value, onChange, parameterName }: any) => (
    <div data-testid="date-range-selector">
      <input
        data-testid="date-range-input"
        placeholder={`Date range for ${parameterName}`}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  ),
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

describe('EnhancedParameterSelector', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Parameter type rendering', () => {
    it('renders ASIN selector for asin_list type', () => {
      const parameter: ParameterDefinition = {
        name: 'asin_list',
        type: 'asin_list',
        required: true,
        sqlContext: 'IN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={[]}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByTestId('asin-selector')).toBeInTheDocument();
      expect(screen.getByTestId('asin-input')).toHaveAttribute('placeholder', 'Select ASINs (required)');
    });

    it('renders Campaign selector for campaign_list type', () => {
      const parameter: ParameterDefinition = {
        name: 'campaigns',
        type: 'campaign_list',
        required: true,
        sqlContext: 'IN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          instanceId="test-instance"
          value={[]}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
    });

    it('renders date input for date type', () => {
      const parameter: ParameterDefinition = {
        name: 'start_date',
        type: 'date',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const dateInput = screen.getByRole('textbox') as HTMLInputElement;
      expect(dateInput).toBeInTheDocument();
      expect(dateInput.type).toBe('date');
    });

    it('renders date range selector for date_range type', () => {
      const parameter: ParameterDefinition = {
        name: 'date_range',
        type: 'date_range',
        required: true,
        sqlContext: 'BETWEEN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByTestId('date-range-selector')).toBeInTheDocument();
    });

    it('renders number input for number type', () => {
      const parameter: ParameterDefinition = {
        name: 'min_impressions',
        type: 'number',
        required: true,
        sqlContext: 'COMPARISON',
        validation: { min: 0, max: 1000000 },
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={100}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const numberInput = screen.getByRole('spinbutton') as HTMLInputElement;
      expect(numberInput).toBeInTheDocument();
      expect(numberInput.type).toBe('number');
      expect(numberInput).toHaveAttribute('min', '0');
      expect(numberInput).toHaveAttribute('max', '1000000');
    });

    it('renders pattern input for pattern type with LIKE context', () => {
      const parameter: ParameterDefinition = {
        name: 'search_pattern',
        type: 'pattern',
        required: true,
        sqlContext: 'LIKE',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const patternInput = screen.getByRole('textbox') as HTMLInputElement;
      expect(patternInput).toHaveAttribute('placeholder', 'e.g., %search_term%');

      // Check for info button
      const infoButton = screen.getByRole('button');
      expect(infoButton).toBeInTheDocument();
    });

    it('renders boolean selector for boolean type', () => {
      const parameter: ParameterDefinition = {
        name: 'is_active',
        type: 'boolean',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={true}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const trueOption = screen.getByLabelText('True') as HTMLInputElement;
      const falseOption = screen.getByLabelText('False') as HTMLInputElement;

      expect(trueOption).toBeInTheDocument();
      expect(falseOption).toBeInTheDocument();
      expect(trueOption).toBeChecked();
      expect(falseOption).not.toBeChecked();
    });

    it('renders textarea for list values with IN context', () => {
      const parameter: ParameterDefinition = {
        name: 'values',
        type: 'text',
        required: true,
        sqlContext: 'IN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={['a', 'b', 'c']}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.tagName).toBe('TEXTAREA');
      expect(textarea.value).toBe('a, b, c');
    });

    it('renders text input for default case', () => {
      const parameter: ParameterDefinition = {
        name: 'generic_param',
        type: 'text',
        required: false,
        sqlContext: 'EQUALS',
        description: 'Enter a value',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const textInput = screen.getByRole('textbox') as HTMLInputElement;
      expect(textInput).toHaveAttribute('placeholder', 'Enter a value');
      expect(textInput).not.toHaveAttribute('required');
    });
  });

  describe('User interactions', () => {
    it('calls onChange when typing in text input', async () => {
      const user = userEvent.setup();
      const parameter: ParameterDefinition = {
        name: 'text_param',
        type: 'text',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'test value');

      // Debounced, so wait for the onChange
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith('test value');
      }, { timeout: 1000 });
    });

    it('calls onChange immediately for number input', async () => {
      const user = userEvent.setup();
      const parameter: ParameterDefinition = {
        name: 'number_param',
        type: 'number',
        required: true,
        sqlContext: 'COMPARISON',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={0}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByRole('spinbutton');
      await user.clear(input);
      await user.type(input, '42');

      expect(mockOnChange).toHaveBeenCalledWith(42);
    });

    it('toggles boolean value when clicking radio buttons', async () => {
      const user = userEvent.setup();
      const parameter: ParameterDefinition = {
        name: 'is_enabled',
        type: 'boolean',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={false}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const trueOption = screen.getByLabelText('True');
      await user.click(trueOption);

      expect(mockOnChange).toHaveBeenCalledWith(true);
    });

    it('shows/hides pattern hints when clicking info button', async () => {
      const user = userEvent.setup();
      const parameter: ParameterDefinition = {
        name: 'pattern',
        type: 'pattern',
        required: true,
        sqlContext: 'LIKE',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      // Hints should not be visible initially
      expect(screen.queryByText(/Use % for any characters/)).not.toBeInTheDocument();

      // Click info button
      const infoButton = screen.getByRole('button');
      await user.click(infoButton);

      // Hints should now be visible
      expect(screen.getByText(/Use % for any characters/)).toBeInTheDocument();
    });

    it('handles comma-separated values for IN context', async () => {
      const user = userEvent.setup();
      const parameter: ParameterDefinition = {
        name: 'ids',
        type: 'text',
        required: true,
        sqlContext: 'IN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={[]}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'id1, id2, id3');

      expect(mockOnChange).toHaveBeenLastCalledWith(['id1', 'id2', 'id3']);
    });
  });

  describe('Visual indicators and metadata', () => {
    it('displays parameter name formatted correctly', () => {
      const parameter: ParameterDefinition = {
        name: 'start_date_time',
        type: 'date',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Start Date Time')).toBeInTheDocument();
    });

    it('shows required indicator for required parameters', () => {
      const parameter: ParameterDefinition = {
        name: 'required_field',
        type: 'text',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('*')).toBeInTheDocument();
    });

    it('displays SQL context badge', () => {
      const parameter: ParameterDefinition = {
        name: 'param',
        type: 'text',
        required: true,
        sqlContext: 'LIKE',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('LIKE')).toBeInTheDocument();
    });

    it('shows description when provided', () => {
      const parameter: ParameterDefinition = {
        name: 'param',
        type: 'text',
        required: false,
        sqlContext: 'EQUALS',
        description: 'This is a helpful description',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('This is a helpful description')).toBeInTheDocument();
    });

    it('displays format pattern hint when available', () => {
      const parameter: ParameterDefinition = {
        name: 'param',
        type: 'text',
        required: true,
        sqlContext: 'IN',
        formatPattern: 'Will be formatted as (\'value1\', \'value2\')',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Will be formatted as/)).toBeInTheDocument();
    });

    it('shows appropriate icon for parameter type', () => {
      const dateParam: ParameterDefinition = {
        name: 'date',
        type: 'date',
        required: true,
        sqlContext: 'EQUALS',
      };

      const { container } = render(
        <EnhancedParameterSelector
          parameter={dateParam}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      // Look for the calendar icon (lucide-react icons have specific classes)
      const calendarIcon = container.querySelector('.lucide-calendar');
      expect(calendarIcon).toBeInTheDocument();
    });
  });

  describe('Validation and constraints', () => {
    it('enforces min/max validation for numbers', () => {
      const parameter: ParameterDefinition = {
        name: 'amount',
        type: 'number',
        required: true,
        sqlContext: 'COMPARISON',
        validation: { min: 10, max: 100 },
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={50}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Min: 10')).toBeInTheDocument();
      expect(screen.getByText('Max: 100')).toBeInTheDocument();
    });

    it('marks input as required when parameter is required', () => {
      const parameter: ParameterDefinition = {
        name: 'required_param',
        type: 'text',
        required: true,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('required');
    });

    it('does not mark input as required for optional parameters', () => {
      const parameter: ParameterDefinition = {
        name: 'optional_param',
        type: 'text',
        required: false,
        sqlContext: 'EQUALS',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByRole('textbox');
      expect(input).not.toHaveAttribute('required');
    });
  });

  describe('Edge cases', () => {
    it('handles empty arrays for list types', () => {
      const parameter: ParameterDefinition = {
        name: 'empty_list',
        type: 'text',
        required: false,
        sqlContext: 'IN',
      };

      render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={[]}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.value).toBe('');
    });

    it('handles null and undefined values gracefully', () => {
      const parameter: ParameterDefinition = {
        name: 'nullable_param',
        type: 'text',
        required: false,
        sqlContext: 'EQUALS',
      };

      const { rerender } = render(
        <EnhancedParameterSelector
          parameter={parameter}
          value={null}
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      let input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('');

      rerender(
        <EnhancedParameterSelector
          parameter={parameter}
          value={undefined}
          onChange={mockOnChange}
        />
      );

      input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('');
    });

    it('handles special date inputs (start_date, end_date)', () => {
      const startDateParam: ParameterDefinition = {
        name: 'start_date',
        type: 'date',
        required: true,
        sqlContext: 'BETWEEN',
      };

      const { rerender } = render(
        <EnhancedParameterSelector
          parameter={startDateParam}
          value="2024-01-01"
          onChange={mockOnChange}
        />,
        { wrapper: createWrapper() }
      );

      let input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('date');
      expect(input.value).toBe('2024-01-01');

      const endDateParam: ParameterDefinition = {
        name: 'end_date',
        type: 'date',
        required: true,
        sqlContext: 'BETWEEN',
      };

      rerender(
        <EnhancedParameterSelector
          parameter={endDateParam}
          value="2024-01-31"
          onChange={mockOnChange}
        />
      );

      input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.type).toBe('date');
      expect(input.value).toBe('2024-01-31');
    });
  });
});