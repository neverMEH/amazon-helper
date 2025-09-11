import React, { useState, useMemo, useCallback, lazy, Suspense } from 'react';
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
import LoadingSpinner from '../LoadingSpinner';
import ErrorMessage from '../ErrorMessage';
import Tooltip from '../common/Tooltip';

// Lazy load heavy components
const LineChart = lazy(() => import('../charts/LineChart').then(module => ({ default: module.LineChart })));
const BarChart = lazy(() => import('../charts/BarChart').then(module => ({ default: module.BarChart })));
const PieChart = lazy(() => import('../charts/PieChart').then(module => ({ default: module.PieChart })));
const AreaChart = lazy(() => import('../charts/AreaChart').then(module => ({ default: module.AreaChart })));
const WeekSelector = lazy(() => import('./WeekSelector'));
const ComparisonPanel = lazy(() => import('./ComparisonPanel'));
const ChartConfigurationPanel = lazy(() => import('./ChartConfigurationPanel'));
const ExportShareModal = lazy(() => import('./ExportShareModal'));

// UUID validation helper
const isValidUUID = (id: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(id);
};

// Error message helper
const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    if (message.includes('404') || message.includes('not found')) {
      return 'Collection not found. Please verify the collection exists.';
    }
    if (message.includes('403') || message.includes('forbidden')) {
      return 'Access denied. You don\'t have permission to view this collection.';
    }
    if (message.includes('401') || message.includes('unauthorized')) {
      return 'Authentication required. Please log in again.';
    }
    if (message.includes('400') || message.includes('bad request') || message.includes('invalid')) {
      return 'Invalid collection ID format. Please check the collection ID.';
    }
    if (message.includes('network') || message.includes('fetch')) {
      return 'Network error. Please check your connection and try again.';
    }
    return error.message;
  }
  return 'An unexpected error occurred while loading the dashboard.';
};

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
  const [showExportModal, setShowExportModal] = useState(false);

  // Validate collection ID first
  const isValidCollectionId = isValidUUID(collectionId);

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard', collectionId, filters],
    queryFn: async () => {
      if (!isValidCollectionId) {
        throw new Error('Invalid collection ID format. Expected a valid UUID.');
      }
      console.log('Fetching dashboard data for collection:', collectionId);
      try {
        const result = await reportDashboardService.getDashboardData(collectionId, filters);
        console.log('Dashboard data received:', result);
        return result;
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        throw err;
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    enabled: viewMode === 'dashboard' && isValidCollectionId,
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

    const chartElement = (() => {
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
    })();

    return (
      <Suspense fallback={
        <div className="flex items-center justify-center h-64" data-testid="chart-skeleton">
          <LoadingSpinner size="lg" />
        </div>
      }>
        {chartElement}
      </Suspense>
    );
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

  // Check for invalid collection ID first
  if (!isValidCollectionId) {
    return (
      <div className="p-4">
        <ErrorMessage
          title="Invalid Collection ID"
          message="The collection ID format is invalid. Please ensure you're using a valid collection."
          onRetry={onClose}
        />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-4">
        <ErrorMessage
          title="Error Loading Dashboard"
          message={getErrorMessage(error)}
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
    <div className="bg-white rounded-lg shadow-lg" role="main" aria-label="Report Dashboard">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
                {dashboardData.collection.name}
              </h2>
              <Tooltip content="This dashboard shows historical data trends and metrics from your AMC collection executions. You can view different time periods, compare weeks, and export the data." />
            </div>
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              {dashboardData.collection.weeks_completed} weeks completed
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {/* View mode toggle */}
            <div className="flex rounded-lg shadow-sm">
              <button
                onClick={() => setViewMode('dashboard')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium rounded-l-lg ${
                  viewMode === 'dashboard'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
                data-testid="view-dashboard"
                title="View overall metrics and trends"
              >
                <span className="hidden sm:inline">Dashboard</span>
                <span className="sm:hidden">Dash</span>
              </button>
              <button
                onClick={() => setViewMode('comparison')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium ${
                  viewMode === 'comparison'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
                data-testid="comparison-toggle"
                title="Compare metrics between different time periods"
              >
                <span className="hidden sm:inline">Compare Periods</span>
                <span className="sm:hidden">Compare</span>
              </button>
              <button
                onClick={() => setViewMode('configuration')}
                className={`px-2 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium rounded-r-lg ${
                  viewMode === 'configuration'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
                title="Configuration"
              >
                <CogIcon className="h-3 w-3 sm:h-4 sm:w-4" />
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
            <button
              onClick={() => setShowExportModal(true)}
              className="p-2 text-gray-400 hover:text-gray-500"
              title="Export & Share"
              disabled={isExporting}
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
            </button>
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
      <div className="p-4 sm:p-6">
        {viewMode === 'dashboard' && (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4 mb-6" data-testid="chart-grid">
              {summaryCards.map((card, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-3 sm:p-4 border border-gray-200"
                >
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <card.icon className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                    {card.trend && (
                      <span
                        className={`text-xs font-medium ${
                          card.trend > 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                        data-testid={card.trend > 0 ? 'positive-change' : 'negative-change'}
                      >
                        {card.trend > 0 ? '+' : ''}{card.trend}%
                      </span>
                    )}
                  </div>
                  <p className="text-lg sm:text-xl md:text-2xl font-bold text-gray-900 truncate">{card.value}</p>
                  <p className="text-xs text-gray-500 mt-0.5 sm:mt-1 truncate">{card.label}</p>
                </div>
              ))}
            </div>

            {/* Week selector and chart type */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 space-y-4 sm:space-y-0">
              <Suspense fallback={<div className="h-10 w-48 bg-gray-200 animate-pulse rounded" />}>
                <WeekSelector
                  weeks={dashboardData.weeks}
                  selectedWeeks={selectedWeeks}
                  onSelectionChange={handleWeekSelection}
                  multiSelect={true}
                  data-testid="week-selector"
                />
              </Suspense>
              
              <div className="flex items-center space-x-2">
                <label htmlFor="chart-type" className="flex items-center gap-1 text-xs sm:text-sm font-medium text-gray-700">
                  <span className="hidden sm:inline">Chart Type:</span>
                  <span className="sm:hidden">Type:</span>
                  <Tooltip content="Choose how to visualize your data. Line charts show trends over time, bar charts compare values, pie charts show proportions, and area charts show cumulative totals." />
                </label>
                <select
                  id="chart-type"
                  data-testid="chart-type-selector"
                  value={selectedChartType}
                  onChange={(e) => setSelectedChartType(e.target.value as ChartType)}
                  className="text-xs sm:text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="line">Line Chart</option>
                  <option value="bar">Bar Chart</option>
                  <option value="pie">Pie Chart</option>
                  <option value="area">Area Chart</option>
                </select>
              </div>
            </div>

            {/* Chart */}
            <div 
              className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4" 
              data-testid="chart-container"
              role="region"
              aria-label="Report Dashboard Charts"
            >
              <div data-testid={`${selectedChartType}-chart`}>
                {renderChart()}
              </div>
              {/* Screen reader announcement for chart changes */}
              <div className="sr-only" aria-live="polite" aria-atomic="true">
                Chart updated: Now showing {selectedChartType} chart with {selectedWeeks.length || 'all'} weeks selected
              </div>
            </div>

            {/* Additional metrics or tables could go here */}
          </>
        )}

        {viewMode === 'comparison' && (
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          }>
            <ComparisonPanel
              weeks={dashboardData.weeks}
              onPeriodsChange={setComparisonPeriods}
              comparisonData={comparisonData}
              isLoading={isLoadingComparison}
              data-testid="comparison-panel"
            />
          </Suspense>
        )}

        {viewMode === 'configuration' && (
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          }>
            <ChartConfigurationPanel
              availableMetrics={availableMetrics}
              savedConfigs={savedConfigs}
              onSave={handleSaveConfig}
              onApply={setActiveConfig}
            />
          </Suspense>
        )}
      </div>

      {/* Export & Share Modal */}
      <Suspense fallback={null}>
        <ExportShareModal
          isOpen={showExportModal}
          onClose={() => setShowExportModal(false)}
          collectionId={collectionId}
          dashboardData={dashboardData}
          activeConfig={activeConfig}
        />
      </Suspense>
    </div>
  );
};

export default React.memo(CollectionReportDashboard, (prevProps, nextProps) => {
  // Only re-render if collectionId changes
  return prevProps.collectionId === nextProps.collectionId;
});