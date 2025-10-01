import { useState, useEffect } from 'react';
import {
  BarChart3,
  LineChart,
  PieChart as PieChartIcon,
  TrendingUp,
  Sparkles,
  Check,
  AlertCircle,
  Lightbulb,
  Settings,
  ChevronDown,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { useChartRecommendations } from '../../hooks/useAIAnalysis';
import type { ChartRecommendation, ChartType } from '../../types/ai';

interface SmartChartSuggestionsProps {
  data: any[];
  columns: string[];
  onApplyChart?: (recommendation: ChartRecommendation) => void;
  isLoading?: boolean;
  error?: string | null;
}

// Chart type icon mapping
const chartTypeIcons: Record<ChartType, typeof BarChart3> = {
  line: LineChart,
  bar: BarChart3,
  pie: PieChartIcon,
  area: TrendingUp,
  scatter: Sparkles,
  table: BarChart3,
  metric_card: BarChart3,
  heatmap: BarChart3,
  funnel: BarChart3,
};

// Chart type display names
const chartTypeNames: Record<ChartType, string> = {
  line: 'Line Chart',
  bar: 'Bar Chart',
  pie: 'Pie Chart',
  area: 'Area Chart',
  scatter: 'Scatter Plot',
  table: 'Data Table',
  metric_card: 'Metric Card',
  heatmap: 'Heatmap',
  funnel: 'Funnel Chart',
};

interface ChartRecommendationCardProps {
  recommendation: ChartRecommendation;
  rank: number;
  isExpanded: boolean;
  onToggle: () => void;
  onApply: () => void;
  isApplied: boolean;
}

function ChartRecommendationCard({
  recommendation,
  rank,
  isExpanded,
  onToggle,
  onApply,
  isApplied,
}: ChartRecommendationCardProps) {
  const Icon = chartTypeIcons[recommendation.chart_type];
  const confidencePercentage = (recommendation.confidence_score * 100).toFixed(0);

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-all ${
        isApplied
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-gray-200 bg-white hover:border-indigo-300'
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50/50 transition-colors"
      >
        <div className="flex items-center space-x-3 flex-1">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-indigo-100">
            <Icon className="h-5 w-5 text-indigo-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold">
                {rank}
              </span>
              <h4 className="text-sm font-semibold text-gray-900">
                {chartTypeNames[recommendation.chart_type]}
              </h4>
              {isApplied && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-600 text-white">
                  <Check className="h-3 w-3 mr-1" />
                  Applied
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Confidence: {confidencePercentage}%
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {!isApplied && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onApply();
              }}
              className="px-3 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded transition-colors"
            >
              Apply
            </button>
          )}
          {isExpanded ? (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Reasoning */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-sm text-gray-700">{recommendation.reasoning}</p>
          </div>

          {/* Confidence Bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">Confidence Score</span>
              <span className="text-xs font-mono text-gray-900">{confidencePercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${confidencePercentage}%` }}
              />
            </div>
          </div>

          {/* Configuration Details */}
          {recommendation.config && (
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="flex items-center mb-2">
                <Settings className="h-4 w-4 text-blue-600 mr-2" />
                <span className="text-xs font-semibold text-blue-900">
                  Suggested Configuration
                </span>
              </div>
              <div className="space-y-1 text-xs text-blue-800">
                {recommendation.config.x_axis && (
                  <div className="flex justify-between">
                    <span className="font-medium">X-Axis:</span>
                    <span className="font-mono">{recommendation.config.x_axis}</span>
                  </div>
                )}
                {recommendation.config.y_axis && recommendation.config.y_axis.length > 0 && (
                  <div className="flex justify-between">
                    <span className="font-medium">Y-Axis:</span>
                    <span className="font-mono">{recommendation.config.y_axis.join(', ')}</span>
                  </div>
                )}
                {recommendation.config.stacked && (
                  <div className="flex justify-between">
                    <span className="font-medium">Stacked:</span>
                    <span>Yes</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Optimization Tips */}
          {recommendation.optimization_tips && recommendation.optimization_tips.length > 0 && (
            <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
              <div className="flex items-center mb-2">
                <Lightbulb className="h-4 w-4 text-yellow-600 mr-2" />
                <span className="text-xs font-semibold text-yellow-900">
                  Optimization Tips
                </span>
              </div>
              <ul className="space-y-1">
                {recommendation.optimization_tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start text-xs text-yellow-800">
                    <span className="text-yellow-600 mr-2">•</span>
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {recommendation.warnings && recommendation.warnings.length > 0 && (
            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
              <div className="flex items-center mb-2">
                <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
                <span className="text-xs font-semibold text-red-900">Warnings</span>
              </div>
              <ul className="space-y-1">
                {recommendation.warnings.map((warning, idx) => (
                  <li key={idx} className="flex items-start text-xs text-red-800">
                    <span className="text-red-600 mr-2">•</span>
                    <span>{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SmartChartSuggestions({
  data,
  columns,
  onApplyChart,
  isLoading = false,
  error = null,
}: SmartChartSuggestionsProps) {
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set([0])); // First card expanded by default
  const [appliedChartIndex, setAppliedChartIndex] = useState<number | null>(null);
  const [recommendations, setRecommendations] = useState<ChartRecommendation[] | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const toggleCard = (index: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleApplyChart = (recommendation: ChartRecommendation, index: number) => {
    setAppliedChartIndex(index);
    if (onApplyChart) {
      onApplyChart(recommendation);
    }
  };

  const chartRecommendationsMutation = useChartRecommendations();

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const response = await chartRecommendationsMutation.mutateAsync({
        data,
        columns,
        chart_types: ['line', 'bar', 'pie', 'area', 'scatter'],
        max_recommendations: 5,
      });
      setRecommendations(response.recommendations);
      setExpandedCards(new Set([0])); // Expand first recommendation
    } catch (err) {
      console.error('Failed to generate chart recommendations:', err);
      // Keep existing recommendations or show empty state
    } finally {
      setIsGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-sm text-gray-600">Loading chart data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-sm text-yellow-700">No data available for chart recommendations</p>
      </div>
    );
  }

  if (!recommendations) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Sparkles className="h-16 w-16 text-indigo-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Smart Chart Suggestions</h3>
        <p className="text-sm text-gray-600 mb-6 text-center max-w-md">
          Get AI-powered chart recommendations optimized for your data structure and patterns.
        </p>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Get Recommendations
            </>
          )}
        </button>
        <p className="text-xs text-gray-500 mt-3">
          Analyzing {data.length.toLocaleString()} rows • {columns.length} columns
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Sparkles className="h-5 w-5 text-indigo-600 mr-2" />
            Chart Recommendations
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {recommendations.length} suggestions ranked by confidence
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 mr-1 ${isGenerating ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Recommendations List */}
      <div className="space-y-3">
        {recommendations.map((recommendation, index) => (
          <ChartRecommendationCard
            key={index}
            recommendation={recommendation}
            rank={index + 1}
            isExpanded={expandedCards.has(index)}
            onToggle={() => toggleCard(index)}
            onApply={() => handleApplyChart(recommendation, index)}
            isApplied={appliedChartIndex === index}
          />
        ))}
      </div>

      {/* Data Info */}
      <div className="text-xs text-gray-500 text-center pt-2">
        Based on analysis of {data.length.toLocaleString()} rows with {columns.length} columns
      </div>
    </div>
  );
}
