import React from 'react';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import LineChart from './LineChart';
import BarChart from './BarChart';
import PieChart from './PieChart';
import TableChart from './TableChart';
import ScatterChart from './ScatterChart';
import HeatmapChart from './HeatmapChart';
import FunnelChart from './FunnelChart';
import AreaChart from './AreaChart';
import ComboChart from './ComboChart';

interface ChartRendererProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  isLoading?: boolean;
  error?: string | null;
  className?: string;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartConfig,
  data,
  isLoading = false,
  error = null,
  className = ''
}) => {
  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 text-center ${className}`}>
        <div className="text-red-600 mb-2">Chart Error</div>
        <div className="text-sm text-red-700">{error}</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-6 text-center ${className}`}>
        <div className="text-gray-600 mb-2">{chartConfig.chart_name}</div>
        <div className="text-sm text-gray-500">No data available</div>
      </div>
    );
  }

  const commonProps = {
    chartConfig,
    data,
    className: 'w-full h-full'
  };

  const renderChart = () => {
    switch (chartConfig.chart_type) {
      case 'line':
        return <LineChart {...commonProps} />;
      case 'bar':
        return <BarChart {...commonProps} />;
      case 'pie':
        return <PieChart {...commonProps} />;
      case 'table':
        return <TableChart {...commonProps} />;
      case 'scatter':
        return <ScatterChart {...commonProps} />;
      case 'heatmap':
        return <HeatmapChart {...commonProps} />;
      case 'funnel':
        return <FunnelChart {...commonProps} />;
      case 'area':
        return <AreaChart {...commonProps} />;
      case 'combo':
        return <ComboChart {...commonProps} />;
      default:
        return (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <div className="text-yellow-600 mb-2">Unsupported Chart Type</div>
            <div className="text-sm text-yellow-700">
              Chart type "{chartConfig.chart_type}" is not yet supported
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* Chart Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">
          {chartConfig.chart_name}
        </h3>
        {chartConfig.chart_config.description && (
          <p className="text-sm text-gray-600 mt-1">
            {chartConfig.chart_config.description}
          </p>
        )}
      </div>

      {/* Chart Content */}
      <div className="p-4">
        <div className="h-96">
          {renderChart()}
        </div>
      </div>
    </div>
  );
};

export default ChartRenderer;