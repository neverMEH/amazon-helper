import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AIQueryAssistant from './AIQueryAssistant';

const mockSqlQuery = `
SELECT
  campaign_id,
  COUNT(*) as impressions,
  COUNT(DISTINCT user_id) as unique_users
FROM impressions
WHERE impression_dt >= '2025-01-01'
GROUP BY campaign_id
ORDER BY impressions DESC
`;

describe('AIQueryAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should render welcome message when no messages', () => {
      render(<AIQueryAssistant />);

      expect(screen.getByText(/Welcome to AI Query Assistant/i)).toBeInTheDocument();
      expect(screen.getByText(/Natural language to SQL conversion/i)).toBeInTheDocument();
    });

    it('should render all mode buttons', () => {
      render(<AIQueryAssistant />);

      expect(screen.getByText('Chat')).toBeInTheDocument();
      expect(screen.getByText('Explain')).toBeInTheDocument();
      expect(screen.getByText('Optimize')).toBeInTheDocument();
      expect(screen.getByText('Suggest')).toBeInTheDocument();
    });

    it('should have chat mode active by default', () => {
      render(<AIQueryAssistant />);

      const chatButton = screen.getByText('Chat').closest('button');
      expect(chatButton).toHaveClass('bg-indigo-600');
    });

    it('should disable explain/optimize/suggest modes without SQL query', () => {
      render(<AIQueryAssistant />);

      const explainButton = screen.getByText('Explain').closest('button');
      const optimizeButton = screen.getByText('Optimize').closest('button');
      const suggestButton = screen.getByText('Suggest').closest('button');

      expect(explainButton).toBeDisabled();
      expect(optimizeButton).toBeDisabled();
      expect(suggestButton).toBeDisabled();
    });

    it('should enable all modes when SQL query provided', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      const optimizeButton = screen.getByText('Optimize').closest('button');
      const suggestButton = screen.getByText('Suggest').closest('button');

      expect(explainButton).not.toBeDisabled();
      expect(optimizeButton).not.toBeDisabled();
      expect(suggestButton).not.toBeDisabled();
    });
  });

  describe('Chat Mode', () => {
    it('should show correct placeholder in chat mode', () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      expect(input).toBeInTheDocument();
    });

    it('should send message when send button clicked', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' }); // Send button has no text

      fireEvent.change(input, { target: { value: 'How do I write a SELECT query?' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('How do I write a SELECT query?')).toBeInTheDocument();
      });
    });

    it('should send message when Enter key pressed', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);

      fireEvent.change(input, { target: { value: 'Help me with SQL' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 13, charCode: 13 });

      await waitFor(() => {
        expect(screen.getByText('Help me with SQL')).toBeInTheDocument();
      });
    });

    it('should not send message when Shift+Enter pressed', () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);

      fireEvent.change(input, { target: { value: 'Test message' } });
      fireEvent.keyPress(input, { key: 'Enter', shiftKey: true });

      expect(screen.queryByText('Test message')).not.toBeInTheDocument();
    });

    it('should clear input after sending', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i) as HTMLInputElement;
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Test query' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('should show processing state', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Test' } });
      fireEvent.click(sendButton);

      expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument();
    });

    it('should display assistant response', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Hello' } });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/I can help you write SQL queries/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Explain Mode', () => {
    it('should switch to explain mode', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      fireEvent.click(explainButton!);

      expect(explainButton).toHaveClass('bg-indigo-600');
    });

    it('should populate input with explain prompt', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      fireEvent.click(explainButton!);

      const input = screen.getByDisplayValue(/Explain this SQL query in detail/i);
      expect(input).toBeInTheDocument();
    });

    it('should display query explanation', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      fireEvent.click(explainButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Query Summary/i)).toBeInTheDocument();
          expect(screen.getByText(/Execution Steps/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should show complexity level', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      fireEvent.click(explainButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/MODERATE Complexity/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should display tables and columns', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const explainButton = screen.getByText('Explain').closest('button');
      fireEvent.click(explainButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Tables Used/i)).toBeInTheDocument();
          expect(screen.getByText(/Key Columns/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Optimize Mode', () => {
    it('should switch to optimize mode', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const optimizeButton = screen.getByText('Optimize').closest('button');
      fireEvent.click(optimizeButton!);

      expect(optimizeButton).toHaveClass('bg-indigo-600');
    });

    it('should populate input with optimize prompt', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const optimizeButton = screen.getByText('Optimize').closest('button');
      fireEvent.click(optimizeButton!);

      const input = screen.getByDisplayValue(/What optimizations can I make/i);
      expect(input).toBeInTheDocument();
    });

    it('should display optimization recommendations', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const optimizeButton = screen.getByText('Optimize').closest('button');
      fireEvent.click(optimizeButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/optimization suggestions/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should show optimization impact levels', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const optimizeButton = screen.getByText('Optimize').closest('button');
      fireEvent.click(optimizeButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/HIGH Impact/i)).toBeInTheDocument();
          expect(screen.getByText(/MEDIUM Impact/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should display before/after code examples', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const optimizeButton = screen.getByText('Optimize').closest('button');
      fireEvent.click(optimizeButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Before:/i)).toBeInTheDocument();
          expect(screen.getByText(/After:/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Suggest Mode', () => {
    it('should switch to suggest mode', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const suggestButton = screen.getByText('Suggest').closest('button');
      fireEvent.click(suggestButton!);

      expect(suggestButton).toHaveClass('bg-indigo-600');
    });

    it('should populate input with suggest prompt', () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const suggestButton = screen.getByText('Suggest').closest('button');
      fireEvent.click(suggestButton!);

      const input = screen.getByDisplayValue(/What improvements would you suggest/i);
      expect(input).toBeInTheDocument();
    });

    it('should display suggestions list', async () => {
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} />);

      const suggestButton = screen.getByText('Suggest').closest('button');
      fireEvent.click(suggestButton!);

      const sendButton = screen.getByRole('button', { name: '' });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Suggestions/i)).toBeInTheDocument();
          expect(screen.getByText(/GROUP BY campaign_id/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Message Display', () => {
    it('should display user messages on right side', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        const userMessage = screen.getByText('Test message').closest('div');
        expect(userMessage?.parentElement).toHaveClass('justify-end');
      });
    });

    it('should display assistant messages on left side', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Hello' } });
      fireEvent.click(sendButton);

      await waitFor(
        () => {
          const assistantMessage = screen.getByText(/I can help you write SQL queries/i).closest('div');
          expect(assistantMessage?.parentElement?.parentElement).toHaveClass('justify-start');
        },
        { timeout: 3000 }
      );
    });

    it('should maintain message order', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      // Send first message
      fireEvent.change(input, { target: { value: 'First message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('First message')).toBeInTheDocument();
      });

      // Wait for first response
      await waitFor(
        () => {
          expect(screen.getByText(/I can help you write SQL queries/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      // Send second message
      fireEvent.change(input, { target: { value: 'Second message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        const messages = screen.getAllByText(/message/i);
        expect(messages.length).toBeGreaterThan(1);
      });
    });
  });

  describe('Input Validation', () => {
    it('should disable send button when input is empty', () => {
      render(<AIQueryAssistant />);

      const sendButton = screen.getByRole('button', { name: '' });
      expect(sendButton).toBeDisabled();
    });

    it('should disable send button when input is only whitespace', () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: '   ' } });
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when input has content', () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Test' } });
      expect(sendButton).not.toBeDisabled();
    });

    it('should disable input during processing', async () => {
      render(<AIQueryAssistant />);

      const input = screen.getByPlaceholderText(/Ask me anything about SQL queries/i);
      const sendButton = screen.getByRole('button', { name: '' });

      fireEvent.change(input, { target: { value: 'Test' } });
      fireEvent.click(sendButton);

      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();
    });
  });

  describe('Callbacks', () => {
    it('should call onQueryUpdate when provided', () => {
      const onQueryUpdate = vi.fn();
      render(<AIQueryAssistant sqlQuery={mockSqlQuery} onQueryUpdate={onQueryUpdate} />);

      // onQueryUpdate would be called when applying optimizations
      // This test documents the callback for future implementation
      expect(onQueryUpdate).not.toHaveBeenCalled();
    });
  });

  describe('Context Support', () => {
    it('should accept context with instance and tables', () => {
      const context = {
        instanceId: 'test-instance',
        availableTables: ['impressions', 'clicks', 'conversions'],
        columns: ['campaign_id', 'user_id'],
      };

      render(<AIQueryAssistant sqlQuery={mockSqlQuery} context={context} />);

      expect(screen.getByText(/Welcome to AI Query Assistant/i)).toBeInTheDocument();
    });
  });
});
