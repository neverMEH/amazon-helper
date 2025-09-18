import { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Activity, Clock, Users,
  BarChart3, Calendar, Zap, AlertCircle, CheckCircle,
  XCircle, Timer, DollarSign, Target
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { queryTemplateService } from '../../services/queryTemplateService';
import type { QueryTemplate } from '../../types/queryTemplate';

interface TemplatePerformanceMetricsProps {
  template: QueryTemplate;
  templateId: string;
  showDetails?: boolean;
}

interface PerformanceMetrics {
  usage_count: number;
  success_rate: number;
  average_execution_time: number;
  last_used_at: string;
  total_data_processed: number;
  error_count: number;
  user_count: number;
  fork_count: number;
  favorite_count: number;
  cost_estimate: number;
  trend_7d: number;
  trend_30d: number;
  popular_parameters?: Record<string, any[]>;
  common_errors?: Array<{ error: string; count: number }>;
  execution_history?: Array<{
    date: string;
    executions: number;
    success: number;
    failed: number;
    avg_time: number;
  }>;
}

export default function TemplatePerformanceMetrics({
  template,
  templateId,
  showDetails = false
}: TemplatePerformanceMetricsProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'7d' | '30d' | '90d'>('30d');
  const [showExecutionHistory, setShowExecutionHistory] = useState(false);

  // Fetch performance metrics
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['templateMetrics', templateId, selectedTimeRange],
    queryFn: async () => {
      // In a real implementation, this would fetch from an API
      // For now, we'll return mock data
      const mockMetrics: PerformanceMetrics = {
        usage_count: template.usage_count || 0,
        success_rate: 94.5,
        average_execution_time: 3.2,
        last_used_at: new Date().toISOString(),
        total_data_processed: 1250000,
        error_count: 12,
        user_count: 45,
        fork_count: 8,
        favorite_count: 23,
        cost_estimate: 0.0025,
        trend_7d: 15,
        trend_30d: 42,
        popular_parameters: {
          date_range: ['Last 30 days', 'Last 7 days', 'Yesterday'],
          campaigns: ['Campaign A', 'Campaign B', 'Campaign C'],
        },
        common_errors: [
          { error: 'Timeout exceeded', count: 5 },
          { error: 'Invalid date range', count: 4 },
          { error: 'Insufficient permissions', count: 3 },
        ],
        execution_history: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          executions: Math.floor(Math.random() * 50) + 10,
          success: Math.floor(Math.random() * 45) + 8,
          failed: Math.floor(Math.random() * 5),
          avg_time: Math.random() * 5 + 1,
        })).reverse(),
      };
      return mockMetrics;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-32 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Failed to load performance metrics</p>
      </div>
    );
  }

  if (!metrics) return null;

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Activity className="h-4 w-4 text-gray-400" />;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Users className="h-5 w-5 text-blue-500" />
            <span className="text-xs text-gray-500">Total Usage</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.usage_count)}</p>
          <div className="flex items-center gap-1 mt-1">
            {getTrendIcon(metrics.trend_30d)}
            <span className={`text-xs ${metrics.trend_30d > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {Math.abs(metrics.trend_30d)}% (30d)
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="text-xs text-gray-500">Success Rate</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.success_rate.toFixed(1)}%</p>
          <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
            <div
              className="bg-green-500 h-1.5 rounded-full"
              style={{ width: `${metrics.success_rate}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <Timer className="h-5 w-5 text-yellow-500" />
            <span className="text-xs text-gray-500">Avg Time</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{metrics.average_execution_time.toFixed(1)}s</p>
          <p className="text-xs text-gray-500 mt-1">Per execution</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="h-5 w-5 text-indigo-500" />
            <span className="text-xs text-gray-500">Est. Cost</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">${metrics.cost_estimate.toFixed(4)}</p>
          <p className="text-xs text-gray-500 mt-1">Per query</p>
        </div>
      </div>

      {/* Detailed Metrics */}
      {showDetails && (
        <>
          {/* Time Range Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">Time Range:</span>
            <div className="flex gap-2">
              {(['7d', '30d', '90d'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setSelectedTimeRange(range)}
                  className={`px-3 py-1 text-sm rounded-md ${
                    selectedTimeRange === range
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {range === '7d' ? 'Week' : range === '30d' ? 'Month' : 'Quarter'}
                </button>
              ))}
            </div>
          </div>

          {/* Usage Breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-600" />
              Usage Breakdown
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Unique Users</p>
                <p className="text-xl font-semibold text-gray-900">{metrics.user_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Times Forked</p>
                <p className="text-xl font-semibold text-gray-900">{metrics.fork_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Favorites</p>
                <p className="text-xl font-semibold text-gray-900">{metrics.favorite_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Data Processed</p>
                <p className="text-xl font-semibold text-gray-900">{formatNumber(metrics.total_data_processed)}</p>
              </div>
            </div>

            <button
              onClick={() => setShowExecutionHistory(!showExecutionHistory)}
              className="mt-4 text-sm text-indigo-600 hover:text-indigo-700"
            >
              {showExecutionHistory ? 'Hide' : 'Show'} Execution History
            </button>
          </div>

          {/* Execution History Chart */}
          {showExecutionHistory && metrics.execution_history && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
                <Activity className="h-5 w-5 text-indigo-600" />
                Execution History
              </h3>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {metrics.execution_history.map((day, index) => (
                  <div key={index} className="flex items-center gap-4 text-sm">
                    <span className="text-gray-600 w-24">{day.date}</span>
                    <div className="flex-1 flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
                        <div className="h-full flex">
                          <div
                            className="bg-green-500"
                            style={{ width: `${(day.success / day.executions) * 100}%` }}
                          ></div>
                          <div
                            className="bg-red-500"
                            style={{ width: `${(day.failed / day.executions) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <span className="text-gray-700 w-16">{day.executions} runs</span>
                      <span className="text-gray-500 w-16">{day.avg_time.toFixed(1)}s avg</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common Errors */}
          {metrics.error_count > 0 && metrics.common_errors && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                Common Issues
              </h3>

              <div className="space-y-2">
                {metrics.common_errors.map((error, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <span className="text-sm text-gray-700">{error.error}</span>
                    <span className="text-sm text-gray-500">{error.count} occurrences</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                <p className="text-xs text-yellow-800">
                  <strong>Tip:</strong> Most errors can be avoided by validating parameters before execution.
                </p>
              </div>
            </div>
          )}

          {/* Popular Parameters */}
          {metrics.popular_parameters && Object.keys(metrics.popular_parameters).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
                <Target className="h-5 w-5 text-indigo-600" />
                Popular Parameter Values
              </h3>

              <div className="space-y-4">
                {Object.entries(metrics.popular_parameters).map(([param, values]) => (
                  <div key={param}>
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      {param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {values.slice(0, 5).map((value, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
                        >
                          {value}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}