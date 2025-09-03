import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type ChartData } from './ChartDataMapper';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface BarChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const BarChart: React.FC<BarChartProps> = ({
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
        position: 'top' as const,
        display: chartData.datasets.length > 1
      },
      title: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            
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
            
            return `${label}: ${formattedValue}`;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: !!chartConfig.data_mapping.x_field,
          text: chartConfig.data_mapping.x_field?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        }
      },
      y: {
        display: true,
        title: {
          display: !!chartConfig.data_mapping.y_field,
          text: chartConfig.data_mapping.y_field?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        },
        beginAtZero: true
      }
    },
    // Support horizontal bar charts
    indexAxis: chartConfig.chart_config.indexAxis || 'x',
    // Apply custom chart config options
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Bar data={chartData as any} options={options} />
    </div>
  );
};

export default BarChart;