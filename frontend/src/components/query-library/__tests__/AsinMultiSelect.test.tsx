import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AsinMultiSelect from '../AsinMultiSelect';

describe('AsinMultiSelect', () => {
  const mockOnChange = vi.fn();
  const defaultProps = {
    value: [],
    onChange: mockOnChange,
    placeholder: 'Enter ASINs',
    required: false,
    disabled: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Functionality', () => {
    it('renders with placeholder text', () => {
      render(<AsinMultiSelect {...defaultProps} />);
      expect(screen.getByPlaceholderText('Enter ASINs')).toBeInTheDocument();
    });

    it('allows manual entry of single ASIN', async () => {
      const user = userEvent.setup();
      render(<AsinMultiSelect {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'B08N5WRWNW{enter}');
      
      expect(mockOnChange).toHaveBeenCalledWith(['B08N5WRWNW']);
    });

    it('allows manual entry of multiple ASINs', async () => {
      const user = userEvent.setup();
      render(<AsinMultiSelect {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'B08N5WRWNW{enter}');
      await user.type(input, 'B07XJ8C8F5{enter}');
      await user.type(input, 'B09B3S4KGC{enter}');
      
      expect(mockOnChange).toHaveBeenLastCalledWith([
        'B08N5WRWNW',
        'B07XJ8C8F5',
        'B09B3S4KGC'
      ]);
    });

    it('displays selected ASINs as tags', () => {
      const selectedAsins = ['B08N5WRWNW', 'B07XJ8C8F5'];
      render(<AsinMultiSelect {...defaultProps} value={selectedAsins} />);
      
      expect(screen.getByText('B08N5WRWNW')).toBeInTheDocument();
      expect(screen.getByText('B07XJ8C8F5')).toBeInTheDocument();
    });

    it('removes ASIN when tag delete button clicked', async () => {
      const selectedAsins = ['B08N5WRWNW', 'B07XJ8C8F5'];
      render(<AsinMultiSelect {...defaultProps} value={selectedAsins} />);
      
      const deleteButtons = screen.getAllByLabelText(/remove/i);
      fireEvent.click(deleteButtons[0]);
      
      expect(mockOnChange).toHaveBeenCalledWith(['B07XJ8C8F5']);
    });

    it('validates ASIN format', async () => {
      const user = userEvent.setup();
      render(<AsinMultiSelect {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'invalid-asin{enter}');
      
      expect(screen.getByText(/invalid asin format/i)).toBeInTheDocument();
      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Bulk Paste Support', () => {
    it('opens bulk paste modal on button click', () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/paste asins/i)).toBeInTheDocument();
    });

    it('handles comma-separated ASINs', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW, B07XJ8C8F5, B09B3S4KGC' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5',
          'B09B3S4KGC'
        ]);
      });
    });

    it('handles newline-separated ASINs', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW\nB07XJ8C8F5\nB09B3S4KGC' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5',
          'B09B3S4KGC'
        ]);
      });
    });

    it('handles tab-separated ASINs', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW\tB07XJ8C8F5\tB09B3S4KGC' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5',
          'B09B3S4KGC'
        ]);
      });
    });

    it('handles mixed separators', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW, B07XJ8C8F5\nB09B3S4KGC\tB07ZPKBL9X' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5',
          'B09B3S4KGC',
          'B07ZPKBL9X'
        ]);
      });
    });

    it('handles 60+ ASINs efficiently', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      // Generate 100 test ASINs
      const asins = Array.from({ length: 100 }, (_, i) => 
        `B${String(i).padStart(9, '0')}`
      );
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: asins.join('\n') }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(asins);
      });
      
      // Verify count display
      expect(screen.getByText(/100 asins selected/i)).toBeInTheDocument();
    });

    it('removes duplicates from bulk paste', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW, B08N5WRWNW, B07XJ8C8F5, B07XJ8C8F5' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5'
        ]);
      });
    });

    it('validates all ASINs in bulk paste', async () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      fireEvent.click(bulkButton);
      
      const textarea = screen.getByRole('textbox', { name: /bulk input/i });
      fireEvent.change(textarea, {
        target: { value: 'B08N5WRWNW, invalid-asin, B07XJ8C8F5' }
      });
      
      const importButton = screen.getByRole('button', { name: /import/i });
      fireEvent.click(importButton);
      
      await waitFor(() => {
        expect(screen.getByText(/1 invalid asin/i)).toBeInTheDocument();
        expect(mockOnChange).toHaveBeenCalledWith([
          'B08N5WRWNW',
          'B07XJ8C8F5'
        ]);
      });
    });
  });

  describe('Clear and Select All', () => {
    it('clears all selected ASINs', () => {
      const selectedAsins = ['B08N5WRWNW', 'B07XJ8C8F5', 'B09B3S4KGC'];
      render(<AsinMultiSelect {...defaultProps} value={selectedAsins} />);
      
      const clearButton = screen.getByRole('button', { name: /clear all/i });
      fireEvent.click(clearButton);
      
      expect(mockOnChange).toHaveBeenCalledWith([]);
    });

    it('disables clear button when no ASINs selected', () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      const clearButton = screen.getByRole('button', { name: /clear all/i });
      expect(clearButton).toBeDisabled();
    });
  });

  describe('Search and Filter', () => {
    it('filters displayed ASINs based on search', async () => {
      const selectedAsins = ['B08N5WRWNW', 'B07XJ8C8F5', 'B09B3S4KGC'];
      render(<AsinMultiSelect {...defaultProps} value={selectedAsins} />);
      
      const searchInput = screen.getByPlaceholderText(/search asins/i);
      fireEvent.change(searchInput, { target: { value: 'B08' } });
      
      await waitFor(() => {
        expect(screen.getByText('B08N5WRWNW')).toBeInTheDocument();
        expect(screen.queryByText('B07XJ8C8F5')).not.toBeInTheDocument();
        expect(screen.queryByText('B09B3S4KGC')).not.toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('renders large number of ASINs without lag', () => {
      const largeAsinList = Array.from({ length: 1000 }, (_, i) => 
        `B${String(i).padStart(9, '0')}`
      );
      
      const startTime = performance.now();
      render(<AsinMultiSelect {...defaultProps} value={largeAsinList} />);
      const endTime = performance.now();
      
      expect(endTime - startTime).toBeLessThan(1000); // Should render in under 1 second
      expect(screen.getByText(/1000 asins selected/i)).toBeInTheDocument();
    });

    it('uses virtualization for large lists', () => {
      const largeAsinList = Array.from({ length: 1000 }, (_, i) => 
        `B${String(i).padStart(9, '0')}`
      );
      
      render(<AsinMultiSelect {...defaultProps} value={largeAsinList} />);
      
      // Check that not all items are rendered at once (virtualization)
      const renderedTags = screen.getAllByTestId('asin-tag');
      expect(renderedTags.length).toBeLessThan(100); // Should use virtualization
    });
  });

  describe('Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<AsinMultiSelect {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.tab();
      expect(input).toHaveFocus();
      
      await user.type(input, 'B08N5WRWNW');
      await user.keyboard('{Enter}');
      
      expect(mockOnChange).toHaveBeenCalledWith(['B08N5WRWNW']);
    });

    it('provides proper ARIA labels', () => {
      render(<AsinMultiSelect {...defaultProps} />);
      
      expect(screen.getByLabelText(/asin input/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /bulk paste/i })).toBeInTheDocument();
    });

    it('announces count changes to screen readers', () => {
      const { rerender } = render(<AsinMultiSelect {...defaultProps} />);
      
      rerender(<AsinMultiSelect {...defaultProps} value={['B08N5WRWNW']} />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('1 ASIN selected');
    });
  });

  describe('Error Handling', () => {
    it('shows error for invalid required field', () => {
      render(<AsinMultiSelect {...defaultProps} required={true} />);
      
      expect(screen.getByText(/this field is required/i)).toBeInTheDocument();
    });

    it('shows custom error message', () => {
      render(
        <AsinMultiSelect
          {...defaultProps}
          error="Please select at least 5 ASINs"
        />
      );
      
      expect(screen.getByText('Please select at least 5 ASINs')).toBeInTheDocument();
    });

    it('disables input when disabled prop is true', () => {
      render(<AsinMultiSelect {...defaultProps} disabled={true} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
      
      const bulkButton = screen.getByRole('button', { name: /bulk paste/i });
      expect(bulkButton).toBeDisabled();
    });
  });
});