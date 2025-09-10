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
  Filler,
  ChartData,
  ChartOptions,
} from 'chart.js';
import BaseChart from './BaseChart';

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

interface AreaChartProps {
  data: ChartData<'line'>;
  title?: string;
  height?: number | string;
  options?: Partial<ChartOptions<'line'>>;
  loading?: boolean;
  error?: string | null;
}

const AreaChart: React.FC<AreaChartProps> = ({
  data,
  title,
  height = 300,
  options = {},
  loading = false,
  error = null,
}) => {
  // Ensure all datasets have fill enabled for area chart
  const areaData = {
    ...data,
    datasets: data.datasets.map((dataset) => ({
      ...dataset,
      fill: dataset.fill !== undefined ? dataset.fill : true,
      tension: dataset.tension !== undefined ? dataset.tension : 0.4,
    })),
  };

  const defaultOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 13,
        },
        bodyFont: {
          size: 12,
        },
        padding: 10,
        displayColors: true,
        callbacks: {
          label: function (context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              // Format based on the data type
              if (context.dataset.label?.toLowerCase().includes('spend') ||
                  context.dataset.label?.toLowerCase().includes('cost') ||
                  context.dataset.label?.toLowerCase().includes('revenue')) {
                label += '$' + context.parsed.y.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                });
              } else if (context.dataset.label?.toLowerCase().includes('rate') ||
                         context.dataset.label?.toLowerCase().includes('ctr') ||
                         context.dataset.label?.toLowerCase().includes('cvr')) {
                label += (context.parsed.y * 100).toFixed(2) + '%';
              } else {
                label += context.parsed.y.toLocaleString();
              }
            }
            return label;
          },
        },
      },
      ...(title && {
        title: {
          display: true,
          text: title,
          font: {
            size: 16,
            weight: 'bold' as const,
          },
          padding: {
            bottom: 20,
          },
        },
      }),
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
          maxRotation: 45,
          minRotation: 0,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          font: {
            size: 11,
          },
          callback: function (value) {
            // Format Y-axis labels
            if (typeof value === 'number') {
              if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M';
              } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K';
              }
              return value.toString();
            }
            return value;
          },
        },
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
  };

  const mergedOptions = {
    ...defaultOptions,
    ...options,
    plugins: {
      ...defaultOptions.plugins,
      ...options.plugins,
    },
    scales: {
      ...defaultOptions.scales,
      ...options.scales,
    },
  };

  return (
    <BaseChart loading={loading} error={error} height={height}>
      <div style={{ height: typeof height === 'number' ? `${height}px` : height }}>
        <Line data={areaData} options={mergedOptions} />
      </div>
    </BaseChart>
  );
};

export default AreaChart;