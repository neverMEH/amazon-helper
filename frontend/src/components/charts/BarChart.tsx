import type { FC } from 'react';
import { Bar } from 'react-chartjs-2';
import type { ChartData, ChartOptions } from 'chart.js';
import { BaseChart, createChartOptions, CHART_COLORS_ARRAY, formatNumber } from './BaseChart';

interface BarChartProps {
  title?: string;
  description?: string;
  data: {
    labels: string[];
    datasets: Array<{
      label: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string | string[];
    }>;
  };
  loading?: boolean;
  error?: string;
  height?: number;
  horizontal?: boolean;
  stacked?: boolean;
  showGrid?: boolean;
  className?: string;
  customOptions?: Partial<ChartOptions<'bar'>>;
}

export const BarChart: FC<BarChartProps> = ({
  title,
  description,
  data,
  loading = false,
  error,
  height = 300,
  horizontal = false,
  stacked = false,
  showGrid = true,
  className = '',
  customOptions = {}
}) => {
  // Prepare chart data with default styling
  const chartData: ChartData<'bar'> = {
    labels: data.labels,
    datasets: data.datasets.map((dataset, index) => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: dataset.backgroundColor || CHART_COLORS_ARRAY[index % CHART_COLORS_ARRAY.length],
      borderColor: dataset.borderColor || CHART_COLORS_ARRAY[index % CHART_COLORS_ARRAY.length],
      borderWidth: 1,
      borderRadius: 4,
      barThickness: 'flex' as const,
      maxBarThickness: 50
    }))
  };

  // Create chart options
  const options = createChartOptions('bar', {
    ...customOptions,
    indexAxis: horizontal ? 'y' as const : 'x' as const,
    scales: {
      x: {
        stacked,
        grid: {
          display: horizontal ? showGrid : false,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          },
          callback: horizontal ? function(value) {
            return formatNumber(value as number);
          } : undefined,
          maxRotation: horizontal ? 0 : 45,
          minRotation: 0
        }
      },
      y: {
        stacked,
        grid: {
          display: horizontal ? false : showGrid,
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          },
          callback: horizontal ? undefined : function(value) {
            return formatNumber(value as number);
          }
        }
      }
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
              const value = horizontal ? context.parsed.x : context.parsed.y;
              label += formatNumber(value);
            }
            return label;
          }
        }
      }
    }
  }) as ChartOptions<'bar'>;

  return (
    <BaseChart
      title={title}
      description={description}
      loading={loading}
      error={error}
      className={className}
    >
      <div style={{ height: `${height}px` }}>
        <Bar data={chartData} options={options} />
      </div>
    </BaseChart>
  );
};

// Grouped Bar Chart variant
interface GroupedBarChartProps extends BarChartProps {
  groupSpacing?: number;
}

export const GroupedBarChart: FC<GroupedBarChartProps> = ({
  groupSpacing = 0.2,
  ...props
}) => {
  const customOptions: Partial<ChartOptions<'bar'>> = {
    ...props.customOptions,
    datasets: {
      bar: {
        categoryPercentage: 1 - groupSpacing,
        barPercentage: 0.9
      }
    }
  };

  return <BarChart {...props} stacked={false} customOptions={customOptions} />;
};