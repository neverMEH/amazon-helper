import React from 'react';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';

interface HeatmapChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const HeatmapChart: React.FC<HeatmapChartProps> = ({ className = '' }) => {
  // Simplified heatmap implementation - would typically use a library like D3 or recharts
  return (
    <div className={className}>
      <div className="bg-gray-100 p-4 rounded text-center">
        <p className="text-gray-600">Heatmap visualization</p>
        <p className="text-sm text-gray-500 mt-2">
          Advanced heatmap charts require additional visualization libraries
        </p>
      </div>
    </div>
  );
};

export default HeatmapChart;