import React, { useState, useMemo, useCallback } from 'react';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import type { WeekData, ComparisonData } from '../../services/reportDashboardService';
import WeekSelector from './WeekSelector';
import { LineChart } from '../charts/LineChart';
import { BarChart } from '../charts/BarChart';
import LoadingSpinner from '../LoadingSpinner';

interface ComparisonPanelProps {
  weeks: WeekData[];
  onPeriodsChange: (periods: { period1: string[]; period2: string[] }) => void;
  comparisonData?: ComparisonData;
  isLoading: boolean;
}

type ComparisonView = 'metrics' | 'trends' | 'breakdown';

const ComparisonPanel: React.FC<ComparisonPanelProps> = ({
  weeks,
  onPeriodsChange,
  comparisonData,
  isLoading,
}) => {
  const [period1Weeks, setPeriod1Weeks] = useState<string[]>([]);
  const [period2Weeks, setPeriod2Weeks] = useState<string[]>([]);
  const [comparisonView, setComparisonView] = useState<ComparisonView>('metrics');
  const selectedMetrics = [
    'impressions',
    'clicks',
    'conversions',
    'spend',
  ];

  // Handle period selection
  const handlePeriod1Change = useCallback(
    (weekIds: string[]) => {
      setPeriod1Weeks(weekIds);
      onPeriodsChange({ period1: weekIds, period2: period2Weeks });
    },
    [period2Weeks, onPeriodsChange]
  );

  const handlePeriod2Change = useCallback(
    (weekIds: string[]) => {
      setPeriod2Weeks(weekIds);
      onPeriodsChange({ period1: period1Weeks, period2: weekIds });
    },
    [period1Weeks, onPeriodsChange]
  );

  // Swap periods
  const handleSwapPeriods = useCallback(() => {
    const temp = period1Weeks;
    setPeriod1Weeks(period2Weeks);
    setPeriod2Weeks(temp);
    onPeriodsChange({ period1: period2Weeks, period2: temp });
  }, [period1Weeks, period2Weeks, onPeriodsChange]);

  // Calculate comparison metrics
  const comparisonMetrics = useMemo(() => {
    if (!comparisonData) return [];

    const metrics: Array<{
      label: string;
      period1Value: number;
      period2Value: number;
      change: number;
      format: string;
    }> = [];
    const { period1, period2, changes } = comparisonData;

    // Default metrics to compare
    const metricConfigs = [
      { key: 'total_impressions', label: 'Impressions', format: 'number' },
      { key: 'total_clicks', label: 'Clicks', format: 'number' },
      { key: 'total_conversions', label: 'Conversions', format: 'number' },
      { key: 'total_spend', label: 'Spend', format: 'currency' },
      { key: 'avg_ctr', label: 'CTR', format: 'percentage' },
      { key: 'avg_cvr', label: 'CVR', format: 'percentage' },
      { key: 'avg_cpc', label: 'CPC', format: 'currency' },
      { key: 'avg_cpa', label: 'CPA', format: 'currency' },
    ];

    metricConfigs.forEach(({ key, label, format }) => {
      const value1 = period1.summary[key] || 0;
      const value2 = period2.summary[key] || 0;
      const changeKey = `${key.replace('total_', '').replace('avg_', '')}_change`;
      const change = changes[changeKey] || 0;

      metrics.push({
        label,
        period1Value: value1,
        period2Value: value2,
        change,
        format,
      });
    });

    return metrics;
  }, [comparisonData]);

  // Format value based on type
  const formatValue = useCallback((value: number, format: string) => {
    switch (format) {
      case 'currency':
        return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      case 'percentage':
        return `${(value * 100).toFixed(2)}%`;
      case 'number':
      default:
        return value.toLocaleString();
    }
  }, []);

  // Generate chart data for trends
  const trendChartData = useMemo(() => {
    if (!comparisonData) return null;

    const period1Data: Record<string, number[]> = {};
    const period2Data: Record<string, number[]> = {};
    const labels: string[] = [];

    // Aggregate data by week
    comparisonData.period1.weeks.forEach((week) => {
      labels.push(`W${week.week_number}`);
      selectedMetrics.forEach((metric) => {
        if (!period1Data[metric]) period1Data[metric] = [];
        period1Data[metric].push(week.execution_results?.metrics[metric] || 0);
      });
    });

    comparisonData.period2.weeks.forEach((week) => {
      selectedMetrics.forEach((metric) => {
        if (!period2Data[metric]) period2Data[metric] = [];
        period2Data[metric].push(week.execution_results?.metrics[metric] || 0);
      });
    });

    // Create datasets for line chart
    const datasets = selectedMetrics.flatMap((metric) => [
      {
        label: `Period 1 - ${metric}`,
        data: period1Data[metric] || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderDash: [5, 5],
      },
      {
        label: `Period 2 - ${metric}`,
        data: period2Data[metric] || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
      },
    ]);

    return {
      labels,
      datasets,
    };
  }, [comparisonData, selectedMetrics]);

  // Generate breakdown chart data
  const breakdownChartData = useMemo(() => {
    if (!comparisonData) return null;

    const labels = selectedMetrics.map((m) => m.charAt(0).toUpperCase() + m.slice(1));
    const period1Values = selectedMetrics.map(
      (metric) => comparisonData.period1.summary[`total_${metric}`] || 0
    );
    const period2Values = selectedMetrics.map(
      (metric) => comparisonData.period2.summary[`total_${metric}`] || 0
    );

    return {
      labels,
      datasets: [
        {
          label: 'Period 1',
          data: period1Values,
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
        },
        {
          label: 'Period 2',
          data: period2Values,
          backgroundColor: 'rgba(34, 197, 94, 0.5)',
          borderColor: 'rgb(34, 197, 94)',
          borderWidth: 1,
        },
      ],
    };
  }, [comparisonData, selectedMetrics]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading comparison data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Period 1</h3>
          <WeekSelector
            weeks={weeks}
            selectedWeeks={period1Weeks}
            onSelectionChange={handlePeriod1Change}
            multiSelect={true}
            className="w-full"
          />
          {period1Weeks.length > 0 && (
            <div className="mt-3 text-sm text-blue-700">
              {period1Weeks.length} week{period1Weeks.length !== 1 ? 's' : ''} selected
            </div>
          )}
        </div>

        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-green-900 mb-3">Period 2</h3>
          <WeekSelector
            weeks={weeks}
            selectedWeeks={period2Weeks}
            onSelectionChange={handlePeriod2Change}
            multiSelect={true}
            className="w-full"
          />
          {period2Weeks.length > 0 && (
            <div className="mt-3 text-sm text-green-700">
              {period2Weeks.length} week{period2Weeks.length !== 1 ? 's' : ''} selected
            </div>
          )}
        </div>
      </div>

      {/* Swap button */}
      <div className="flex justify-center">
        <button
          onClick={handleSwapPeriods}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          disabled={period1Weeks.length === 0 && period2Weeks.length === 0}
        >
          <ArrowsRightLeftIcon className="h-4 w-4 mr-2" />
          Swap Periods
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonData && (
        <>
          {/* View Toggle */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setComparisonView('metrics')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  comparisonView === 'metrics'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Metrics Comparison
              </button>
              <button
                onClick={() => setComparisonView('trends')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  comparisonView === 'trends'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Trend Analysis
              </button>
              <button
                onClick={() => setComparisonView('breakdown')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  comparisonView === 'breakdown'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Breakdown
              </button>
            </nav>
          </div>

          {/* Metrics Comparison View */}
          {comparisonView === 'metrics' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {comparisonMetrics.map((metric, index) => (
                <div
                  key={index}
                  className="bg-white border border-gray-200 rounded-lg p-4"
                >
                  <h4 className="text-sm font-medium text-gray-500 mb-3">
                    {metric.label}
                  </h4>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-blue-600">Period 1</span>
                      <span className="text-sm font-semibold">
                        {formatValue(metric.period1Value, metric.format)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-green-600">Period 2</span>
                      <span className="text-sm font-semibold">
                        {formatValue(metric.period2Value, metric.format)}
                      </span>
                    </div>
                    
                    <div className="pt-2 border-t border-gray-100">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Change</span>
                        <div className="flex items-center">
                          {metric.change > 0 ? (
                            <ArrowUpIcon className="h-4 w-4 text-green-500 mr-1" />
                          ) : metric.change < 0 ? (
                            <ArrowDownIcon className="h-4 w-4 text-red-500 mr-1" />
                          ) : null}
                          <span
                            className={`text-sm font-bold ${
                              metric.change > 0
                                ? 'text-green-600'
                                : metric.change < 0
                                ? 'text-red-600'
                                : 'text-gray-600'
                            }`}
                          >
                            {metric.change > 0 ? '+' : ''}
                            {metric.change.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Trend Analysis View */}
          {comparisonView === 'trends' && trendChartData && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Trend Comparison
                </h3>
                <p className="text-sm text-gray-500">
                  Compare trends between the two selected periods
                </p>
              </div>
              <LineChart data={trendChartData} height={400} />
            </div>
          )}

          {/* Breakdown View */}
          {comparisonView === 'breakdown' && breakdownChartData && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Metric Breakdown
                </h3>
                <p className="text-sm text-gray-500">
                  Side-by-side comparison of key metrics
                </p>
              </div>
              <BarChart data={breakdownChartData} height={400} />
            </div>
          )}
        </>
      )}

      {/* No data message */}
      {!comparisonData && period1Weeks.length > 0 && period2Weeks.length > 0 && !isLoading && (
        <div className="text-center py-8 text-gray-500">
          <ChartBarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p>Select periods to see comparison</p>
        </div>
      )}
    </div>
  );
};

export default ComparisonPanel;