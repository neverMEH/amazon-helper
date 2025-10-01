import { useState } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Zap,
  Target,
  Settings,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Download,
  Copy,
  Sparkles,
  BarChart3,
  Info,
  Check
} from 'lucide-react';
import type {
  DataInsight,
  AnalyzeDataResponse,
  InsightCategory,
  ImpactLevel
} from '../../types/ai';

interface AIAnalysisPanelProps {
  data: any[]; // Execution result data
  columns: string[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

// Category icon and color mappings
const categoryIcons: Record<InsightCategory, typeof TrendingUp> = {
  trend: TrendingUp,
  anomaly: AlertTriangle,
  correlation: Zap,
  performance: Target,
  optimization: Settings,
  pattern: BarChart3,
  forecast: Sparkles,
};

const categoryColors: Record<InsightCategory, { bg: string; text: string; border: string }> = {
  trend: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  anomaly: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  correlation: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  performance: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  optimization: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  pattern: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  forecast: { bg: 'bg-pink-50', text: 'text-pink-700', border: 'border-pink-200' },
};

const impactColors: Record<ImpactLevel, { bg: string; text: string }> = {
  low: { bg: 'bg-gray-100', text: 'text-gray-700' },
  medium: { bg: 'bg-blue-100', text: 'text-blue-700' },
  high: { bg: 'bg-red-100', text: 'text-red-700' },
};

interface InsightCardProps {
  insight: DataInsight;
  isExpanded: boolean;
  onToggle: () => void;
}

function InsightCard({ insight, isExpanded, onToggle }: InsightCardProps) {
  const Icon = categoryIcons[insight.category];
  const colors = categoryColors[insight.category];
  const impactColor = impactColors[insight.impact];
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = `${insight.title}\n${insight.description}${insight.recommendation ? `\n\nRecommendation: ${insight.recommendation}` : ''}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`border ${colors.border} rounded-lg overflow-hidden ${colors.bg}`}>
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center space-x-3 flex-1">
          <Icon className={`h-5 w-5 ${colors.text}`} />
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className={`text-sm font-semibold ${colors.text}`}>{insight.title}</h4>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${impactColor.bg} ${impactColor.text}`}>
                {insight.impact.charAt(0).toUpperCase() + insight.impact.slice(1)} Impact
              </span>
            </div>
            <p className={`text-xs ${colors.text} opacity-75 mt-1`}>
              {insight.category.charAt(0).toUpperCase() + insight.category.slice(1)} • Confidence: {(insight.confidence * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            className={`p-1 hover:bg-white/50 rounded transition-colors ${colors.text}`}
            title="Copy insight"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          </button>
          {isExpanded ? (
            <ChevronDown className={`h-5 w-5 ${colors.text}`} />
          ) : (
            <ChevronRight className={`h-5 w-5 ${colors.text}`} />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          <div className="bg-white/50 rounded-lg p-3">
            <p className="text-sm text-gray-700">{insight.description}</p>
          </div>

          {insight.recommendation && (
            <div className="bg-white/70 rounded-lg p-3 border border-gray-200">
              <div className="flex items-start space-x-2">
                <Info className="h-4 w-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-indigo-900 mb-1">Recommendation</p>
                  <p className="text-sm text-gray-700">{insight.recommendation}</p>
                </div>
              </div>
            </div>
          )}

          {insight.supporting_data && Object.keys(insight.supporting_data).length > 0 && (
            <div className="bg-white/50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-700 mb-2">Supporting Data</p>
              <pre className="text-xs text-gray-600 overflow-x-auto">
                {JSON.stringify(insight.supporting_data, null, 2)}
              </pre>
            </div>
          )}

          {/* Confidence bar */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-600 font-medium">Confidence:</span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${colors.text.replace('text-', 'bg-')}`}
                style={{ width: `${insight.confidence * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-600 font-mono">{(insight.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AIAnalysisPanel({
  data,
  columns,
  isLoading = false,
  error = null,
  onRefresh
}: AIAnalysisPanelProps) {
  const [expandedInsights, setExpandedInsights] = useState<Set<number>>(new Set());
  const [analysisData, setAnalysisData] = useState<AnalyzeDataResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const toggleInsight = (index: number) => {
    setExpandedInsights(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    // TODO: Implement API call to /api/ai/analyze-data
    // This will be implemented in Task 2.4 (AI Services Integration)
    setTimeout(() => {
      // Mock data for now
      setAnalysisData({
        insights: [
          {
            category: 'trend',
            title: 'Upward trend in conversions',
            description: 'Your conversion rate has increased by 15% over the past week, indicating improved campaign performance.',
            confidence: 0.89,
            impact: 'high',
            recommendation: 'Continue current optimization strategy and consider scaling budget by 10-15%.',
            timestamp: new Date().toISOString(),
          },
          {
            category: 'anomaly',
            title: 'Unusual spike in cost per click',
            description: 'CPC increased by 45% on Tuesday, which is significantly higher than the 7-day average.',
            confidence: 0.92,
            impact: 'medium',
            recommendation: 'Review bid adjustments and check for new competitor activity during this period.',
            timestamp: new Date().toISOString(),
          },
          {
            category: 'optimization',
            title: 'Opportunity to improve ROAS',
            description: 'Several keywords are showing strong impression volume but low click-through rates, indicating optimization potential.',
            confidence: 0.76,
            impact: 'medium',
            recommendation: 'Consider testing new ad copy or adjusting keyword match types for these terms.',
            timestamp: new Date().toISOString(),
          },
        ],
        statistical_summary: {
          metrics: {},
          correlations: {},
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
          rows_analyzed: data.length,
        },
      });
      setIsAnalyzing(false);
    }, 2000);
  };

  const handleExport = () => {
    if (!analysisData) return;
    const dataStr = JSON.stringify(analysisData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-insights-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Group insights by category
  const groupedInsights = analysisData?.insights.reduce((acc, insight, idx) => {
    if (!acc[insight.category]) {
      acc[insight.category] = [];
    }
    acc[insight.category].push({ insight, index: idx });
    return acc;
  }, {} as Record<InsightCategory, Array<{ insight: DataInsight; index: number }>>);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-sm text-gray-600">Loading execution data...</p>
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
        <p className="text-sm text-yellow-700">No data available for analysis</p>
      </div>
    );
  }

  if (!analysisData) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Sparkles className="h-16 w-16 text-indigo-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered Insights</h3>
        <p className="text-sm text-gray-600 mb-6 text-center max-w-md">
          Generate intelligent insights from your query results including trends, anomalies, and actionable recommendations.
        </p>
        <button
          onClick={handleAnalyze}
          disabled={isAnalyzing}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Insights
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
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Sparkles className="h-5 w-5 text-indigo-600 mr-2" />
            AI Insights
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {analysisData.insights.length} insights found • {data.length.toLocaleString()} rows analyzed
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isAnalyzing ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <Download className="h-4 w-4 mr-1" />
            Export
          </button>
        </div>
      </div>

      {/* Overall recommendations */}
      {analysisData.recommendations && analysisData.recommendations.length > 0 && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-indigo-900 mb-2 flex items-center">
            <Target className="h-4 w-4 mr-2" />
            Key Recommendations
          </h4>
          <ul className="space-y-2">
            {analysisData.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start space-x-2 text-sm text-indigo-800">
                <span className="text-indigo-600 font-bold mt-0.5">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Grouped insights */}
      {groupedInsights && Object.entries(groupedInsights).map(([category, items]) => (
        <div key={category}>
          <h4 className="text-sm font-medium text-gray-700 mb-2 capitalize">
            {category} ({items.length})
          </h4>
          <div className="space-y-2">
            {items.map(({ insight, index }) => (
              <InsightCard
                key={index}
                insight={insight}
                isExpanded={expandedInsights.has(index)}
                onToggle={() => toggleInsight(index)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
