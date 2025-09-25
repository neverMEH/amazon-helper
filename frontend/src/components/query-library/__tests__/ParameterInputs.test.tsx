import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ParameterInputs from '../ParameterInputs';
import type { ParameterDefinition } from '../../../types/queryTemplate';

// Mock dependencies
vi.mock('../CampaignSelector', () => ({
  CampaignSelector: ({ value, onChange, multiple, placeholder }: any) => (
    <div data-testid="campaign-selector">
      <input
        type="text"
        value={value.join(',')}
        onChange={(e) => onChange(e.target.value.split(','))}
        placeholder={placeholder}
        data-multiple={multiple}
      />
    </div>
  )
}));

vi.mock('../ASINSelector', () => ({
  ASINSelector: ({ value, onChange, placeholder }: any) => (
    <div data-testid="asin-selector">
      <input
        type="text"
        value={value.join(',')}
        onChange={(e) => onChange(e.target.value.split(','))}
        placeholder={placeholder}
      />
    </div>
  )
}));

describe('ParameterInputs', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Text Parameter Input', () => {
    it('should render text input with proper attributes', () => {
      const parameter: ParameterDefinition = {
        name: 'testParam',
        type: 'text',
        required: true,
        description: 'Test parameter',
        displayName: 'Test Parameter'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value="test value"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('test value');
      expect(input).toHaveAttribute('aria-label', 'Test Parameter');
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    it('should show validation error for required empty field', () => {
      const parameter: ParameterDefinition = {
        name: 'testParam',
        type: 'text',
        required: true,
        description: 'Test parameter'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      fireEvent.blur(input); // Trigger validation by blurring the field

      expect(screen.getByText('This field is required')).toBeInTheDocument();
    });

    it('should call onChange when text is entered', () => {
      const parameter: ParameterDefinition = {
        name: 'textParam',
        type: 'text',
        required: false
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'new value' } });

      expect(mockOnChange).toHaveBeenCalledWith('new value');
    });
  });

  describe('Number Parameter Input', () => {
    it('should render number input with validation', () => {
      const parameter: ParameterDefinition = {
        name: 'numberParam',
        type: 'number',
        required: true,
        validation: {
          min: 0,
          max: 100
        }
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={50}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '0');
      expect(input).toHaveAttribute('max', '100');
      expect(input).toHaveValue(50);
    });

    it('should show error for value outside range', () => {
      const parameter: ParameterDefinition = {
        name: 'numberParam',
        type: 'number',
        required: true,
        validation: {
          min: 0,
          max: 100
        }
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={150}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('spinbutton');
      fireEvent.blur(input); // Trigger validation

      expect(screen.getByText('Value must be at most 100')).toBeInTheDocument();
    });
  });

  describe('Date Parameter Input', () => {
    it('should render date input', () => {
      const parameter: ParameterDefinition = {
        name: 'dateParam',
        type: 'date',
        required: true
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value="2024-01-15"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByLabelText(/date/i);
      expect(input).toHaveAttribute('type', 'date');
      expect(input).toHaveValue('2024-01-15');
    });

    it('should handle date change', () => {
      const parameter: ParameterDefinition = {
        name: 'dateParam',
        type: 'date',
        required: false
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      const input = screen.getByLabelText(/date/i);
      fireEvent.change(input, { target: { value: '2024-02-20' } });

      expect(mockOnChange).toHaveBeenCalledWith('2024-02-20');
    });
  });

  describe('Date Range Parameter Input', () => {
    it('should render start and end date inputs', () => {
      const parameter: ParameterDefinition = {
        name: 'dateRangeParam',
        type: 'date_range',
        required: true
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={{ start: '2024-01-01', end: '2024-01-31' }}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByLabelText(/start date/i)).toHaveValue('2024-01-01');
      expect(screen.getByLabelText(/end date/i)).toHaveValue('2024-01-31');
    });

    it('should validate end date is after start date', () => {
      const parameter: ParameterDefinition = {
        name: 'dateRangeParam',
        type: 'date_range',
        required: true
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={{ start: '2024-01-31', end: '2024-01-01' }}
          onChange={mockOnChange}
        />
      );

      const endDateInput = screen.getByLabelText(/end date/i);
      fireEvent.blur(endDateInput); // Trigger validation

      expect(screen.getByText('End date must be after start date')).toBeInTheDocument();
    });
  });

  describe('Campaign List Parameter Input', () => {
    it('should render CampaignSelector for campaign_list type', () => {
      const parameter: ParameterDefinition = {
        name: 'campaignParam',
        type: 'campaign_list',
        required: true
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={['campaign1', 'campaign2']}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('campaign1,campaign2');
    });

    it('should handle campaign selection', () => {
      const parameter: ParameterDefinition = {
        name: 'campaignParam',
        type: 'campaign_list',
        required: false
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={[]}
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'new-campaign' } });

      expect(mockOnChange).toHaveBeenCalledWith(['new-campaign']);
    });
  });

  describe('ASIN List Parameter Input', () => {
    it('should render ASINSelector for asin_list type', () => {
      const parameter: ParameterDefinition = {
        name: 'asinParam',
        type: 'asin_list',
        required: true
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={['B001234567', 'B002345678']}
          onChange={mockOnChange}
        />
      );

      expect(screen.getByTestId('asin-selector')).toBeInTheDocument();
      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('B001234567,B002345678');
    });
  });

  describe('Pattern Parameter Input', () => {
    it('should render pattern input with helper text', () => {
      const parameter: ParameterDefinition = {
        name: 'patternParam',
        type: 'pattern',
        required: true,
        description: 'Enter a search pattern'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value="%search%"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveValue('%search%');
      expect(screen.getByText(/Use % for wildcards/i)).toBeInTheDocument();
    });

    it('should validate pattern format', () => {
      const parameter: ParameterDefinition = {
        name: 'patternParam',
        type: 'pattern',
        required: true,
        validation: {
          pattern: '^%.*%$'
        }
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value="invalid"
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      fireEvent.blur(input); // Trigger validation

      expect(screen.getByText(/Pattern must start and end with %/i)).toBeInTheDocument();
    });
  });

  describe('Boolean Parameter Input', () => {
    it('should render checkbox for boolean type', () => {
      const parameter: ParameterDefinition = {
        name: 'boolParam',
        type: 'boolean',
        required: false,
        description: 'Enable feature'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={true}
          onChange={mockOnChange}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeChecked();
      expect(screen.getByText('Enable feature')).toBeInTheDocument();
    });

    it('should handle boolean toggle', () => {
      const parameter: ParameterDefinition = {
        name: 'boolParam',
        type: 'boolean',
        required: false
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value={false}
          onChange={mockOnChange}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      fireEvent.click(checkbox);

      expect(mockOnChange).toHaveBeenCalledWith(true);
    });
  });

  describe('Visual Indicators', () => {
    it('should show required indicator for required fields', () => {
      const parameter: ParameterDefinition = {
        name: 'requiredParam',
        type: 'text',
        required: true,
        displayName: 'Required Field'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('*')).toBeInTheDocument();
      expect(screen.getByText('Required Field')).toBeInTheDocument();
    });

    it('should show description as helper text', () => {
      const parameter: ParameterDefinition = {
        name: 'paramWithDesc',
        type: 'text',
        required: false,
        description: 'This is a helpful description'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      expect(screen.getByText('This is a helpful description')).toBeInTheDocument();
    });

    it('should show default value placeholder', () => {
      const parameter: ParameterDefinition = {
        name: 'paramWithDefault',
        type: 'text',
        required: false,
        defaultValue: 'Default text'
      };

      render(
        <ParameterInputs
          parameter={parameter}
          value=""
          onChange={mockOnChange}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('placeholder', 'Default: Default text');
    });
  });
});