import type { FC } from 'react';
import { Line } from 'react-chartjs-2';
import type { ChartData, ChartOptions } from 'chart.js';
import { BaseChart, createChartOptions, CHART_COLORS_ARRAY, formatNumber } from './BaseChart';

interface LineChartProps {
  title?: string;
  description?: string;
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      borderColor?: string;
      backgroundColor?: string;
      tension?: number;
      fill?: boolean;
    }>;
  };
  loading?: boolean;
  error?: string;
  height?: number;
  showGrid?: boolean;
  timeScale?: boolean;
  stacked?: boolean;
  className?: string;
  customOptions?: Partial<ChartOptions<'line'>>;
}

export const LineChart: FC<LineChartProps> = ({
  title,
  description,
  data,
  loading = false,
  error,
  height = 300,
  showGrid = true,
  timeScale = false,
  stacked = false,
  className = '',
  customOptions = {}
}) => {
  // Prepare chart data with default styling
  const chartData: ChartData<'line'> = {
    labels: data.labels,
    datasets: data.datasets.map((dataset, index) => ({
      label: dataset.label,
      data: dataset.data,
      borderColor: dataset.borderColor || CHART_COLORS_ARRAY[index % CHART_COLORS_ARRAY.length],
      backgroundColor: dataset.backgroundColor || `${CHART_COLORS_ARRAY[index % CHART_COLORS_ARRAY.length]}20`,
      tension: dataset.tension ?? 0.4,
      fill: dataset.fill ?? false,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 2
    }))
  };

  // Create chart options
  const options = createChartOptions('line', {
    ...customOptions,
    scales: {
      x: {
        type: timeScale ? 'time' : 'category',
        time: timeScale ? {
          unit: 'day',
          displayFormats: {
            day: 'MMM dd',
            week: 'MMM dd',
            month: 'MMM yyyy'
          }
        } : undefined,
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          },
          maxRotation: 45,
          minRotation: 0
        }
      },
      y: {
        stacked,
        grid: {
          display: showGrid,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          },
          callback: function(value) {
            return formatNumber(value as number);
          }
        }
      }
    },
    interaction: {
      mode: 'index' as const,
      intersect: false
    },
    plugins: {
      ...customOptions.plugins,
      tooltip: {
        ...customOptions.plugins?.tooltip,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += formatNumber(context.parsed.y);
            }
            return label;
          }
        }
      }
    }
  }) as ChartOptions<'line'>;

  return (
    <BaseChart
      title={title}
      description={description}
      loading={loading}
      error={error}
      className={className}
    >
      <div style={{ height: `${height}px` }}>
        <Line data={chartData} options={options} />
      </div>
    </BaseChart>
  );
};

// Area Chart variant (filled line chart)
interface AreaChartProps extends Omit<LineChartProps, 'data'> {
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      borderColor?: string;
      backgroundColor?: string;
    }>;
  };
}

export const AreaChart: FC<AreaChartProps> = (props) => {
  // Transform data to include fill property
  const areaData = {
    ...props.data,
    datasets: props.data.datasets.map((dataset, index) => ({
      ...dataset,
      fill: true,
      tension: 0.4,
      backgroundColor: dataset.backgroundColor || `${CHART_COLORS_ARRAY[index % CHART_COLORS_ARRAY.length]}30`
    }))
  };

  return <LineChart {...props} data={areaData} />;
};