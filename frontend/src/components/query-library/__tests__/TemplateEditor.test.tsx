import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TemplateEditor from '../TemplateEditor';
import type { QueryTemplate } from '../../../types/queryTemplate';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange, height }: any) => (
    <div data-testid="monaco-editor" style={{ height }}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="SQL Editor"
      />
    </div>
  )
}));

describe('TemplateEditor', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();
  
  const defaultTemplate: Partial<QueryTemplate> = {
    name: 'Test Template',
    description: 'Test description',
    category: 'Product Performance',
    sqlTemplate: 'SELECT * FROM products WHERE {{start_date}} AND {{end_date}}',
    parametersSchema: {
      start_date: {
        type: 'date',
        required: true,
        description: 'Start date for analysis'
      },
      end_date: {
        type: 'date',
        required: true,
        description: 'End date for analysis'
      }
    },
    defaultParameters: {},
    isPublic: false,
    tags: ['test', 'products']
  };

  const defaultProps = {
    template: undefined,
    onSave: mockOnSave,
    onCancel: mockOnCancel,
    isOpen: true
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Create Mode', () => {
    it('renders create template form', () => {
      render(<TemplateEditor {...defaultProps} />);
      
      expect(screen.getByText('Create New Template')).toBeInTheDocument();
      expect(screen.getByLabelText(/template name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/category/i)).toBeInTheDocument();
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    it('validates required fields', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/category is required/i)).toBeInTheDocument();
        expect(screen.getByText(/sql template is required/i)).toBeInTheDocument();
      });
    });

    it('creates new template with valid data', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      await user.type(screen.getByLabelText(/template name/i), 'New Template');
      await user.type(screen.getByLabelText(/description/i), 'Template description');
      await user.selectOptions(screen.getByLabelText(/category/i), 'Advertising');
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns' }
      });
      
      await user.type(screen.getByLabelText(/tags/i), 'campaign,performance');
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);
      
      expect(mockOnSave).toHaveBeenCalledWith({
        name: 'New Template',
        description: 'Template description',
        category: 'Advertising',
        sql_template: 'SELECT * FROM campaigns',
        parameters_schema: {},
        default_parameters: {},
        is_public: false,
        tags: ['campaign', 'performance']
      });
    });
  });

  describe('Edit Mode', () => {
    it('renders edit template form with existing data', () => {
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);
      
      expect(screen.getByText('Edit Template')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test description')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Product Performance')).toBeInTheDocument();
    });

    it('updates existing template', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);
      
      const nameInput = screen.getByLabelText(/template name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Template');
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);
      
      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Updated Template'
      }));
    });
  });

  describe('Parameter Detection', () => {
    it('detects parameters from SQL template', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { 
          value: 'SELECT * FROM products WHERE date >= {{start_date}} AND date <= {{end_date}} AND asin IN ({{asins}})'
        }
      });
      
      await waitFor(() => {
        expect(screen.getByText(/detected parameters/i)).toBeInTheDocument();
        expect(screen.getByText('start_date')).toBeInTheDocument();
        expect(screen.getByText('end_date')).toBeInTheDocument();
        expect(screen.getByText('asins')).toBeInTheDocument();
      });
    });

    it('allows configuring detected parameters', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin = {{asin}}' }
      });
      
      await waitFor(() => {
        expect(screen.getByText('asin')).toBeInTheDocument();
      });
      
      // Configure parameter type
      const typeSelect = screen.getByLabelText(/type for asin/i);
      await user.selectOptions(typeSelect, 'string');
      
      // Set as required
      const requiredCheckbox = screen.getByLabelText(/required for asin/i);
      await user.click(requiredCheckbox);
      
      // Add description
      const descriptionInput = screen.getByLabelText(/description for asin/i);
      await user.type(descriptionInput, 'Product ASIN');
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);
      
      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        parameters_schema: {
          asin: {
            type: 'string',
            required: true,
            description: 'Product ASIN'
          }
        }
      }));
    });

    it('handles complex parameter types', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { 
          value: `SELECT * FROM campaigns 
                  WHERE campaign_id IN ({{campaign_ids}})
                  AND date BETWEEN {{start_date}} AND {{end_date}}
                  AND spend > {{min_spend}}`
        }
      });
      
      await waitFor(() => {
        expect(screen.getByText('campaign_ids')).toBeInTheDocument();
        expect(screen.getByText('start_date')).toBeInTheDocument();
        expect(screen.getByText('end_date')).toBeInTheDocument();
        expect(screen.getByText('min_spend')).toBeInTheDocument();
      });
      
      // Configure array parameter
      const campaignTypeSelect = screen.getByLabelText(/type for campaign_ids/i);
      await user.selectOptions(campaignTypeSelect, 'array');
      
      // Configure date parameters
      const startDateTypeSelect = screen.getByLabelText(/type for start_date/i);
      await user.selectOptions(startDateTypeSelect, 'date');
      
      const endDateTypeSelect = screen.getByLabelText(/type for end_date/i);
      await user.selectOptions(endDateTypeSelect, 'date');
      
      // Configure number parameter
      const minSpendTypeSelect = screen.getByLabelText(/type for min_spend/i);
      await user.selectOptions(minSpendTypeSelect, 'number');
    });

    it('removes parameters when deleted from SQL', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      
      // Add parameters
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin = {{asin}} AND date = {{date}}' }
      });
      
      await waitFor(() => {
        expect(screen.getByText('asin')).toBeInTheDocument();
        expect(screen.getByText('date')).toBeInTheDocument();
      });
      
      // Remove one parameter
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin = {{asin}}' }
      });
      
      await waitFor(() => {
        expect(screen.getByText('asin')).toBeInTheDocument();
        expect(screen.queryByText('date')).not.toBeInTheDocument();
      });
    });
  });

  describe('SQL Validation', () => {
    it('validates SQL syntax', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'INVALID SQL QUERY' }
      });
      
      await waitFor(() => {
        expect(screen.getByText(/invalid sql syntax/i)).toBeInTheDocument();
      });
    });

    it('checks for SQL injection attempts', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products; DROP TABLE users;' }
      });
      
      await waitFor(() => {
        expect(screen.getByText(/potential sql injection/i)).toBeInTheDocument();
      });
    });

    it('validates AMC-specific SQL functions', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { 
          value: `SELECT 
                    advertiser_id,
                    COUNT(DISTINCT user_id) as unique_users
                  FROM impressions
                  WHERE date >= {{start_date}}
                  GROUP BY advertiser_id`
        }
      });
      
      await waitFor(() => {
        expect(screen.queryByText(/invalid/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Preview Mode', () => {
    it('shows SQL preview with sample parameters', async () => {
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { 
          value: 'SELECT * FROM products WHERE date >= {{start_date}} AND date <= {{end_date}}'
        }
      });
      
      const previewButton = screen.getByRole('button', { name: /preview/i });
      fireEvent.click(previewButton);
      
      await waitFor(() => {
        expect(screen.getByText(/sql preview/i)).toBeInTheDocument();
        // Should show SQL with sample values
        expect(screen.getByText(/2025-01-01/)).toBeInTheDocument();
        expect(screen.getByText(/2025-01-31/)).toBeInTheDocument();
      });
    });

    it('allows testing with custom parameter values', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin = {{asin}}' }
      });
      
      const previewButton = screen.getByRole('button', { name: /preview/i });
      fireEvent.click(previewButton);
      
      await waitFor(() => {
        expect(screen.getByLabelText(/test value for asin/i)).toBeInTheDocument();
      });
      
      const testInput = screen.getByLabelText(/test value for asin/i);
      await user.type(testInput, 'B08N5WRWNW');
      
      const runPreviewButton = screen.getByRole('button', { name: /run preview/i });
      fireEvent.click(runPreviewButton);
      
      await waitFor(() => {
        expect(screen.getByText(/B08N5WRWNW/)).toBeInTheDocument();
      });
    });
  });

  describe('Template Sharing', () => {
    it('toggles public/private visibility', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const publicCheckbox = screen.getByLabelText(/make template public/i);
      expect(publicCheckbox).not.toBeChecked();
      
      await user.click(publicCheckbox);
      expect(publicCheckbox).toBeChecked();
      
      // Should show sharing warning
      expect(screen.getByText(/public templates can be used by all users/i)).toBeInTheDocument();
    });

    it('shows sharing options for public templates', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const publicCheckbox = screen.getByLabelText(/make template public/i);
      await user.click(publicCheckbox);
      
      expect(screen.getByLabelText(/allow forking/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/show author/i)).toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('saves on Ctrl+S', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);
      
      await user.keyboard('{Control>}s{/Control}');
      
      expect(mockOnSave).toHaveBeenCalled();
    });

    it('cancels on Escape', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      await user.keyboard('{Escape}');
      
      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('formats SQL on Shift+Alt+F', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);
      
      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'select * from products where date>={{start_date}}' }
      });
      
      await user.keyboard('{Shift>}{Alt>}f{/Alt}{/Shift}');
      
      await waitFor(() => {
        // Should format SQL
        expect(sqlEditor).toHaveValue(expect.stringContaining('SELECT'));
        expect(sqlEditor).toHaveValue(expect.stringContaining('FROM'));
        expect(sqlEditor).toHaveValue(expect.stringContaining('WHERE'));
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error when save fails', async () => {
      mockOnSave.mockRejectedValueOnce(new Error('Failed to save template'));
      
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to save template/i)).toBeInTheDocument();
      });
    });

    it('handles network errors gracefully', async () => {
      mockOnSave.mockRejectedValueOnce(new Error('Network error'));
      
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);
      
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });
});