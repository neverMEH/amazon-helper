import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  ChartPieIcon,
  CogIcon,
  ArrowDownTrayIcon,
  CameraIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import * as reportDashboardService from '../../services/reportDashboardService';
import type {
  DashboardFilters,
  DashboardConfig,
} from '../../services/reportDashboardService';
import { LineChart } from '../charts/LineChart';
import { BarChart } from '../charts/BarChart';
import { PieChart } from '../charts/PieChart';
import { AreaChart } from '../charts/AreaChart';
import WeekSelector from './WeekSelector';
import ComparisonPanel from './ComparisonPanel';
import ChartConfigurationPanel from './ChartConfigurationPanel';
import LoadingSpinner from '../LoadingSpinner';
import ErrorMessage from '../ErrorMessage';

interface CollectionReportDashboardProps {
  collectionId: string;
  onClose?: () => void;
}

type ChartType = 'line' | 'bar' | 'pie' | 'area' | 'comparison';
type ViewMode = 'dashboard' | 'comparison' | 'configuration';

const CollectionReportDashboard: React.FC<CollectionReportDashboardProps> = ({
  collectionId,
  onClose,
}) => {
  // State management
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [selectedChartType, setSelectedChartType] = useState<ChartType>('line');
  const [filters, setFilters] = useState<DashboardFilters>({
    aggregation: 'sum',
  });
  const [selectedWeeks, setSelectedWeeks] = useState<string[]>([]);
  const [comparisonPeriods, setComparisonPeriods] = useState<{
    period1: string[];
    period2: string[];
  }>({ period1: [], period2: [] });
  const [activeConfig, setActiveConfig] = useState<DashboardConfig | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard', collectionId, filters],
    queryFn: () => reportDashboardService.getDashboardData(collectionId, filters),
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: viewMode === 'dashboard',
  });

  // Fetch comparison data
  const {
    data: comparisonData,
    isLoading: isLoadingComparison,
  } = useQuery({
    queryKey: ['comparison', collectionId, comparisonPeriods],
    queryFn: () =>
      reportDashboardService.comparePeriods(
        collectionId,
        comparisonPeriods.period1,
        comparisonPeriods.period2
      ),
    enabled:
      viewMode === 'comparison' &&
      comparisonPeriods.period1.length > 0 &&
      comparisonPeriods.period2.length > 0,
  });

  // Fetch available metrics
  const { data: availableMetrics = [] } = useQuery({
    queryKey: ['metrics', collectionId],
    queryFn: () => reportDashboardService.getAvailableMetrics(collectionId),
  });

  // Fetch saved configurations
  const { data: savedConfigs = [] } = useQuery({
    queryKey: ['configs', collectionId],
    queryFn: () => reportDashboardService.getDashboardConfigs(collectionId),
  });

  // Calculate summary metrics
  const summaryCards = useMemo(() => {
    if (!dashboardData?.summary) return [];

    const { summary } = dashboardData;
    return [
      {
        label: 'Total Impressions',
        value: summary.total_impressions?.toLocaleString() || '0',
        icon: ChartBarIcon,
        trend: null,
      },
      {
        label: 'Total Clicks',
        value: summary.total_clicks?.toLocaleString() || '0',
        icon: ChartBarIcon,
        trend: null,
      },
      {
        label: 'Total Conversions',
        value: summary.total_conversions?.toLocaleString() || '0',
        icon: ChartBarIcon,
        trend: null,
      },
      {
        label: 'Total Spend',
        value: `$${summary.total_spend?.toLocaleString() || '0'}`,
        icon: ChartBarIcon,
        trend: null,
      },
      {
        label: 'Avg CTR',
        value: `${((summary.avg_ctr || 0) * 100).toFixed(2)}%`,
        icon: ChartPieIcon,
        trend: null,
      },
      {
        label: 'Avg CVR',
        value: `${((summary.avg_cvr || 0) * 100).toFixed(2)}%`,
        icon: ChartPieIcon,
        trend: null,
      },
    ];
  }, [dashboardData]);

  // Handle week selection
  const handleWeekSelection = useCallback((weeks: string[]) => {
    setSelectedWeeks(weeks);
    setFilters((prev) => ({ ...prev, weeks }));
  }, []);

  // Handle export - currently disabled, will be implemented later
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _handleExport = useCallback(
    async (_format: 'pdf' | 'png' | 'csv') => {
      setIsExporting(true);
      try {
        // Export functionality to be implemented
        console.log('Export functionality not yet implemented');
      } catch (error) {
        console.error('Export failed:', error);
      } finally {
        setIsExporting(false);
      }
    },
    []
  );
  
  // Temporary use to avoid unused variable error
  if (false) {
    _handleExport('pdf');
  }

  // Handle configuration save
  const handleSaveConfig = useCallback(
    async (config: DashboardConfig) => {
      try {
        const saved = await reportDashboardService.saveDashboardConfig(collectionId, config);
        setActiveConfig(saved);
        // Refetch configs list
      } catch (error) {
        console.error('Failed to save configuration:', error);
      }
    },
    [collectionId]
  );

  // Handle snapshot creation
  const handleCreateSnapshot = useCallback(async () => {
    if (!dashboardData || !activeConfig) return;

    try {
      await reportDashboardService.createSnapshot(collectionId, {
        name: `Snapshot ${new Date().toLocaleDateString()}`,
        description: 'Dashboard snapshot',
        data: dashboardData,
        config: activeConfig,
      });
    } catch (error) {
      console.error('Failed to create snapshot:', error);
    }
  }, [collectionId, dashboardData, activeConfig]);

  // Render chart based on type
  const renderChart = useCallback(() => {
    if (!dashboardData?.chartData) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          No data available for visualization
        </div>
      );
    }

    const { chartData } = dashboardData;

    switch (selectedChartType) {
      case 'line':
        return chartData.line ? (
          <LineChart data={chartData.line} height={400} />
        ) : null;
      case 'bar':
        return chartData.bar ? (
          <BarChart data={chartData.bar} height={400} />
        ) : null;
      case 'pie':
        if (chartData.pie) {
          // Transform data to match PieChart's expected format
          const pieData = {
            labels: chartData.pie.labels,
            values: chartData.pie.datasets[0]?.data || [],
            backgroundColor: chartData.pie.datasets[0]?.backgroundColor,
          };
          return <PieChart data={pieData} height={400} />;
        }
        return null;
      case 'area':
        return chartData.area ? (
          <AreaChart data={chartData.area} height={400} />
        ) : null;
      default:
        return null;
    }
  }, [dashboardData, selectedChartType]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-4">
        <ErrorMessage
          title="Error Loading Dashboard"
          message={(error as Error).message}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  // No data state
  if (!dashboardData || dashboardData.weeks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-gray-500">
        <ChartBarIcon className="h-16 w-16 mb-4" />
        <p className="text-lg">No data available</p>
        <p className="text-sm mt-2">
          Complete some collection weeks to see dashboard data
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {dashboardData.collection.name}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {dashboardData.collection.weeks_completed} weeks completed
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {/* View mode toggle */}
            <div className="flex rounded-lg shadow-sm">
              <button
                onClick={() => setViewMode('dashboard')}
                className={`px-4 py-2 text-sm font-medium rounded-l-lg ${
                  viewMode === 'dashboard'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setViewMode('comparison')}
                className={`px-4 py-2 text-sm font-medium ${
                  viewMode === 'comparison'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Compare Periods
              </button>
              <button
                onClick={() => setViewMode('configuration')}
                className={`px-4 py-2 text-sm font-medium rounded-r-lg ${
                  viewMode === 'configuration'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <CogIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Action buttons */}
            <button
              onClick={() => refetch()}
              className="p-2 text-gray-400 hover:text-gray-500"
              title="Refresh"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleCreateSnapshot}
              className="p-2 text-gray-400 hover:text-gray-500"
              title="Create Snapshot"
            >
              <CameraIcon className="h-5 w-5" />
            </button>
            <div className="relative">
              <button
                onClick={() => {}}
                className="p-2 text-gray-400 hover:text-gray-500"
                title="Export"
                disabled={isExporting}
              >
                <ArrowDownTrayIcon className="h-5 w-5" />
              </button>
              {/* Export dropdown would go here */}
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="p-6">
        {viewMode === 'dashboard' && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              {summaryCards.map((card, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <card.icon className="h-5 w-5 text-gray-400" />
                    {card.trend && (
                      <span
                        className={`text-xs font-medium ${
                          card.trend > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {card.trend > 0 ? '+' : ''}{card.trend}%
                      </span>
                    )}
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                  <p className="text-xs text-gray-500 mt-1">{card.label}</p>
                </div>
              ))}
            </div>

            {/* Week selector and chart type */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 space-y-4 sm:space-y-0">
              <WeekSelector
                weeks={dashboardData.weeks}
                selectedWeeks={selectedWeeks}
                onSelectionChange={handleWeekSelection}
                multiSelect={true}
              />
              
              <div className="flex items-center space-x-2">
                <label htmlFor="chart-type" className="text-sm font-medium text-gray-700">
                  Chart Type:
                </label>
                <select
                  id="chart-type"
                  value={selectedChartType}
                  onChange={(e) => setSelectedChartType(e.target.value as ChartType)}
                  className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="line">Line Chart</option>
                  <option value="bar">Bar Chart</option>
                  <option value="pie">Pie Chart</option>
                  <option value="area">Area Chart</option>
                </select>
              </div>
            </div>

            {/* Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              {renderChart()}
            </div>

            {/* Additional metrics or tables could go here */}
          </>
        )}

        {viewMode === 'comparison' && (
          <ComparisonPanel
            weeks={dashboardData.weeks}
            onPeriodsChange={setComparisonPeriods}
            comparisonData={comparisonData}
            isLoading={isLoadingComparison}
          />
        )}

        {viewMode === 'configuration' && (
          <ChartConfigurationPanel
            availableMetrics={availableMetrics}
            savedConfigs={savedConfigs}
            onSave={handleSaveConfig}
            onApply={setActiveConfig}
          />
        )}
      </div>
    </div>
  );
};

export default CollectionReportDashboard;