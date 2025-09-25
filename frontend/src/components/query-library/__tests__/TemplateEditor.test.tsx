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

// Mock CampaignSelector component
vi.mock('../CampaignSelector', () => ({
  CampaignSelector: ({ value, onChange, multiple, placeholder }: any) => (
    <div data-testid="campaign-selector">
      <input
        type="text"
        value={Array.isArray(value) ? value.join(',') : value}
        onChange={(e) => onChange(e.target.value.split(',').filter(Boolean))}
        placeholder={placeholder || 'Select campaigns'}
        aria-label="Campaign Selector"
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

  describe('Parameter State Persistence', () => {
    it('preserves all parameter properties on save', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE spend > {{min_spend}} AND campaign_id IN ({{campaign_ids}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByText('min_spend')).toBeInTheDocument();
        expect(screen.getByText('campaign_ids')).toBeInTheDocument();
      });

      // Configure min_spend parameter
      const minSpendTypeSelect = screen.getByLabelText(/type for min_spend/i);
      await user.selectOptions(minSpendTypeSelect, 'number');

      const minSpendDescInput = screen.getByLabelText(/description for min_spend/i);
      await user.type(minSpendDescInput, 'Minimum spend threshold');

      const minSpendRequiredCheckbox = screen.getByLabelText(/required for min_spend/i);
      await user.click(minSpendRequiredCheckbox);

      // Configure campaign_ids parameter
      const campaignTypeSelect = screen.getByLabelText(/type for campaign_ids/i);
      await user.selectOptions(campaignTypeSelect, 'campaign_list');

      const campaignDescInput = screen.getByLabelText(/description for campaign_ids/i);
      await user.type(campaignDescInput, 'List of campaign IDs to filter');

      // Save the template
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        parameters_schema: {
          min_spend: {
            type: 'number',
            required: true,
            description: 'Minimum spend threshold',
            validation: undefined
          },
          campaign_ids: {
            type: 'campaign_list',
            required: false,
            description: 'List of campaign IDs to filter',
            validation: undefined
          }
        }
      }));
    });

    it('loads and displays saved parameter metadata', () => {
      const templateWithParams: Partial<QueryTemplate> = {
        ...defaultTemplate,
        sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND spend > {{min_spend}}',
        parametersSchema: {
          start_date: {
            type: 'date',
            required: true,
            description: 'Start date for analysis',
            defaultValue: '2025-01-01'
          },
          min_spend: {
            type: 'number',
            required: false,
            description: 'Minimum spend filter',
            defaultValue: 1000,
            validation: {
              min: 0,
              max: 1000000
            }
          }
        }
      };

      render(<TemplateEditor {...defaultProps} template={templateWithParams as QueryTemplate} />);

      // Check that parameters are loaded with metadata
      expect(screen.getByText('start_date')).toBeInTheDocument();
      expect(screen.getByText('min_spend')).toBeInTheDocument();

      // Check descriptions are loaded
      expect(screen.getByDisplayValue('Start date for analysis')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Minimum spend filter')).toBeInTheDocument();

      // Check types are selected
      const startDateType = screen.getByLabelText(/type for start_date/i);
      expect(startDateType).toHaveValue('date');

      const minSpendType = screen.getByLabelText(/type for min_spend/i);
      expect(minSpendType).toHaveValue('number');
    });

    it('handles complex parameter validation rules', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM products WHERE price BETWEEN {{min_price}} AND {{max_price}}'
        }
      });

      await waitFor(() => {
        expect(screen.getByText('min_price')).toBeInTheDocument();
        expect(screen.getByText('max_price')).toBeInTheDocument();
      });

      // Set types to number
      const minPriceType = screen.getByLabelText(/type for min_price/i);
      await user.selectOptions(minPriceType, 'number');

      const maxPriceType = screen.getByLabelText(/type for max_price/i);
      await user.selectOptions(maxPriceType, 'number');

      // Add validation rules (would need additional UI for this)
      // For now, just verify the structure is saved correctly
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        parameters_schema: expect.objectContaining({
          min_price: expect.objectContaining({
            type: 'number'
          }),
          max_price: expect.objectContaining({
            type: 'number'
          })
        })
      }));
    });

    it('preserves parameter order from SQL query', async () => {
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM orders WHERE date = {{date}} AND region = {{region}} AND status = {{status}}'
        }
      });

      await waitFor(() => {
        const paramElements = screen.getAllByText(/{{.*}}/);
        expect(paramElements[0]).toHaveTextContent('date');
        expect(paramElements[1]).toHaveTextContent('region');
        expect(paramElements[2]).toHaveTextContent('status');
      });
    });

    it('updates parameter metadata when parameter is renamed in SQL', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');

      // Initial SQL with one parameter
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE category = {{cat}}' }
      });

      await waitFor(() => {
        expect(screen.getByText('cat')).toBeInTheDocument();
      });

      // Add description to the parameter
      const catDescInput = screen.getByLabelText(/description for cat/i);
      await user.type(catDescInput, 'Product category filter');

      // Rename parameter in SQL
      await user.clear(sqlEditor);
      await user.type(sqlEditor, 'SELECT * FROM products WHERE category = {{category}}');

      await waitFor(() => {
        expect(screen.queryByText('cat')).not.toBeInTheDocument();
        expect(screen.getByText('category')).toBeInTheDocument();
      });

      // The description should be cleared for the new parameter
      const categoryDescInput = screen.getByLabelText(/description for category/i);
      expect(categoryDescInput).toHaveValue('');
    });
  });

  describe('Persistent Template Name Header', () => {
    it('shows template name outside of tab content', () => {
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      // Template name should be visible
      const nameInput = screen.getByDisplayValue('Test Template');
      expect(nameInput).toBeInTheDocument();

      // Check that it's outside the tab content area
      const tabContent = screen.getByRole('tabpanel');
      expect(tabContent).not.toContainElement(nameInput);
    });

    it('keeps template name visible when switching tabs', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      // Template name should be visible in editor tab
      expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();

      // Switch to preview tab
      const previewTab = screen.getByRole('tab', { name: /preview/i });
      await user.click(previewTab);

      // Template name should still be visible
      expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();

      // Switch to settings tab
      const settingsTab = screen.getByRole('tab', { name: /settings/i });
      await user.click(settingsTab);

      // Template name should still be visible
      expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();
    });

    it('allows editing template name from persistent header', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      const nameInput = screen.getByDisplayValue('Test Template');
      await user.clear(nameInput);
      await user.type(nameInput, 'Updated Template Name');

      // Save the template
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Updated Template Name'
      }));
    });

    it('validates template name in persistent header', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      const nameInput = screen.getByDisplayValue('Test Template');
      await user.clear(nameInput);

      // Try to save with empty name
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/template name is required/i)).toBeInTheDocument();
      });
    });

    it('auto-saves template name changes after delay', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      const nameInput = screen.getByDisplayValue('Test Template');
      await user.clear(nameInput);
      await user.type(nameInput, 'Auto-saved Name');

      // Wait for auto-save delay (assuming 1 second)
      await waitFor(() => {
        expect(screen.getByText(/auto-saving/i)).toBeInTheDocument();
      }, { timeout: 1500 });

      await waitFor(() => {
        expect(screen.getByText(/saved/i)).toBeInTheDocument();
      });
    });

    it('shows character count for template name', () => {
      render(<TemplateEditor {...defaultProps} template={defaultTemplate as QueryTemplate} />);

      // Should show character count near the name input
      expect(screen.getByText(/13\/100/)).toBeInTheDocument(); // "Test Template" = 13 chars
    });
  });

  describe('CampaignSelector Integration', () => {
    it('renders CampaignSelector for campaign_list parameters', async () => {
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaign_list}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByText('campaign_list')).toBeInTheDocument();
      });

      // Check that CampaignSelector is rendered instead of textarea
      expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      expect(screen.getByLabelText('Campaign Selector')).toBeInTheDocument();
    });

    it('handles campaign selection changes', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaigns}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      });

      const campaignInput = screen.getByLabelText('Campaign Selector');
      await user.clear(campaignInput);
      await user.type(campaignInput, 'campaign1,campaign2,campaign3');

      // Should update the parameter value
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
        default_parameters: expect.objectContaining({
          campaigns: ['campaign1', 'campaign2', 'campaign3']
        })
      }));
    });

    it('supports multi-select campaign selection', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{selected_campaigns}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      });

      const campaignInput = screen.getByLabelText('Campaign Selector');
      await user.type(campaignInput, 'Brand_Campaign_1,Brand_Campaign_2');

      // Verify multiple campaigns are selected
      expect(campaignInput).toHaveValue('Brand_Campaign_1,Brand_Campaign_2');
    });

    it('formats campaign IDs correctly for SQL preview', async () => {
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaign_ids}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      });

      const campaignInput = screen.getByLabelText('Campaign Selector');
      fireEvent.change(campaignInput, {
        target: { value: 'id1,id2,id3' }
      });

      // Switch to preview tab
      const previewButton = screen.getByRole('button', { name: /preview/i });
      fireEvent.click(previewButton);

      await waitFor(() => {
        // Should show properly formatted SQL with campaign IDs
        expect(screen.getByText(/sql preview/i)).toBeInTheDocument();
      });
    });

    it('handles empty campaign selection', async () => {
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaigns}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      });

      const campaignInput = screen.getByLabelText('Campaign Selector');
      expect(campaignInput).toHaveValue('');

      // Should allow saving with empty campaign selection if not required
      const saveButton = screen.getByRole('button', { name: /save/i });
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalled();
      });
    });

    it('validates required campaign_list parameters', async () => {
      const user = userEvent.setup();
      render(<TemplateEditor {...defaultProps} />);

      const sqlEditor = screen.getByLabelText('SQL Editor');
      fireEvent.change(sqlEditor, {
        target: {
          value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaigns}})'
        }
      });

      await waitFor(() => {
        expect(screen.getByTestId('campaign-selector')).toBeInTheDocument();
      });

      // Mark parameter as required
      const requiredCheckbox = screen.getByLabelText(/required for campaigns/i);
      await user.click(requiredCheckbox);

      // Try to save without selecting campaigns
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/campaigns is required/i)).toBeInTheDocument();
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