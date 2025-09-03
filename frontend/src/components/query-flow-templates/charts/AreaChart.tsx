import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type ChartData } from './ChartDataMapper';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface AreaChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const AreaChart: React.FC<AreaChartProps> = ({ chartConfig, data, className = '' }) => {
  const chartData = ChartDataMapper.mapToChartData(data, chartConfig) as ChartData;
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' as const },
      tooltip: {
        mode: 'index' as const,
        intersect: false
      }
    },
    scales: {
      x: { display: true },
      y: { display: true, beginAtZero: true, stacked: true }
    },
    elements: {
      line: { tension: 0.4 },
      point: { radius: 3 }
    },
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default AreaChart;