import React, { useState, useEffect } from 'react';
import { BarChart3, Table, Download, Maximize2, Minimize2 } from 'lucide-react';
import type { QueryFlowTemplate, TemplateChartConfig } from '../../types/queryFlowTemplate';
import ChartRenderer from './charts/ChartRenderer';

interface TemplateResultsViewerProps {
  template: QueryFlowTemplate;
  executionData: {
    results: any[];
    status: string;
    error?: string;
  };
  isLoading?: boolean;
  className?: string;
}

const TemplateResultsViewer: React.FC<TemplateResultsViewerProps> = ({
  template,
  executionData,
  isLoading = false,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [isExpanded, setIsExpanded] = useState(false);

  // Get chart configurations, sorted by order and prioritizing default charts
  const chartConfigs = template.chart_configs?.sort((a, b) => {
    if (a.is_default && !b.is_default) return -1;
    if (!a.is_default && b.is_default) return 1;
    return a.order_index - b.order_index;
  }) || [];

  // Set default active tab
  useEffect(() => {
    if (chartConfigs.length > 0) {
      const defaultChart = chartConfigs.find(c => c.is_default) || chartConfigs[0];
      setActiveTab(defaultChart.chart_name);
    }
  }, [chartConfigs]);

  const handleExportData = () => {
    if (!executionData.results || executionData.results.length === 0) return;

    const csv = [
      // Header row
      Object.keys(executionData.results[0]).join(','),
      // Data rows
      ...executionData.results.map(row =>
        Object.values(row).map(value => `"${String(value).replace(/"/g, '""')}"`).join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${template.name.replace(/\s+/g, '_')}_results.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">
            {executionData.results?.length.toLocaleString() || 0}
          </div>
          <div className="text-sm text-gray-600">Total Records</div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">
            {chartConfigs.length}
          </div>
          <div className="text-sm text-gray-600">Visualizations</div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">
            {executionData.status === 'completed' ? 'Success' : executionData.status}
          </div>
          <div className="text-sm text-gray-600">Status</div>
        </div>
      </div>

      {/* Default Chart Preview */}
      {chartConfigs.length > 0 && executionData.results && executionData.results.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {chartConfigs[0].chart_name}
          </h3>
          <div className="h-64">
            <ChartRenderer
              chartConfig={chartConfigs[0]}
              data={executionData.results}
              isLoading={isLoading}
              error={executionData.error}
            />
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="flex space-x-4">
        <button
          onClick={handleExportData}
          disabled={!executionData.results || executionData.results.length === 0}
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Download className="h-4 w-4" />
          <span>Export Data</span>
        </button>
      </div>
    </div>
  );

  const renderChartTab = (chartConfig: TemplateChartConfig) => (
    <div className="h-96">
      <ChartRenderer
        chartConfig={chartConfig}
        data={executionData.results || []}
        isLoading={isLoading}
        error={executionData.error}
      />
    </div>
  );

  if (executionData.error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 text-red-600 mb-2">
          <BarChart3 className="h-5 w-5" />
          <span className="font-medium">Execution Error</span>
        </div>
        <p className="text-red-700">{executionData.error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${isExpanded ? 'fixed inset-4 z-50' : ''} ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            {template.name} Results
          </h2>
          <p className="text-sm text-gray-600">
            {executionData.results?.length.toLocaleString() || 0} records • {chartConfigs.length} visualizations
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportData}
            disabled={!executionData.results || executionData.results.length === 0}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
          >
            <Download className="h-3 w-3" />
            <span>Export</span>
          </button>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            {isExpanded ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Table className="h-4 w-4" />
              <span>Overview</span>
            </div>
          </button>

          {chartConfigs.map((chartConfig) => (
            <button
              key={chartConfig.chart_name}
              onClick={() => setActiveTab(chartConfig.chart_name)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === chartConfig.chart_name
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>{chartConfig.chart_name}</span>
                {chartConfig.is_default && (
                  <span className="text-xs bg-indigo-100 text-indigo-600 px-1 rounded">
                    Default
                  </span>
                )}
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className={`p-6 ${isExpanded ? 'h-full overflow-y-auto' : ''}`}>
        {activeTab === 'overview' && renderOverviewTab()}
        
        {chartConfigs.map((chartConfig) => (
          activeTab === chartConfig.chart_name && (
            <div key={chartConfig.chart_name}>
              {renderChartTab(chartConfig)}
            </div>
          )
        ))}
      </div>
    </div>
  );
};

export default TemplateResultsViewer;