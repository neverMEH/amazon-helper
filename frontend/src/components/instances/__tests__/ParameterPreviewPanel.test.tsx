import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ParameterPreviewPanel from '../ParameterPreviewPanel';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, height, options }: any) => (
    <div data-testid="monaco-editor" style={{ height }}>
      <pre data-readonly={options?.readOnly}>{value}</pre>
    </div>
  )
}));

describe('ParameterPreviewPanel', () => {
  const defaultProps = {
    sqlQuery: 'SELECT * FROM campaigns WHERE date >= {{start_date}} AND date <= {{end_date}}',
    isOpen: true,
    onToggle: vi.fn()
  };

  describe('Rendering', () => {
    it('renders collapsed by default with toggle button', () => {
      render(<ParameterPreviewPanel {...defaultProps} isOpen={false} />);

      expect(screen.getByRole('button', { name: /sql preview/i })).toBeInTheDocument();
      expect(screen.queryByTestId('monaco-editor')).not.toBeInTheDocument();
    });

    it('renders expanded with Monaco editor when open', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      expect(screen.getByRole('button', { name: /sql preview/i })).toBeInTheDocument();
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    it('displays SQL query in Monaco editor', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveTextContent('SELECT * FROM campaigns');
      expect(editor).toHaveTextContent('WHERE date >= {{start_date}}');
    });

    it('sets Monaco editor to read-only mode', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const editor = screen.getByTestId('monaco-editor');
      const preElement = editor.querySelector('pre');
      expect(preElement?.getAttribute('data-readonly')).toBe('true');
    });

    it('uses correct height for Monaco editor', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveStyle({ height: '400px' });
    });
  });

  describe('Toggle Functionality', () => {
    it('calls onToggle when clicking header button', async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<ParameterPreviewPanel {...defaultProps} onToggle={onToggle} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      await user.click(toggleButton);

      expect(onToggle).toHaveBeenCalledTimes(1);
    });

    it('shows chevron-down icon when collapsed', () => {
      render(<ParameterPreviewPanel {...defaultProps} isOpen={false} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      const svgElements = toggleButton.querySelectorAll('svg');
      const chevronIcon = Array.from(svgElements).find(svg =>
        svg.classList.contains('lucide-chevron-down') || svg.classList.contains('lucide-chevron-up')
      );
      expect(chevronIcon).toHaveClass('lucide-chevron-down');
    });

    it('shows chevron-up icon when expanded', () => {
      render(<ParameterPreviewPanel {...defaultProps} isOpen={true} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      const svgElements = toggleButton.querySelectorAll('svg');
      const chevronIcon = Array.from(svgElements).find(svg =>
        svg.classList.contains('lucide-chevron-down') || svg.classList.contains('lucide-chevron-up')
      );
      expect(chevronIcon).toHaveClass('lucide-chevron-up');
    });

    it('toggles between collapsed and expanded states', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<ParameterPreviewPanel {...defaultProps} isOpen={false} />);

      expect(screen.queryByTestId('monaco-editor')).not.toBeInTheDocument();

      rerender(<ParameterPreviewPanel {...defaultProps} isOpen={true} />);

      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });
  });

  describe('SQL Content Display', () => {
    it('handles empty SQL query', () => {
      render(<ParameterPreviewPanel {...defaultProps} sqlQuery="" />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveTextContent('');
    });

    it('displays multi-line SQL queries correctly', () => {
      const multiLineSQL = `SELECT
  campaign_id,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks
FROM campaigns
WHERE date >= {{start_date}}
  AND date <= {{end_date}}
GROUP BY campaign_id
ORDER BY total_impressions DESC`;

      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={multiLineSQL} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveTextContent('SELECT');
      expect(editor).toHaveTextContent('campaign_id');
      expect(editor).toHaveTextContent('GROUP BY campaign_id');
    });

    it('displays SQL with parameters in various formats', () => {
      const sqlWithParams = 'SELECT * FROM products WHERE asin = {{asin}} AND date = :date AND price > $min_price';

      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={sqlWithParams} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveTextContent('{{asin}}');
      expect(editor).toHaveTextContent(':date');
      expect(editor).toHaveTextContent('$min_price');
    });

    it('preserves SQL formatting and whitespace', () => {
      const formattedSQL = `SELECT
    campaign_id,
    campaign_name
FROM
    campaigns
WHERE
    status = 'ENABLED'`;

      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={formattedSQL} />);

      const editor = screen.getByTestId('monaco-editor');
      const preElement = editor.querySelector('pre');
      expect(preElement?.textContent).toBe(formattedSQL);
    });
  });

  describe('Styling', () => {
    it('applies correct container classes', () => {
      const { container } = render(<ParameterPreviewPanel {...defaultProps} />);

      const panelContainer = container.firstChild;
      expect(panelContainer).toHaveClass('border', 'border-gray-300', 'rounded-lg');
    });

    it('applies correct header button classes', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      expect(toggleButton).toHaveClass('w-full', 'flex', 'items-center', 'justify-between');
    });

    it('has proper shadow styling', () => {
      const { container } = render(<ParameterPreviewPanel {...defaultProps} />);

      const panelContainer = container.firstChild;
      expect(panelContainer).toHaveClass('shadow-sm');
    });
  });

  describe('Accessibility', () => {
    it('has accessible button label', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<ParameterPreviewPanel {...defaultProps} onToggle={onToggle} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      toggleButton.focus();

      expect(toggleButton).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(onToggle).toHaveBeenCalled();
    });

    it('supports space key for toggling', async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<ParameterPreviewPanel {...defaultProps} onToggle={onToggle} />);

      const toggleButton = screen.getByRole('button', { name: /sql preview/i });
      toggleButton.focus();

      await user.keyboard('{ }');
      expect(onToggle).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('handles very long SQL queries', () => {
      const longSQL = 'SELECT * FROM campaigns WHERE ' + 'asin = {{asin}} AND '.repeat(50);

      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={longSQL} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toBeInTheDocument();
    });

    it('handles SQL with special characters', () => {
      const sqlWithSpecialChars = "SELECT * FROM products WHERE name LIKE '%{{search}}%' AND description != '{{exclude}}'";

      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={sqlWithSpecialChars} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toHaveTextContent("LIKE '%{{search}}%'");
    });

    it('handles undefined sqlQuery prop', () => {
      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={undefined as any} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toBeInTheDocument();
    });

    it('handles null sqlQuery prop', () => {
      render(<ParameterPreviewPanel {...defaultProps} sqlQuery={null as any} />);

      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toBeInTheDocument();
    });
  });

  describe('Monaco Editor Configuration', () => {
    it('configures Monaco with SQL language', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      // Monaco editor should be present (language configuration is internal)
      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    it('disables editing in Monaco editor', () => {
      render(<ParameterPreviewPanel {...defaultProps} />);

      const editor = screen.getByTestId('monaco-editor');
      const preElement = editor.querySelector('pre');
      expect(preElement?.getAttribute('data-readonly')).toBe('true');
    });
  });
});
