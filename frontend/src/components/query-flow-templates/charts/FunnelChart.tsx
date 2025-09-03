import React from 'react';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';

interface FunnelChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const FunnelChart: React.FC<FunnelChartProps> = ({ chartConfig, data, className = '' }) => {
  // Simplified funnel implementation
  const processedData = data.map((item, index) => ({
    label: item[chartConfig.data_mapping.x_field!],
    value: item[chartConfig.data_mapping.y_field!],
    percentage: index === 0 ? 100 : (item[chartConfig.data_mapping.y_field!] / data[0][chartConfig.data_mapping.y_field!]) * 100
  }));

  return (
    <div className={className}>
      <div className="space-y-2">
        {processedData.map((item, index) => (
          <div key={index} className="text-center">
            <div 
              className="bg-indigo-500 text-white py-3 rounded"
              style={{ width: `${item.percentage}%`, margin: '0 auto' }}
            >
              <div className="text-sm font-medium">{item.label}</div>
              <div className="text-xs">{item.value.toLocaleString()} ({item.percentage.toFixed(1)}%)</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FunnelChart;