import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SmartChartSuggestions from './SmartChartSuggestions';
import type { ChartRecommendation } from '../../types/ai';

// Mock data
const mockData = [
  { date: '2025-01-01', impressions: 1000, clicks: 50, conversions: 5 },
  { date: '2025-01-02', impressions: 1200, clicks: 60, conversions: 6 },
  { date: '2025-01-03', impressions: 1100, clicks: 55, conversions: 7 },
];

const mockColumns = ['date', 'impressions', 'clicks', 'conversions'];

const mockRecommendations: ChartRecommendation[] = [
  {
    chart_type: 'line',
    confidence_score: 0.92,
    reasoning: 'Time-series data detected with temporal patterns.',
    suggested_title: 'Performance Metrics Over Time',
    config: {
      x_axis: 'date',
      y_axis: ['impressions', 'clicks'],
      x_axis_label: 'Date',
      y_axis_label: 'Value',
      color_palette: ['#6366f1', '#8b5cf6'],
      enable_tooltips: true,
      enable_zoom: true,
      enable_legend: true,
      stacked: false,
      show_grid: true,
      animation_enabled: true,
    },
    optimization_tips: ['Consider aggregating data by week', 'Enable zoom for detailed exploration'],
    warnings: [],
  },
  {
    chart_type: 'bar',
    confidence_score: 0.85,
    reasoning: 'Multiple categorical values with numeric metrics.',
    suggested_title: 'Comparison by Category',
    config: {
      x_axis: 'date',
      y_axis: ['impressions'],
      color_palette: ['#6366f1'],
      enable_tooltips: true,
      enable_zoom: false,
      enable_legend: true,
      stacked: false,
      show_grid: true,
      animation_enabled: true,
    },
    optimization_tips: ['Sort categories by value', 'Limit to top 10 categories'],
    warnings: ['Large number of categories may make chart cluttered'],
  },
];

describe('SmartChartSuggestions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should render loading state', () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} isLoading={true} />);

      expect(screen.getByText(/Loading chart data/i)).toBeInTheDocument();
    });

    it('should render error state', () => {
      const errorMessage = 'Failed to load chart recommendations';
      render(
        <SmartChartSuggestions
          data={mockData}
          columns={mockColumns}
          error={errorMessage}
        />
      );

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('should render empty state when no data', () => {
      render(<SmartChartSuggestions data={[]} columns={[]} />);

      expect(screen.getByText(/No data available for chart recommendations/i)).toBeInTheDocument();
    });

    it('should render get recommendations button before generation', () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      expect(screen.getByText(/Smart Chart Suggestions/i)).toBeInTheDocument();
      expect(screen.getByText(/Get Recommendations/i)).toBeInTheDocument();
      expect(screen.getByText(/Analyzing 3 rows • 4 columns/i)).toBeInTheDocument();
    });
  });

  describe('Generate Recommendations', () => {
    it('should show analyzing state when button clicked', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument();
    });

    it('should display recommendations after generation', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      expect(screen.getByText(/Line Chart/i)).toBeInTheDocument();
      expect(screen.getByText(/Bar Chart/i)).toBeInTheDocument();
    });
  });

  describe('Recommendations Display', () => {
    beforeEach(async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should display recommendation count', () => {
      expect(screen.getByText(/3 suggestions ranked by confidence/i)).toBeInTheDocument();
    });

    it('should display chart type names', () => {
      expect(screen.getByText(/Line Chart/i)).toBeInTheDocument();
      expect(screen.getByText(/Bar Chart/i)).toBeInTheDocument();
      expect(screen.getByText(/Area Chart/i)).toBeInTheDocument();
    });

    it('should display confidence scores', () => {
      expect(screen.getByText(/92%/)).toBeInTheDocument();
      expect(screen.getByText(/85%/)).toBeInTheDocument();
      expect(screen.getByText(/78%/)).toBeInTheDocument();
    });

    it('should display rank numbers', () => {
      const rankBadges = screen.getAllByText(/^[1-3]$/);
      expect(rankBadges.length).toBe(3);
    });

    it('should expand first card by default', () => {
      expect(
        screen.getByText(/Time-series data detected with temporal patterns/i)
      ).toBeInTheDocument();
    });

    it('should display apply buttons', () => {
      const applyButtons = screen.getAllByText(/Apply/i);
      expect(applyButtons.length).toBeGreaterThan(0);
    });
  });

  describe('Card Interactions', () => {
    beforeEach(async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should collapse expanded card when clicked', () => {
      // First card is expanded by default
      expect(
        screen.getByText(/Time-series data detected with temporal patterns/i)
      ).toBeInTheDocument();

      const lineChartTitle = screen.getByText(/Line Chart/i);
      const cardButton = lineChartTitle.closest('button');
      if (cardButton) fireEvent.click(cardButton);

      // Should collapse - reasoning not visible
      expect(
        screen.queryByText(/Time-series data detected with temporal patterns/i)
      ).not.toBeInTheDocument();
    });

    it('should expand collapsed card when clicked', () => {
      // Second card is collapsed by default
      expect(
        screen.queryByText(/Multiple categorical values with numeric metrics/i)
      ).not.toBeInTheDocument();

      const barChartTitle = screen.getByText(/Bar Chart/i);
      const cardButton = barChartTitle.closest('button');
      if (cardButton) fireEvent.click(cardButton);

      // Should expand - reasoning visible
      expect(
        screen.getByText(/Multiple categorical values with numeric metrics/i)
      ).toBeInTheDocument();
    });

    it('should display configuration details when expanded', () => {
      // First card expanded by default
      expect(screen.getByText(/Suggested Configuration/i)).toBeInTheDocument();
      expect(screen.getByText(/X-Axis:/i)).toBeInTheDocument();
      expect(screen.getByText(/Y-Axis:/i)).toBeInTheDocument();
    });

    it('should display optimization tips when expanded', () => {
      // First card expanded by default
      expect(screen.getByText(/Optimization Tips/i)).toBeInTheDocument();
      expect(screen.getByText(/Consider aggregating data by week/i)).toBeInTheDocument();
    });

    it('should display warnings when present', async () => {
      // Expand second card which has warnings
      const barChartTitle = screen.getByText(/Bar Chart/i);
      const cardButton = barChartTitle.closest('button');
      if (cardButton) fireEvent.click(cardButton);

      await waitFor(() => {
        expect(screen.getByText(/Warnings/i)).toBeInTheDocument();
      });

      expect(
        screen.getByText(/Large number of categories may make chart cluttered/i)
      ).toBeInTheDocument();
    });
  });

  describe('Apply Chart', () => {
    it('should call onApplyChart callback when apply clicked', async () => {
      const onApplyChart = vi.fn();
      render(
        <SmartChartSuggestions
          data={mockData}
          columns={mockColumns}
          onApplyChart={onApplyChart}
        />
      );

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const applyButtons = screen.getAllByText(/Apply/i);
      fireEvent.click(applyButtons[0]);

      expect(onApplyChart).toHaveBeenCalledTimes(1);
      expect(onApplyChart).toHaveBeenCalledWith(
        expect.objectContaining({
          chart_type: 'line',
          confidence_score: 0.92,
        })
      );
    });

    it('should show applied badge after applying chart', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const applyButtons = screen.getAllByText(/Apply/i);
      fireEvent.click(applyButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Applied/i)).toBeInTheDocument();
      });
    });

    it('should highlight applied chart card', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const applyButtons = screen.getAllByText(/Apply/i);
      fireEvent.click(applyButtons[0]);

      await waitFor(() => {
        const lineChartCard = screen.getByText(/Line Chart/i).closest('div');
        expect(lineChartCard?.parentElement).toHaveClass('border-indigo-500');
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should have refresh button after recommendations generated', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Refresh/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should regenerate recommendations when refresh clicked', async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Refresh/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const refreshButton = screen.getByText(/Refresh/i);
      fireEvent.click(refreshButton);

      // Should show analyzing state
      await waitFor(() => {
        expect(refreshButton).toHaveClass('disabled:bg-gray-100');
      });
    });
  });

  describe('Confidence Visualization', () => {
    beforeEach(async () => {
      render(<SmartChartSuggestions data={mockData} columns={mockColumns} />);

      const generateButton = screen.getByText(/Get Recommendations/i);
      fireEvent.click(generateButton);

      await waitFor(
        () => {
          expect(screen.getByText(/Chart Recommendations/i)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should display confidence bars when expanded', () => {
      // First card expanded by default
      expect(screen.getByText(/Confidence Score/i)).toBeInTheDocument();

      // Find the confidence bar
      const confidenceBars = document.querySelectorAll('.bg-indigo-600.h-2');
      expect(confidenceBars.length).toBeGreaterThan(0);
    });

    it('should show confidence percentage in collapsed view', () => {
      expect(screen.getByText(/Confidence: 92%/i)).toBeInTheDocument();
      expect(screen.getByText(/Confidence: 85%/i)).toBeInTheDocument();
      expect(screen.getByText(/Confidence: 78%/i)).toBeInTheDocument();
    });
  });
});
