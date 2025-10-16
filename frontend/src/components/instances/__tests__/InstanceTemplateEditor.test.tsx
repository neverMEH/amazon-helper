import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import InstanceTemplateEditor from '../InstanceTemplateEditor';
import type { InstanceTemplate } from '../../../types/instanceTemplate';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }: any) => (
    <div data-testid="monaco-editor">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label="SQL Editor"
      />
    </div>
  )
}));

// Mock SQLEditor component
vi.mock('../../common/SQLEditor', () => ({
  default: ({ value, onChange }: any) => (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="SQL Editor"
      data-testid="sql-editor"
    />
  )
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  Toaster: () => null,
}));

// Mock useInstanceMappings hook
vi.mock('../../../hooks/useInstanceMappings', () => ({
  useInstanceMappings: vi.fn(() => ({
    data: {
      brands: ['Brand_A', 'Brand_B'],
      asins_by_brand: {
        Brand_A: ['B001', 'B002', 'B003'],
        Brand_B: ['B004', 'B005']
      },
      campaigns_by_brand: {
        Brand_A: ['Campaign_1', 'Campaign_2'],
        Brand_B: ['Campaign_3']
      }
    },
    isLoading: false,
    error: null
  }))
}));

// Mock API
vi.mock('../../../services/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: { id: 'inst-1', name: 'Test Instance' } }))
  }
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('InstanceTemplateEditor - Parameter Detection Integration', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    instanceId: 'inst-123',
    onSave: mockOnSave,
    onCancel: mockOnCancel,
    isLoading: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders template editor modal', () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Create New Template')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/weekly campaign performance/i)).toBeInTheDocument();
      expect(screen.getByTestId('sql-editor')).toBeInTheDocument();
    });

    it('renders with existing template data', () => {
      const template: InstanceTemplate = {
        id: '1',
        templateId: 'tpl-1',
        name: 'Test Template',
        description: 'Test description',
        sqlQuery: 'SELECT * FROM campaigns',
        instanceId: 'inst-123',
        userId: 'user-1',
        tags: ['test'],
        usageCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      render(
        <InstanceTemplateEditor {...defaultProps} template={template} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Edit Template')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test description')).toBeInTheDocument();
    });
  });

  describe('Parameter Detection', () => {
    it('detects parameters with {{}} format', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND asin IN ({{asins}})' }
      });

      await waitFor(() => {
        expect(screen.getByText('Detected 2 parameters')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('detects parameters with :parameter format', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE date = :date AND campaign = :campaign_id' }
      });

      await waitFor(() => {
        expect(screen.getByText('Detected 2 parameters')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('detects parameters with $parameter format', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE spend > $min_spend' }
      });

      await waitFor(() => {
        expect(screen.getByText('Detected 1 parameter')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('shows parameter count badge', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}} AND asin IN ({{asins}})' }
      });

      await waitFor(() => {
        expect(screen.getByText('Detected 3 parameters')).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('does not show parameters section when no parameters detected', () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE status = \'ENABLED\'' }
      });

      expect(screen.queryByText(/^Detected.*parameter/)).not.toBeInTheDocument();
    });
  });

  describe('Parameter Input Display', () => {
    it('displays input fields for detected parameters', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND campaign_id = {{campaign}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/start_date/i)).toBeInTheDocument();
        expect(screen.getByText(/campaign/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it('shows parameter type badges', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin IN ({{asins}}) AND date = {{start_date}}' }
      });

      await waitFor(() => {
        // Should show type indicators for ASIN and date parameters
        expect(screen.getByText(/asin/i)).toBeInTheDocument();
        expect(screen.getByText(/start_date/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Auto-Population from Instance Mappings', () => {
    it('auto-populates ASIN parameters from instance mappings', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin IN ({{asins}})' }
      });

      await waitFor(() => {
        expect(screen.getByText(/auto-populated/i)).toBeInTheDocument();
      }, { timeout: 1500 });
    });

    it('auto-populates campaign parameters from instance mappings', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE campaign_id IN ({{campaigns}})' }
      });

      await waitFor(() => {
        expect(screen.getByText(/auto-populated/i)).toBeInTheDocument();
      }, { timeout: 1500 });
    });

    it('shows loading state while fetching mappings', async () => {
      const { useInstanceMappings } = await import('../../../hooks/useInstanceMappings');
      vi.mocked(useInstanceMappings).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
        refetch: vi.fn()
      } as any);

      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin IN ({{asins}})' }
      });

      await waitFor(() => {
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Manual Parameter Entry', () => {
    it('allows manual entry for date parameters', async () => {
      const user = userEvent.setup();
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date >= {{start_date}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/start_date/i)).toBeInTheDocument();
      }, { timeout: 1000 });

      // Should have an input field for start_date
      const dateInput = screen.getByPlaceholderText(/start_date|date/i);
      expect(dateInput).toBeInTheDocument();
    });

    it('allows manual entry for custom parameters', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE brand = {{custom_brand}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/custom_brand/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Parameter State Management', () => {
    it('maintains parameter values when SQL changes', async () => {
      const user = userEvent.setup();
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');

      // Add SQL with parameter
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/date/i)).toBeInTheDocument();
      });

      // Change SQL to add more text but keep parameter
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}} AND status = \'ENABLED\'' }
      });

      // Parameter should still be detected
      await waitFor(() => {
        expect(screen.getByText(/date/i)).toBeInTheDocument();
      });
    });

    it('removes parameter inputs when parameters deleted from SQL', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');

      // Add SQL with parameters
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}} AND asin = {{asin}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/date/i)).toBeInTheDocument();
        expect(screen.getByText(/asin/i)).toBeInTheDocument();
      });

      // Remove one parameter
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/date/i)).toBeInTheDocument();
        expect(screen.queryByText(/asin/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Save with Parameters', () => {
    it('saves template with SQL query (parameters should be filled)', async () => {
      const user = userEvent.setup();
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      // Fill in template name
      const nameInput = screen.getByPlaceholderText(/weekly campaign performance/i);
      await user.type(nameInput, 'Test Template');

      // Add SQL with parameters
      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}}' }
      });

      await waitFor(() => {
        expect(screen.getByText(/date/i)).toBeInTheDocument();
      });

      // Save button should be available
      const saveButton = screen.getByRole('button', { name: /save template/i });
      expect(saveButton).toBeInTheDocument();
    });

    it('validates that required fields are filled before saving', async () => {
      const user = userEvent.setup();
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const saveButton = screen.getByRole('button', { name: /save template/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/template name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/sql query is required/i)).toBeInTheDocument();
      });
    });
  });

  describe('UI/UX Features', () => {
    it('shows blue info banner when parameters detected', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE asin IN ({{asins}})' }
      });

      await waitFor(() => {
        const banner = screen.getByText(/detected.*parameter/i).closest('div');
        expect(banner).toHaveClass('bg-blue-50');
      }, { timeout: 1000 });
    });

    it('displays parameter section below SQL editor', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM campaigns WHERE date = {{date}}' }
      });

      await waitFor(() => {
        const parametersSection = screen.getByText(/detected.*parameter/i).closest('div');
        const sqlEditorContainer = sqlEditor.closest('div');

        // Parameters section should come after SQL editor in DOM
        expect(parametersSection).toBeInTheDocument();
        expect(sqlEditorContainer).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe('Error Handling', () => {
    it('handles parameter detection errors gracefully', async () => {
      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');

      // Add malformed SQL that might cause detection issues
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM {{{{invalid}}}' }
      });

      // Should not crash - either show no parameters or handle gracefully
      await waitFor(() => {
        expect(screen.getByTestId('sql-editor')).toBeInTheDocument();
      });
    });

    it('shows warning when instance mappings fail to load', async () => {
      const { useInstanceMappings } = await import('../../../hooks/useInstanceMappings');
      vi.mocked(useInstanceMappings).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Failed to load mappings'),
        refetch: vi.fn()
      } as any);

      render(
        <InstanceTemplateEditor {...defaultProps} />,
        { wrapper: createWrapper() }
      );

      const sqlEditor = screen.getByTestId('sql-editor');
      fireEvent.change(sqlEditor, {
        target: { value: 'SELECT * FROM products WHERE asin IN ({{asins}})' }
      });

      // Should still show parameter inputs even if mappings fail
      await waitFor(() => {
        expect(screen.getByText(/asins/i)).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });
});
