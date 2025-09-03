import React from 'react';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type ChartData } from './ChartDataMapper';

ChartJS.register(LinearScale, PointElement, Title, Tooltip, Legend);

interface ScatterChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const ScatterChart: React.FC<ScatterChartProps> = ({ chartConfig, data, className = '' }) => {
  const chartData = ChartDataMapper.mapToChartData(data, chartConfig) as ChartData;
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' as const },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: (${context.parsed.x}, ${context.parsed.y})`;
          }
        }
      }
    },
    scales: {
      x: { type: 'linear' as const, position: 'bottom' as const },
      y: { beginAtZero: true }
    },
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Scatter data={chartData} options={options} />
    </div>
  );
};

export default ScatterChart;