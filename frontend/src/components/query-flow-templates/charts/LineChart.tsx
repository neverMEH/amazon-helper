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

// Register Chart.js components
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

interface LineChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const LineChart: React.FC<LineChartProps> = ({
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
        display: false // We show title in the wrapper
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: function(context: any) {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            
            // Format value based on data mapping
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
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false
    },
    // Apply custom chart config options
    ...chartConfig.chart_config
  };

  return (
    <div className={className}>
      <Line data={chartData as any} options={options} />
    </div>
  );
};

export default LineChart;