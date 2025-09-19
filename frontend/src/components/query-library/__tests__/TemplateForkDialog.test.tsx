import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TemplateForkDialog from '../TemplateForkDialog';
import type { QueryTemplate } from '../../../types/queryTemplate';

// Mock the queryTemplateService
vi.mock('../../../services/queryTemplateService', () => ({
  queryTemplateService: {
    forkTemplate: vi.fn(),
  },
}));

// Mock SQLEditor component
vi.mock('../../common/SQLEditor', () => ({
  default: ({ value, onChange, height }: any) => (
    <textarea
      data-testid="sql-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ height }}
      placeholder="SQL Editor"
    />
  ),
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { queryTemplateService } from '../../../services/queryTemplateService';
import toast from 'react-hot-toast';

const mockTemplate: QueryTemplate = {
  id: 'template-1',
  name: 'Original Template',
  description: 'This is the original template',
  category: 'performance',
  report_type: 'performance',
  sqlTemplate: 'SELECT * FROM campaigns WHERE date >= {{start_date}}',
  sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}}',
  parameters: {},
  parameter_definitions: {},
  ui_schema: {},
  instance_types: [],
  usage_count: 42,
  created_by: 'user123',
  version: 1,
  version_history: [
    { version: 1, date: '2024-01-01', changes: 'Initial version' },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

describe('TemplateForkDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnForked = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Dialog rendering', () => {
    it('renders the dialog when open', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
          onForked={mockOnForked}
        />
      );

      expect(screen.getByText('Fork Template')).toBeInTheDocument();
      expect(screen.getByText('Forking from:')).toBeInTheDocument();
      expect(screen.getByText('Original Template')).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      render(
        <TemplateForkDialog
          isOpen={false}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      expect(screen.queryByText('Fork Template')).not.toBeInTheDocument();
    });

    it('displays original template information', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      expect(screen.getByText('Original Template')).toBeInTheDocument();
      expect(screen.getByText('This is the original template')).toBeInTheDocument();
      expect(screen.getByText('Used 42 times')).toBeInTheDocument();
      expect(screen.getByText('Created by user123')).toBeInTheDocument();
      expect(screen.getByText('Version 1')).toBeInTheDocument();
    });

    it('shows default fork name with (Fork) suffix', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const nameInput = screen.getByDisplayValue('Original Template (Fork)');
      expect(nameInput).toBeInTheDocument();
    });

    it('displays SQL editor with template SQL', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const sqlEditor = screen.getByTestId('sql-editor') as HTMLTextAreaElement;
      expect(sqlEditor.value).toBe('SELECT * FROM campaigns WHERE date >= {{start_date}}');
    });
  });

  describe('Version history', () => {
    it('shows version history when button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      // Version history should not be visible initially
      expect(screen.queryByText('Version History')).toBeInTheDocument();
      expect(screen.queryByText('Initial version')).not.toBeInTheDocument();

      // Click version history button
      const versionButton = screen.getByRole('button', { name: /Version History/i });
      await user.click(versionButton);

      // Version history should now be visible
      expect(screen.getByText('Initial version')).toBeInTheDocument();
      expect(screen.getByText('v1')).toBeInTheDocument();
    });

    it('handles templates without version history', async () => {
      const user = userEvent.setup();
      const templateNoHistory = { ...mockTemplate, version_history: undefined };

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={templateNoHistory}
        />
      );

      const versionButton = screen.getByRole('button', { name: /Version History/i });
      await user.click(versionButton);

      expect(screen.getByText('No version history available')).toBeInTheDocument();
    });
  });

  describe('User interactions', () => {
    it('updates fork name when typing', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const nameInput = screen.getByDisplayValue('Original Template (Fork)') as HTMLInputElement;
      await user.clear(nameInput);
      await user.type(nameInput, 'My Custom Fork');

      expect(nameInput.value).toBe('My Custom Fork');
    });

    it('updates description when typing', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const descriptionInput = screen.getByDisplayValue('This is the original template') as HTMLTextAreaElement;
      await user.clear(descriptionInput);
      await user.type(descriptionInput, 'My modified description');

      expect(descriptionInput.value).toBe('My modified description');
    });

    it('updates SQL when editing', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const sqlEditor = screen.getByTestId('sql-editor') as HTMLTextAreaElement;
      await user.clear(sqlEditor);
      await user.type(sqlEditor, 'SELECT * FROM modified_table');

      expect(sqlEditor.value).toBe('SELECT * FROM modified_table');
    });

    it('toggles privacy checkbox', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const privacyCheckbox = screen.getByLabelText('Keep this fork private') as HTMLInputElement;
      expect(privacyCheckbox).toBeChecked(); // Default is private

      await user.click(privacyCheckbox);
      expect(privacyCheckbox).not.toBeChecked();

      // Privacy text should update
      expect(screen.getByText('Others in your organization can discover and use this fork')).toBeInTheDocument();
    });

    it('closes dialog when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('closes dialog when X button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const closeButton = screen.getByRole('button', { name: '' }); // X button typically has no text
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Fork creation', () => {
    it('successfully creates a fork with valid data', async () => {
      const user = userEvent.setup();
      const forkedTemplate = { ...mockTemplate, id: 'fork-1', name: 'My Fork' };

      vi.mocked(queryTemplateService.forkTemplate).mockResolvedValue(forkedTemplate);

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
          onForked={mockOnForked}
        />
      );

      // Modify the fork name
      const nameInput = screen.getByDisplayValue('Original Template (Fork)') as HTMLInputElement;
      await user.clear(nameInput);
      await user.type(nameInput, 'My Fork');

      // Click create fork button
      const createButton = screen.getByRole('button', { name: /Create Fork/i });
      await user.click(createButton);

      // Verify service was called with correct data
      await waitFor(() => {
        expect(queryTemplateService.forkTemplate).toHaveBeenCalledWith('template-1', {
          name: 'My Fork',
          description: 'This is the original template',
          sql_query: 'SELECT * FROM campaigns WHERE date >= {{start_date}}',
          is_public: false,
          parent_template_id: 'template-1',
          version: 1,
        });
      });

      // Verify success toast
      expect(toast.success).toHaveBeenCalledWith('Template forked successfully');

      // Verify callback and close
      expect(mockOnForked).toHaveBeenCalledWith(forkedTemplate);
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('shows error when fork name is empty', async () => {
      const user = userEvent.setup();

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      // Clear the name input
      const nameInput = screen.getByDisplayValue('Original Template (Fork)') as HTMLInputElement;
      await user.clear(nameInput);

      // Try to create fork
      const createButton = screen.getByRole('button', { name: /Create Fork/i });
      await user.click(createButton);

      // Should show error toast
      expect(toast.error).toHaveBeenCalledWith('Please provide a name for your fork');

      // Service should not be called
      expect(queryTemplateService.forkTemplate).not.toHaveBeenCalled();
    });

    it('handles fork creation failure', async () => {
      const user = userEvent.setup();
      const error = new Error('Network error');

      vi.mocked(queryTemplateService.forkTemplate).mockRejectedValue(error);

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const createButton = screen.getByRole('button', { name: /Create Fork/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Network error');
      });

      // Dialog should remain open
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('disables create button when fork name is empty', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={{ ...mockTemplate }}
        />
      );

      // Set name to empty
      const nameInput = screen.getByDisplayValue('Original Template (Fork)') as HTMLInputElement;
      fireEvent.change(nameInput, { target: { value: '' } });

      const createButton = screen.getByRole('button', { name: /Create Fork/i });
      expect(createButton).toBeDisabled();
    });

    it('shows loading state while creating fork', async () => {
      const user = userEvent.setup();

      // Create a promise that we can control
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      vi.mocked(queryTemplateService.forkTemplate).mockReturnValue(pendingPromise as any);

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      const createButton = screen.getByRole('button', { name: /Create Fork/i });
      await user.click(createButton);

      // Should show loading state
      expect(screen.getByText('Creating Fork...')).toBeInTheDocument();
      expect(createButton).toBeDisabled();

      // Resolve the promise
      resolvePromise!({ ...mockTemplate, id: 'fork-1' });

      await waitFor(() => {
        expect(screen.queryByText('Creating Fork...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Fork attribution', () => {
    it('displays fork attribution notice', () => {
      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={mockTemplate}
        />
      );

      expect(screen.getByText('Fork Attribution')).toBeInTheDocument();
      expect(screen.getByText(/linked to the original template/)).toBeInTheDocument();
      expect(screen.getByText(/original author will be credited/)).toBeInTheDocument();
    });
  });

  describe('Template variations', () => {
    it('handles template without description', () => {
      const templateNoDesc = { ...mockTemplate, description: undefined };

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={templateNoDesc}
        />
      );

      const descriptionInput = screen.getByPlaceholderText('Describe your modifications...') as HTMLTextAreaElement;
      expect(descriptionInput.value).toBe('');
    });

    it('handles template without usage count', () => {
      const templateNoUsage = { ...mockTemplate, usage_count: undefined };

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={templateNoUsage}
        />
      );

      expect(screen.queryByText(/Used \d+ times/)).not.toBeInTheDocument();
    });

    it('handles template without created_by', () => {
      const templateNoCreator = { ...mockTemplate, created_by: undefined };

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={templateNoCreator}
        />
      );

      expect(screen.queryByText(/Created by/)).not.toBeInTheDocument();
    });

    it('handles template without version', () => {
      const templateNoVersion = { ...mockTemplate, version: undefined };

      render(
        <TemplateForkDialog
          isOpen={true}
          onClose={mockOnClose}
          template={templateNoVersion}
        />
      );

      expect(screen.queryByText(/Version \d+/)).not.toBeInTheDocument();
    });
  });
});