import { useState } from 'react';
import {
  MessageSquare,
  Send,
  Sparkles,
  Code,
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  FileText,
  Wand2,
  Zap,
  RefreshCw,
} from 'lucide-react';

interface AIQueryAssistantProps {
  sqlQuery?: string;
  onQueryUpdate?: (updatedQuery: string) => void;
  context?: {
    instanceId?: string;
    availableTables?: string[];
    columns?: string[];
  };
}

type MessageType = 'user' | 'assistant';
type AssistantMode = 'chat' | 'explain' | 'optimize' | 'suggest';

interface Message {
  id: string;
  type: MessageType;
  content: string;
  mode?: AssistantMode;
  metadata?: {
    suggestions?: string[];
    optimizations?: Optimization[];
    explanation?: QueryExplanation;
    sqlQuery?: string;
  };
  timestamp: Date;
}

interface Optimization {
  type: 'performance' | 'readability' | 'best_practice';
  title: string;
  description: string;
  before?: string;
  after?: string;
  impact: 'low' | 'medium' | 'high';
}

interface QueryExplanation {
  summary: string;
  steps: ExplanationStep[];
  tables: string[];
  columns: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  estimatedRows?: number;
}

interface ExplanationStep {
  step: number;
  operation: string;
  description: string;
  details?: string;
}

const optimizationImpactColors = {
  low: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  high: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

function OptimizationCard({ optimization }: { optimization: Optimization }) {
  const colors = optimizationImpactColors[optimization.impact];

  return (
    <div className={`border ${colors.border} rounded-lg p-3 ${colors.bg}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Zap className={`h-4 w-4 ${colors.text}`} />
          <h4 className={`text-sm font-semibold ${colors.text}`}>{optimization.title}</h4>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${colors.bg} ${colors.text}`}>
          {optimization.impact.toUpperCase()} Impact
        </span>
      </div>
      <p className="text-sm text-gray-700 mb-3">{optimization.description}</p>
      {optimization.before && optimization.after && (
        <div className="space-y-2">
          <div>
            <p className="text-xs font-medium text-gray-600 mb-1">Before:</p>
            <pre className="text-xs bg-gray-800 text-gray-100 p-2 rounded overflow-x-auto">
              {optimization.before}
            </pre>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-600 mb-1">After:</p>
            <pre className="text-xs bg-green-800 text-green-100 p-2 rounded overflow-x-auto">
              {optimization.after}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ExplanationView({ explanation }: { explanation: QueryExplanation }) {
  const complexityColors = {
    simple: 'text-green-600',
    moderate: 'text-yellow-600',
    complex: 'text-red-600',
  };

  return (
    <div className="space-y-4">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-indigo-900">Query Summary</h4>
          <span className={`text-xs font-medium ${complexityColors[explanation.complexity]}`}>
            {explanation.complexity.toUpperCase()} Complexity
          </span>
        </div>
        <p className="text-sm text-indigo-800">{explanation.summary}</p>
        {explanation.estimatedRows && (
          <p className="text-xs text-indigo-600 mt-2">
            Estimated result rows: ~{explanation.estimatedRows.toLocaleString()}
          </p>
        )}
      </div>

      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-2">Execution Steps</h4>
        <div className="space-y-2">
          {explanation.steps.map((step) => (
            <div key={step.step} className="flex items-start space-x-3 bg-gray-50 p-3 rounded-lg">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex-shrink-0">
                {step.step}
              </span>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{step.operation}</p>
                <p className="text-xs text-gray-600 mt-1">{step.description}</p>
                {step.details && (
                  <p className="text-xs text-gray-500 mt-1 italic">{step.details}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Tables Used</h4>
          <div className="space-y-1">
            {explanation.tables.map((table, idx) => (
              <div key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                {table}
              </div>
            ))}
          </div>
        </div>
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Key Columns</h4>
          <div className="space-y-1">
            {explanation.columns.slice(0, 5).map((column, idx) => (
              <div key={idx} className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                {column}
              </div>
            ))}
            {explanation.columns.length > 5 && (
              <div className="text-xs text-gray-500 px-2 py-1">
                +{explanation.columns.length - 5} more
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AIQueryAssistant({
  sqlQuery,
  onQueryUpdate,
  context,
}: AIQueryAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeMode, setActiveMode] = useState<AssistantMode>('chat');

  const addMessage = (type: MessageType, content: string, metadata?: Message['metadata']) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      mode: type === 'assistant' ? activeMode : undefined,
      metadata,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    addMessage('user', userMessage);
    setInput('');
    setIsProcessing(true);

    // TODO: Implement API call based on activeMode
    // This will be implemented in Task 2.4 (AI Services Integration)
    setTimeout(() => {
      if (activeMode === 'chat') {
        addMessage(
          'assistant',
          "I can help you write SQL queries for Amazon Marketing Cloud. Try asking me to 'explain this query' or 'optimize this query' to get started!"
        );
      } else if (activeMode === 'explain' && sqlQuery) {
        const mockExplanation: QueryExplanation = {
          summary:
            'This query analyzes campaign performance by aggregating impression and click data from the impressions table.',
          steps: [
            {
              step: 1,
              operation: 'Table Scan',
              description: 'Scan impressions table',
              details: 'Reads all rows from impressions table matching date range',
            },
            {
              step: 2,
              operation: 'Filter',
              description: 'Apply WHERE conditions',
              details: 'Filters by date range and campaign status',
            },
            {
              step: 3,
              operation: 'Aggregate',
              description: 'Calculate metrics by campaign',
              details: 'Groups by campaign_id and calculates SUM/COUNT',
            },
            {
              step: 4,
              operation: 'Sort',
              description: 'Order results by impressions',
              details: 'Sorts descending by total impressions',
            },
          ],
          tables: ['impressions', 'campaigns'],
          columns: ['campaign_id', 'impression_dt', 'user_id', 'creative_id'],
          complexity: 'moderate',
          estimatedRows: 1500,
        };
        addMessage('assistant', 'Here is an explanation of your SQL query:', {
          explanation: mockExplanation,
        });
      } else if (activeMode === 'optimize' && sqlQuery) {
        const mockOptimizations: Optimization[] = [
          {
            type: 'performance',
            title: 'Add date range filter to reduce scan size',
            description:
              'Filtering by date early in the query reduces the amount of data scanned and improves performance.',
            impact: 'high',
            before: 'SELECT * FROM impressions WHERE campaign_id = 123',
            after:
              "SELECT * FROM impressions WHERE impression_dt BETWEEN '2025-01-01' AND '2025-01-31' AND campaign_id = 123",
          },
          {
            type: 'readability',
            title: 'Use explicit column names instead of SELECT *',
            description: 'Selecting only needed columns improves readability and performance.',
            impact: 'medium',
            before: 'SELECT * FROM impressions',
            after: 'SELECT campaign_id, impression_dt, user_id FROM impressions',
          },
        ];
        addMessage('assistant', 'Here are some optimization suggestions for your query:', {
          optimizations: mockOptimizations,
        });
      } else if (activeMode === 'suggest') {
        const mockSuggestions = [
          'Add a GROUP BY campaign_id to aggregate metrics',
          'Include date range filter for better performance',
          'Add ORDER BY to sort results by impressions DESC',
          'Consider using COUNT(DISTINCT user_id) for unique users',
        ];
        addMessage('assistant', 'Here are some suggestions to improve your query:', {
          suggestions: mockSuggestions,
        });
      }
      setIsProcessing(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleModeChange = (mode: AssistantMode) => {
    setActiveMode(mode);
    if (mode === 'explain' && sqlQuery) {
      setInput('Explain this SQL query in detail');
    } else if (mode === 'optimize' && sqlQuery) {
      setInput('What optimizations can I make to this query?');
    } else if (mode === 'suggest' && sqlQuery) {
      setInput('What improvements would you suggest?');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-indigo-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Query Assistant</h3>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex space-x-2">
          <button
            onClick={() => handleModeChange('chat')}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeMode === 'chat'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <MessageSquare className="h-3 w-3 inline-block mr-1" />
            Chat
          </button>
          <button
            onClick={() => handleModeChange('explain')}
            disabled={!sqlQuery}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeMode === 'explain'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <FileText className="h-3 w-3 inline-block mr-1" />
            Explain
          </button>
          <button
            onClick={() => handleModeChange('optimize')}
            disabled={!sqlQuery}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeMode === 'optimize'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Wand2 className="h-3 w-3 inline-block mr-1" />
            Optimize
          </button>
          <button
            onClick={() => handleModeChange('suggest')}
            disabled={!sqlQuery}
            className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
              activeMode === 'suggest'
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed'
            }`}
          >
            <Lightbulb className="h-3 w-3 inline-block mr-1" />
            Suggest
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Sparkles className="h-12 w-12 text-indigo-400 mb-3" />
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              Welcome to AI Query Assistant
            </h4>
            <p className="text-sm text-gray-600 max-w-sm">
              I can help you write, explain, and optimize your Amazon Marketing Cloud SQL queries.
            </p>
            <div className="mt-6 space-y-2 text-xs text-gray-500">
              <p className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                Natural language to SQL conversion
              </p>
              <p className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                Query explanation and analysis
              </p>
              <p className="flex items-center">
                <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                Performance optimization tips
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl ${
                  message.type === 'user'
                    ? 'bg-indigo-600 text-white rounded-lg px-4 py-2'
                    : 'bg-gray-100 rounded-lg px-4 py-3 w-full'
                }`}
              >
                {message.type === 'user' ? (
                  <p className="text-sm">{message.content}</p>
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm text-gray-700">{message.content}</p>

                    {/* Render metadata based on mode */}
                    {message.metadata?.explanation && (
                      <ExplanationView explanation={message.metadata.explanation} />
                    )}

                    {message.metadata?.optimizations && (
                      <div className="space-y-2">
                        {message.metadata.optimizations.map((opt, idx) => (
                          <OptimizationCard key={idx} optimization={opt} />
                        ))}
                      </div>
                    )}

                    {message.metadata?.suggestions && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <div className="flex items-center mb-2">
                          <Lightbulb className="h-4 w-4 text-yellow-600 mr-2" />
                          <span className="text-sm font-semibold text-yellow-900">
                            Suggestions
                          </span>
                        </div>
                        <ul className="space-y-1">
                          {message.metadata.suggestions.map((suggestion, idx) => (
                            <li key={idx} className="flex items-start text-sm text-yellow-800">
                              <span className="text-yellow-600 mr-2">•</span>
                              <span>{suggestion}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <RefreshCw className="h-4 w-4 text-indigo-600 animate-spin" />
                <span className="text-sm text-gray-600">Analyzing...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              activeMode === 'chat'
                ? 'Ask me anything about SQL queries...'
                : activeMode === 'explain'
                ? 'Ask about the query...'
                : activeMode === 'optimize'
                ? 'Request optimizations...'
                : 'Request suggestions...'
            }
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            disabled={isProcessing}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing || !input.trim()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
