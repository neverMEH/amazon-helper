import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Database, GitBranch, Tag, Sparkles, TrendingUp, AlertTriangle, Lightbulb, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import api from '../services/api';
import { useAIAnalysis } from '../hooks/useAIAnalysis';
import type { DataInsight } from '../types/ai';

interface DashboardStats {
  totalInstances: number;
  totalWorkflows: number;
  totalCampaigns: number;
  recentExecutions: number;
}

export default function Dashboard() {
  const [showAIInsights, setShowAIInsights] = useState(true);
  const [aiInsights, setAiInsights] = useState<DataInsight[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null);

  const aiAnalysisMutation = useAIAnalysis();

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      // For now, we'll use placeholder data
      // TODO: Create a dedicated stats endpoint
      const [instances, workflows, campaigns] = await Promise.all([
        api.get('/instances'),
        api.get('/workflows'),
        api.get('/campaigns'),
      ]);

      return {
        totalInstances: instances.data.length || 0,
        totalWorkflows: workflows.data.length || 0,
        totalCampaigns: campaigns.data.length || 0,
        recentExecutions: 0,
      };
    },
  });

  // Generate AI insights when stats are loaded
  const handleGenerateInsights = async () => {
    if (!stats) return;

    setIsAnalyzing(true);
    try {
      const dashboardData = [
        ['AMC Instances', stats.totalInstances],
        ['Workflows', stats.totalWorkflows],
        ['Campaigns', stats.totalCampaigns],
        ['Recent Executions', stats.recentExecutions],
      ];

      const response = await aiAnalysisMutation.mutateAsync({
        data: {
          columns: ['metric', 'value'],
          rows: dashboardData,
        },
        analysis_type: 'comprehensive',
        confidence_threshold: 0.6,
        max_insights: 5,
      });

      setAiInsights(response.insights);
      setLastRefreshTime(new Date());
    } catch (error) {
      console.error('Failed to generate AI insights:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Auto-refresh AI insights when enabled
  useEffect(() => {
    if (autoRefresh && stats && !isAnalyzing) {
      const interval = setInterval(() => {
        handleGenerateInsights();
      }, 60000); // Refresh every 60 seconds

      return () => clearInterval(interval);
    }
  }, [autoRefresh, stats, isAnalyzing]);

  // Auto-generate insights on first load if stats are available
  useEffect(() => {
    if (stats && aiInsights.length === 0 && !isAnalyzing && autoRefresh) {
      handleGenerateInsights();
    }
  }, [stats]);

  const cards = [
    {
      title: 'AMC Instances',
      value: stats?.totalInstances || 0,
      icon: Database,
      color: 'bg-blue-500',
    },
    {
      title: 'Workflows',
      value: stats?.totalWorkflows || 0,
      icon: GitBranch,
      color: 'bg-green-500',
    },
    {
      title: 'Campaigns',
      value: stats?.totalCampaigns || 0,
      icon: Tag,
      color: 'bg-purple-500',
    },
    {
      title: 'Recent Executions',
      value: stats?.recentExecutions || 0,
      icon: BarChart3,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your Amazon Marketing Cloud resources
        </p>
      </div>

      {/* Stats Cards */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading...</div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((card) => (
              <div
                key={card.title}
                className="bg-white overflow-hidden shadow rounded-lg"
              >
                <div className="p-5">
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 ${card.color} rounded-md p-3`}>
                      <card.icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {card.title}
                        </dt>
                        <dd className="text-2xl font-semibold text-gray-900">
                          {card.value}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* AI Insights Panel */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-5 w-5 text-indigo-600" />
                  <h2 className="text-lg font-semibold text-gray-900">AI Insights</h2>
                  {lastRefreshTime && (
                    <span className="text-xs text-gray-500">
                      Updated {lastRefreshTime.toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  {/* Auto-refresh toggle */}
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoRefresh}
                      onChange={(e) => setAutoRefresh(e.target.checked)}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-gray-700 flex items-center">
                      <RefreshCw className="h-3.5 w-3.5 mr-1" />
                      Auto-refresh
                    </span>
                  </label>
                  <button
                    onClick={handleGenerateInsights}
                    disabled={isAnalyzing}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-1.5" />
                        Generate Insights
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setShowAIInsights(!showAIInsights)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    {showAIInsights ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>

            {showAIInsights && (
              <div className="p-5">
                {aiInsights.length === 0 ? (
                  <div className="text-center py-8">
                    <Lightbulb className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No insights yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Click "Generate Insights" to analyze your dashboard metrics with AI
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {aiInsights.map((insight, index) => {
                      const Icon = insight.category === 'trend' ? TrendingUp : insight.category === 'anomaly' ? AlertTriangle : Lightbulb;
                      const colorClass = insight.impact === 'high' ? 'text-red-600' : insight.impact === 'medium' ? 'text-yellow-600' : 'text-blue-600';

                      return (
                        <div key={index} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                          <Icon className={`h-5 w-5 mt-0.5 ${colorClass}`} />
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-gray-900">{insight.title}</h4>
                            <p className="mt-1 text-sm text-gray-600">{insight.description}</p>
                            {insight.recommendation && (
                              <div className="mt-2 flex items-start space-x-2">
                                <Lightbulb className="h-4 w-4 text-indigo-600 mt-0.5" />
                                <p className="text-sm text-indigo-700 font-medium">{insight.recommendation}</p>
                              </div>
                            )}
                            <div className="mt-2 flex items-center space-x-4">
                              <span className="text-xs text-gray-500">
                                Confidence: {(insight.confidence * 100).toFixed(0)}%
                              </span>
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                insight.impact === 'high' ? 'bg-red-100 text-red-800' :
                                insight.impact === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {insight.impact} impact
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Contextual Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-blue-900">Quick Tips</h3>
                <ul className="mt-2 text-sm text-blue-700 space-y-1 list-disc list-inside">
                  <li>Use AI insights to identify optimization opportunities across your workflows</li>
                  <li>Monitor your execution trends to spot performance patterns</li>
                  <li>Set up automated reports to track campaign performance over time</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}