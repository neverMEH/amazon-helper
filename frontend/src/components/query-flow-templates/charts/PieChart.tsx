import React from 'react';
import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type ChartData } from './ChartDataMapper';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface PieChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const PieChart: React.FC<PieChartProps> = ({
  chartConfig,
  data,
  className = ''
}) => {
  const chartData = ChartDataMapper.mapToChartData(data, chartConfig) as ChartData;
  
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
        display: true
      },
      title: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            
            const format = chartConfig.data_mapping.value_format;
            let formattedValue = value;
            
            switch (format) {
              case 'currency':
                formattedValue = new Intl.NumberFormat('en-US', { 
                  style: 'currency', 
                  currency: 'USD' 
                }).format(value);
                break;
              case 'percentage':
                formattedValue = `${(value * 100).toFixed(2)}%`;
                break;
              case 'number':
                formattedValue = value.toLocaleString();
                break;
              default:
                formattedValue = value;
            }
            
            return `${label}: ${formattedValue} (${percentage}%)`;
          }
        }
      }
    },
    // Apply custom chart config options
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default PieChart;