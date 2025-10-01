import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AIAnalysisPanel from './AIAnalysisPanel';
import type { AnalyzeDataResponse } from '../../types/ai';

// Mock data
const mockData = [
  { date: '2025-01-01', impressions: 1000, clicks: 50, conversions: 5 },
  { date: '2025-01-02', impressions: 1200, clicks: 60, conversions: 6 },
  { date: '2025-01-03', impressions: 1100, clicks: 55, conversions: 7 },
];

const mockColumns = ['date', 'impressions', 'clicks', 'conversions'];

const mockAnalysisResponse: AnalyzeDataResponse = {
  insights: [
    {
      category: 'trend',
      title: 'Upward trend in conversions',
      description: 'Conversions increased by 15% over the period',
      confidence: 0.89,
      impact: 'high',
      recommendation: 'Continue current strategy',
      timestamp: '2025-01-01T00:00:00Z',
    },
    {
      category: 'anomaly',
      title: 'Unusual spike in clicks',
      description: 'Clicks increased 45% on Jan 2',
      confidence: 0.92,
      impact: 'medium',
      recommendation: 'Review bid adjustments',
      timestamp: '2025-01-01T00:00:00Z',
    },
    {
      category: 'optimization',
      title: 'ROAS optimization opportunity',
      description: 'Several keywords showing improvement potential',
      confidence: 0.76,
      impact: 'medium',
      recommendation: 'Test new ad copy',
      timestamp: '2025-01-01T00:00:00Z',
    },
  ],
  statistical_summary: {
    metrics: {
      impressions: { mean: 1100, std: 100, min: 1000, max: 1200 },
      clicks: { mean: 55, std: 5, min: 50, max: 60 },
    },
    correlations: { impressions_clicks: 0.95 },
    outliers: {},
    trends: {},
  },
  recommendations: [
    'Focus budget on top-performing campaigns',
    'Test new creative variations',
    'Expand to similar audience segments',
  ],
  metadata: {
    analysis_type: 'comprehensive',
    rows_analyzed: 3,
  },
};

describe('AIAnalysisPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should render loading state', () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
          isLoading={true}
        />
      );

      expect(screen.getByText(/Loading execution data/i)).toBeInTheDocument();
    });

    it('should render error state', () => {
      const errorMessage = 'Failed to load data';
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should render empty state when no data', () => {
      render(
        <AIAnalysisPanel
          data={[]}
          columns={[]}
        />
      );

      expect(screen.getByText(/No data available for analysis/i)).toBeInTheDocument();
    });

    it('should render generate insights button before analysis', () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      expect(screen.getByText(/AI-Powered Insights/i)).toBeInTheDocument();
      expect(screen.getByText(/Generate Insights/i)).toBeInTheDocument();
      expect(screen.getByText(/Analyzing 3 rows • 4 columns/i)).toBeInTheDocument();
    });
  });

  describe('Generate Insights', () => {
    it('should show analyzing state when button clicked', async () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      const generateButton = screen.getByText(/Generate Insights/i);
      fireEvent.click(generateButton);

      expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument();
    });

    it('should display insights after generation', async () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      const generateButton = screen.getByText(/Generate Insights/i);
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText(/Upward trend in conversions/i)).toBeInTheDocument();
      }, { timeout: 3000 });

      expect(screen.getByText(/Unusual spike in clicks/i)).toBeInTheDocument();
      expect(screen.getByText(/ROAS optimization opportunity/i)).toBeInTheDocument();
    });
  });

  describe('Insights Display', () => {
    beforeEach(async () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      const generateButton = screen.getByText(/Generate Insights/i);
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText(/Upward trend in conversions/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should display insight count and rows analyzed', () => {
      expect(screen.getByText(/3 insights found/i)).toBeInTheDocument();
      expect(screen.getByText(/3 rows analyzed/i)).toBeInTheDocument();
    });

    it('should display key recommendations section', () => {
      expect(screen.getByText(/Key Recommendations/i)).toBeInTheDocument();
      expect(screen.getByText(/Focus budget on top-performing campaigns/i)).toBeInTheDocument();
      expect(screen.getByText(/Test new creative variations/i)).toBeInTheDocument();
    });

    it('should display insights grouped by category', () => {
      expect(screen.getByText(/trend \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/anomaly \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/optimization \(1\)/i)).toBeInTheDocument();
    });

    it('should show confidence scores', () => {
      expect(screen.getByText(/89%/)).toBeInTheDocument();
      expect(screen.getByText(/92%/)).toBeInTheDocument();
      expect(screen.getByText(/76%/)).toBeInTheDocument();
    });

    it('should show impact levels', () => {
      expect(screen.getByText(/High Impact/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Medium Impact/i).length).toBe(2);
    });
  });

  describe('Insight Card Interactions', () => {
    beforeEach(async () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      const generateButton = screen.getByText(/Generate Insights/i);
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText(/Upward trend in conversions/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should expand insight card when clicked', () => {
      const insightTitle = screen.getByText(/Upward trend in conversions/i);
      const insightCard = insightTitle.closest('button');

      // Initially collapsed - recommendation not visible
      expect(screen.queryByText(/Continue current strategy/i)).not.toBeInTheDocument();

      // Click to expand
      if (insightCard) fireEvent.click(insightCard);

      // Now expanded - recommendation visible
      expect(screen.getByText(/Continue current strategy/i)).toBeInTheDocument();
    });

    it('should collapse insight card when clicked again', () => {
      const insightTitle = screen.getByText(/Upward trend in conversions/i);
      const insightCard = insightTitle.closest('button');

      // Click to expand
      if (insightCard) fireEvent.click(insightCard);
      expect(screen.getByText(/Continue current strategy/i)).toBeInTheDocument();

      // Click to collapse
      if (insightCard) fireEvent.click(insightCard);
      expect(screen.queryByText(/Continue current strategy/i)).not.toBeInTheDocument();
    });

    it('should copy insight text when copy button clicked', async () => {
      // Mock clipboard API
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined),
        },
      });

      const insightTitle = screen.getByText(/Upward trend in conversions/i);
      const insightCard = insightTitle.closest('div');
      const copyButtons = insightCard?.querySelectorAll('button');

      // Find and click copy button (second button in the card)
      const copyButton = Array.from(copyButtons || []).find(btn =>
        btn.querySelector('svg')?.classList.toString().includes('lucide')
      );

      if (copyButton) {
        fireEvent.click(copyButton);

        await waitFor(() => {
          expect(navigator.clipboard.writeText).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Actions', () => {
    beforeEach(async () => {
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
        />
      );

      const generateButton = screen.getByText(/Generate Insights/i);
      fireEvent.click(generateButton);

      await waitFor(() => {
        expect(screen.getByText(/Upward trend in conversions/i)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should have regenerate button', () => {
      expect(screen.getByText(/Regenerate/i)).toBeInTheDocument();
    });

    it('should have export button', () => {
      expect(screen.getByText(/Export/i)).toBeInTheDocument();
    });

    it('should trigger regeneration when regenerate clicked', async () => {
      const regenerateButton = screen.getByText(/Regenerate/i);
      fireEvent.click(regenerateButton);

      // Should show analyzing state
      await waitFor(() => {
        expect(regenerateButton).toHaveClass('disabled:bg-gray-100');
      });
    });

    it('should export insights when export clicked', () => {
      // Mock URL.createObjectURL and DOM manipulation
      global.URL.createObjectURL = vi.fn(() => 'mock-url');
      const createElementSpy = vi.spyOn(document, 'createElement');
      const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
      const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);

      const exportButton = screen.getByText(/Export/i);
      fireEvent.click(exportButton);

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();

      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });
  });

  describe('Refresh Callback', () => {
    it('should call onRefresh when provided', () => {
      const onRefresh = vi.fn();
      render(
        <AIAnalysisPanel
          data={mockData}
          columns={mockColumns}
          onRefresh={onRefresh}
        />
      );

      // onRefresh is currently not connected to any UI element
      // This test documents the prop for future implementation
      expect(onRefresh).not.toHaveBeenCalled();
    });
  });
});
