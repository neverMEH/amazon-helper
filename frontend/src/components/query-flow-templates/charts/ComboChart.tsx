import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';
import { Chart } from 'react-chartjs-2';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type ChartData } from './ChartDataMapper';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

interface ComboChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const ComboChart: React.FC<ComboChartProps> = ({ chartConfig, data, className = '' }) => {
  const chartData = ChartDataMapper.mapToChartData(data, chartConfig) as ChartData;
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' as const }
    },
    scales: {
      x: { display: true },
      y: { display: true, beginAtZero: true }
    },
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Chart type="bar" data={chartData as any} options={options} />
    </div>
  );
};

export default ComboChart;