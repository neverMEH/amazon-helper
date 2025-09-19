import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TemplateTagsManager from '../TemplateTagsManager';
import type { QueryTemplate } from '../../../types/queryTemplate';

const mockTemplate: QueryTemplate = {
  id: 'template-1',
  name: 'Test Template',
  description: 'Test description',
  category: 'performance',
  report_type: 'performance',
  tags: ['campaign-metrics', 'roas'],
  sqlTemplate: 'SELECT * FROM campaigns',
  sql_query: 'SELECT * FROM campaigns',
  parameters: {},
  parameter_definitions: {},
  ui_schema: {},
  instance_types: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

describe('TemplateTagsManager', () => {
  const mockOnUpdate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component rendering', () => {
    it('renders with template data', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Tags')).toBeInTheDocument();
      expect(screen.getByText('Performance Analysis')).toBeInTheDocument();
    });

    it('displays existing tags', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('campaign-metrics')).toBeInTheDocument();
      expect(screen.getByText('roas')).toBeInTheDocument();
    });

    it('shows selected category as active', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const performanceButton = screen.getByRole('button', { name: /Performance Analysis/i });
      expect(performanceButton).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('displays tag statistics', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('2')).toBeInTheDocument(); // Total tags
      expect(screen.getByText('Total Tags')).toBeInTheDocument();
      expect(screen.getByText('Suggested')).toBeInTheDocument();
      expect(screen.getByText('Matched')).toBeInTheDocument();
    });

    it('shows category info panel', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('Performance Analysis')).toBeInTheDocument();
      expect(screen.getByText('2 tags applied')).toBeInTheDocument();
    });
  });

  describe('Category selection', () => {
    it('changes category when clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const attributionButton = screen.getByRole('button', { name: /Attribution/i });
      await user.click(attributionButton);

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas'],
        'attribution'
      );
    });

    it('shows suggested tags for new category', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const attributionButton = screen.getByRole('button', { name: /Attribution/i });
      await user.click(attributionButton);

      // Should show suggested tags for attribution
      await waitFor(() => {
        expect(screen.getByText('multi-touch')).toBeInTheDocument();
        expect(screen.getByText('last-touch')).toBeInTheDocument();
      });
    });

    it('filters suggested tags to exclude existing ones', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      // campaign-metrics and roas are already in the tags, so they shouldn't appear in suggestions
      const suggestedSection = screen.queryByText('Suggested tags for Performance Analysis:');
      if (suggestedSection) {
        const parent = suggestedSection.parentElement;
        expect(parent?.textContent).not.toContain('campaign-metrics');
        expect(parent?.textContent).not.toContain('roas');
      }
    });

    it('disables category selection in readOnly mode', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
          readOnly={true}
        />
      );

      const performanceButton = screen.getByRole('button', { name: /Performance Analysis/i });
      expect(performanceButton).toBeDisabled();
      expect(performanceButton).toHaveClass('cursor-not-allowed', 'opacity-60');
    });
  });

  describe('Tag management', () => {
    it('adds new tag when typing and pressing Enter', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, 'new-tag{Enter}');

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas', 'new-tag'],
        'performance'
      );
    });

    it('normalizes tag names (lowercase, hyphenated)', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, 'New Tag Name{Enter}');

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas', 'new-tag-name'],
        'performance'
      );
    });

    it('prevents duplicate tags', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, 'campaign-metrics{Enter}');

      // Should not call onUpdate since tag already exists
      expect(mockOnUpdate).not.toHaveBeenCalled();
    });

    it('removes tag when X button clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      // Find the remove button for 'roas' tag
      const roasTag = screen.getByText('roas').parentElement;
      const removeButton = roasTag?.querySelector('button');

      if (removeButton) {
        await user.click(removeButton);
      }

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics'],
        'performance'
      );
    });

    it('adds tag when clicking Plus button', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, 'new-tag');

      const addButton = screen.getByRole('button', { name: '' }); // Plus icon button
      await user.click(addButton);

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas', 'new-tag'],
        'performance'
      );
    });

    it('clears input after adding tag', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...') as HTMLInputElement;
      await user.type(input, 'new-tag{Enter}');

      expect(input.value).toBe('');
    });

    it('does not show add tag input in readOnly mode', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
          readOnly={true}
        />
      );

      expect(screen.queryByPlaceholderText('Add a tag...')).not.toBeInTheDocument();
    });

    it('does not show remove buttons in readOnly mode', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
          readOnly={true}
        />
      );

      const tags = screen.getAllByText(/campaign-metrics|roas/);
      tags.forEach(tag => {
        const removeButton = tag.parentElement?.querySelector('button');
        expect(removeButton).not.toBeInTheDocument();
      });
    });
  });

  describe('Suggested tags', () => {
    it('shows suggested tags for current category', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: [] }}
          onUpdate={mockOnUpdate}
        />
      );

      // Performance category should show its suggested tags
      expect(screen.getByText('acos')).toBeInTheDocument();
      expect(screen.getByText('conversion-rate')).toBeInTheDocument();
    });

    it('adds suggested tag when clicked', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: [] }}
          onUpdate={mockOnUpdate}
        />
      );

      const suggestedTag = screen.getByRole('button', { name: /acos/i });
      await user.click(suggestedTag);

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['acos'],
        'performance'
      );
    });

    it('hides suggested tags that are already added', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      // roas is already in tags, should not appear in suggestions
      const suggestions = screen.queryAllByRole('button', { name: /roas/i });
      // Filter out the actual tag display
      const suggestionButtons = suggestions.filter(btn =>
        btn.textContent?.includes('+')
      );
      expect(suggestionButtons).toHaveLength(0);
    });

    it('updates suggested tags when category changes', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: [] }}
          onUpdate={mockOnUpdate}
        />
      );

      // Switch to attribution category
      const attributionButton = screen.getByRole('button', { name: /Attribution/i });
      await user.click(attributionButton);

      // Should show attribution-specific suggestions
      expect(screen.getByText('multi-touch')).toBeInTheDocument();
      expect(screen.getByText('path-analysis')).toBeInTheDocument();

      // Should not show performance suggestions
      expect(screen.queryByText('acos')).not.toBeInTheDocument();
    });

    it('hides suggestions when none available', () => {
      // Custom category has no suggested tags
      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, category: 'custom', tags: [] }}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.queryByText(/Suggested tags/)).not.toBeInTheDocument();
    });

    it('does not show suggestions in readOnly mode', () => {
      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: [] }}
          onUpdate={mockOnUpdate}
          readOnly={true}
        />
      );

      expect(screen.queryByText(/Suggested tags/)).not.toBeInTheDocument();
    });
  });

  describe('Statistics calculation', () => {
    it('calculates correct total tags count', () => {
      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: ['tag1', 'tag2', 'tag3'] }}
          onUpdate={mockOnUpdate}
        />
      );

      const totalTags = screen.getByText('3');
      expect(totalTags).toBeInTheDocument();
      expect(screen.getByText('Total Tags')).toBeInTheDocument();
    });

    it('shows correct number of suggested tags for category', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      // Performance category has 7 suggested tags
      const suggested = screen.getByText('7');
      expect(suggested).toBeInTheDocument();
    });

    it('calculates matched tags correctly', () => {
      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      // campaign-metrics and roas are from performance suggestions
      const matched = screen.getByText('2');
      const matchedLabel = screen.getByText('Matched');
      expect(matched).toBeInTheDocument();
      expect(matchedLabel).toBeInTheDocument();
    });

    it('updates statistics when tags change', async () => {
      const user = userEvent.setup();

      const { rerender } = render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('2')).toBeInTheDocument(); // Initial count

      // Simulate tag addition
      rerender(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: ['campaign-metrics', 'roas', 'ctr'] }}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument(); // Updated count
    });
  });

  describe('Edge cases', () => {
    it('handles template without category', () => {
      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, category: undefined }}
          onUpdate={mockOnUpdate}
        />
      );

      // Should default to 'custom' category
      const customButton = screen.getByRole('button', { name: /Custom/i });
      expect(customButton).toHaveClass('bg-gray-100', 'text-gray-800');
    });

    it('handles template without tags', () => {
      render(
        <TemplateTagsManager
          template={{ ...mockTemplate, tags: undefined }}
          onUpdate={mockOnUpdate}
        />
      );

      expect(screen.getByText('0')).toBeInTheDocument(); // No tags
      expect(screen.queryByText('campaign-metrics')).not.toBeInTheDocument();
    });

    it('handles empty tag input', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, '   {Enter}'); // Just spaces

      expect(mockOnUpdate).not.toHaveBeenCalled();
    });

    it('trims whitespace from tags', async () => {
      const user = userEvent.setup();

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, '  new-tag  {Enter}');

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas', 'new-tag'],
        'performance'
      );
    });

    it('handles very long tag names', async () => {
      const user = userEvent.setup();
      const longTagName = 'a'.repeat(100);

      render(
        <TemplateTagsManager
          template={mockTemplate}
          onUpdate={mockOnUpdate}
        />
      );

      const input = screen.getByPlaceholderText('Add a tag...');
      await user.type(input, `${longTagName}{Enter}`);

      expect(mockOnUpdate).toHaveBeenCalledWith(
        ['campaign-metrics', 'roas', longTagName],
        'performance'
      );
    });
  });
});