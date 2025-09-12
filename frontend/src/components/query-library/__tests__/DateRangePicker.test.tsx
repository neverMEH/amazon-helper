import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { addDays, subDays, format } from 'date-fns';
import DateRangePicker from '../DateRangePicker';

describe('DateRangePicker', () => {
  const mockOnChange = vi.fn();
  const today = new Date();
  const defaultProps = {
    value: {
      startDate: subDays(today, 7).toISOString(),
      endDate: today.toISOString()
    },
    onChange: mockOnChange,
    required: false,
    disabled: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Functionality', () => {
    it('renders with selected date range', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const startDateInput = screen.getByLabelText(/start date/i);
      const endDateInput = screen.getByLabelText(/end date/i);
      
      expect(startDateInput).toHaveValue(format(subDays(today, 7), 'yyyy-MM-dd'));
      expect(endDateInput).toHaveValue(format(today, 'yyyy-MM-dd'));
    });

    it('updates date range on manual input', async () => {
      const user = userEvent.setup();
      render(<DateRangePicker {...defaultProps} />);
      
      const startDateInput = screen.getByLabelText(/start date/i);
      await user.clear(startDateInput);
      await user.type(startDateInput, '2025-01-01');
      
      const endDateInput = screen.getByLabelText(/end date/i);
      await user.clear(endDateInput);
      await user.type(endDateInput, '2025-01-31');
      
      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: '2025-01-01T00:00:00.000Z',
        endDate: '2025-01-31T00:00:00.000Z'
      });
    });

    it('validates end date is after start date', async () => {
      const user = userEvent.setup();
      render(<DateRangePicker {...defaultProps} />);
      
      const startDateInput = screen.getByLabelText(/start date/i);
      const endDateInput = screen.getByLabelText(/end date/i);
      
      await user.clear(startDateInput);
      await user.type(startDateInput, '2025-01-31');
      
      await user.clear(endDateInput);
      await user.type(endDateInput, '2025-01-01');
      
      await waitFor(() => {
        expect(screen.getByText(/end date must be after start date/i)).toBeInTheDocument();
      });
    });
  });

  describe('Preset Date Ranges', () => {
    it('displays preset options', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const presetButton = screen.getByRole('button', { name: /presets/i });
      fireEvent.click(presetButton);
      
      expect(screen.getByText('Last 7 days')).toBeInTheDocument();
      expect(screen.getByText('Last 14 days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 days')).toBeInTheDocument();
      expect(screen.getByText('Last 90 days')).toBeInTheDocument();
      expect(screen.getByText('This month')).toBeInTheDocument();
      expect(screen.getByText('Last month')).toBeInTheDocument();
      expect(screen.getByText('This quarter')).toBeInTheDocument();
      expect(screen.getByText('Last quarter')).toBeInTheDocument();
      expect(screen.getByText('This year')).toBeInTheDocument();
      expect(screen.getByText('Last year')).toBeInTheDocument();
    });

    it('applies preset: Last 7 days', async () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const presetButton = screen.getByRole('button', { name: /presets/i });
      fireEvent.click(presetButton);
      
      const last7Days = screen.getByText('Last 7 days');
      fireEvent.click(last7Days);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith({
          startDate: expect.any(String),
          endDate: expect.any(String)
        });
        
        const call = mockOnChange.mock.calls[0][0];
        const start = new Date(call.startDate);
        const end = new Date(call.endDate);
        const daysDiff = Math.round((end - start) / (1000 * 60 * 60 * 24));
        expect(daysDiff).toBe(6); // 7 days inclusive
      });
    });

    it('applies preset: This month', async () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const presetButton = screen.getByRole('button', { name: /presets/i });
      fireEvent.click(presetButton);
      
      const thisMonth = screen.getByText('This month');
      fireEvent.click(thisMonth);
      
      await waitFor(() => {
        const call = mockOnChange.mock.calls[0][0];
        const start = new Date(call.startDate);
        const end = new Date(call.endDate);
        
        expect(start.getDate()).toBe(1);
        expect(start.getMonth()).toBe(today.getMonth());
        expect(start.getFullYear()).toBe(today.getFullYear());
      });
    });

    it('applies preset: Last quarter', async () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const presetButton = screen.getByRole('button', { name: /presets/i });
      fireEvent.click(presetButton);
      
      const lastQuarter = screen.getByText('Last quarter');
      fireEvent.click(lastQuarter);
      
      await waitFor(() => {
        const call = mockOnChange.mock.calls[0][0];
        const start = new Date(call.startDate);
        const end = new Date(call.endDate);
        
        // Verify it's a 3-month period
        const monthsDiff = (end.getFullYear() - start.getFullYear()) * 12 + 
                          (end.getMonth() - start.getMonth());
        expect(monthsDiff).toBeGreaterThanOrEqual(2);
        expect(monthsDiff).toBeLessThanOrEqual(3);
      });
    });
  });

  describe('Dynamic Date Expressions', () => {
    it('supports relative date expressions', async () => {
      render(<DateRangePicker {...defaultProps} supportDynamic={true} />);
      
      const dynamicToggle = screen.getByRole('button', { name: /use dynamic dates/i });
      fireEvent.click(dynamicToggle);
      
      const startInput = screen.getByLabelText(/start expression/i);
      const endInput = screen.getByLabelText(/end expression/i);
      
      await userEvent.type(startInput, 'today - 7 days');
      await userEvent.type(endInput, 'today');
      
      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: 'today - 7 days',
        endDate: 'today',
        isDynamic: true
      });
    });

    it('validates dynamic expressions', async () => {
      render(<DateRangePicker {...defaultProps} supportDynamic={true} />);
      
      const dynamicToggle = screen.getByRole('button', { name: /use dynamic dates/i });
      fireEvent.click(dynamicToggle);
      
      const startInput = screen.getByLabelText(/start expression/i);
      await userEvent.type(startInput, 'invalid expression');
      
      await waitFor(() => {
        expect(screen.getByText(/invalid date expression/i)).toBeInTheDocument();
      });
    });

    it('shows expression examples', () => {
      render(<DateRangePicker {...defaultProps} supportDynamic={true} />);
      
      const dynamicToggle = screen.getByRole('button', { name: /use dynamic dates/i });
      fireEvent.click(dynamicToggle);
      
      const helpButton = screen.getByRole('button', { name: /help/i });
      fireEvent.click(helpButton);
      
      expect(screen.getByText(/today/i)).toBeInTheDocument();
      expect(screen.getByText(/yesterday/i)).toBeInTheDocument();
      expect(screen.getByText(/start of month/i)).toBeInTheDocument();
      expect(screen.getByText(/end of month/i)).toBeInTheDocument();
      expect(screen.getByText(/start of quarter/i)).toBeInTheDocument();
      expect(screen.getByText(/end of quarter/i)).toBeInTheDocument();
    });

    it('supports complex expressions', async () => {
      render(<DateRangePicker {...defaultProps} supportDynamic={true} />);
      
      const dynamicToggle = screen.getByRole('button', { name: /use dynamic dates/i });
      fireEvent.click(dynamicToggle);
      
      const startInput = screen.getByLabelText(/start expression/i);
      const endInput = screen.getByLabelText(/end expression/i);
      
      await userEvent.type(startInput, 'start of month - 1 month');
      await userEvent.type(endInput, 'end of month - 1 month');
      
      expect(mockOnChange).toHaveBeenCalledWith({
        startDate: 'start of month - 1 month',
        endDate: 'end of month - 1 month',
        isDynamic: true
      });
    });

    it('previews resolved dates for expressions', async () => {
      render(<DateRangePicker {...defaultProps} supportDynamic={true} />);
      
      const dynamicToggle = screen.getByRole('button', { name: /use dynamic dates/i });
      fireEvent.click(dynamicToggle);
      
      const startInput = screen.getByLabelText(/start expression/i);
      await userEvent.type(startInput, 'today - 7 days');
      
      await waitFor(() => {
        const preview = screen.getByText(/resolves to:/i);
        expect(preview).toBeInTheDocument();
        // Should show the actual date
        expect(preview.parentElement).toHaveTextContent(
          format(subDays(today, 7), 'MMM dd, yyyy')
        );
      });
    });
  });

  describe('Calendar Widget', () => {
    it('opens calendar on button click', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const calendarButton = screen.getByRole('button', { name: /open calendar/i });
      fireEvent.click(calendarButton);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(format(today, 'MMMM yyyy'))).toBeInTheDocument();
    });

    it('allows date selection from calendar', async () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const calendarButton = screen.getByRole('button', { name: /open calendar/i });
      fireEvent.click(calendarButton);
      
      // Select a date (assuming 15th is visible)
      const date15 = screen.getByText('15');
      fireEvent.click(date15);
      
      // Select end date (assuming 20th is visible)
      const date20 = screen.getByText('20');
      fireEvent.click(date20);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalled();
      });
    });

    it('highlights selected range in calendar', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const calendarButton = screen.getByRole('button', { name: /open calendar/i });
      fireEvent.click(calendarButton);
      
      const selectedDates = screen.getAllByRole('button', { pressed: true });
      expect(selectedDates.length).toBeGreaterThan(0);
    });

    it('navigates between months', async () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const calendarButton = screen.getByRole('button', { name: /open calendar/i });
      fireEvent.click(calendarButton);
      
      const currentMonth = format(today, 'MMMM yyyy');
      expect(screen.getByText(currentMonth)).toBeInTheDocument();
      
      const nextButton = screen.getByRole('button', { name: /next month/i });
      fireEvent.click(nextButton);
      
      const nextMonth = format(addDays(today, 32), 'MMMM yyyy');
      expect(screen.getByText(nextMonth)).toBeInTheDocument();
      
      const prevButton = screen.getByRole('button', { name: /previous month/i });
      fireEvent.click(prevButton);
      fireEvent.click(prevButton);
      
      const prevMonth = format(subDays(today, 32), 'MMMM yyyy');
      expect(screen.getByText(prevMonth)).toBeInTheDocument();
    });
  });

  describe('AMC Lookback Period', () => {
    it('shows AMC data availability warning', () => {
      render(<DateRangePicker {...defaultProps} showAmcWarning={true} />);
      
      expect(screen.getByText(/amc data has a 14-day lookback period/i)).toBeInTheDocument();
    });

    it('disables dates beyond AMC lookback period', () => {
      render(<DateRangePicker {...defaultProps} showAmcWarning={true} />);
      
      const calendarButton = screen.getByRole('button', { name: /open calendar/i });
      fireEvent.click(calendarButton);
      
      // Future dates and very recent dates should be disabled
      const tomorrow = format(addDays(today, 1), 'd');
      const tomorrowButton = screen.getByText(tomorrow);
      expect(tomorrowButton.closest('button')).toBeDisabled();
    });

    it('adjusts preset ranges for AMC lookback', () => {
      render(<DateRangePicker {...defaultProps} showAmcWarning={true} />);
      
      const presetButton = screen.getByRole('button', { name: /presets/i });
      fireEvent.click(presetButton);
      
      const last7Days = screen.getByText('Last 7 days (adjusted for AMC)');
      fireEvent.click(last7Days);
      
      const call = mockOnChange.mock.calls[0][0];
      const end = new Date(call.endDate);
      const amcCutoff = subDays(today, 14);
      
      expect(end <= amcCutoff).toBe(true);
    });
  });

  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<DateRangePicker {...defaultProps} />);
      
      await user.tab();
      const startDateInput = screen.getByLabelText(/start date/i);
      expect(startDateInput).toHaveFocus();
      
      await user.tab();
      const endDateInput = screen.getByLabelText(/end date/i);
      expect(endDateInput).toHaveFocus();
    });

    it('announces selected range to screen readers', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent(/selected range/i);
    });

    it('provides proper ARIA labels', () => {
      render(<DateRangePicker {...defaultProps} />);
      
      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /open calendar/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /presets/i })).toBeInTheDocument();
    });
  });

  describe('Error States', () => {
    it('shows required field error', () => {
      render(<DateRangePicker value={null} onChange={mockOnChange} required={true} />);
      
      expect(screen.getByText(/date range is required/i)).toBeInTheDocument();
    });

    it('shows custom error message', () => {
      render(
        <DateRangePicker
          {...defaultProps}
          error="Please select a date range within the last 30 days"
        />
      );
      
      expect(screen.getByText('Please select a date range within the last 30 days')).toBeInTheDocument();
    });

    it('disables inputs when disabled prop is true', () => {
      render(<DateRangePicker {...defaultProps} disabled={true} />);
      
      const startDateInput = screen.getByLabelText(/start date/i);
      const endDateInput = screen.getByLabelText(/end date/i);
      
      expect(startDateInput).toBeDisabled();
      expect(endDateInput).toBeDisabled();
    });
  });

  describe('Integration with Form', () => {
    it('integrates with form validation', async () => {
      const mockSubmit = vi.fn();
      const FormWrapper = () => {
        const [value, setValue] = React.useState(null);
        const [error, setError] = React.useState('');
        
        const handleSubmit = (e: React.FormEvent) => {
          e.preventDefault();
          if (!value) {
            setError('Date range is required');
            return;
          }
          mockSubmit(value);
        };
        
        return (
          <form onSubmit={handleSubmit}>
            <DateRangePicker
              value={value}
              onChange={setValue}
              required={true}
              error={error}
            />
            <button type="submit">Submit</button>
          </form>
        );
      };
      
      render(<FormWrapper />);
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/date range is required/i)).toBeInTheDocument();
      });
      
      // Select dates
      const startDateInput = screen.getByLabelText(/start date/i);
      const endDateInput = screen.getByLabelText(/end date/i);
      
      await userEvent.type(startDateInput, '2025-01-01');
      await userEvent.type(endDateInput, '2025-01-31');
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSubmit).toHaveBeenCalled();
      });
    });
  });
});